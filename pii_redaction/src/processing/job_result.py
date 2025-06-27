#!/usr/bin/env python3
"""
Job Result Data Structure
Represents the result of processing a voice metadata file.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class JobResult:
    """Result of processing a voice metadata file."""
    
    # File information
    source_file: str
    dest_file: Optional[str]
    
    # Processing statistics
    total_payloads: int
    processed_payloads: int
    failed_payloads: int
    
    # PII statistics
    total_pii_detected: int
    total_pii_redacted: int
    payloads_with_pii: int
    
    # Timing information
    processing_start: str
    processing_end: str
    processing_time_seconds: float
    
    # Job configuration
    detection_config: Dict[str, Any]
    redaction_config: Dict[str, Any]
    
    # Status and errors
    status: str  # 'success', 'partial', 'failed'
    errors: List[str]
    warnings: List[str]
    
    @classmethod
    def create_success(cls, source_file: str, dest_file: str, 
                      total_payloads: int, total_pii: int, redacted_pii: int,
                      payloads_with_pii: int, processing_time: float,
                      detection_config: Dict[str, Any], redaction_config: Dict[str, Any]) -> 'JobResult':
        """Create a successful job result."""
        return cls(
            source_file=source_file,
            dest_file=dest_file,
            total_payloads=total_payloads,
            processed_payloads=total_payloads,
            failed_payloads=0,
            total_pii_detected=total_pii,
            total_pii_redacted=redacted_pii,
            payloads_with_pii=payloads_with_pii,
            processing_start=datetime.utcnow().isoformat(),
            processing_end=datetime.utcnow().isoformat(),
            processing_time_seconds=processing_time,
            detection_config=detection_config,
            redaction_config=redaction_config,
            status='success',
            errors=[],
            warnings=[]
        )
    
    @classmethod
    def create_failed(cls, source_file: str, error_message: str) -> 'JobResult':
        """Create a failed job result."""
        return cls(
            source_file=source_file,
            dest_file=None,
            total_payloads=0,
            processed_payloads=0,
            failed_payloads=0,
            total_pii_detected=0,
            total_pii_redacted=0,
            payloads_with_pii=0,
            processing_start=datetime.utcnow().isoformat(),
            processing_end=datetime.utcnow().isoformat(),
            processing_time_seconds=0.0,
            detection_config={},
            redaction_config={},
            status='failed',
            errors=[error_message],
            warnings=[]
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the job result."""
        return {
            'status': self.status,
            'file': self.source_file,
            'payloads_processed': self.processed_payloads,
            'pii_detected': self.total_pii_detected,
            'pii_redacted': self.total_pii_redacted,
            'processing_time': f"{self.processing_time_seconds:.2f}s",
            'pii_rate': f"{self.total_pii_detected/self.total_payloads:.2f}" if self.total_payloads > 0 else "0.00"
        }