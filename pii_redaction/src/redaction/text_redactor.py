#!/usr/bin/env python3
"""
Text Redactor - Simplified
Main redaction orchestrator - focused on core redaction logic only.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

# Import detection types
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from detection.pii_entity import PIIEntity

from redaction_strategies import get_strategy, get_available_strategies
from redaction_result import RedactionResult
from redaction_validator import validate_redaction

logger = logging.getLogger(__name__)

class TextRedactor:
    """Main text redaction orchestrator - simplified and focused."""
    
    def __init__(self, strategy_name: str = 'placeholder'):
        """
        Initialize text redactor.
        
        Args:
            strategy_name: Redaction strategy to use
        """
        self.strategy_name = strategy_name
        self.strategy = get_strategy(strategy_name)
        logger.info(f"Initialized TextRedactor with strategy: {strategy_name}")
    
    def redact_text(self, text: str, entities: List[PIIEntity]) -> RedactionResult:
        """
        Redact PII entities from text.
        
        Args:
            text: Original text
            entities: List of detected PII entities
            
        Returns:
            RedactionResult with redacted text and metadata
        """
        if not entities:
            return RedactionResult.create_empty(text, self.strategy_name)
        
        # Sort entities by start position in descending order
        sorted_entities = sorted(entities, key=lambda x: x.start_pos, reverse=True)
        
        redacted_text = text
        redaction_metadata = []
        
        for entity in sorted_entities:
            # Get redaction replacement
            replacement = self.strategy.redact(entity.text, entity.entity_type)
            
            # Replace in text
            redacted_text = (
                redacted_text[:entity.start_pos] + 
                replacement + 
                redacted_text[entity.end_pos:]
            )
            
            # Track redaction metadata
            redaction_metadata.append({
                'original_text': entity.text,
                'entity_type': entity.entity_type,
                'start_pos': entity.start_pos,
                'end_pos': entity.end_pos,
                'replacement': replacement,
                'confidence': entity.confidence,
                'source': entity.source
            })
            
            logger.debug(f"Redacted {entity.entity_type}: '{entity.text}' → '{replacement}'")
        
        result = RedactionResult(
            original_text=text,
            redacted_text=redacted_text,
            entities_redacted=redaction_metadata,
            redaction_count=len(redaction_metadata),
            strategy_used=self.strategy_name,
            redacted_at=datetime.utcnow().isoformat()
        )
        
        logger.info(f"Redacted {len(redaction_metadata)} PII entities")
        return result
    
    def get_redaction_info(self) -> Dict[str, Any]:
        """Get information about current redaction configuration."""
        return {
            'current_strategy': self.strategy_name,
            'available_strategies': get_available_strategies(),
            'strategy_class': self.strategy.__class__.__name__
        }

def test_redactor():
    """Simple test of the redactor."""
    from detection.pii_entity import PIIEntity
    
    # Mock test entities
    test_entities = [
        PIIEntity("john@email.com", "EMAIL", 15, 29, 0.95, "REGEX"),
        PIIEntity("555-123-4567", "PHONE", 45, 57, 0.90, "COMPREHEND")
    ]
    
    test_text = "Email me at john@email.com or call 555-123-4567"
    
    print("🔧 Testing Simple Text Redactor...")
    redactor = TextRedactor('placeholder')
    result = redactor.redact_text(test_text, test_entities)
    
    print(f"Original: {result.original_text}")
    print(f"Redacted: {result.redacted_text}")
    print(f"Count: {result.redaction_count}")
    
    # Test validation
    validation = validate_redaction(result)
    print(f"Valid: {validation['is_valid']}")

if __name__ == "__main__":
    test_redactor()