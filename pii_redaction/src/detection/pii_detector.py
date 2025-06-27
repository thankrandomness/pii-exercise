#!/usr/bin/env python3
"""
Main PII Detector
Combines regex detection with optional AWS Comprehend detection.
"""

import logging
from typing import List, Optional

from pii_entity import PIIEntity
from regex_detector import RegexDetector
from comprehend_detector import ComprehendDetector
from detection_utils import merge_entity_lists

logger = logging.getLogger(__name__)

class PIIDetector:
    """Main PII detector that combines multiple detection methods."""
    
    def __init__(self, use_comprehend: bool = False, cer_endpoint_arn: Optional[str] = None):
        """
        Initialize the PII detector.
        
        Args:
            use_comprehend: Whether to use AWS Comprehend built-in PII detection
            cer_endpoint_arn: Optional CER endpoint ARN for custom entity recognition
        """
        self.regex_detector = RegexDetector()
        self.use_comprehend = use_comprehend
        self.cer_endpoint_arn = cer_endpoint_arn
        
        # Initialize Comprehend detector if requested
        self.comprehend_detector = None
        if use_comprehend:
            self.comprehend_detector = ComprehendDetector()
            if not self.comprehend_detector.is_available():
                logger.warning("Comprehend requested but not available, falling back to regex-only")
                self.use_comprehend = False
    
    def detect_pii(self, text: str) -> List[PIIEntity]:
        """
        Detect PII using all available methods.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected PII entities (deduplicated)
        """
        if not text or not text.strip():
            return []
        
        entity_lists = []
        
        # Always use regex detection
        regex_entities = self.regex_detector.detect(text)
        entity_lists.append(regex_entities)
        logger.debug(f"Regex found {len(regex_entities)} entities")
        
        # Use Comprehend built-in PII detection if available
        if self.use_comprehend and self.comprehend_detector:
            comprehend_entities = self.comprehend_detector.detect_pii(text)
            entity_lists.append(comprehend_entities)
            logger.debug(f"Comprehend found {len(comprehend_entities)} entities")
        
        # Use CER if endpoint provided
        if self.cer_endpoint_arn and self.comprehend_detector:
            cer_entities = self.comprehend_detector.detect_entities_with_cer(
                text, self.cer_endpoint_arn
            )
            entity_lists.append(cer_entities)
            logger.debug(f"CER found {len(cer_entities)} entities")
        
        # Merge all entity lists and deduplicate
        all_entities = merge_entity_lists(*entity_lists)
        
        logger.info(f"Total detected {len(all_entities)} PII entities in text: '{text[:50]}...'")
        return all_entities
    
    def get_detection_info(self) -> dict:
        """Get information about available detection methods."""
        return {
            'regex_available': True,
            'comprehend_available': self.use_comprehend and self.comprehend_detector is not None,
            'cer_endpoint': self.cer_endpoint_arn is not None,
            'detection_methods': self._get_active_methods()
        }
    
    def _get_active_methods(self) -> List[str]:
        """Get list of active detection methods."""
        methods = ['regex']
        if self.use_comprehend and self.comprehend_detector:
            methods.append('comprehend')
        if self.cer_endpoint_arn:
            methods.append('cer')
        return methods
    
    def test_setup(self) -> bool:
        """
        Test that all configured detection methods are working.
        
        Returns:
            True if all methods are working
        """
        logger.info("Testing PII detector setup...")
        
        # Test regex (should always work)
        test_text = "Test email: test@example.com"
        regex_result = self.regex_detector.detect(test_text)
        if not regex_result:
            logger.error("❌ Regex detection test failed")
            return False
        logger.info("✅ Regex detection working")
        
        # Test Comprehend if enabled
        if self.use_comprehend and self.comprehend_detector:
            if not self.comprehend_detector.test_connection():
                logger.error("❌ Comprehend connection test failed")
                return False
        
        logger.info("✅ All detection methods working")
        return True

# Simple test function
def test_detector():
    """Quick test of the detector with different configurations."""
    test_sentences = [
        "It is 10 Test Lane, um, also Test, New York, 14625.",
        "It is my first and last name, testtest@gmail.",
        "My name is John Smith and call me at 555-123-4567."
    ]
    
    print("🔍 Testing Complete PII Detector...")
    print("=" * 50)
    
    # Test with different configurations
    configs = [
        ("Regex Only", PIIDetector(use_comprehend=False)),
        ("Regex + Comprehend", PIIDetector(use_comprehend=True))
    ]
    
    for config_name, detector in configs:
        print(f"\n📋 Configuration: {config_name}")
        print(f"   Detection info: {detector.get_detection_info()}")
        
        for sentence in test_sentences:
            print(f"\n📝 Text: {sentence}")
            entities = detector.detect_pii(sentence)
            
            if entities:
                for entity in entities:
                    print(f"   {entity}")
            else:
                print("   ✅ No PII detected")

if __name__ == "__main__":
    test_detector()