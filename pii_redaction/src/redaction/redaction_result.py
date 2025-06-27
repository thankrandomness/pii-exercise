#!/usr/bin/env python3
"""
Redaction Result Data Structure
Simple dataclass for redaction results.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime

@dataclass
class RedactionResult:
    """Result of redacting text."""
    original_text: str
    redacted_text: str
    entities_redacted: List[Dict[str, Any]]
    redaction_count: int
    strategy_used: str
    redacted_at: str
    
    @classmethod
    def create_empty(cls, text: str, strategy: str) -> 'RedactionResult':
        """Create result for text with no redactions."""
        return cls(
            original_text=text,
            redacted_text=text,
            entities_redacted=[],
            redaction_count=0,
            strategy_used=strategy,
            redacted_at=datetime.utcnow().isoformat()
        )