#!/usr/bin/env python3
"""
Redaction Validation
Simple validation functions for redaction results.
"""

from typing import Dict, Any
from redaction_result import RedactionResult

def validate_redaction(result: RedactionResult) -> Dict[str, Any]:
    """
    Validate that redaction was performed correctly.
    
    Args:
        result: RedactionResult to validate
        
    Returns:
        Validation results
    """
    validation = {
        'is_valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Check that no original PII text remains
    for redaction in result.entities_redacted:
        original_pii = redaction['original_text'].lower()
        redacted_text_lower = result.redacted_text.lower()
        
        if original_pii in redacted_text_lower:
            validation['is_valid'] = False
            validation['errors'].append(
                f"PII text '{redaction['original_text']}' still present in redacted text"
            )
    
    # Check for reasonable length changes
    original_length = len(result.original_text)
    redacted_length = len(result.redacted_text)
    
    if redacted_length > original_length * 1.5:
        validation['warnings'].append(
            f"Redacted text significantly longer than original "
            f"({redacted_length} vs {original_length} chars)"
        )
    
    return validation