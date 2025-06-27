#!/usr/bin/env python3
"""
Payload Processor
Handles voice metadata payload redaction using TextRedactor.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime

# Import detection types
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from detection.pii_entity import PIIEntity

from text_redactor import TextRedactor

logger = logging.getLogger(__name__)

class PayloadProcessor:
    """Processes voice metadata payloads for PII redaction."""
    
    def __init__(self, strategy_name: str = 'placeholder'):
        """
        Initialize payload processor.
        
        Args:
            strategy_name: Redaction strategy to use
        """
        self.redactor = TextRedactor(strategy_name)
        self.pii_fields = ['sentence', 'description', 'notes', 'comments', 'transcript']
    
    def process_payload(self, payload: Dict[str, Any], 
                       entities_by_field: Dict[str, List[PIIEntity]]) -> Dict[str, Any]:
        """
        Process a single voice metadata payload.
        
        Args:
            payload: Original payload
            entities_by_field: PII entities grouped by field name
            
        Returns:
            Redacted payload with metadata
        """
        redacted_payload = payload.copy()
        all_redactions = []
        
        for field_name, entities in entities_by_field.items():
            if self._should_process_field(payload, field_name):
                original_text = payload[field_name]
                
                # Redact the field
                result = self.redactor.redact_text(original_text, entities)
                redacted_payload[field_name] = result.redacted_text
                
                # Add field context to metadata
                for redaction in result.entities_redacted:
                    redaction['field_name'] = field_name
                all_redactions.extend(result.entities_redacted)
        
        # Add payload-level metadata
        if all_redactions:
            redacted_payload['_redaction_metadata'] = {
                'redacted_at': datetime.utcnow().isoformat(),
                'redaction_count': len(all_redactions),
                'strategy_used': self.redactor.strategy_name,
                'redactions': all_redactions
            }
        
        return redacted_payload
    
    def process_multiple_payloads(self, payloads: List[Dict[str, Any]], 
                                 detection_results: List[Dict[str, List[PIIEntity]]]) -> List[Dict[str, Any]]:
        """
        Process multiple payloads efficiently.
        
        Args:
            payloads: List of voice metadata payloads
            detection_results: Detection results for each payload
            
        Returns:
            List of redacted payloads
        """
        redacted_payloads = []
        
        for payload, entities_by_field in zip(payloads, detection_results):
            redacted_payload = self.process_payload(payload, entities_by_field)
            redacted_payloads.append(redacted_payload)
        
        logger.info(f"Processed {len(payloads)} payloads")
        return redacted_payloads
    
    def _should_process_field(self, payload: Dict[str, Any], field_name: str) -> bool:
        """Check if field should be processed."""
        return (field_name in payload and 
                isinstance(payload[field_name], str) and
                payload[field_name].strip())

def test_payload_processor():
    """Test payload processing."""
    from detection.pii_entity import PIIEntity
    
    # Sample payload
    payload = {
        "verbatim_id": 12345,
        "sentence": "Call John Smith at john@email.com",
        "type": "client"
    }
    
    # Mock entities
    entities = [
        PIIEntity("John Smith", "PERSON", 5, 15, 0.9, "COMPREHEND"),
        PIIEntity("john@email.com", "EMAIL", 19, 33, 0.95, "REGEX")
    ]
    
    entities_by_field = {'sentence': entities}
    
    print("🔄 Testing Payload Processor...")
    processor = PayloadProcessor('placeholder')
    result = processor.process_payload(payload, entities_by_field)
    
    print(f"Original: {payload['sentence']}")
    print(f"Redacted: {result['sentence']}")
    print(f"Redaction count: {result['_redaction_metadata']['redaction_count']}")

if __name__ == "__main__":
    test_payload_processor()