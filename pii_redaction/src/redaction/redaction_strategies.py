#!/usr/bin/env python3
"""
Redaction Strategies
Different approaches for redacting PII from text.
Consistent with detection module style - simple and direct.
"""

from abc import ABC, abstractmethod

class RedactionStrategy(ABC):
    """Abstract base class for redaction strategies."""
    
    @abstractmethod
    def redact(self, original_text: str, entity_type: str) -> str:
        """
        Redact PII text using this strategy.
        
        Args:
            original_text: The PII text to redact
            entity_type: Type of PII (EMAIL, PHONE, etc.)
            
        Returns:
            Redacted replacement text
        """
        pass

class PlaceholderStrategy(RedactionStrategy):
    """Replace PII with typed placeholders like [REDACTED_EMAIL]."""
    
    def __init__(self):
        self.placeholders = {
            'EMAIL': '[REDACTED_EMAIL]',
            'PHONE': '[REDACTED_PHONE]',
            'PERSON': '[REDACTED_PERSON]',
            'SSN': '[REDACTED_SSN]',
            'ADDRESS': '[REDACTED_ADDRESS]',
            'ZIP_CODE': '[REDACTED_ZIP]',
            'CREDIT_CARD': '[REDACTED_CREDIT_CARD]',
            'CUSTOMER_ACCOUNT': '[REDACTED_ACCOUNT]',
            'NAME': '[REDACTED_NAME]',
            'OTHER': '[REDACTED]'
        }
    
    def redact(self, original_text: str, entity_type: str) -> str:
        return self.placeholders.get(entity_type, '[REDACTED]')

class MaskStrategy(RedactionStrategy):
    """Mask PII by showing first/last characters with asterisks."""
    
    def redact(self, original_text: str, entity_type: str) -> str:
        text = original_text.strip()
        
        if len(text) <= 2:
            return '*' * len(text)
        elif len(text) <= 4:
            return text[0] + '*' * (len(text) - 2) + text[-1]
        else:
            # Show first 2 and last 1 character for longer text
            middle_length = len(text) - 3
            return text[:2] + '*' * middle_length + text[-1]

class RemoveStrategy(RedactionStrategy):
    """Completely remove PII from text."""
    
    def redact(self, original_text: str, entity_type: str) -> str:
        return ''

class HashStrategy(RedactionStrategy):
    """Replace PII with a consistent hash."""
    
    def __init__(self):
        self.hash_cache = {}
    
    def redact(self, original_text: str, entity_type: str) -> str:
        # Use cached hash for consistency
        if original_text in self.hash_cache:
            return self.hash_cache[original_text]
        
        import hashlib
        hash_obj = hashlib.md5(original_text.encode())
        hash_str = hash_obj.hexdigest()[:8]  # Use first 8 characters
        redacted = f"[{entity_type}_{hash_str}]"
        
        self.hash_cache[original_text] = redacted
        return redacted

class PartialStrategy(RedactionStrategy):
    """Keep some characters visible based on PII type."""
    
    def redact(self, original_text: str, entity_type: str) -> str:
        text = original_text.strip()
        
        if entity_type == 'EMAIL':
            # Show domain but mask username
            if '@' in text:
                username, domain = text.split('@', 1)
                masked_username = username[0] + '*' * (len(username) - 1) if username else '*'
                return f"{masked_username}@{domain}"
            return self._default_mask(text)
        
        elif entity_type == 'PHONE':
            # Show last 4 digits
            digits_only = ''.join(filter(str.isdigit, text))
            if len(digits_only) >= 4:
                return f"***-***-{digits_only[-4:]}"
            return self._default_mask(text)
        
        elif entity_type == 'CREDIT_CARD':
            # Show last 4 digits
            digits_only = ''.join(filter(str.isdigit, text))
            if len(digits_only) >= 4:
                return f"****-****-****-{digits_only[-4:]}"
            return self._default_mask(text)
        
        else:
            return self._default_mask(text)
    
    def _default_mask(self, text: str) -> str:
        """Default masking for unknown types."""
        if len(text) <= 2:
            return '*' * len(text)
        return text[0] + '*' * (len(text) - 2) + text[-1]

# Strategy registry (simple dictionary)
STRATEGIES = {
    'placeholder': PlaceholderStrategy,
    'mask': MaskStrategy,
    'remove': RemoveStrategy,
    'hash': HashStrategy,
    'partial': PartialStrategy
}

def get_strategy(strategy_name: str) -> RedactionStrategy:
    """
    Get a redaction strategy by name.
    
    Args:
        strategy_name: Name of the strategy
        
    Returns:
        RedactionStrategy instance
        
    Raises:
        ValueError: If strategy name is not recognized
    """
    if strategy_name not in STRATEGIES:
        available = list(STRATEGIES.keys())
        raise ValueError(f"Unknown strategy '{strategy_name}'. Available: {available}")
    
    return STRATEGIES[strategy_name]()

def get_available_strategies() -> list:
    """Get list of available redaction strategy names."""
    return list(STRATEGIES.keys())