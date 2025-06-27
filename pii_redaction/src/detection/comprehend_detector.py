#!/usr/bin/env python3
"""
AWS Comprehend PII Detector
Handles PII detection using AWS Comprehend services.
"""

import logging
from typing import List, Optional

from pii_entity import PIIEntity

logger = logging.getLogger(__name__)

class ComprehendDetector:
    """Detects PII using AWS Comprehend services."""
    
    def __init__(self, region_name: str = 'us-east-1'):
        """
        Initialize Comprehend detector.
        
        Args:
            region_name: AWS region for Comprehend client
        """
        self.region_name = region_name
        self.comprehend_client = self._init_client()
    
    def _init_client(self):
        """Initialize AWS Comprehend client."""
        try:
            import boto3
            client = boto3.client('comprehend', region_name=self.region_name)
            logger.info("✅ AWS Comprehend client initialized")
            return client
        except ImportError:
            logger.warning("⚠️  boto3 not installed, Comprehend detection unavailable")
            return None
        except Exception as e:
            logger.warning(f"⚠️  Failed to initialize Comprehend: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if Comprehend detection is available."""
        return self.comprehend_client is not None
    
    def detect_pii(self, text: str) -> List[PIIEntity]:
        """
        Detect PII using Comprehend's built-in PII detection.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected PII entities
        """
        if not self.comprehend_client:
            logger.debug("Comprehend client not available")
            return []
        
        if not text or not text.strip():
            return []
        
        entities = []
        
        try:
            response = self.comprehend_client.detect_pii_entities(
                Text=text,
                LanguageCode='en'
            )
            
            for entity in response.get('Entities', []):
                pii_entity = PIIEntity(
                    text=text[entity['BeginOffset']:entity['EndOffset']],
                    entity_type=entity['Type'],
                    start_pos=entity['BeginOffset'],
                    end_pos=entity['EndOffset'],
                    confidence=entity['Score'],
                    source='COMPREHEND'
                )
                entities.append(pii_entity)
            
            logger.debug(f"Comprehend detected {len(entities)} entities")
            
        except Exception as e:
            logger.warning(f"Comprehend PII detection failed: {e}")
        
        return entities
    
    def detect_entities_with_cer(self, text: str, cer_endpoint_arn: str) -> List[PIIEntity]:
        """
        Detect entities using a Custom Entity Recognizer endpoint.
        
        Args:
            text: Text to analyze
            cer_endpoint_arn: ARN of the CER endpoint
            
        Returns:
            List of detected entities
        """
        if not self.comprehend_client:
            logger.debug("Comprehend client not available")
            return []
        
        if not text or not text.strip():
            return []
        
        entities = []
        
        try:
            response = self.comprehend_client.detect_entities(
                Text=text,
                LanguageCode='en',
                EndpointArn=cer_endpoint_arn
            )
            
            for entity in response.get('Entities', []):
                pii_entity = PIIEntity(
                    text=text[entity['BeginOffset']:entity['EndOffset']],
                    entity_type=entity['Type'],
                    start_pos=entity['BeginOffset'],
                    end_pos=entity['EndOffset'],
                    confidence=entity['Score'],
                    source='CER'
                )
                entities.append(pii_entity)
            
            logger.debug(f"CER detected {len(entities)} entities")
            
        except Exception as e:
            logger.warning(f"CER detection failed: {e}")
        
        return entities
    
    def test_connection(self) -> bool:
        """
        Test connection to AWS Comprehend.
        
        Returns:
            True if connection successful
        """
        if not self.comprehend_client:
            return False
        
        try:
            # Simple test with minimal text
            self.comprehend_client.detect_pii_entities(
                Text="test",
                LanguageCode='en'
            )
            logger.info("✅ Comprehend connection test successful")
            return True
        except Exception as e:
            logger.warning(f"❌ Comprehend connection test failed: {e}")
            return False