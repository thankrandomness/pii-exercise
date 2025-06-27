#!/usr/bin/env python3
"""
PII Entity Data Structure
Simple dataclass to represent detected PII entities.
"""

from dataclasses import dataclass

@dataclass
class PIIEntity:
    """Represents a detected PII entity."""
    text: str           # The actual PII text found
    entity_type: str    # Type: EMAIL, PHONE, ADDRESS, etc.
    start_pos: int      # Start position in original text
    end_pos: int        # End position in original text
    confidence: float   # Confidence score (0.0 to 1.0)
    source: str         # Detection source: 'REGEX' or 'COMPREHEND'
    
    def __str__(self):
        return f"{self.entity_type}: '{self.text}' [{self.start_pos}:{self.end_pos}] ({self.confidence:.2f})"