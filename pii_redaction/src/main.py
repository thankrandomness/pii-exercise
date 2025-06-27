#!/usr/bin/env python3
"""
PII Redaction System - Main Entry Point
Complete voice metadata PII detection and redaction system.
"""

import argparse
import logging
import sys
import time
from typing import Dict, Any

# Import all modules
from src.detection import PIIDetector
from src.redaction import TextRedactor
from src.processing import BatchOrchestrator, JobResult

def setup_logging(verbose: bool = False):
    """Configure logging for the application."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def create_config_from_args(args) -> tuple:
    """Create detection and redaction configs from command line arguments."""
    
    detection_config = {
        'use_comprehend': args.use_comprehend,
        'cer_endpoint_arn': args.cer_endpoint
    }
    
    redaction_config = {
        'strategy': args.strategy
    }
    
    return detection_config, redaction_config

def validate_file_paths(input_file: str, output_file: str = None):
    """Validate input and output file paths."""
    import os
    
    # Check input file exists
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Check input file is readable
    if not os.access(input_file, os.R_OK):
        raise PermissionError(f"Cannot read input file: {input_file}")
    
    # Check output directory is writable (if output file specified)
    if output_file:
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

def print_job_summary(result: JobResult):
    """Print a detailed job summary."""
    print("\n" + "="*60)
    print("🎯 PII REDACTION JOB SUMMARY")
    print("="*60)
    
    print(f"📁 Source File: {result.source_file}")
    if result.dest_file:
        print(f"📁 Output File: {result.dest_file}")
    
    print(f"\n📊 Processing Results:")
    print(f"   Status: {'✅ SUCCESS' if result.status == 'success' else '❌ FAILED'}")
    print(f"   Total Payloads: {result.total_payloads}")
    print(f"   Processed Successfully: {result.processed_payloads}")
    
    if result.failed_payloads > 0:
        print(f"   Failed Payloads: {result.failed_payloads}")
    
    print(f"\n🔍 PII Detection:")
    print(f"   Total PII Detected: {result.total_pii_detected}")
    print(f"   Payloads with PII: {result.payloads_with_pii}")
    if result.total_payloads > 0:
        pii_rate = (result.total_pii_detected / result.total_payloads)
        print(f"   PII Rate: {pii_rate:.2f} entities per payload")
    
    print(f"\n🔧 Redaction:")
    print(f"   PII Redacted: {result.total_pii_redacted}")
    print(f"   Strategy Used: {result.redaction_config.get('current_strategy', 'unknown')}")
    
    print(f"\n⏱️  Performance:")
    print(f"   Processing Time: {result.processing_time_seconds:.2f} seconds")
    if result.total_payloads > 0:
        rate = result.total_payloads / result.processing_time_seconds
        print(f"   Processing Rate: {rate:.1f} payloads/second")
    
    if result.warnings:
        print(f"\n⚠️  Warnings:")
        for warning in result.warnings:
            print(f"   • {warning}")
    
    if result.errors:
        print(f"\n❌ Errors:")
        for error in result.errors:
            print(f"   • {error}")
    
    print("="*60)

def run_test_mode():
    """Run in test mode with sample data."""
    print("🧪 Running in TEST MODE with sample data...")
    
    # Create sample test data
    sample_data = [
        {
            "verbatim_id": 1,
            "sentence": "Customer John Smith called from john.smith@email.com",
            "type": "client",
            "call_id": 12345
        },
        {
            "verbatim_id": 2,
            "sentence": "Please call me back at 555-123-4567 or (555) 987-6543",
            "type": "agent",
            "call_id": 12345
        },
        {
            "verbatim_id": 3,
            "sentence": "My address is 123 Main Street, Springfield, IL 62701",
            "type": "client", 
            "call_id": 12345
        },
        {
            "verbatim_id": 4,
            "sentence": "Thank you for your help today",
            "type": "client",
            "call_id": 12345
        }
    ]
    
    # Save test data
    import json
    test_input = "test_sample.json"
    test_output = "test_sample_redacted.json"
    
    with open(test_input, 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print(f"Created test input file: {test_input}")
    print(f"Processing with placeholder strategy...")
    
    # Process with orchestrator
    orchestrator = BatchOrchestrator(
        detection_config={'use_comprehend': False},
        redaction_config={'strategy': 'placeholder'}
    )
    
    result = orchestrator.process_file(test_input, test_output)
    
    # Show results
    print_job_summary(result)
    
    # Show sample output
    if result.status == 'success':
        print(f"\n📋 Sample redacted output:")
        with open(test_output, 'r') as f:
            output_data = json.load(f)
        
        for payload in output_data[:2]:  # Show first 2 payloads
            print(f"   Original: {sample_data[payload['verbatim_id']-1]['sentence']}")
            print(f"   Redacted: {payload['sentence']}")
            print()
    
    # Cleanup
    import os
    os.remove(test_input)
    if os.path.exists(test_output):
        os.remove(test_output)

def main():
    """Main entry point for the PII redaction system."""
    parser = argparse.ArgumentParser(
        description='PII Redaction System for Voice Metadata',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with local detection
  python main.py --input data/voice_metadata.json --output data/redacted.json
  
  # With AWS Comprehend
  python main.py --input data/voice_metadata.json --output data/redacted.json --use-comprehend
  
  # With custom redaction strategy
  python main.py --input data/voice_metadata.json --output data/redacted.json --strategy mask
  
  # Test mode with sample data
  python main.py --test
        """
    )
    
    # Input/Output arguments
    parser.add_argument('--input', '-i', help='Input JSON file path')
    parser.add_argument('--output', '-o', help='Output JSON file path (optional)')
    
    # Detection configuration
    parser.add_argument('--use-comprehend', action='store_true',
                       help='Use AWS Comprehend for PII detection')
    parser.add_argument('--cer-endpoint', 
                       help='Custom Entity Recognizer endpoint ARN')
    
    # Redaction configuration
    parser.add_argument('--strategy', default='placeholder',
                       choices=['placeholder', 'mask', 'partial', 'remove', 'hash'],
                       help='Redaction strategy (default: placeholder)')
    
    # Utility arguments
    parser.add_argument('--test', action='store_true',
                       help='Run test mode with sample data')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--dry-run', action='store_true',
                       help='Process file but do not save output')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Handle test mode
        if args.test:
            run_test_mode()
            return 0
        
        # Validate required arguments
        if not args.input:
            parser.error("--input is required (or use --test for test mode)")
        
        # Validate file paths
        output_file = None if args.dry_run else args.output
        validate_file_paths(args.input, output_file)
        
        # Create configurations
        detection_config, redaction_config = create_config_from_args(args)
        
        # Initialize orchestrator
        logger.info("🚀 Initializing PII Redaction System...")
        orchestrator = BatchOrchestrator(detection_config, redaction_config)
        
        # Log configuration
        logger.info(f"📁 Input file: {args.input}")
        logger.info(f"📁 Output file: {output_file or 'None (dry run)'}")
        logger.info(f"🔍 Detection: {'Comprehend + Regex' if args.use_comprehend else 'Regex only'}")
        logger.info(f"🔧 Redaction strategy: {args.strategy}")
        
        # Process file
        logger.info("⚡ Starting file processing...")
        start_time = time.time()
        
        result = orchestrator.process_file(args.input, output_file)
        
        total_time = time.time() - start_time
        logger.info(f"🏁 Processing completed in {total_time:.2f} seconds")
        
        # Display results
        print_job_summary(result)
        
        # Return appropriate exit code
        return 0 if result.status == 'success' else 1
        
    except KeyboardInterrupt:
        print("\n❌ Processing interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())