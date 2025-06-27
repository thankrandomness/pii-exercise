# PII Redaction System for Voice Metadata

A comprehensive, modular system for detecting and redacting personally identifiable information (PII) from voice call metadata. Combines regex patterns, AWS Comprehend, and Custom Entity Recognition for maximum accuracy.

## Project Structure

```
pii-redaction-system/
├── main.py                          # Main entry point
├── README.md                        # This file
├── requirements.txt                 # Python dependencies
├── src/
│   ├── detection/                   # PII Detection Module
│   │   ├── README.md               # Detection module docs
│   │   ├── pii_entity.py           # PIIEntity data structure
│   │   ├── pii_patterns.py         # Regex patterns library
│   │   ├── regex_detector.py       # Pattern-based detection
│   │   ├── comprehend_detector.py  # AWS Comprehend integration
│   │   ├── utils.py               # Helper functions
│   │   └── pii_detector.py        # Main detector (hybrid)
│   │
│   ├── redaction/                   # PII Redaction Module
│   │   ├── README.md               # Redaction module docs
│   │   ├── redaction_result.py     # RedactionResult data structure
│   │   ├── redaction_strategies.py # 5 redaction strategies
│   │   ├── redaction_validator.py  # Validation functions
│   │   ├── text_redactor.py        # Core redaction logic
│   │   └── payload_processor.py    # Voice metadata processing
│   │
│   └── processing/                  # File Processing & Orchestration
│       ├── job_result.py           # Job result data structure
│       ├── payload_processor.py    # Individual payload coordination
│       ├── file_processor.py       # File-level operations
│       └── batch_orchestrator.py   # Main job orchestrator
```

## Core Concepts

### 1. Hybrid PII Detection

The system uses **three detection methods** combined for maximum accuracy:

```python
# Detection pipeline combines:
PIIDetector = RegexDetector + ComprehendDetector + CustomEntityRecognizer
               ↓               ↓                    ↓
            Fast/Offline    High Accuracy      Voice-Specific
            Standard PII    AWS Maintained     Custom Patterns
```

**Detection Flow:**
1. **Regex Detection** - Fast pattern matching for standard PII (emails, phones, SSNs)
2. **AWS Comprehend** - Cloud-based detection for names, addresses, etc.
3. **Custom Entity Recognizer** - Domain-specific patterns trained on voice data
4. **Deduplication** - Merge results, keeping highest confidence detections

### 2. Flexible Redaction Strategies

Five redaction strategies for different use cases:

| Strategy | Input | Output | Use Case |
|----------|-------|--------|----------|
| **placeholder** | `john@email.com` | `[REDACTED_EMAIL]` | Audit trails, clear labeling |
| **mask** | `john@email.com` | `jo***@email.com` | Partial visibility |
| **partial** | `555-123-4567` | `***-***-4567` | Context-aware (keep last 4) |
| **remove** | `john@email.com` | _(removed)_ | Minimal output |
| **hash** | `john@email.com` | `[EMAIL_a1b2c3d4]` | Consistent anonymization |

### 3. Voice Metadata Processing

**Input Format** (Voice Call Transcripts):
```json
{
  "verbatim_id": 294150667,
  "type": "client",
  "language": "english", 
  "sentence": "It is 10 Test Lane, um, also Test, New York, 14625.",
  "call_id": 36367033071,
  "call_date": "2025-06-21T16:17:36.000Z",
  "attributes": {
    "userid": "736fd238-dc26-4720-b0e8-3bba4f3a4e51",
    "employee_id": "12345"
  }
}
```

**Output Format** (Redacted + Metadata):
```json
{
  "verbatim_id": 294150667,
  "type": "client", 
  "language": "english",
  "sentence": "It is [REDACTED_ADDRESS], um, also Test, New York, [REDACTED_ZIP].",
  "call_id": 36367033071,
  "call_date": "2025-06-21T16:17:36.000Z",
  "attributes": { ... },
  "_redaction_metadata": {
    "redacted_at": "2025-06-27T10:30:00Z",
    "redaction_count": 2,
    "strategy_used": "placeholder",
    "redactions": [
      {
        "original_text": "10 Test Lane",
        "entity_type": "ADDRESS",
        "replacement": "[REDACTED_ADDRESS]",
        "confidence": 0.92,
        "source": "COMPREHEND"
      }
    ]
  }
}
```

## Detailed Flow Walkthrough

### Step 1: File Loading (`FileProcessor`)
```python
# Load voice metadata JSON file
payloads = load_json_file("voice_metadata.json")  # List of 15,000+ payloads
```

### Step 2: Individual Payload Processing (`PayloadProcessor`)
```python
for payload in payloads:
    # Extract text from PII-sensitive fields
    sentence = payload["sentence"]  # Main content field
    
    # Step 2a: PII Detection (Detection Module)
    entities = detector.detect_pii(sentence)
    # Returns: [PIIEntity("10 Test Lane", "ADDRESS", 6, 18, 0.92, "COMPREHEND")]
    
    # Step 2b: PII Redaction (Redaction Module)  
    result = redactor.redact_text(sentence, entities)
    # Returns: RedactionResult with redacted text and metadata
    
    # Step 2c: Update Payload
    payload["sentence"] = result.redacted_text
    payload["_redaction_metadata"] = result.metadata
```

### Step 3: File Output & Statistics (`JobResult`)
```python
# Save redacted payloads to output file
save_json_file(redacted_payloads, "redacted_metadata.json")

# Generate comprehensive statistics
job_result = JobResult(
    total_payloads=15000,
    total_pii_detected=3247,
    processing_time_seconds=45.2,
    status="success"
)
```