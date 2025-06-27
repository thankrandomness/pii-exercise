#!/usr/bin/env python3
"""
File Processor
Handles processing of complete voice metadata JSON files.
Manages file I/O and coordinates payload processing.
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from payload_processor import PayloadProcessor
from job_result import JobResult

logger = logging.getLogger(__name__)

class FileProcessor:
    """Processes complete voice metadata JSON files."""
    
    def __init__(self, payload_processor: PayloadProcessor):
        """
        Initialize file processor.
        
        Args:
            payload_processor: PayloadProcessor instance for individual payloads
        """
        self.payload_processor = payload_processor
    
    def process_file(self, input_file_path: str, output_file_path: Optional[str] = None) -> JobResult:
        """
        Process a complete voice metadata JSON file.
        
        Args:
            input_file_path: Path to input JSON file
            output_file_path: Path to output file (optional)
            
        Returns:
            JobResult with processing statistics and results
        """
        start_time = time.time()
        
        try:
            # Step 1: Load the input file
            logger.info(f"Loading file: {input_file_path}")
            payloads = self._load_json_file(input_file_path)
            
            if not payloads:
                return JobResult.create_failed(input_file_path, "No payloads found in file")
            
            logger.info(f"Loaded {len(payloads)} payloads")
            
            # Step 2: Process all payloads
            logger.info("Processing payloads for PII detection and redaction...")
            redacted_payloads, stats_list = self.payload_processor.process_multiple_payloads(payloads)
            
            # Step 3: Calculate processing statistics
            processing_stats = self._calculate_processing_stats(stats_list)
            
            # Step 4: Save the output file (if path provided)
            if output_file_path:
                logger.info(f"Saving redacted file: {output_file_path}")
                self._save_json_file(redacted_payloads, output_file_path)
            
            # Step 5: Create job result
            processing_time = time.time() - start_time
            
            job_result = JobResult.create_success(
                source_file=input_file_path,
                dest_file=output_file_path,
                total_payloads=len(payloads),
                total_pii=processing_stats['total_pii_detected'],
                redacted_pii=processing_stats['total_pii_redacted'],
                payloads_with_pii=processing_stats['payloads_with_pii'],
                processing_time=processing_time,
                detection_config=self.payload_processor.detector.get_detection_info(),
                redaction_config=self.payload_processor.redactor.get_redaction_info()
            )
            
            # Add any warnings
            if processing_stats['failed_payloads'] > 0:
                job_result.warnings.append(f"{processing_stats['failed_payloads']} payloads failed to process")
            
            logger.info(f"File processing completed successfully in {processing_time:.2f} seconds")
            return job_result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"File processing failed after {processing_time:.2f} seconds: {str(e)}")
            return JobResult.create_failed(input_file_path, str(e))
    
    def _load_json_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Load and parse JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Handle different JSON formats
            data = json.loads(content)
            
            # Convert single payload to list
            if isinstance(data, dict):
                return [data]
            elif isinstance(data, list):
                return data
            else:
                raise ValueError(f"Unexpected JSON format: {type(data)}")
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except FileNotFoundError:
            raise ValueError(f"File not found: {file_path}")
        except Exception as e:
            raise ValueError(f"Error reading file: {str(e)}")
    
    def _save_json_file(self, data: List[Dict[str, Any]], file_path: str):
        """Save data as JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ValueError(f"Error writing file: {str(e)}")
    
    def _calculate_processing_stats(self, stats_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall processing statistics."""
        total_pii_detected = sum(stats.get('pii_detected', 0) for stats in stats_list)
        failed_payloads = sum(1 for stats in stats_list if stats.get('status') == 'failed')
        payloads_with_pii = sum(1 for stats in stats_list if stats.get('pii_detected', 0) > 0)
        
        return {
            'total_pii_detected': total_pii_detected,
            'total_pii_redacted': total_pii_detected,  # Assume all detected PII is redacted
            'failed_payloads': failed_payloads,
            'payloads_with_pii': payloads_with_pii
        }
    
    def process_file_in_place(self, file_path: str) -> JobResult:
        """Process file and overwrite with redacted version."""
        backup_path = f"{file_path}.backup"
        
        # Create backup
        import shutil
        shutil.copy2(file_path, backup_path)
        
        try:
            result = self.process_file(file_path, file_path)
            if result.status == 'success':
                # Remove backup on success
                import os
                os.remove(backup_path)
            return result
        except Exception as e:
            # Restore backup on failure
            shutil.move(backup_path, file_path)
            raise

def test_file_processor():
    """Test the file processor with sample data."""
    
    # Create sample data file
    sample_data = [
        {
            "verbatim_id": 1,
            "sentence": "Customer John Smith called from john@email.com",
            "type": "client"
        },
        {
            "verbatim_id": 2,
            "sentence": "Please call back at 555-123-4567",
            "type": "agent"
        },
        {
            "verbatim_id": 3,
            "sentence": "Thank you for your help",
            "type": "client"
        }
    ]
    
    # Save sample data
    input_file = "test_input.json"
    output_file = "test_output.json"
    
    with open(input_file, 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print("🔄 Testing File Processor...")
    
    # Initialize components
    from detection import PIIDetector
    from redaction import TextRedactor
    
    detector = PIIDetector(use_comprehend=False)
    redactor = TextRedactor('placeholder')
    payload_processor = PayloadProcessor(detector, redactor)
    file_processor = FileProcessor(payload_processor)
    
    # Process file
    result = file_processor.process_file(input_file, output_file)
    
    print(f"Processing result: {result.get_summary()}")
    
    # Clean up
    import os
    if os.path.exists(input_file):
        os.remove(input_file)
    if os.path.exists(output_file):
        os.remove(output_file)

if __name__ == "__main__":
    test_file_processor()