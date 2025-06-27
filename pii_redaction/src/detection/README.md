# PII Detection Module

Hybrid PII detection system combining regex patterns, AWS Comprehend, and Custom Entity Recognition (CER) for voice metadata processing.

## Control Flow

### 1. Detection Pipeline
```
Input Text → PIIDetector.detect_pii()
    ↓
┌─────────────────────────────────────────┐
│  PARALLEL DETECTION                     │
│  ┌─────────────┬─────────────┬─────────┐│
│  │   Regex     │ Comprehend  │   CER   ││
│  │ Patterns    │  Built-in   │ Custom  ││
│  │  (local)    │   (AWS)     │ (AWS)   ││
│  └─────────────┴─────────────┴─────────┘│
│               ↓                         │
│  merge_entity_lists() → deduplicate     │
└─────────────────────────────────────────┘
    ↓
List[PIIEntity] (final result)
```

### 2. Detection Methods

| Method | Purpose | Speed | Accuracy | Coverage |
|--------|---------|-------|----------|----------|
| **Regex** | Standard patterns | Fast | Medium | EMAIL, PHONE, SSN, ADDRESS |
| **Comprehend** | AWS built-in PII | Medium | High | PERSON, ADDRESS, PHONE, etc. |
| **CER** | Voice-specific | Medium | High* | ACCOUNT_ID, CUSTOMER_TYPE, etc. |

*CER accuracy depends on training data quality

### 3. Step-by-Step Flow

**Input**: `"Customer John Smith called about Rochester account, phone 555-123-4567"`

```python
# Step 1: Regex Detection
regex_entities = [
    PIIEntity("555-123-4567", "PHONE", 63, 75, 0.8, "REGEX")
]

# Step 2: Comprehend Built-in  
comprehend_entities = [
    PIIEntity("John Smith", "PERSON", 9, 19, 0.95, "COMPREHEND"),
    PIIEntity("555-123-4567", "PHONE", 63, 75, 0.99, "COMPREHEND")  # Higher confidence
]

# Step 3: CER Custom Detection
cer_entities = [
    PIIEntity("Rochester account", "CUSTOMER_ACCOUNT", 32, 48, 0.88, "CER")
]

# Step 4: Merge & Deduplicate (utils.py)
final_entities = [
    PIIEntity("John Smith", "PERSON", 9, 19, 0.95, "COMPREHEND"),
    PIIEntity("Rochester account", "CUSTOMER_ACCOUNT", 32, 48, 0.88, "CER"),
    PIIEntity("555-123-4567", "PHONE", 63, 75, 0.99, "COMPREHEND")  # Kept highest confidence
]
```

## Module Structure

```
detection/
├── pii_entity.py           # PIIEntity data structure
├── pii_patterns.py         # Regex patterns library  
├── regex_detector.py       # Pattern-based detection
├── comprehend_detector.py  # AWS Comprehend integration
├── utils.py               # Merge & deduplication logic
└── pii_detector.py        # Main orchestrator (entry point)
```

## Core Data Structure

```python
@dataclass
class PIIEntity:
    text: str           # "john@email.com"
    entity_type: str    # "EMAIL" 
    start_pos: int      # 15
    end_pos: int        # 29
    confidence: float   # 0.95
    source: str         # "REGEX" | "COMPREHEND" | "CER"
```
