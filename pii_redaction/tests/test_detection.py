#!/usr/bin/env python3
"""
Test PII detection with real data from TestUseCase_TestFile.json
"""

import json
import os
import sys
from pathlib import Path

# Add src to Python path so we can import our modules
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from ..src.detection.pii_detector import PIIDetector

def load_test_file():
    """Load the real test file from tests/data/input/."""
    
    # Get the path to the test file
    test_file_path = Path(__file__).parent / 'data' / 'input' / 'TestUseCase_TestFile.json'
    
    if not test_file_path.exists():
        print(f"❌ Test file not found at: {test_file_path}")
        print("Please save TestUseCase_TestFile.json in tests/data/input/")
        return []
    
    print(f"📁 Loading test data from: {test_file_path}")
    
    payloads = []
    try:
        with open(test_file_path, 'r') as f:
            content = f.read().strip()
            
            # Try to parse as JSON array first
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    payloads = data
                    print("✅ Loaded as JSON array")
                else:
                    payloads = [data]
                    print("✅ Loaded as single JSON object")
            except json.JSONDecodeError:
                # Fall back to JSONL format (one JSON per line)
                print("📝 Trying JSONL format...")
                for line_num, line in enumerate(content.split('\n'), 1):
                    line = line.strip()
                    if line:  # Skip empty lines
                        try:
                            payload = json.loads(line)
                            payloads.append(payload)
                        except json.JSONDecodeError as e:
                            print(f"⚠️  Error parsing line {line_num}: {e}")
                            continue
        
        print(f"✅ Loaded {len(payloads)} payloads from test file")
        return payloads
        
    except Exception as e:
        print(f"❌ Error reading test file: {e}")
        return []

def test_with_real_data():
    """Test detection with the actual voice metadata from the test file."""
    
    print("🔍 Testing PII Detection with Real Voice Metadata")
    print("=" * 60)
    
    # Load the actual test file
    payloads = load_test_file()
    
    if not payloads:
        print("❌ No test data loaded, exiting...")
        return
    
    # Initialize detector (regex-only for local testing)
    print("\n🔧 Initializing PII Detector...")
    detector = PIIDetector(use_comprehend=False)
    
    # Test detector setup
    if not detector.test_setup():
        print("❌ Detector setup failed!")
        return
    
    print(f"\n📋 Detection Configuration:")
    detection_info = detector.get_detection_info()
    for key, value in detection_info.items():
        print(f"   • {key}: {value}")
    
    print(f"\n📝 Processing {len(payloads)} voice metadata payloads...")
    print("-" * 60)
    
    total_entities = 0
    payloads_with_pii = 0
    
    for i, payload in enumerate(payloads, 1):
        verbatim_id = payload.get('verbatim_id', f'unknown_{i}')
        sentence = payload.get('sentence', '')
        
        # Show first 60 chars of sentence for readability
        sentence_preview = sentence[:60] + "..." if len(sentence) > 60 else sentence
        print(f"\n🎤 Payload {verbatim_id}: \"{sentence_preview}\"")
        
        # Detect PII in the sentence
        entities = detector.detect_pii(sentence)
        
        if entities:
            print(f"   🚨 Found {len(entities)} PII entities:")
            for entity in entities:
                print(f"      • {entity.entity_type}: '{entity.text}' "
                      f"[pos {entity.start_pos}:{entity.end_pos}] "
                      f"(confidence: {entity.confidence:.2f}, source: {entity.source})")
            total_entities += len(entities)
            payloads_with_pii += 1
        else:
            print("   ✅ No PII detected (clean)")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Detection Summary:")
    print(f"   • Total payloads processed: {len(payloads)}")
    print(f"   • Payloads with PII: {payloads_with_pii}")
    print(f"   • Clean payloads: {len(payloads) - payloads_with_pii}")
    print(f"   • Total PII entities found: {total_entities}")
    print(f"   • Average entities per payload: {total_entities/len(payloads):.2f}")
    print(f"   • PII detection rate: {payloads_with_pii/len(payloads)*100:.1f}%")
    
    # Show which types of PII were found
    if total_entities > 0:
        entity_types = {}
        for payload in payloads:
            entities = detector.detect_pii(payload.get('sentence', ''))
            for entity in entities:
                entity_types[entity.entity_type] = entity_types.get(entity.entity_type, 0) + 1
        
        print(f"\n📈 PII Types Detected:")
        for pii_type, count in sorted(entity_types.items()):
            print(f"   • {pii_type}: {count} occurrences")
    
    print("\n✅ PII detection test completed!")

if __name__ == "__main__":
    test_with_real_data()