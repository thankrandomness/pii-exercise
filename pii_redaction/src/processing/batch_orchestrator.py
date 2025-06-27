#!/usr/bin/env python3
"""
Batch Orchestrator
Main job coordinator that manages the complete PII redaction workflow.
This is the entry point for batch job execution.
"""

import logging
import argparse
import time
from typing import Dict, Any, Optional
from datetime import datetime

# Import all processing components
from detection import PIIDetector
from redaction import TextRedactor
from payload_processor import PayloadProcessor
from file_processor import FileProcessor
from job_result import JobResult

logger = logging.getLogger(__name__)

class BatchOrchestrator:
    """Main orchestrator for PII redaction batch jobs."""
    
    def __init__(self, detection_config: Dict[str, Any] = None, 
                 redaction_config: Dict[str, Any] = None):
        """
        Initialize batch orchestrator.
        
        Args:
            detection_config: Configuration for PII detection
            redaction_config: Configuration for PII redaction
        """
        # Default configurations
        self.detection_config = detection_config or {
            'use_comprehend': False,
            'cer_endpoint_arn': None
        }
        
        self.redaction_config = redaction_config or {
            'strategy': 'placeholder'
        }
        
        # Initialize components
        self.detector = self._create_detector()
        self.redactor = self._create_redactor()
        self.payload_processor = PayloadProcessor(self.detector, self.redactor)
        self.file_processor = FileProcessor(self.payload_processor)
        
        logger.info("BatchOrchestrator initialized successfully")
    
    def process_file(self, input_file: str, output_file: str = None) -> JobResult:
        """
        Process a single voice metadata file.
        
        Args:
            input_file: Path to input JSON file
            output_file: Path to output file (optional)
            
        Returns:
            JobResult with processing results
        """
        logger.info(f"Starting batch job for file: {input_file}")
        
        # Validate setup
        if not self._validate_setup():
            return JobResult.create_failed(input_file, "Setup validation failed")
        
        # Process the file
        result = self.file_processor.process_file(input_file, output_file)
        
        # Log results
        self._log_job_results(result)
        
        return result
    
    def process_multiple_files(self, file_pairs: list) -> list:
        """
        Process multiple files in sequence.
        
        Args:
            file_pairs: List of (input_file, output_file) tuples
            
        Returns:
            List of JobResult objects
        """
        results = []
        
        logger.info(f"Starting batch processing for {len(file_pairs)} files")
        
        for input_file, output_file in file_pairs:
            result = self.process_file(input_file, output_file)
            results.append(result)
        
        # Log overall results
        self._log_batch_results(results)
        
        return results
    
    def _create_detector(self) -> PIIDetector:
        """Create and configure PII detector."""
        return PIIDetector(
            use_comprehend=self.detection_config.get('use_comprehend', False),
            cer_endpoint_arn=self.detection_config.get('cer_endpoint_arn')
        )
    
    def _create_redactor(self) -> TextRedactor:
        """Create and configure text redactor."""
        return TextRedactor(
            strategy_name=self.redaction_config.get('strategy', 'placeholder')
        )
    
    def _validate_setup(self) -> bool:
        """Validate that all components are properly configured."""
        try:
            # Test detector
            test_result = self.detector.detect_pii("test text")
            logger.debug("✅ Detector validation passed")
            
            # Test redactor
            redactor_info = self.redactor.get_redaction_info()
            logger.debug("✅ Redactor validation passed")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup validation failed: {str(e)}")
            return False
    
    def _log_job_results(self, result: JobResult):
        """Log the results of a job."""
        if result.status == 'success':
            logger.info(f"✅ Job completed successfully:")
            logger.info(f"   Processed: {result.processed_payloads} payloads")
            logger.info(f"   PII detected: {result.total_pii_detected}")
            logger.info(f"   PII redacted: {result.total_pii_redacted}")
            logger.info(f"   Processing time: {result.processing_time_seconds:.2f}s")
        else:
            logger.error(f"❌ Job failed:")
            logger.error(f"   File: {result.source_file}")
            logger.error(f"   Errors: {result.errors}")
    
    def _log_batch_results(self, results: list):
        """Log the results of batch processing."""
        successful = [r for r in results if r.status == 'success']
        failed = [r for r in results if r.status == 'failed']
        
        total_payloads = sum(r.processed_payloads for r in successful)
        total_pii = sum(r.total_pii_detected for r in successful)
        
        logger.info(f"📊 Batch processing summary:")
        logger.info(f"   Files processed: {len(successful)}/{len(results)}")
        logger.info(f"   Total payloads: {total_payloads}")
        logger.info(f"   Total PII detected: {total_pii}")
        
        if failed:
            logger.warning(f"   Failed files: {len(failed)}")
    
    def get_orchestrator_info(self) -> Dict[str, Any]:
        """Get information about the orchestrator configuration."""
        return {
            'detection_config': self.detection_config,
            'redaction_config': self.redaction_config,
            'detector_info': self.detector.get_detection_info(),
            'redactor_info': self.redactor.get_redaction_info()
        }

def main():
    """Main entry point for batch job execution."""
    parser = argparse.ArgumentParser(description='PII Redaction Batch Job')
    parser.add_argument('--input', required=True, help='Input JSON file path')
    parser.add_argument('--output', help='Output JSON file path (optional)')
    parser.add_argument('--strategy', default='placeholder', 
                       choices=['placeholder', 'mask', 'partial', 'remove', 'hash'],
                       help='Redaction strategy')
    parser.add_argument('--use-comprehend', action='store_true', 
                       help='Use AWS Comprehend for detection')
    parser.add_argument('--cer-endpoint', help='CER endpoint ARN for custom detection')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create configuration
    detection_config = {
        'use_comprehend': args.use_comprehend,
        'cer_endpoint_arn': args.cer_endpoint
    }
    
    redaction_config = {
        'strategy': args.strategy
    }
    
    # Initialize orchestrator
    orchestrator = BatchOrchestrator(detection_config, redaction_config)
    
    # Log configuration
    logger.info("🚀 Starting PII Redaction Batch Job")
    logger.info(f"   Input file: {args.input}")
    logger.info(f"   Output file: {args.output or 'None (dry run)'}")
    logger.info(f"   Detection: {'Comprehend + Regex' if args.use_comprehend else 'Regex only'}")
    logger.info(f"   Redaction strategy: {args.strategy}")
    
    # Process file
    start_time = time.time()
    result = orchestrator.process_file(args.input, args.output)
    total_time = time.time() - start_time
    
    # Final summary
    logger.info(f"🏁 Batch job completed in {total_time:.2f} seconds")
    print(f"\nJob Summary: {result.get_summary()}")
    
    # Exit with appropriate code
    exit(0 if result.status == 'success' else 1)

if __name__ == "__main__":
    main()