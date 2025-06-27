#!/usr/bin/env python3
"""
Payload Processor
Handles processing of individual voice metadata payloads.
Coordinates detection and redaction for single payloads.
"""

import logging
from typing import Dict, List, Any, Tuple

# Import detection and redaction modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from detection import PIIDetector, PIIEntity
from redaction import TextRedactor, RedactionResult

logger = logging.getLogger(__name__)

class PayloadProcessor:
    """Processes individual voice metadata payloads through detection and redaction."""
    
    def __init__(self, detector: PIIDetector, redactor: TextRedactor):
        """
        Initialize payload processor.
        
        Args:
            detector: PIIDetector instance for PII detection
            redactor: TextRedactor instance for PII redaction
        """
        self.detector = detector
        self.redactor = redactor
        self.pii_fields = ['sentence', 'description', 'notes', 'comments', 'transcript']
        
    def process_payload(self, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Process a single voice metadata payload.
        
        Args:
            payload: Voice metadata payload
            
        Returns:
            Tuple of (redacted_payload, processing_stats)
        """
        try:
            # Step 1: Detect PII in all relevant fields
            entities_by_field = {}
            total_entities = 0
            
            for field_name in self.pii_fields:
                if self._should_process_field(payload, field_name):
                    text = payload[field_name]
                    entities = self.detector.detect_pii(text)
                    
                    if entities:
                        entities_by_field[field_name] = entities
                        total_entities += len(entities)
                        logger.debug(f"Found {len(entities)} PII entities in field '{field_name}'")
            
            # Step 2: Redact PII from the payload
            if entities_by_field:
                redacted_payload = self._redact_payload_fields(payload, entities_by_field)
            else:
                redacted_payload = payload.copy()
            
            # Step 3: Create processing statistics
            processing_stats = {
                'payload_id': payload.get('verbatim_id', 'unknown'),
                'pii_detected': total_entities,
                'fields_with_pii': list(entities_by_field.keys()),
                'status': 'success'
            }
            
            return redacted_payload, processing_stats
            
        except Exception as e:
            logger.error(f"Error processing payload {payload.get('verbatim_id', 'unknown')}: {str(e)}")
            
            # Return original payload and error stats
            processing_stats = {
                'payload_id': payload.get('verbatim_id', 'unknown'),
                'pii_detected': 0,
                'fields_with_pii': [],
                'status': 'failed',
                'error': str(e)
            }
            
            return payload, processing_stats
    
    def process_multiple_payloads(self, payloads: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process multiple payloads efficiently.
        
        Args:
            payloads: List of voice metadata payloads
            
        Returns:
            Tuple of (redacted_payloads, processing_stats_list)
        """
        redacted_payloads = []
        processing_stats_list = []
        
        for payload in payloads:
            redacted_payload, stats = self.process_payload(payload)
            redacted_payloads.append(redacted_payload)
            processing_stats_list.append(stats)
        
        logger.info(f"Processed {len(payloads)} payloads")
        return redacted_payloads, processing_stats_list
    
    def _should_process_field(self, payload: Dict[str, Any], field_name: str) -> bool:
        """Check if field should be processed for PII."""
        return (field_name in payload and 
                isinstance(payload[field_name], str) and
                payload[field_name].strip())
    
    def _redact_payload_fields(self, payload: Dict[str, Any], 
                              entities_by_field: Dict[str, List[PIIEntity]]) -> Dict[str, Any]:
        """Redact PII from payload fields."""
        redacted_payload = payload.copy()
        all_redactions = []
        
        for field_name, entities in entities_by_field.items():
            original_text = payload[field_name]
            
            # Redact the field
            redaction_result = self.redactor.redact_text(original_text, entities)
            redacted_payload[field_name] = redaction_result.redacted_text
            
            # Add field context to metadata
            for redaction in redaction_result.entities_redacted:
                redaction['field_name'] = field_name
            all_redactions.extend(redaction_result.entities_redacted)
        
        # Add overall redaction metadata to payload
        if all_redactions:
            redacted_payload['_redaction_metadata'] = {
                'redacted_at': redaction_result.redacted_at,
                'redaction_count': len(all_redactions),
                'strategy_used': self.redactor.strategy_name,
                'redactions': all_redactions
            }
        
        return redacted_payload
    
    def get_processor_info(self) -> Dict[str, Any]:
        """Get information about the processor configuration."""
        return {
            'detection_config': self.detector.get_detection_info(),
            'redaction_config': self.redactor.get_redaction_info(),
            'pii_fields': self.pii_fields
        }

def test_payload_processor():
    """Test the payload processor."""
    
    # Sample payload
    payload = {
        "verbatim_id": 12345,
        "sentence": "Customer John Smith called from john@email.com",
        "type": "client",
        "call_id": 98765
    }
    
    print("🔄 Testing Payload Processor...")
    print(f"Original payload: {payload}")
    
    # Initialize components
    detector = PIIDetector(use_comprehend=False)
    redactor = TextRedactor('placeholder')
    processor = PayloadProcessor(detector, redactor)
    
    # Process payload
    redacted_payload, stats = processor.process_payload(payload)
    
    print(f"\nRedacted payload: {redacted_payload}")
    print(f"Processing stats: {stats}")
    
    # Show processor info
    info = processor.get_processor_info()
    print(f"\nProcessor config: {info}")

if __name__ == "__main__":
    test_payload_processor()