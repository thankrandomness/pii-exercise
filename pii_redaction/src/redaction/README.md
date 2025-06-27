# PII Redaction Module

Text redaction system that replaces detected PII entities with safe alternatives using multiple redaction strategies for voice metadata processing.

## Quick Start

```python
from redaction import TextRedactor, PayloadProcessor

# Basic text redaction
redactor = TextRedactor('placeholder')
result = redactor.redact_text("Call John at 555-1234", detected_entities)

# Voice metadata processing
processor = PayloadProcessor('mask')
redacted_payload = processor.process_payload(payload, entities_by_field)
```

## Control Flow

### 1. Redaction Pipeline
```
Detected PIIEntities → TextRedactor → RedactionStrategy → RedactedText + Metadata
        ↓                   ↓              ↓                    ↓
   [EMAIL entity]    Choose Strategy   Apply Strategy      "Contact [REDACTED_EMAIL]"
   [PHONE entity]    (placeholder)     (replacement)       "Call [REDACTED_PHONE]"
        ↓                   ↓              ↓                    ↓
   RedactionResult ← validate_redaction ← Position-aware   ← Sort by position
                                         replacement
```

### 2. Redaction Strategies

| Strategy | Example Input | Example Output | Use Case |
|----------|---------------|----------------|----------|
| **placeholder** | `john@email.com` | `[REDACTED_EMAIL]` | Clear labeling, audit trails |
| **mask** | `john@email.com` | `jo***@email.com` | Partial visibility |
| **partial** | `john@email.com` | `j***@email.com` | Domain-aware masking |
| **remove** | `john@email.com` | _(removed)_ | Minimal text |
| **hash** | `john@email.com` | `[EMAIL_a1b2c3d4]` | Consistent anonymization |

### 3. Step-by-Step Flow

**Input**: Detected entities + `"Call John Smith at john@email.com or 555-123-4567"`

```python
# Step 1: Sort entities by position (reverse order to avoid shifts)
sorted_entities = [
    PIIEntity("555-123-4567", "PHONE", 43, 55, 0.99, "COMPREHEND"),  # Process last
    PIIEntity("john@email.com", "EMAIL", 26, 40, 0.95, "REGEX"),      # Process middle  
    PIIEntity("John Smith", "PERSON", 5, 15, 0.88, "CER")            # Process first
]

# Step 2: Apply redaction strategy to each entity
redacted_text = "Call John Smith at john@email.com or 555-123-4567"
# → "Call [REDACTED_PERSON] at john@email.com or 555-123-4567"
# → "Call [REDACTED_PERSON] at [REDACTED_EMAIL] or 555-123-4567"  
# → "Call [REDACTED_PERSON] at [REDACTED_EMAIL] or [REDACTED_PHONE]"

# Step 3: Create RedactionResult with metadata
result = RedactionResult(
    original_text="Call John Smith at john@email.com or 555-123-4567",
    redacted_text="Call [REDACTED_PERSON] at [REDACTED_EMAIL] or [REDACTED_PHONE]",
    redaction_count=3,
    entities_redacted=[...metadata...]
)
```

## Module Structure

```
redaction/
├── redaction_result.py         # RedactionResult data structure
├── redaction_strategies.py     # 5 redaction strategy implementations  
├── redaction_validator.py      # Validation functions
├── text_redactor.py           # Core text redaction logic
└── payload_processor.py       # Voice metadata payload processing
```

## Core Components

### TextRedactor (Main Entry Point)
```python
redactor = TextRedactor('placeholder')
result = redactor.redact_text(text, entities) → RedactionResult
redactor.get_redaction_info() → dict
```

### PayloadProcessor (Voice Metadata)
```python
processor = PayloadProcessor('mask')
redacted_payload = processor.process_payload(payload, entities_by_field) → dict
redacted_list = processor.process_multiple_payloads(payloads, results) → list
```

### RedactionResult (Data Structure)
```python
@dataclass
class RedactionResult:
    original_text: str              # "Call John at 555-1234"
    redacted_text: str              # "Call [REDACTED_PERSON] at [REDACTED_PHONE]"
    entities_redacted: List[dict]   # Detailed redaction metadata
    redaction_count: int            # 2
    strategy_used: str              # "placeholder"
    redacted_at: str               # ISO timestamp
```

## Configuration

```python
# Strategy selection
redactor = TextRedactor('placeholder')  # Labeled placeholders
redactor = TextRedactor('mask')         # Masked with asterisks  
redactor = TextRedactor('partial')      # Context-aware masking
redactor = TextRedactor('remove')       # Complete removal
redactor = TextRedactor('hash')         # Consistent hashing

# Voice metadata processing
processor = PayloadProcessor('mask')    # Uses TextRedactor internally
```
