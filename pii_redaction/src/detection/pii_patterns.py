#!/usr/bin/env python3
"""
PII Regex Patterns
Centralized collection of regex patterns for detecting different types of PII.
"""

# Regex patterns for common PII types
PII_PATTERNS = {
    'EMAIL': [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\b'  # Partial emails like "testtest@gmail"
    ],
    
    'PHONE': [
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 555-123-4567 or 5551234567
        r'\(\d{3}\)\s*\d{3}[-.]?\d{4}\b',  # (555) 123-4567
        r'\b\d{3}\s+\d{3}\s+\d{4}\b'      # 555 123 4567
    ],
    
    'SSN': [
        r'\b\d{3}[-]?\d{2}[-]?\d{4}\b'     # 123-45-6789 or 123456789
    ],
    
    'ZIP_CODE': [
        r'\b\d{5}(?:-\d{4})?\b'            # 12345 or 12345-6789
    ],
    
    'ADDRESS': [
        # Street addresses like "10 Test Lane"
        r'\b\d+\s+[A-Za-z\s]+(Street|St|Lane|Ln|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Circle|Cir|Court|Ct)\b',
        # City, State patterns like "Test, New York"
        r'\b[A-Za-z\s]+,\s+[A-Za-z\s]+(?:,\s+\d{5})?\b'
    ],
    
    'CREDIT_CARD': [
        r'\b(?:\d{4}[-\s]?){3}\d{4}\b'     # 4444-4444-4444-4444
    ],
    
    'NAME': [
        # Look for "my name is" patterns
        r'(?:my name is|I am|I\'m)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        # Look for "first and last name" context
        r'(?:first and last name[,\s]+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
    ]
}

# Known false positives to filter out
FALSE_POSITIVES = {
    'EMAIL': ['@gmail', '@yahoo', '@hotmail'],  # Incomplete emails
    'NAME': ['Test', 'test', 'My Name', 'Last Name'],  # Generic terms
    'ADDRESS': ['New York', 'Test Lane']  # Too generic
}

def get_patterns_for_type(entity_type: str):
    """Get regex patterns for a specific PII type."""
    return PII_PATTERNS.get(entity_type, [])

def get_all_pattern_types():
    """Get list of all supported PII types."""
    return list(PII_PATTERNS.keys())

def is_false_positive(entity_type: str, text: str) -> bool:
    """Check if detected text is a known false positive."""
    if entity_type in FALSE_POSITIVES:
        return text.lower() in [fp.lower() for fp in FALSE_POSITIVES[entity_type]]
    return False