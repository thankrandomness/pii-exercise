#!/usr/bin/env python3
"""
Regex-based PII Detector
Uses regex patterns to detect PII in text.
"""

import re
import logging
from typing import List

from pii_entity import PIIEntity
from pii_patterns import PII_PATTERNS, is_false_positive

logger = logging.getLogger(__name__)

class RegexDetector:
    """Detects PII using regex patterns."""
    
    def __init__(self, confidence_score: float = 0.8):
        """
        Initialize regex detector.
        
        Args:
            confidence_score: Default confidence score for regex matches
        """
        self.confidence_score = confidence_score
    
    def detect(self, text: str) -> List[PIIEntity]:
        """
        Detect PII in text using regex patterns.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected PII entities
        """
        if not text or not text.strip():
            return []
        
        entities = []
        
        for entity_type, patterns in PII_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    entity = self._create_entity_from_match(
                        match, entity_type, text
                    )
                    
                    if entity and self._is_valid_entity(entity):
                        entities.append(entity)
        
        logger.debug(f"Regex detected {len(entities)} entities")
        return entities
    
    def _create_entity_from_match(self, match, entity_type: str, text: str) -> PIIEntity:
        """Create PIIEntity from regex match."""
        # For NAME patterns with groups, extract the captured group
        if entity_type == 'NAME' and match.groups():
            matched_text = match.group(1)
            start_pos = match.start(1)
            end_pos = match.end(1)
        else:
            matched_text = match.group(0)
            start_pos = match.start()
            end_pos = match.end()
        
        return PIIEntity(
            text=matched_text,
            entity_type=entity_type,
            start_pos=start_pos,
            end_pos=end_pos,
            confidence=self.confidence_score,
            source='REGEX'
        )
    
    def _is_valid_entity(self, entity: PIIEntity) -> bool:
        """Validate detected entity."""
        # Skip very short matches
        if len(entity.text.strip()) < 2:
            return False
        
        # Check against known false positives
        if is_false_positive(entity.entity_type, entity.text):
            return False
        
        return True