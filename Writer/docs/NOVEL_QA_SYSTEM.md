# Novel QA System Documentation

Industrial-grade quality assurance system for AI-generated novel content, providing comprehensive validation, auto-fixing, and manual review capabilities.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Validators](#validators)
   - [CharacterProfileManager](#characterprofilemanager)
   - [TimelineValidator](#timelinevalidator)
   - [ReferenceValidator](#referencevalidator)
   - [HallucinationDetector](#hallucinationdetector)
   - [ChapterTransitionChecker](#chaptertransitionchecker)
4. [Integration](#integration)
   - [ValidationOrchestrator](#validationorchestrator)
   - [AutoFixer](#autofixer)
5. [Manual Review](#manual-review)
6. [Performance](#performance)
   - [ValidationMetrics](#validationmetrics)
   - [PerformanceBenchmark](#performancebenchmark)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### Purpose

The Novel QA System ensures consistency and quality in AI-generated novel content by detecting and fixing issues across multiple dimensions:

- **Character Consistency**: Characters don't act after death, have impossible timelines, or contradict established traits
- **Timeline Integrity**: Events occur in logical temporal order without paradoxes
- **Reference Validation**: Statements about past events have supporting evidence in the narrative
- **Hallucination Detection**: Content doesn't invent facts contradicting established world-building
- **Chapter Transitions**: Narrative continuity is maintained between chapters

### Goals

1. Catch 95%+ of consistency errors before publication
2. Provide actionable fix suggestions with confidence scores
3. Enable iterative auto-fixing with up to 3 repair attempts
4. Escalate high-confidence issues for human review
5. Maintain performance under 5 seconds per chapter validation

### Key Features

- **Parallel Validation**: Multiple validators run concurrently for performance
- **Confidence Scoring**: Every issue has a confidence score (0.0-1.0) for prioritization
- **Low-Confidence Flagging**: Items below threshold (default 0.7) flagged for manual review
- **Iterative Repair**: Auto-fix loop with verification after each attempt
- **Comprehensive Reporting**: Detailed validation reports with suggestions

---

## Architecture

### Four-Wave Validation Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         WAVE 1: CHARACTER                                │
│  CharacterProfileManager: Track character states, detect conflicts      │
│  - Multiple deaths detection                                             │
│  - Actions after death                                                   │
│  - Timeline paradoxes (birth after death)                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          WAVE 2: TIMELINE                                │
│  TimelineValidator: Validate temporal consistency                        │
│  - Event ordering validation                                             │
│  - Interval warnings (too fast/slow pacing)                             │
│  - Character timeline conflicts                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        WAVE 3: REFERENCE                                 │
│  ReferenceValidator + HallucinationDetector                             │
│  - Verify citations against knowledge graph                              │
│  - Detect hallucinated quotes and facts                                  │
│  - Vector similarity checking                                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       WAVE 4: TRANSITION                                 │
│  ChapterTransitionChecker: Detect narrative discontinuities             │
│  - Unresolved suspense detection                                         │
│  - Scene jump detection                                                  │
│  - Missing transition markers                                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATION LAYER                                  │
│  ValidationOrchestrator: Aggregate results, manage parallel execution   │
│  AutoFixer: Iterative repair with LLM regeneration                      │
│  ManualReviewAPI: Human-in-the-loop for edge cases                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Input**: Chapter content, world context, previous chapter content
2. **Validation**: Parallel execution of all configured validators
3. **Aggregation**: ValidationOrchestrator combines results into ValidationResult
4. **Fix Decision**: Issues categorized by severity and confidence
5. **Auto-Fix Loop**: High-confidence issues sent to AutoFixer (max 3 iterations)
6. **Manual Review**: Low-confidence or unfixable issues escalated
7. **Output**: Validated/fixed content with comprehensive report

---

## Validators

### CharacterProfileManager

Manages character profiles with timeline tracking and conflict detection.

**Location**: `src/novel/character_profile.py`

**Key Classes**:
- `CharacterProfile`: Complete character profile with timeline and relationships
- `CharacterTimelineEvent`: Single event in character's timeline
- `TimelineConflict`: Detected conflict between timeline events

**Detection Capabilities**:
- Multiple deaths (character dies more than once)
- Actions after confirmed death
- Temporal paradoxes (birth chapter after death chapter)
- Duplicate major events (same injury twice)
- Status inconsistencies

**Usage Example**:

```python
from src.novel.character_profile import CharacterProfileManager, CharacterTimelineEvent, EventType

# Initialize manager
manager = CharacterProfileManager(postgres_client=db_client)

# Create character profile
profile = await manager.create_profile(
    name="林晚",
    birth_chapter=1,
    current_status="alive"
)

# Add timeline event
event = CharacterTimelineEvent(
    chapter=5,
    event_type=EventType.DEATH,
    description="林晚牺牲自己保护同伴",
    importance="critical",
    evidence="林晚的身影消失在火光中..."
)
await manager.add_event("林晚", event)

# Extract events from chapter text
events = manager.extract_events_from_chapter(chapter_content, chapter_num=10)
for event in events:
    print(f"Found {event.event_type}: {event.description}")

# Detect conflicts
conflicts = await manager.detect_timeline_conflicts("林晚")
for conflict in conflicts:
    print(f"Conflict: {conflict.description}")
    print(f"Suggestion: {conflict.suggested_resolution}")
```

**Event Types Supported**:
- `BIRTH`: Character birth or introduction
- `DEATH`: Character death
- `INJURY`: Physical injury
- `RECOVERY`: Recovery from injury
- `APPEARANCE`: Chapter appearance
- `DISAPPEARANCE`: Character goes missing
- `RELATIONSHIP_CHANGE`: Marriage, alliance, betrayal
- `LOCATION_CHANGE`: Movement to new location
- `STATUS_CHANGE`: Social status change (crowned, exiled)
- `SKILL_ACQUISITION`: New ability learned
- `ITEM_ACQUISITION`/`ITEM_LOSS`: Gained/lost items
- `MAJOR_EVENT`: Other significant events

---

### TimelineValidator

Validates temporal consistency across the novel timeline.

**Location**: `src/novel/timeline_validator.py`

**Key Classes**:
- `TimelineValidator`: Main validator class
- `TimelineReport`: Comprehensive validation report
- `TimeConflict`: Detected time conflict
- `OrderViolation`: Event ordering issue
- `IntervalWarning`: Timing/pacing warning

**Detection Capabilities**:
- Dead characters performing actions
- Characters acting before introduction
- Born after death (logical impossibility)
- Married before meeting
- Impossible event sequences
- Pacing issues (too fast/slow)

**Usage Example**:

```python
from src.novel.timeline_validator import TimelineValidator, Configuration

# Configure validator
config = Configuration(
    min_chapter_gap=1,
    max_chapter_gap=50,
    dead_character_action_threshold=5,
)

validator = TimelineValidator(postgres_client=db_client, config=config)

# Validate timeline
report = await validator.validate_timeline("novel_001")

# Check results
if report.has_issues():
    print(f"Total conflicts: {report.total_conflicts}")
    print(f"Order violations: {report.total_order_violations}")
    print(f"Interval warnings: {report.total_interval_warnings}")
    
    for conflict in report.conflicts:
        print(f"[{conflict.severity.value}] {conflict.reason}")
        print(f"  Character: {conflict.character_name}")
        print(f"  Chapter: {conflict.chapter}")
```

**Severity Levels**:
- `CRITICAL`: Logical impossibilities (born after death)
- `ERROR`: Timeline contradictions (action after death)
- `WARNING`: Potential issues (missing character action)
- `INFO`: Minor notes (pacing observations)

---

### ReferenceValidator

Extracts and validates references to past events in the narrative.

**Location**: `src/novel/reference_validator.py`

**Key Classes**:
- `ReferenceValidator`: Main validator class
- `Reference`: Extracted reference from text
- `ReferenceVerification`: Verification result

**Detection Patterns** (Chinese):
- `A说过"B"` - Direct quotation
- `A曾提到B` - Mentioned reference
- `据A回忆B` - Memory reference
- `正如A所言B` - Quote reference

**Usage Example**:

```python
from src.novel.reference_validator import ReferenceValidator
from src.novel.knowledge_graph import KnowledgeGraph

# Initialize
kg = KnowledgeGraph()
validator = ReferenceValidator(
    knowledge_graph=kg,
    vector_store=vector_store,
    similarity_threshold=0.75,
)

# Extract references
references = validator.extract_references(chapter_content, chapter_num=5)
for ref in references:
    print(f"Speaker: {ref.speaker}")
    print(f"Action: {ref.referenced_action}")
    print(f"Content: {ref.referenced_content}")

# Validate all references
verifications = await validator.validate_chapter_references(chapter_content, chapter_num=5)
for v in verifications:
    if not v.is_valid:
        print(f"Invalid reference: {v.reference.text[:50]}")
        print(f"Confidence: {v.confidence:.2f}")
        print(f"Issues: {v.issues}")
```

**Verification Sources**:
1. Knowledge graph for explicit facts
2. Vector store for semantic similarity
3. Character existence validation

---

### HallucinationDetector

Detects hallucinated content contradicting established facts.

**Location**: `src/novel/hallucination_detector.py`

**Key Classes**:
- `HallucinationDetector`: Main detector class
- `Hallucination`: Detected hallucination instance
- `HallucinationReport`: Comprehensive detection report

**Detection Methods**:
1. **Rule-Based**: Pattern matching for quotations and factual claims
2. **Vector Similarity**: Compare against world context embeddings
3. **HHEM-2.1-Open**: Optional ML model integration

**Hallucination Types**:
- `FACTUAL_HALLUCINATION`: Contradicts established facts
- `CREATIVE_FICTION`: Reasonable creative addition (not an error)
- `UNVERIFIABLE`: Cannot be verified against context
- `POTENTIAL_ERROR`: May be an error, needs review

**Usage Example**:

```python
from src.novel.hallucination_detector import HallucinationDetector

detector = HallucinationDetector(
    vector_store=vector_store,
    threshold=0.8,
    use_hhem=False,
    min_text_length=20,
)

# Detect hallucinations
report = await detector.detect_hallucinations(
    generated_chapter=chapter_content,
    world_context=world_context,
    check_quotations=True,
    check_factual_claims=True,
)

if not report.is_clean:
    print(f"Found {len(report.factual_hallucinations)} factual issues")
    
    for h in report.get_high_confidence_issues():
        print(f"[{h.confidence_level.value}] {h.reason}")
        print(f"Text: {h.text[:100]}")
        print(f"Suggestions: {h.suggestions}")
```

**Creative Fiction Detection**:
The detector recognizes that some content is acceptable creative writing:
- Similes (仿佛, 好像, 似乎)
- Uncertainty markers (也许, 可能, 大概)
- Imagination contexts (幻想, 梦境)
- Legend/folklore (据说, 传说)

---

### ChapterTransitionChecker

Detects narrative discontinuities between chapters.

**Location**: `src/novel/transition_checker.py`

**Key Classes**:
- `ChapterTransitionChecker`: Main checker class
- `TransitionReport`: Validation report
- `UnresolvedEvent`: Unresolved suspense event

**Detection Capabilities**:
- Unresolved suspense at chapter endings
- Scene jumps without transition markers
- Missing resolution of previous chapter's events

**Suspense Patterns Detected**:
- Secret letters/messages received but not opened
- Discoveries (secrets, truths) not followed up
- Cliffhanger timing (正要...时)
- Sudden events not resolved
- Unanswered questions

**Usage Example**:

```python
from src.novel.transition_checker import ChapterTransitionChecker

checker = ChapterTransitionChecker()

report = checker.check_transition(
    prev_chapter_content=prev_chapter,
    current_chapter_content=current_chapter,
    chapter_num=4,
)

if report.has_issues:
    print(f"Severity: {report.severity}")
    print(f"Confidence: {report.confidence:.2f}")
    
    for event in report.ignored_events:
        print(f"Ignored event: {event.description}")
        print(f"Importance: {event.importance}")
    
    if report.scene_jump_detected:
        print(f"Scene jump: {report.scene_jump_details}")
    
    for suggestion in report.transition_suggestions:
        print(f"Suggestion: {suggestion}")
```

**Transition Markers Recognized**:
- Time: 次日, 翌日, 第二日, 三日后, 清晨, 黄昏
- Location: 来到, 到了, 回到, 抵达
- Narrative: 话说, 且说, 再说, 却说

---

## Integration

### ValidationOrchestrator

Coordinates all validators for comprehensive chapter validation.

**Location**: `src/novel/validation_orchestrator.py`

**Key Classes**:
- `ValidationOrchestrator`: Main orchestrator class
- `ValidationResult`: Aggregated validation result
- `ValidationIssue`: Single validation issue

**Features**:
- Parallel validator execution
- Unified issue aggregation
- Low-confidence flagging
- Performance timing

**Usage Example**:

```python
from src.novel.validation_orchestrator import ValidationOrchestrator, create_validation_orchestrator

# Create orchestrator with all validators
orchestrator = create_validation_orchestrator(
    knowledge_graph=kg,
    vector_store=vector_store,
    postgres_client=db_client,
    low_confidence_threshold=0.7,
)

# Validate chapter
result = await orchestrator.validate_chapter(
    chapter_content=chapter_content,
    chapter_num=5,
    world_context=world_context,
    prev_chapter_content=prev_chapter,
    novel_id="novel_001",
)

# Check results
if not result.is_valid:
    print(result.summary)
    print(f"Critical issues: {result.critical_issues}")
    print(f"Major issues: {result.major_issues}")
    
    # Get issues by category
    for issue in result.character_issues:
        print(f"[Character] {issue.message}")
    
    for issue in result.hallucination_issues:
        print(f"[Hallucination] {issue.message}")
    
    # Low-confidence items need manual review
    for issue in result.low_confidence_items:
        print(f"[Review] {issue.message} (confidence: {issue.confidence:.2f})")
```

**Factory Function**:

```python
def create_validation_orchestrator(
    knowledge_graph: KnowledgeGraph | None = None,
    vector_store: VectorStore | None = None,
    postgres_client: PostgresClient | None = None,
    low_confidence_threshold: float = 0.7,
) -> ValidationOrchestrator:
    """Create fully configured ValidationOrchestrator with all validators."""
```

**ValidationIssue Attributes**:
- `category`: Validator type (character, reference, hallucination, timeline, transition)
- `severity`: Issue severity (critical, major, minor, info)
- `message`: Human-readable description
- `chapter`: Chapter number
- `confidence`: Confidence score (0.0-1.0)
- `is_low_confidence`: Whether manual review needed
- `suggestion`: Optional fix suggestion
- `metadata`: Additional issue-specific data

---

### AutoFixer

Automated fixing system with iterative repair loop.

**Location**: `src/novel/auto_fixer.py`

**Key Classes**:
- `AutoFixer`: Main auto-fixer class
- `AutoFixResult`: Result of auto-fix process
- `FixSuggestion`: Suggested fix for an issue
- `RepairHistory`: Complete repair attempt history

**Workflow**:
1. Run all validators to collect issues
2. Generate fix suggestions with priorities
3. Build combined fix prompt for LLM
4. Regenerate content with LLM
5. Re-verify to check if issues resolved
6. Repeat up to 3 times
7. Escalate if unrecoverable

**Usage Example**:

```python
from src.novel.auto_fixer import AutoFixer
from src.novel.consistency_verifier import ConsistencyVerifier

# Initialize
fixer = AutoFixer(
    verifier=ConsistencyVerifier(),
    llm=llm_client,
    timeline_validator=timeline_validator,
    reference_validator=reference_validator,
    hallucination_detector=hallucination_detector,
    transition_checker=transition_checker,
    max_retries=3,
)

# Initial verification
verification = fixer.verify(chapter_content, chapter_number=5)

# Run auto-fix loop
result = await fixer.fix_and_regenerate(
    content=chapter_content,
    verification_result=verification,
    prev_chapter_content=prev_chapter,
    world_context=world_context,
)

# Check result
print(fixer.get_fix_summary(result))

if result.success:
    print("Content fixed successfully")
    final_content = result.final_content
else:
    print(f"Remaining issues: {len(result.issues_remaining)}")
    if result.manual_review_required:
        print("Manual review required")
```

**Fix Suggestion Types**:
- `REMOVE_CONTRADICTION`: Remove contradictory content
- `UPDATE_LOCATION`: Fix location inconsistency
- `FIX_TIMELINE`: Correct timeline errors
- `CORRECT_CHARACTER_STATE`: Fix character state
- `ADD_MISSING_CONTEXT`: Add missing context
- `REWRITE_PASSAGE`: Rewrite problematic section
- `FIX_HALLUCINATION`: Correct hallucinated content
- `FIX_REFERENCE`: Fix invalid reference
- `FIX_TRANSITION`: Add missing transition

**Degradation Strategy**:
- Escalate if >2 critical issues remain
- Escalate if high-confidence hallucination (>0.9)
- Escalate if timeline conflict requires human verification
- Allow partial fix otherwise

---

## Manual Review

### ManualReviewAPI

FastAPI web interface for reviewing escalated issues.

**Location**: `src/novel/manual_review_api.py`

**Endpoints**:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/issues/pending` | List pending issues for review |
| GET | `/issues/{issue_id}` | Get issue details |
| POST | `/issues/{issue_id}/decision` | Submit approve/reject decision |
| GET | `/stats` | Get review statistics |
| POST | `/issues/add` | Add issue manually (testing) |
| DELETE | `/issues/clear` | Clear all issues (testing) |

**Usage Example**:

```python
import httpx

# Start the API server
# uvicorn src.novel.manual_review_api:app --host 0.0.0.0 --port 8000

async with httpx.AsyncClient() as client:
    # Get pending issues
    response = await client.get("http://localhost:8000/issues/pending")
    issues = response.json()
    
    for issue in issues:
        print(f"[{issue['issue_id']}] Chapter {issue['chapter_number']}: {issue['description']}")
    
    # Get issue details
    response = await client.get(f"http://localhost:8000/issues/{issue['issue_id']}")
    details = response.json()
    print(f"Context: {details['context']}")
    
    # Submit decision
    response = await client.post(
        f"http://localhost:8000/issues/{issue['issue_id']}/decision",
        json={"decision": "approve", "reason": "Fix is acceptable"}
    )
```

**ReviewIssue Attributes**:
- `issue_id`: Unique identifier
- `chapter_number`: Chapter where issue was found
- `description`: Human-readable description
- `severity`: Severity level (1-5)
- `status`: pending, approved, rejected
- `created_at`: When issue was created
- `resolved_at`: When issue was resolved
- `reason`: Reason for decision
- `context`: Additional context

---

## Performance

### ValidationMetrics

Tracks performance metrics for validation operations.

**Location**: `src/novel/validation_metrics.py`

**Key Classes**:
- `ValidationMetrics`: Metrics tracker
- `ValidationRecord`: Single validation record
- `FixRecord`: Single fix attempt record

**Usage Example**:

```python
from src.novel.validation_metrics import ValidationMetrics

metrics = ValidationMetrics(max_records=10000)

# Record validation
metrics.record_validation(
    chapter=5,
    duration_ms=150.5,
    issues_count=3,
    validator="character"
)

# Record fix
metrics.record_fix(
    chapter=5,
    duration_ms=50.0,
    success=True
)

# Get chapter metrics
chapter_metrics = metrics.get_chapter_metrics(5)
print(f"Validations: {chapter_metrics['validations_count']}")
print(f"Fix success rate: {chapter_metrics['fix_success_rate']:.1%}")

# Get summary
summary = metrics.get_summary()
print(f"Total validations: {summary['total_validations']}")
print(f"Average validation time: {summary['avg_validation_time_ms']:.2f}ms")

# Generate report
print(metrics.generate_report(format="text"))
# Or JSON
print(metrics.generate_report(format="json"))
```

**Per-Validator Statistics**:
```python
validator_stats = metrics.get_validator_performance("character")
print(f"Count: {validator_stats['count']}")
print(f"Total issues: {validator_stats['total_issues']}")
print(f"Avg time: {validator_stats['avg_time_ms']:.2f}ms")
```

---

### PerformanceBenchmark

Benchmarking suite for performance validation.

**Location**: `src/novel/performance_benchmark.py`

**Key Classes**:
- `PerformanceBenchmark`: Benchmark suite
- `BenchmarkResult`: Single benchmark result

**Performance Requirements**:
- Validation time < 5 seconds per chapter
- Memory usage < 500MB

**Usage Example**:

```python
from src.novel.performance_benchmark import PerformanceBenchmark

benchmark = PerformanceBenchmark()

# Time a validator
def my_validator(content: str) -> dict:
    # Validation logic
    return {"valid": True, "issues": []}

result = benchmark.time_validation(
    validator=my_validator,
    content=chapter_content,
    iterations=10
)
print(f"Avg time: {result.duration_ms:.2f}ms")
print(f"Peak memory: {result.memory_mb:.2f}MB")

# Run full benchmark suite
report = benchmark.run_full_benchmark("novel_001")
print(f"Thresholds met: {report['summary']['thresholds_met']}")

# Check thresholds
if benchmark.check_thresholds(validation_time_s=5.0, memory_mb=500.0):
    print("Performance within acceptable limits")
else:
    print("Performance issues detected")

# Generate report
print(benchmark.generate_report())
```

**Benchmark Scenarios**:
1. **Single Chapter**: Measure validation time per chapter
2. **Multi-Chapter**: Test throughput across multiple chapters
3. **Memory Stress**: Test memory usage under load

---

## Configuration

### Environment Variables

```bash
# Required for LLM operations
DEEPSEEK_API_KEY=your_api_key

# Database connections
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/novel_db
REDIS_URL=redis://localhost:6379/0

# Vector store (Pinecone)
PINECONE_API_KEY=your_api_key
PINECONE_ENVIRONMENT=your_environment
PINECONE_INDEX_NAME=novel-embeddings

# Optional HHEM model
USE_HHEM_MODEL=false
```

### Validator Configuration

```python
# TimelineValidator configuration
from src.novel.timeline_validator import Configuration

timeline_config = Configuration(
    min_chapter_gap=1,           # Minimum chapters between events
    max_chapter_gap=50,          # Maximum chapters before warning
    dead_character_action_threshold=5,  # Chapters after death to flag
    missing_character_threshold=2,      # Chapters before introduction to flag
)

# HallucinationDetector configuration
detector = HallucinationDetector(
    vector_store=vector_store,
    threshold=0.8,               # Confidence threshold
    use_hhem=False,              # Enable HHEM model
    min_text_length=20,          # Minimum text for detection
)

# ValidationOrchestrator configuration
orchestrator = ValidationOrchestrator(
    character_manager=char_mgr,
    reference_validator=ref_val,
    hallucination_detector=hall_det,
    timeline_validator=time_val,
    transition_checker=trans_check,
    low_confidence_threshold=0.7,  # Flag for manual review
)
```

### AutoFixer Configuration

```python
fixer = AutoFixer(
    verifier=verifier,
    llm=llm_client,
    max_retries=3,               # Maximum fix attempts
)

# Degradation thresholds
fixer._critical_threshold = 2           # Max critical issues before escalation
fixer._hallucination_threshold = 0.9    # Hallucination confidence for escalation
fixer._timeline_confidence_threshold = 0.85  # Timeline confidence for escalation
```

---

## Troubleshooting

### Common Issues

#### 1. "Character dies multiple times"

**Cause**: Multiple death events detected in character timeline.

**Solution**:
- Verify if death is real or apparent (faked death, vision)
- Add metadata to death events to distinguish types
- Use flashback detection for death scenes

```python
# Add death event with metadata
event = CharacterTimelineEvent(
    chapter=5,
    event_type=EventType.DEATH,
    description="林晚溺水",
    metadata={"death_type": "apparent", "context": "vision"}
)
```

#### 2. "Action after confirmed death"

**Cause**: Character has events after a death event.

**Solution**:
- Check for resurrection storyline
- Add resurrection explanation event
- Mark death as "apparent" if misleading

```python
# Add resurrection event
resurrection = CharacterTimelineEvent(
    chapter=10,
    event_type=EventType.MAJOR_EVENT,
    description="林晚奇迹般生还",
    metadata={"resurrection": True, "explanation": "被神秘力量救起"}
)
```

#### 3. "Hallucination detected for valid quote"

**Cause**: Quote doesn't have exact match in world context.

**Solution**:
- Add quote to knowledge graph
- Update world context with established quotes
- Mark as creative fiction if appropriate

```python
# Mark as creative fiction with narrative context
"正如传说所言..."  # Uses "传说" marker
```

#### 4. "Transition issue: Unresolved suspense"

**Cause**: Chapter ends with cliffhanger not addressed in next chapter.

**Solution**:
- Add transition marker (次日, 翌日)
- Address the suspense in chapter opening
- Add character reaction to the event

```python
# Add transition at chapter start
"次日清晨，林晚拆开了那封密信..."
```

#### 5. "Low confidence validation results"

**Cause**: Validator confidence below threshold (0.7).

**Solution**:
- Review flagged items manually
- Add more context to world building
- Increase similarity thresholds

```python
# Adjust threshold
orchestrator.low_confidence_threshold = 0.5  # Lower for more automation
orchestrator.low_confidence_threshold = 0.8  # Higher for stricter review
```

#### 6. "Validation too slow (>5s)"

**Cause**: Validators running sequentially or database latency.

**Solution**:
- Check parallel execution is enabled
- Optimize database queries
- Reduce vector store query size

```python
# Monitor performance
metrics.record_validation(chapter=5, duration_ms=...)
report = metrics.generate_report()

# Benchmark validators
benchmark.time_validation(validator, content, iterations=10)
```

#### 7. "Memory usage exceeds 500MB"

**Cause**: Large content or embedding vectors in memory.

**Solution**:
- Process chapters in batches
- Clear caches between validations
- Use streaming for large novels

```python
# Check memory
benchmark.memory_usage()

# Process in batches
for batch in chapter_batches:
    result = await orchestrator.validate_chapter(batch, ...)
    # Process result
    # Clear caches if needed
```

### Debug Logging

Enable debug logging for detailed output:

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Or for specific modules
logging.getLogger("src.novel.validation_orchestrator").setLevel(logging.DEBUG)
logging.getLogger("src.novel.auto_fixer").setLevel(logging.DEBUG)
```

### Getting Help

1. Check validation metrics: `metrics.generate_report()`
2. Review benchmark results: `benchmark.generate_report()`
3. Examine low-confidence items in ValidationResult
4. Review repair history in AutoFixResult
5. Use Manual Review API for edge cases

---

## API Reference Quick Links

| Module | Main Class | Purpose |
|--------|-----------|---------|
| `validation_orchestrator.py` | `ValidationOrchestrator` | Coordinate all validators |
| `auto_fixer.py` | `AutoFixer` | Iterative repair loop |
| `character_profile.py` | `CharacterProfileManager` | Character timeline tracking |
| `timeline_validator.py` | `TimelineValidator` | Temporal consistency |
| `reference_validator.py` | `ReferenceValidator` | Citation verification |
| `hallucination_detector.py` | `HallucinationDetector` | Hallucination detection |
| `transition_checker.py` | `ChapterTransitionChecker` | Chapter transitions |
| `manual_review_api.py` | `ManualReviewAPI` | Human review interface |
| `validation_metrics.py` | `ValidationMetrics` | Performance tracking |
| `performance_benchmark.py` | `PerformanceBenchmark` | Benchmarking suite |

---

## Version History

- **v1.0**: Initial release with 5 validators
- **v1.1**: Added AutoFixer with iterative repair
- **v1.2**: Added Manual Review API
- **v1.3**: Performance optimization with parallel validation
- **v1.4**: Enhanced hallucination detection with HHEM support
- **v2.0**: Four-wave validation architecture

---

*Last updated: 2026-03-03*