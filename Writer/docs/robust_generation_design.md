# Robust Novel Generation System Design

## Executive Summary

This document outlines a comprehensive improvement plan for the novel generation system to address critical failure modes:
- Title duplication
- Content discontinuity  
- Hallucinated references
- Missing chapters
- Inconsistent backstory

## Current System Analysis

### Existing Strengths
1. **ContinuityManager** (`src/novel/continuity.py`)
   - Tracks character states, plot threads, locations
   - Detects death, fusion, capture patterns
   - Prunes key events intelligently

2. **ConsistencyVerifier** (`src/novel/consistency_verifier.py`)
   - Detects dead character appearances
   - Location consistency checking
   - Timeline error detection

3. **CheckpointManager** (`src/novel/checkpointing.py`)
   - Mid-chapter progress preservation
   - Checksum verification
   - Automatic cleanup

4. **AutoFixer** (`src/novel/auto_fixer.py`)
   - Iterative verification-regeneration loop
   - Priority-based fix suggestions

### Critical Gaps
1. No centralized title/chapter registry
2. Reference validation not integrated into generation
3. No pre-generation validation layer
4. Limited error recovery mechanisms
5. No anomaly detection for quality issues

---

## 1. Validation Layer Architecture

### 1.1 Pre-Generation Validation

```python
# src/novel/validation/pre_generator.py

@dataclass
class PreGenerationContext:
    """Context required before chapter generation."""
    chapter_number: int
    expected_characters: list[str]
    required_plot_threads: list[str]
    previous_chapter_state: StoryState | None
    title_format: str  # e.g., "Chapter {n}: {title}"
    min_word_count: int
    max_word_count: int


@dataclass
class PreValidationResult:
    """Result of pre-generation validation."""
    is_valid: bool
    blockers: list[str]  # Critical issues that prevent generation
    warnings: list[str]  # Non-critical issues
    context_ready: bool
    missing_prerequisites: list[str]


class PreGenerationValidator:
    """Validates prerequisites before chapter generation."""
    
    def validate(self, context: PreGenerationContext) -> PreValidationResult:
        """
        Checks:
        1. Previous chapter exists (if not chapter 1)
        2. All required characters are defined
        3. Plot threads reference existing events
        4. Story state is consistent
        5. Title is unique and well-formed
        """
        blockers = []
        warnings = []
        missing = []
        
        # Check chapter sequence
        if context.chapter_number > 1:
            if not self._previous_chapter_exists(context.chapter_number - 1):
                blockers.append(f"Chapter {context.chapter_number - 1} does not exist")
        
        # Check character definitions
        for char in context.expected_characters:
            if not self._character_defined(char):
                missing.append(f"Character '{char}' not defined")
        
        # Check plot thread references
        for thread in context.required_plot_threads:
            if not self._plot_thread_exists(thread):
                warnings.append(f"Plot thread '{thread}' not found in story state")
        
        return PreValidationResult(
            is_valid=len(blockers) == 0,
            blockers=blockers,
            warnings=warnings,
            context_ready=len(missing) == 0,
            missing_prerequisites=missing,
        )
```

### 1.2 Post-Generation Verification

```python
# src/novel/validation/post_verifier.py

@dataclass
class PostVerificationResult:
    """Result of post-generation verification."""
    passed: bool
    content_hash: str
    word_count: int
    issues: list[ContentIssue]
    references_validated: dict[str, bool]  # reference -> is_valid
    character_appearances: dict[str, int]  # character -> mention_count
    quality_score: float


class PostGenerationVerifier:
    """Verifies generated content meets all requirements."""
    
    def verify(
        self,
        content: str,
        chapter_number: int,
        expected: PreGenerationContext,
        story_state: StoryState,
    ) -> PostVerificationResult:
        """
        Verifies:
        1. Content is not empty/duplicate
        2. All expected characters appear
        3. References point to existing events
        4. No continuity violations
        5. Word count within bounds
        6. Quality metrics acceptable
        """
        issues = []
        
        # 1. Content validation
        if len(content.strip()) < 100:
            issues.append(ContentIssue(
                severity="critical",
                type="empty_content",
                message="Generated content is too short",
            ))
        
        # 2. Duplicate detection
        content_hash = self._compute_hash(content)
        if self._is_duplicate_content(content_hash):
            issues.append(ContentIssue(
                severity="critical",
                type="duplicate_content",
                message="Content appears to be a duplicate",
            ))
        
        # 3. Reference validation
        references = self._extract_references(content)
        ref_validation = {}
        for ref in references:
            is_valid = self._validate_reference(ref, story_state)
            ref_validation[ref] = is_valid
            if not is_valid:
                issues.append(ContentIssue(
                    severity="high",
                    type="invalid_reference",
                    message=f"Reference '{ref}' does not exist in story",
                    location=self._find_reference_location(content, ref),
                ))
        
        # 4. Character appearance check
        char_appearances = {}
        for char in expected.expected_characters:
            count = self._count_mentions(content, char)
            char_appearances[char] = count
            if count == 0:
                issues.append(ContentIssue(
                    severity="medium",
                    type="missing_character",
                    message=f"Expected character '{char}' does not appear",
                ))
        
        # 5. Continuity check (use existing ConsistencyVerifier)
        continuity_issues = self._check_continuity(content, story_state)
        issues.extend(continuity_issues)
        
        return PostVerificationResult(
            passed=len([i for i in issues if i.severity in ("critical", "high")]) == 0,
            content_hash=content_hash,
            word_count=len(content.split()),
            issues=issues,
            references_validated=ref_validation,
            character_appearances=char_appearances,
            quality_score=self._compute_quality_score(issues),
        )
```

### 1.3 Cross-Chapter Consistency Checker

```python
# src/novel/validation/cross_chapter.py

@dataclass
class CrossChapterIssue:
    """Issue spanning multiple chapters."""
    issue_type: str
    chapter_range: tuple[int, int]
    description: str
    affected_entities: list[str]
    severity: str


class CrossChapterValidator:
    """Validates consistency across multiple chapters."""
    
    def validate_range(
        self,
        start_chapter: int,
        end_chapter: int,
        story_registry: "StoryRegistry",
    ) -> list[CrossChapterIssue]:
        """
        Cross-chapter validations:
        1. Character arc consistency
        2. Timeline coherence
        3. Plot thread resolution
        4. Location transition logic
        5. Relationship evolution
        """
        issues = []
        
        # Load all chapters in range
        chapters = story_registry.get_chapters(start_chapter, end_chapter)
        
        # Build character journey map
        character_journeys = self._build_character_journeys(chapters)
        
        # Check for teleportation (character in two places)
        for char, locations in character_journeys.items():
            for i in range(len(locations) - 1):
                if not self._valid_transition(locations[i], locations[i+1]):
                    issues.append(CrossChapterIssue(
                        issue_type="location_teleport",
                        chapter_range=(i+start_chapter, i+start_chapter+1),
                        description=f"Character '{char}' appears in {locations[i]} then immediately in {locations[i+1]}",
                        affected_entities=[char],
                        severity="high",
                    ))
        
        # Check plot thread continuity
        thread_states = self._track_plot_threads(chapters)
        for thread, states in thread_states.items():
            # Thread appears, disappears, then reappears without explanation
            if self._has_unexplained_gaps(states):
                issues.append(CrossChapterIssue(
                    issue_type="plot_thread_gap",
                    chapter_range=self._find_gap_range(states),
                    description=f"Plot thread '{thread}' has unexplained gaps",
                    affected_entities=[thread],
                    severity="medium",
                ))
        
        return issues
```

### 1.4 Story Arc Coherence Validator

```python
# src/novel/validation/arc_validator.py

@dataclass
class ArcValidationResult:
    """Result of story arc validation."""
    is_coherent: bool
    act_structure_valid: bool
    pacing_issues: list[dict]
    unresolved_threads: list[str]
    emotional_arc_score: float


class StoryArcValidator:
    """Validates overall story arc coherence."""
    
    # Three-act structure thresholds (for 100-chapter novel)
    ACT_BOUNDARIES = {
        "act1_end": 0.25,  # 25%
        "act2_midpoint": 0.50,  # 50%
        "act2_end": 0.75,  # 75%
    }
    
    def validate_arc(
        self,
        outline: dict,
        completed_chapters: int,
        total_chapters: int,
    ) -> ArcValidationResult:
        """
        Validates:
        1. Three-act structure adherence
        2. Pacing consistency
        3. Emotional arc progression
        4. Foreshadowing payoff tracking
        5. Climax positioning
        """
        progress = completed_chapters / total_chapters
        
        # Check act structure
        act_issues = self._validate_act_structure(outline, progress)
        
        # Analyze pacing
        pacing_issues = self._analyze_pacing(outline, completed_chapters)
        
        # Track foreshadowing
        unresolved = self._check_foreshadowing_payoff(outline, progress)
        
        # Emotional arc analysis
        emotional_score = self._score_emotional_arc(outline, progress)
        
        return ArcValidationResult(
            is_coherent=len(act_issues) == 0,
            act_structure_valid=len(act_issues) == 0,
            pacing_issues=pacing_issues,
            unresolved_threads=unresolved,
            emotional_arc_score=emotional_score,
        )
```

---

## 2. Error Recovery System

### 2.1 Retry with Exponential Backoff

```python
# src/novel/recovery/retry_handler.py

@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_errors: list[str] = field(default_factory=lambda: [
        "rate_limit",
        "timeout",
        "temporary_failure",
        "content_too_short",
    ])


@dataclass
class RetryResult:
    """Result of retry operation."""
    success: bool
    attempts: int
    final_content: str | None
    last_error: str | None
    total_delay_seconds: float


class RetryHandler:
    """Handles retry logic with exponential backoff."""
    
    def __init__(self, config: RetryConfig | None = None):
        self.config = config or RetryConfig()
    
    async def execute_with_retry(
        self,
        operation: Callable[[], Awaitable[str]],
        validator: Callable[[str], bool] | None = None,
    ) -> RetryResult:
        """
        Execute operation with retry and backoff.
        
        Args:
            operation: Async function that generates content
            validator: Optional function to validate result
        
        Returns:
            RetryResult with final outcome
        """
        attempts = 0
        total_delay = 0.0
        last_error = None
        content = None
        
        while attempts < self.config.max_attempts:
            attempts += 1
            
            try:
                content = await operation()
                
                # Validate if validator provided
                if validator and not validator(content):
                    raise RetryableError("Validation failed")
                
                return RetryResult(
                    success=True,
                    attempts=attempts,
                    final_content=content,
                    last_error=None,
                    total_delay_seconds=total_delay,
                )
                
            except RetryableError as e:
                last_error = str(e)
                
                if attempts < self.config.max_attempts:
                    delay = self._calculate_delay(attempts)
                    total_delay += delay
                    logger.warning(
                        f"Attempt {attempts} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                    
            except NonRetryableError as e:
                # Don't retry non-retryable errors
                return RetryResult(
                    success=False,
                    attempts=attempts,
                    final_content=None,
                    last_error=str(e),
                    total_delay_seconds=total_delay,
                )
        
        return RetryResult(
            success=False,
            attempts=attempts,
            final_content=content,
            last_error=last_error,
            total_delay_seconds=total_delay,
        )
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and optional jitter."""
        delay = self.config.base_delay_seconds * (
            self.config.exponential_base ** (attempt - 1)
        )
        delay = min(delay, self.config.max_delay_seconds)
        
        if self.config.jitter:
            # Add up to 25% jitter
            delay *= (1 + 0.25 * random.random())
        
        return delay
```

### 2.2 Graceful Degradation Strategies

```python
# src/novel/recovery/degradation.py

class DegradationLevel(str, Enum):
    """Levels of degradation for graceful fallback."""
    FULL_QUALITY = "full"  # Normal operation
    REDUCED_QUALITY = "reduced"  # Fewer iterations, lower threshold
    MINIMAL_QUALITY = "minimal"  # Basic generation only
    EMERGENCY = "emergency"  # Skeleton content with placeholders


@dataclass
class DegradationConfig:
    """Configuration for degradation levels."""
    level: DegradationLevel
    max_iterations: int
    quality_threshold: float
    enable_learning: bool
    enable_market_research: bool
    token_budget: int


DEGRADATION_CONFIGS: dict[DegradationLevel, DegradationConfig] = {
    DegradationLevel.FULL_QUALITY: DegradationConfig(
        level=DegradationLevel.FULL_QUALITY,
        max_iterations=5,
        quality_threshold=9.0,
        enable_learning=True,
        enable_market_research=True,
        token_budget=16000,
    ),
    DegradationLevel.REDUCED_QUALITY: DegradationConfig(
        level=DegradationLevel.REDUCED_QUALITY,
        max_iterations=3,
        quality_threshold=7.5,
        enable_learning=True,
        enable_market_research=False,
        token_budget=12000,
    ),
    DegradationLevel.MINIMAL_QUALITY: DegradationConfig(
        level=DegradationLevel.MINIMAL_QUALITY,
        max_iterations=2,
        quality_threshold=6.0,
        enable_learning=False,
        enable_market_research=False,
        token_budget=8000,
    ),
    DegradationLevel.EMERGENCY: DegradationConfig(
        level=DegradationLevel.EMERGENCY,
        max_iterations=1,
        quality_threshold=5.0,
        enable_learning=False,
        enable_market_research=False,
        token_budget=4000,
    ),
}


class GracefulDegradation:
    """Manages graceful degradation of generation quality."""
    
    def __init__(self):
        self.current_level = DegradationLevel.FULL_QUALITY
        self.failure_count = 0
        self.success_count = 0
    
    def record_failure(self, error_type: str) -> DegradationLevel:
        """
        Record a failure and potentially degrade.
        
        Returns:
            New degradation level
        """
        self.failure_count += 1
        
        # Calculate failure rate
        total = self.failure_count + self.success_count
        failure_rate = self.failure_count / total if total > 0 else 0
        
        # Degrade if failure rate exceeds threshold
        if failure_rate > 0.3 and self.current_level != DegradationLevel.EMERGENCY:
            self._degrade()
        
        return self.current_level
    
    def record_success(self) -> DegradationLevel:
        """
        Record a success and potentially recover.
        
        Returns:
            New degradation level
        """
        self.success_count += 1
        
        # Recover after consecutive successes
        if self.success_count >= 5 and self.current_level != DegradationLevel.FULL_QUALITY:
            self._recover()
        
        return self.current_level
    
    def get_config(self) -> DegradationConfig:
        """Get current degradation configuration."""
        return DEGRADATION_CONFIGS[self.current_level]
    
    def _degrade(self) -> None:
        """Move to next degradation level."""
        levels = list(DegradationLevel)
        current_idx = levels.index(self.current_level)
        if current_idx < len(levels) - 1:
            self.current_level = levels[current_idx + 1]
            logger.warning(f"Degraded to {self.current_level.value} quality")
            self.success_count = 0  # Reset success counter
    
    def _recover(self) -> None:
        """Move to previous degradation level."""
        levels = list(DegradationLevel)
        current_idx = levels.index(self.current_level)
        if current_idx > 0:
            self.current_level = levels[current_idx - 1]
            logger.info(f"Recovered to {self.current_level.value} quality")
            self.success_count = 0
```

### 2.3 State Checkpointing Enhancement

```python
# src/novel/recovery/state_checkpoint.py

@dataclass
class GenerationState:
    """Complete state of generation process."""
    novel_id: str
    current_chapter: int
    completed_chapters: list[int]
    story_state: StoryState
    outline: dict
    characters: dict[str, Any]
    world_context: dict
    generation_log: list[dict]
    created_at: datetime
    checksum: str


class StateCheckpointManager:
    """Enhanced checkpointing with full state preservation."""
    
    def __init__(self, checkpoint_dir: Path):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Integrate with existing CheckpointManager
        self.content_checkpoints = CheckpointManager(checkpoint_dir / "content")
    
    def save_state(self, state: GenerationState) -> str:
        """
        Save complete generation state.
        
        Returns:
            Checkpoint ID
        """
        checkpoint_id = f"state_{state.novel_id}_ch{state.current_chapter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Serialize state
        state_dict = {
            "novel_id": state.novel_id,
            "current_chapter": state.current_chapter,
            "completed_chapters": state.completed_chapters,
            "story_state": asdict(state.story_state),
            "outline": state.outline,
            "characters": state.characters,
            "world_context": state.world_context,
            "generation_log": state.generation_log[-100:],  # Keep last 100 entries
            "created_at": state.created_at.isoformat(),
            "checksum": state.checksum,
        }
        
        # Save with atomic write
        temp_path = self.checkpoint_dir / f"{checkpoint_id}.tmp"
        final_path = self.checkpoint_dir / f"{checkpoint_id}.json"
        
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(state_dict, f, indent=2, ensure_ascii=False)
        
        temp_path.rename(final_path)
        
        logger.info(f"Saved state checkpoint: {checkpoint_id}")
        return checkpoint_id
    
    def load_state(self, checkpoint_id: str) -> GenerationState | None:
        """Load generation state from checkpoint."""
        path = self.checkpoint_dir / f"{checkpoint_id}.json"
        
        if not path.exists():
            return None
        
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            
            return GenerationState(
                novel_id=data["novel_id"],
                current_chapter=data["current_chapter"],
                completed_chapters=data["completed_chapters"],
                story_state=self._deserialize_story_state(data["story_state"]),
                outline=data["outline"],
                characters=data["characters"],
                world_context=data["world_context"],
                generation_log=data["generation_log"],
                created_at=datetime.fromisoformat(data["created_at"]),
                checksum=data["checksum"],
            )
        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_id}: {e}")
            return None
    
    def get_latest_state(self, novel_id: str) -> GenerationState | None:
        """Get most recent state for a novel."""
        pattern = f"state_{novel_id}_ch*.json"
        checkpoints = sorted(self.checkpoint_dir.glob(pattern), reverse=True)
        
        for path in checkpoints:
            state = self.load_state(path.stem)
            if state:
                return state
        
        return None
```

### 2.4 Rollback Mechanism

```python
# src/novel/recovery/rollback.py

@dataclass
class RollbackPoint:
    """A point in generation that can be rolled back to."""
    chapter_number: int
    state_checkpoint_id: str
    content_checkpoint_id: str
    created_at: datetime
    reason: str


class RollbackManager:
    """Manages rollback to previous generation states."""
    
    def __init__(
        self,
        state_manager: StateCheckpointManager,
        content_manager: CheckpointManager,
    ):
        self.state_manager = state_manager
        self.content_manager = content_manager
        self.rollback_history: list[RollbackPoint] = []
    
    def create_rollback_point(
        self,
        chapter_number: int,
        reason: str,
        state: GenerationState,
        content: str,
    ) -> RollbackPoint:
        """Create a rollback point before risky operation."""
        state_id = self.state_manager.save_state(state)
        content_id = self.content_manager.create_checkpoint(
            chapter_number=chapter_number,
            word_count=len(content.split()),
            content=content,
            state_snapshot=asdict(state.story_state),
        ).checkpoint_id if self.content_manager.create_checkpoint(
            chapter_number=chapter_number,
            word_count=len(content.split()),
            content=content,
            state_snapshot=asdict(state.story_state),
        ) else ""
        
        rollback = RollbackPoint(
            chapter_number=chapter_number,
            state_checkpoint_id=state_id,
            content_checkpoint_id=content_id,
            created_at=datetime.now(),
            reason=reason,
        )
        
        self.rollback_history.append(rollback)
        logger.info(f"Created rollback point for chapter {chapter_number}: {reason}")
        
        return rollback
    
    def rollback(self, rollback_point: RollbackPoint) -> tuple[GenerationState, str] | None:
        """
        Rollback to a previous point.
        
        Returns:
            Tuple of (state, content) or None if rollback failed
        """
        state = self.state_manager.load_state(rollback_point.state_checkpoint_id)
        if not state:
            logger.error(f"Failed to load state for rollback: {rollback_point.state_checkpoint_id}")
            return None
        
        content_checkpoint = self.content_manager.load_checkpoint(
            rollback_point.content_checkpoint_id
        )
        content = content_checkpoint.content if content_checkpoint else ""
        
        logger.warning(
            f"Rolled back to chapter {rollback_point.chapter_number} "
            f"(reason: {rollback_point.reason})"
        )
        
        return state, content
    
    def get_rollback_points(self, chapter_number: int | None = None) -> list[RollbackPoint]:
        """Get available rollback points."""
        if chapter_number is None:
            return self.rollback_history
        return [rp for rp in self.rollback_history if rp.chapter_number == chapter_number]
```

---

## 3. Quality Assurance System

### 3.1 Title Format Enforcement

```python
# src/novel/qa/title_validator.py

@dataclass
class TitleValidationResult:
    """Result of title validation."""
    is_valid: bool
    formatted_title: str
    issues: list[str]
    similarity_to_existing: dict[str, float]  # existing_title -> similarity


class TitleValidator:
    """Ensures title format consistency and uniqueness."""
    
    # Title format patterns
    TITLE_PATTERNS = {
        "numbered": r"第(\d+)章[：:\s]*(.+)",  # Chinese: 第1章：开端
        "english": r"Chapter\s+(\d+)[：:\s]*(.+)",  # English: Chapter 1: The Beginning
        "simple": r"(.+)",  # Just the title
    }
    
    def __init__(self, registry: "StoryRegistry"):
        self.registry = registry
        self.used_titles: dict[int, str] = {}  # chapter -> title
        self.title_embeddings: dict[str, list[float]] = {}
    
    def validate_title(
        self,
        raw_title: str,
        chapter_number: int,
        format_type: str = "numbered",
        language: str = "zh",
    ) -> TitleValidationResult:
        """
        Validate and format title.
        
        Checks:
        1. Format compliance
        2. Uniqueness (no duplicate titles)
        3. Similarity to existing titles (avoid near-duplicates)
        4. Length constraints
        5. Character restrictions
        """
        issues = []
        
        # Format the title
        formatted = self._format_title(raw_title, chapter_number, format_type, language)
        
        # Check format compliance
        if not self._matches_pattern(formatted, format_type):
            issues.append(f"Title does not match expected format: {format_type}")
        
        # Check uniqueness
        for existing_ch, existing_title in self.used_titles.items():
            if existing_ch != chapter_number and existing_title == formatted:
                issues.append(f"Duplicate title: same as chapter {existing_ch}")
        
        # Check similarity to existing titles
        similarities = {}
        title_text = self._extract_title_text(formatted)
        
        for existing_ch, existing_title in self.used_titles.items():
            if existing_ch != chapter_number:
                existing_text = self._extract_title_text(existing_title)
                similarity = self._compute_similarity(title_text, existing_text)
                similarities[existing_title] = similarity
                
                if similarity > 0.8:  # Very similar
                    issues.append(
                        f"Title too similar to chapter {existing_ch} "
                        f"(similarity: {similarity:.1%})"
                    )
        
        # Check length
        if len(title_text) < 2:
            issues.append("Title too short")
        elif len(title_text) > 50:
            issues.append("Title too long (max 50 characters)")
        
        return TitleValidationResult(
            is_valid=len(issues) == 0,
            formatted_title=formatted,
            issues=issues,
            similarity_to_existing=similarities,
        )
    
    def register_title(self, chapter_number: int, title: str) -> None:
        """Register a title as used."""
        self.used_titles[chapter_number] = title
    
    def _format_title(
        self,
        raw: str,
        chapter: int,
        format_type: str,
        language: str,
    ) -> str:
        """Format title according to pattern."""
        # Clean up raw title
        title_text = raw.strip()
        
        # Remove existing chapter prefix if present
        for pattern in self.TITLE_PATTERNS.values():
            match = re.match(pattern, title_text)
            if match:
                # Extract just the title part
                groups = match.groups()
                if len(groups) > 1:
                    title_text = groups[-1].strip()
                break
        
        # Apply format
        if format_type == "numbered":
            if language == "zh":
                return f"第{chapter}章：{title_text}"
            else:
                return f"Chapter {chapter}: {title_text}"
        elif format_type == "english":
            return f"Chapter {chapter}: {title_text}"
        else:
            return title_text
```

### 3.2 Reference Validation System

```python
# src/novel/qa/reference_validator.py

@dataclass
class Reference:
    """A reference to a story element in content."""
    reference_type: str  # "character", "event", "location", "item", "ability"
    referenced_entity: str
    context: str  # Surrounding text
    position: int  # Character position in content
    confidence: float


@dataclass
class ReferenceValidationResult:
    """Result of reference validation."""
    total_references: int
    valid_references: int
    invalid_references: list[tuple[Reference, str]]  # (reference, reason)
    unverified_references: list[Reference]


class ReferenceValidator:
    """Validates that references in content point to existing story elements."""
    
    def __init__(self, story_registry: "StoryRegistry"):
        self.registry = story_registry
        self._entity_extractors = {
            "character": self._extract_character_references,
            "event": self._extract_event_references,
            "location": self._extract_location_references,
            "item": self._extract_item_references,
            "ability": self._extract_ability_references,
        }
    
    def validate_references(
        self,
        content: str,
        chapter_number: int,
        story_state: StoryState,
    ) -> ReferenceValidationResult:
        """
        Validate all references in content.
        
        Checks:
        1. Characters mentioned exist and are in valid state
        2. Events referenced actually occurred
        3. Locations exist in world
        4. Items have been introduced
        5. Abilities have been established
        """
        all_references: list[Reference] = []
        invalid: list[tuple[Reference, str]] = []
        unverified: list[Reference] = []
        
        # Extract all references by type
        for ref_type, extractor in self._entity_extractors.items():
            refs = extractor(content)
            all_references.extend(refs)
        
        # Validate each reference
        for ref in all_references:
            is_valid, reason = self._validate_single_reference(
                ref, chapter_number, story_state
            )
            
            if not is_valid:
                invalid.append((ref, reason))
            elif reason == "unverified":
                unverified.append(ref)
        
        valid_count = len(all_references) - len(invalid)
        
        return ReferenceValidationResult(
            total_references=len(all_references),
            valid_references=valid_count,
            invalid_references=invalid,
            unverified_references=unverified,
        )
    
    def _validate_single_reference(
        self,
        reference: Reference,
        chapter_number: int,
        story_state: StoryState,
    ) -> tuple[bool, str]:
        """Validate a single reference."""
        if reference.reference_type == "character":
            return self._validate_character_reference(
                reference.referenced_entity, chapter_number, story_state
            )
        elif reference.reference_type == "event":
            return self._validate_event_reference(
                reference.referenced_entity, chapter_number
            )
        elif reference.reference_type == "location":
            return self._validate_location_reference(reference.referenced_entity)
        # ... other types
        
        return True, "unverified"
    
    def _validate_character_reference(
        self,
        character_name: str,
        chapter_number: int,
        story_state: StoryState,
    ) -> tuple[bool, str]:
        """Validate character reference."""
        # Check if character exists
        if character_name not in story_state.character_states:
            # Check if it's a new character being introduced
            if not self.registry.character_exists(character_name):
                return False, f"Character '{character_name}' not defined in story"
        
        # Check if character is alive (if dead, should be in memorial context)
        char_state = story_state.character_states.get(character_name)
        if char_state and char_state.is_dead():
            # This should be caught by ConsistencyVerifier, but flag here too
            return True, "dead_character"
        
        return True, "valid"
    
    def _validate_event_reference(
        self,
        event_description: str,
        current_chapter: int,
    ) -> tuple[bool, str]:
        """Validate event reference."""
        # Check if event exists in story history
        events = self.registry.get_events()
        
        for event in events:
            if self._events_match(event_description, event.description):
                # Event exists, check if it happened before current chapter
                if event.chapter <= current_chapter:
                    return True, "valid"
                else:
                    return False, f"Event references future chapter {event.chapter}"
        
        return True, "unverified"  # Might be implied event
    
    def _extract_character_references(self, content: str) -> list[Reference]:
        """Extract character name references from content."""
        # Use pattern matching and NLP to find character mentions
        references = []
        
        # Pattern: Capitalized names, names before dialogue verbs
        patterns = [
            r"([A-Z][a-z]+)(?:说|道|喊|叫|想|看)",
            r"([A-Z][a-z]+)的",
            r"([一-龥]{2,4})(?:说|道|喊|叫|想|看)",
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                references.append(Reference(
                    reference_type="character",
                    referenced_entity=match.group(1),
                    context=content[max(0, match.start()-20):match.end()+20],
                    position=match.start(),
                    confidence=0.8,
                ))
        
        return references
```

### 3.3 Character Consistency Checker

```python
# src/novel/qa/character_consistency.py

@dataclass
class CharacterConsistencyIssue:
    """An inconsistency in character portrayal."""
    character_name: str
    issue_type: str  # "personality", "ability", "relationship", "appearance"
    description: str
    expected: str
    actual: str
    severity: str
    location: str


class CharacterConsistencyChecker:
    """Checks character portrayal consistency."""
    
    def __init__(self, character_memory: CharacterMemory):
        self.memory = character_memory
    
    async def check_consistency(
        self,
        content: str,
        chapter_number: int,
        appearing_characters: list[str],
    ) -> list[CharacterConsistencyIssue]:
        """
        Check character consistency in content.
        
        Validates:
        1. Personality traits match established profile
        2. Abilities used are within established limits
        3. Relationships portrayed consistently
        4. Physical appearance consistent
        5. Speech patterns match character voice
        """
        issues = []
        
        for char_name in appearing_characters:
            profile = await self.memory.retrieve_character(char_name)
            if not profile:
                continue
            
            # Check personality
            personality_issues = self._check_personality(content, char_name, profile)
            issues.extend(personality_issues)
            
            # Check abilities
            ability_issues = self._check_abilities(content, char_name, profile)
            issues.extend(ability_issues)
            
            # Check relationships
            relationship_issues = self._check_relationships(
                content, char_name, profile, chapter_number
            )
            issues.extend(relationship_issues)
            
            # Check appearance
            appearance_issues = self._check_appearance(content, char_name, profile)
            issues.extend(appearance_issues)
        
        return issues
    
    def _check_personality(
        self,
        content: str,
        char_name: str,
        profile: dict,
    ) -> list[CharacterConsistencyIssue]:
        """Check if character actions match personality."""
        issues = []
        
        personality = profile.get("personality", {})
        traits = personality.get("traits", [])
        
        # Define trait-behavior mappings
        trait_behaviors = {
            "brave": ["fled", "cowered", "hid"],
            "cautious": ["rushed in", "acted impulsively"],
            "honest": ["lied", "deceived"],
            "kind": ["cruel", "mocked", "insulted"],
        }
        
        for trait in traits:
            if trait.lower() in trait_behaviors:
                contradictory = trait_behaviors[trait.lower()]
                for behavior in contradictory:
                    if self._character_did_action(content, char_name, behavior):
                        issues.append(CharacterConsistencyIssue(
                            character_name=char_name,
                            issue_type="personality",
                            description=f"Character with '{trait}' trait acts contrary",
                            expected=f"Behavior consistent with {trait}",
                            actual=f"Character {behavior}",
                            severity="medium",
                            location=self._find_action_location(content, char_name, behavior),
                        ))
        
        return issues
```

### 3.4 Plot Continuity Verifier

```python
# src/novel/qa/plot_continuity.py

@dataclass
class PlotContinuityIssue:
    """An issue with plot continuity."""
    issue_type: str  # "unresolved_thread", "forgotten_event", "timeline_gap"
    description: str
    affected_chapters: list[int]
    severity: str
    suggestion: str


class PlotContinuityVerifier:
    """Verifies plot continuity across chapters."""
    
    def __init__(self, plot_memory: PlotMemory):
        self.memory = plot_memory
    
    async def verify_continuity(
        self,
        current_chapter: int,
        chapter_content: str,
        story_state: StoryState,
    ) -> list[PlotContinuityIssue]:
        """
        Verify plot continuity.
        
        Checks:
        1. Active plot threads are addressed
        2. Important events aren't forgotten
        3. Timeline is consistent
        4. Foreshadowing is paid off
        5. Subplots are resolved
        """
        issues = []
        
        # Get active plot threads
        active_threads = story_state.get_active_plot_threads()
        
        # Check if threads are being addressed
        for thread in active_threads:
            if not self._thread_addressed(chapter_content, thread):
                chapters_since_mention = await self._chapters_since_thread_mention(
                    thread.name, current_chapter
                )
                if chapters_since_mention > 5:  # Thread ignored for 5+ chapters
                    issues.append(PlotContinuityIssue(
                        issue_type="unresolved_thread",
                        description=f"Plot thread '{thread.name}' not addressed for {chapters_since_mention} chapters",
                        affected_chapters=list(range(current_chapter - chapters_since_mention, current_chapter + 1)),
                        severity="medium",
                        suggestion=f"Consider addressing or resolving '{thread.name}' plot thread",
                    ))
        
        # Check foreshadowing payoffs
        foreshadowing = await self.memory.get_foreshadowing_for_chapter(current_chapter)
        for element in foreshadowing:
            if element.get("payoff_chapter") == current_chapter:
                if not self._foreshadowing_paid_off(chapter_content, element):
                    issues.append(PlotContinuityIssue(
                        issue_type="missed_payoff",
                        description=f"Expected payoff for foreshadowing: {element.get('method')}",
                        affected_chapters=[element.get("planted_chapter"), current_chapter],
                        severity="high",
                        suggestion="Add payoff for established foreshadowing",
                    ))
        
        return issues
```

---

## 4. Monitoring & Logging System

### 4.1 Generation Metrics Tracker

```python
# src/novel/monitoring/metrics.py

@dataclass
class GenerationMetrics:
    """Metrics for a single chapter generation."""
    chapter_number: int
    start_time: datetime
    end_time: datetime | None
    duration_seconds: float | None
    attempt_count: int
    token_count: int
    word_count: int
    quality_score: float
    validation_passed: bool
    issues_found: int
    issues_critical: int
    degradation_level: str
    llm_model: str
    error_type: str | None


@dataclass
class AggregateMetrics:
    """Aggregated metrics across chapters."""
    total_chapters: int
    successful_chapters: int
    failed_chapters: int
    total_tokens: int
    total_words: int
    average_quality: float
    average_duration: float
    average_attempts: float
    error_rate: float
    degradation_events: int


class MetricsTracker:
    """Tracks generation metrics for monitoring."""
    
    def __init__(self, storage_path: Path | None = None):
        self.storage_path = storage_path or Path("data/metrics")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.current_metrics: dict[int, GenerationMetrics] = {}
    
    def start_generation(self, chapter_number: int, llm_model: str) -> None:
        """Record start of generation."""
        self.current_metrics[chapter_number] = GenerationMetrics(
            chapter_number=chapter_number,
            start_time=datetime.now(),
            end_time=None,
            duration_seconds=None,
            attempt_count=0,
            token_count=0,
            word_count=0,
            quality_score=0.0,
            validation_passed=False,
            issues_found=0,
            issues_critical=0,
            degradation_level="full",
            llm_model=llm_model,
            error_type=None,
        )
    
    def record_attempt(self, chapter_number: int, tokens: int) -> None:
        """Record a generation attempt."""
        if chapter_number in self.current_metrics:
            self.current_metrics[chapter_number].attempt_count += 1
            self.current_metrics[chapter_number].token_count += tokens
    
    def complete_generation(
        self,
        chapter_number: int,
        word_count: int,
        quality_score: float,
        validation_passed: bool,
        issues: list,
        degradation_level: str,
    ) -> None:
        """Record completion of generation."""
        if chapter_number in self.current_metrics:
            metrics = self.current_metrics[chapter_number]
            metrics.end_time = datetime.now()
            metrics.duration_seconds = (metrics.end_time - metrics.start_time).total_seconds()
            metrics.word_count = word_count
            metrics.quality_score = quality_score
            metrics.validation_passed = validation_passed
            metrics.issues_found = len(issues)
            metrics.issues_critical = len([i for i in issues if i.severity in ("critical", "high")])
            metrics.degradation_level = degradation_level
            
            # Persist metrics
            self._save_metrics(metrics)
    
    def record_error(self, chapter_number: int, error_type: str) -> None:
        """Record generation error."""
        if chapter_number in self.current_metrics:
            self.current_metrics[chapter_number].error_type = error_type
    
    def get_aggregate_metrics(
        self,
        start_chapter: int | None = None,
        end_chapter: int | None = None,
    ) -> AggregateMetrics:
        """Get aggregated metrics for chapter range."""
        metrics_list = self._load_metrics_range(start_chapter, end_chapter)
        
        if not metrics_list:
            return AggregateMetrics(
                total_chapters=0,
                successful_chapters=0,
                failed_chapters=0,
                total_tokens=0,
                total_words=0,
                average_quality=0.0,
                average_duration=0.0,
                average_attempts=0.0,
                error_rate=0.0,
                degradation_events=0,
            )
        
        successful = [m for m in metrics_list if m.validation_passed]
        failed = [m for m in metrics_list if not m.validation_passed]
        
        return AggregateMetrics(
            total_chapters=len(metrics_list),
            successful_chapters=len(successful),
            failed_chapters=len(failed),
            total_tokens=sum(m.token_count for m in metrics_list),
            total_words=sum(m.word_count for m in metrics_list),
            average_quality=sum(m.quality_score for m in metrics_list) / len(metrics_list),
            average_duration=sum(m.duration_seconds or 0 for m in metrics_list) / len(metrics_list),
            average_attempts=sum(m.attempt_count for m in metrics_list) / len(metrics_list),
            error_rate=len(failed) / len(metrics_list),
            degradation_events=sum(1 for m in metrics_list if m.degradation_level != "full"),
        )
    
    def _save_metrics(self, metrics: GenerationMetrics) -> None:
        """Save metrics to storage."""
        path = self.storage_path / f"chapter_{metrics.chapter_number:04d}.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(asdict(metrics), f, indent=2, default=str)
```

### 4.2 Anomaly Detection

```python
# src/novel/monitoring/anomaly_detector.py

@dataclass
class Anomaly:
    """Detected anomaly in generation."""
    anomaly_type: str
    chapter_number: int
    severity: str
    description: str
    metric_value: float
    expected_range: tuple[float, float]
    detected_at: datetime


class AnomalyDetector:
    """Detects anomalies in generation patterns."""
    
    # Thresholds for anomaly detection
    THRESHOLDS = {
        "quality_drop": 2.0,  # Drop by 2 points is anomaly
        "durationSpike": 3.0,  # 3x normal duration
        "attemptSpike": 3,  # 3x normal attempts
        "tokenSpike": 2.0,  # 2x normal tokens
        "errorRateSpike": 0.3,  # Error rate > 30%
    }
    
    def __init__(self, metrics_tracker: MetricsTracker):
        self.metrics = metrics_tracker
        self.baselines: dict[str, tuple[float, float]] = {}
    
    def update_baselines(self, window_size: int = 10) -> None:
        """Update baseline metrics from recent history."""
        recent = self._get_recent_metrics(window_size)
        
        if len(recent) < 5:
            return  # Not enough data
        
        # Calculate baselines
        qualities = [m.quality_score for m in recent]
        durations = [m.duration_seconds or 0 for m in recent]
        attempts = [m.attempt_count for m in recent]
        tokens = [m.token_count for m in recent]
        
        self.baselines = {
            "quality": (self._percentile(qualities, 25), self._percentile(qualities, 75)),
            "duration": (self._percentile(durations, 25), self._percentile(durations, 75)),
            "attempts": (self._percentile(attempts, 25), self._percentile(attempts, 75)),
            "tokens": (self._percentile(tokens, 25), self._percentile(tokens, 75)),
        }
    
    def detect_anomalies(self, current: GenerationMetrics) -> list[Anomaly]:
        """Detect anomalies in current metrics."""
        anomalies = []
        
        if not self.baselines:
            return anomalies
        
        # Quality drop detection
        quality_low, quality_high = self.baselines["quality"]
        if current.quality_score < quality_low - self.THRESHOLDS["qualityDrop"]:
            anomalies.append(Anomaly(
                anomaly_type="quality_drop",
                chapter_number=current.chapter_number,
                severity="high",
                description=f"Quality score {current.quality_score:.1f} significantly below baseline ({quality_low:.1f}-{quality_high:.1f})",
                metric_value=current.quality_score,
                expected_range=(quality_low, quality_high),
                detected_at=datetime.now(),
            ))
        
        # Duration spike detection
        duration_low, duration_high = self.baselines["duration"]
        if current.duration_seconds and current.duration_seconds > duration_high * self.THRESHOLDS["durationSpike"]:
            anomalies.append(Anomaly(
                anomaly_type="duration_spike",
                chapter_number=current.chapter_number,
                severity="medium",
                description=f"Generation took {current.duration_seconds:.1f}s, {self.THRESHOLDS['durationSpike']}x normal",
                metric_value=current.duration_seconds,
                expected_range=(duration_low, duration_high),
                detected_at=datetime.now(),
            ))
        
        # Attempt spike detection
        attempts_low, attempts_high = self.baselines["attempts"]
        if current.attempt_count > attempts_high * self.THRESHOLDS["attemptSpike"]:
            anomalies.append(Anomaly(
                anomaly_type="attempt_spike",
                chapter_number=current.chapter_number,
                severity="medium",
                description=f"Required {current.attempt_count} attempts, {self.THRESHOLDS['attemptSpike']}x normal",
                metric_value=float(current.attempt_count),
                expected_range=(float(attempts_low), float(attempts_high)),
                detected_at=datetime.now(),
            ))
        
        return anomalies
    
    def _percentile(self, data: list[float], percentile: int) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
```

### 4.3 Performance Monitoring

```python
# src/novel/monitoring/performance.py

@dataclass
class PerformanceReport:
    """Performance analysis report."""
    period_start: datetime
    period_end: datetime
    chapters_generated: int
    total_time_hours: float
    average_chapter_time_minutes: float
    token_efficiency: float  # words per token
    cost_estimate: float  # Estimated API cost
    bottlenecks: list[dict]
    recommendations: list[str]


class PerformanceMonitor:
    """Monitors and analyzes generation performance."""
    
    def __init__(
        self,
        metrics_tracker: MetricsTracker,
        anomaly_detector: AnomalyDetector,
    ):
        self.metrics = metrics_tracker
        self.detector = anomaly_detector
    
    def generate_report(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> PerformanceReport:
        """Generate performance report for time period."""
        metrics_list = self._get_metrics_in_range(start_time, end_time)
        
        if not metrics_list:
            return PerformanceReport(
                period_start=start_time,
                period_end=end_time,
                chapters_generated=0,
                total_time_hours=0.0,
                average_chapter_time_minutes=0.0,
                token_efficiency=0.0,
                cost_estimate=0.0,
                bottlenecks=[],
                recommendations=[],
            )
        
        total_time = sum(m.duration_seconds or 0 for m in metrics_list)
        total_words = sum(m.word_count for m in metrics_list)
        total_tokens = sum(m.token_count for m in metrics_list)
        
        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(metrics_list)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics_list, bottlenecks)
        
        return PerformanceReport(
            period_start=start_time,
            period_end=end_time,
            chapters_generated=len(metrics_list),
            total_time_hours=total_time / 3600,
            average_chapter_time_minutes=total_time / len(metrics_list) / 60,
            token_efficiency=total_words / total_tokens if total_tokens > 0 else 0,
            cost_estimate=self._estimate_cost(total_tokens),
            bottlenecks=bottlenecks,
            recommendations=recommendations,
        )
    
    def _identify_bottlenecks(self, metrics: list[GenerationMetrics]) -> list[dict]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        # High retry rate
        high_retry = [m for m in metrics if m.attempt_count > 3]
        if len(high_retry) > len(metrics) * 0.2:
            bottlenecks.append({
                "type": "high_retry_rate",
                "affected_chapters": len(high_retry),
                "description": f"{len(high_retry)} chapters required >3 attempts",
                "impact": "Increases generation time and token usage",
            })
        
        # Quality issues
        low_quality = [m for m in metrics if m.quality_score < 7.0]
        if len(low_quality) > len(metrics) * 0.1:
            bottlenecks.append({
                "type": "quality_issues",
                "affected_chapters": len(low_quality),
                "description": f"{len(low_quality)} chapters scored <7.0",
                "impact": "May require manual review or regeneration",
            })
        
        # Token inefficiency
        inefficient = [m for m in metrics if m.word_count / max(m.token_count, 1) < 0.3]
        if len(inefficient) > len(metrics) * 0.2:
            bottlenecks.append({
                "type": "token_inefficiency",
                "affected_chapters": len(inefficient),
                "description": "Low word-to-token ratio indicating verbose generation",
                "impact": "Increases API costs",
            })
        
        return bottlenecks
    
    def _generate_recommendations(
        self,
        metrics: list[GenerationMetrics],
        bottlenecks: list[dict],
    ) -> list[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        for bottleneck in bottlenecks:
            if bottleneck["type"] == "high_retry_rate":
                recommendations.append(
                    "Consider adjusting quality thresholds or improving prompt templates "
                    "to reduce retry rates"
                )
            elif bottleneck["type"] == "quality_issues":
                recommendations.append(
                    "Review failed chapters to identify patterns and adjust "
                    "generation parameters or validation rules"
                )
            elif bottleneck["type"] == "token_inefficiency":
                recommendations.append(
                    "Optimize prompts to encourage more concise generation "
                    "or implement output length constraints"
                )
        
        # General recommendations
        avg_quality = sum(m.quality_score for m in metrics) / len(metrics)
        if avg_quality < 8.0:
            recommendations.append(
                "Overall quality below target. Consider enhancing learning hints "
                "or adjusting genre-specific writing guidelines."
            )
        
        return recommendations
```

### 4.4 Structured Logging

```python
# src/novel/monitoring/logging_config.py

import logging
import json
from datetime import datetime
from typing import Any


class StructuredLogger:
    """Structured JSON logging for generation events."""
    
    def __init__(self, name: str, log_dir: Path | None = None):
        self.logger = logging.getLogger(name)
        self.log_dir = log_dir or Path("logs/generation")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Current session log
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_log: list[dict] = []
    
    def log_generation_start(
        self,
        chapter_number: int,
        context: dict[str, Any],
    ) -> None:
        """Log generation start event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "generation_start",
            "chapter_number": chapter_number,
            "context": context,
        }
        self._log_event(event)
    
    def log_generation_complete(
        self,
        chapter_number: int,
        result: dict[str, Any],
    ) -> None:
        """Log generation completion event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "generation_complete",
            "chapter_number": chapter_number,
            "result": result,
        }
        self._log_event(event)
    
    def log_validation(
        self,
        chapter_number: int,
        validation_type: str,
        result: dict[str, Any],
    ) -> None:
        """Log validation event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "validation",
            "validation_type": validation_type,
            "chapter_number": chapter_number,
            "result": result,
        }
        self._log_event(event)
    
    def log_error(
        self,
        chapter_number: int,
        error_type: str,
        error_message: str,
        traceback: str | None = None,
    ) -> None:
        """Log error event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "error",
            "chapter_number": chapter_number,
            "error_type": error_type,
            "error_message": error_message,
            "traceback": traceback,
        }
        self._log_event(event)
    
    def log_recovery(
        self,
        chapter_number: int,
        recovery_type: str,
        details: dict[str, Any],
    ) -> None:
        """Log recovery action."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "recovery",
            "recovery_type": recovery_type,
            "chapter_number": chapter_number,
            "details": details,
        }
        self._log_event(event)
    
    def _log_event(self, event: dict) -> None:
        """Log event to session and file."""
        self.session_log.append(event)
        self.logger.info(json.dumps(event, ensure_ascii=False))
    
    def save_session(self) -> Path:
        """Save session log to file."""
        path = self.log_dir / f"session_{self.session_id}.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                "session_id": self.session_id,
                "events": self.session_log,
            }, f, indent=2, ensure_ascii=False)
        return path
```

---

## 5. Centralized Story Registry

### 5.1 Story Registry

```python
# src/novel/registry/story_registry.py

@dataclass
class ChapterRecord:
    """Record of a completed chapter."""
    number: int
    title: str
    content_hash: str
    word_count: int
    created_at: datetime
    quality_score: float
    state_snapshot_id: str


@dataclass
class EventRecord:
    """Record of a story event."""
    chapter: int
    description: str
    event_type: str  # "character_death", "location_change", "relationship", etc.
    entities: list[str]
    importance: str  # "critical", "major", "minor"


class StoryRegistry:
    """
    Centralized registry for story elements.
    
    Prevents:
    - Title duplication
    - Missing chapters
    - Orphaned references
    """
    
    def __init__(self, novel_id: str, storage_path: Path):
        self.novel_id = novel_id
        self.storage_path = storage_path / novel_id
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory indices
        self._chapters: dict[int, ChapterRecord] = {}
        self._events: list[EventRecord] = []
        self._characters: set[str] = set()
        self._locations: set[str] = set()
        self._titles: dict[int, str] = {}  # chapter -> title
        
        self._load_registry()
    
    def register_chapter(
        self,
        number: int,
        title: str,
        content: str,
        quality_score: float,
        state_snapshot_id: str,
    ) -> bool:
        """Register a completed chapter."""
        # Validate chapter number
        if number in self._chapters:
            logger.error(f"Chapter {number} already exists")
            return False
        
        # Check for sequence gap (except chapter 1)
        if number > 1 and (number - 1) not in self._chapters:
            logger.error(f"Cannot register chapter {number}: chapter {number-1} missing")
            return False
        
        # Check title uniqueness
        title_text = self._extract_title_text(title)
        for ch, existing_title in self._titles.items():
            if self._extract_title_text(existing_title) == title_text:
                logger.error(f"Title '{title_text}' already used in chapter {ch}")
                return False
        
        # Register chapter
        record = ChapterRecord(
            number=number,
            title=title,
            content_hash=hashlib.sha256(content.encode()).hexdigest()[:16],
            word_count=len(content.split()),
            created_at=datetime.now(),
            quality_score=quality_score,
            state_snapshot_id=state_snapshot_id,
        )
        
        self._chapters[number] = record
        self._titles[number] = title
        
        self._save_registry()
        return True
    
    def register_event(
        self,
        chapter: int,
        description: str,
        event_type: str,
        entities: list[str],
        importance: str = "major",
    ) -> None:
        """Register a story event."""
        event = EventRecord(
            chapter=chapter,
            description=description,
            event_type=event_type,
            entities=entities,
            importance=importance,
        )
        self._events.append(event)
        self._save_registry()
    
    def register_character(self, name: str) -> None:
        """Register a character."""
        self._characters.add(name)
        self._save_registry()
    
    def register_location(self, name: str) -> None:
        """Register a location."""
        self._locations.add(name)
        self._save_registry()
    
    def chapter_exists(self, number: int) -> bool:
        """Check if chapter exists."""
        return number in self._chapters
    
    def get_missing_chapters(self, up_to: int) -> list[int]:
        """Find gaps in chapter sequence."""
        existing = set(self._chapters.keys())
        expected = set(range(1, up_to + 1))
        return sorted(expected - existing)
    
    def get_events(self, chapter: int | None = None) -> list[EventRecord]:
        """Get events, optionally filtered by chapter."""
        if chapter is None:
            return self._events
        return [e for e in self._events if e.chapter <= chapter]
    
    def character_exists(self, name: str) -> bool:
        """Check if character is registered."""
        return name in self._characters
    
    def location_exists(self, name: str) -> bool:
        """Check if location is registered."""
        return name in self._locations
    
    def get_chapters(self, start: int, end: int) -> list[ChapterRecord]:
        """Get chapters in range."""
        return [
            self._chapters[n]
            for n in range(start, end + 1)
            if n in self._chapters
        ]
    
    def _load_registry(self) -> None:
        """Load registry from storage."""
        registry_path = self.storage_path / "registry.json"
        if registry_path.exists():
            with open(registry_path, encoding='utf-8') as f:
                data = json.load(f)
            
            for ch_data in data.get("chapters", []):
                record = ChapterRecord(**ch_data)
                self._chapters[record.number] = record
                self._titles[record.number] = record.title
            
            for ev_data in data.get("events", []):
                self._events.append(EventRecord(**ev_data))
            
            self._characters = set(data.get("characters", []))
            self._locations = set(data.get("locations", []))
    
    def _save_registry(self) -> None:
        """Save registry to storage."""
        registry_path = self.storage_path / "registry.json"
        data = {
            "chapters": [asdict(ch) for ch in self._chapters.values()],
            "events": [asdict(ev) for ev in self._events],
            "characters": list(self._characters),
            "locations": list(self._locations),
        }
        
        # Atomic write
        temp_path = registry_path.with_suffix(".tmp")
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        temp_path.rename(registry_path)
```

---

## 6. Implementation Plan

### 6.1 Phase 1: Foundation (Week 1-2)

**Priority: Critical**

1. **Create StoryRegistry** (`src/novel/registry/`)
   - Chapter registration with sequence validation
   - Title uniqueness enforcement
   - Event tracking
   - Character/location registry

2. **Enhance CheckpointManager**
   - Integrate with StateCheckpointManager
   - Add RollbackManager
   - Full state preservation

3. **Create PreGenerationValidator**
   - Chapter sequence check
   - Character definition validation
   - Plot thread reference validation

### 6.2 Phase 2: Validation Layer (Week 3-4)

**Priority: High**

1. **PostGenerationVerifier**
   - Content validation
   - Duplicate detection
   - Reference validation
   - Word count bounds

2. **ReferenceValidator**
   - Character reference validation
   - Event reference validation
   - Location validation

3. **CrossChapterValidator**
   - Character journey tracking
   - Plot thread continuity
   - Location transition validation

### 6.3 Phase 3: Error Recovery (Week 5-6)

**Priority: High**

1. **RetryHandler**
   - Exponential backoff
   - Retryable error classification
   - Configurable thresholds

2. **GracefulDegradation**
   - Degradation levels
   - Automatic recovery
   - Quality/quantity trade-offs

3. **RollbackManager**
   - Rollback point creation
   - State restoration
   - History tracking

### 6.4 Phase 4: Quality Assurance (Week 7-8)

**Priority: High**

1. **TitleValidator**
   - Format enforcement
   - Uniqueness checking
   - Similarity detection

2. **CharacterConsistencyChecker**
   - Personality consistency
   - Ability limits
   - Relationship tracking

3. **PlotContinuityVerifier**
   - Thread addressing
   - Foreshadowing payoff
   - Timeline consistency

### 6.5 Phase 5: Monitoring (Week 9-10)

**Priority: Medium**

1. **MetricsTracker**
   - Generation metrics
   - Aggregate statistics
   - Persistence

2. **AnomalyDetector**
   - Baseline calculation
   - Anomaly detection
   - Alerting

3. **PerformanceMonitor**
   - Performance reports
   - Bottleneck identification
   - Recommendations

4. **StructuredLogger**
   - JSON logging
   - Session tracking
   - Event history

---

## 7. Test Strategy

### 7.1 Unit Tests

```python
# tests/novel/validation/test_pre_generator.py

class TestPreGenerationValidator:
    """Tests for pre-generation validation."""
    
    def test_validate_chapter_sequence(self):
        """Should fail if previous chapter missing."""
        validator = PreGenerationValidator()
        context = PreGenerationContext(
            chapter_number=5,
            expected_characters=["Alice"],
            required_plot_threads=[],
            previous_chapter_state=None,
            title_format="Chapter {n}: {title}",
            min_word_count=1000,
            max_word_count=5000,
        )
        
        result = validator.validate(context)
        
        assert not result.is_valid
        assert "chapter 4 does not exist" in " ".join(result.blockers).lower()
    
    def test_validate_missing_character(self):
        """Should warn if expected character not defined."""
        validator = PreGenerationValidator()
        # Setup: no characters defined
        
        context = PreGenerationContext(
            chapter_number=1,
            expected_characters=["Alice", "Bob"],
            required_plot_threads=[],
            previous_chapter_state=None,
            title_format="Chapter {n}: {title}",
            min_word_count=1000,
            max_word_count=5000,
        )
        
        result = validator.validate(context)
        
        assert not result.context_ready
        assert len(result.missing_prerequisites) == 2
    
    def test_validate_passes_with_all_prerequisites(self):
        """Should pass when all prerequisites met."""
        validator = PreGenerationValidator()
        validator._character_defined = lambda x: x == "Alice"
        
        context = PreGenerationContext(
            chapter_number=1,
            expected_characters=["Alice"],
            required_plot_threads=[],
            previous_chapter_state=None,
            title_format="Chapter {n}: {title}",
            min_word_count=1000,
            max_word_count=5000,
        )
        
        result = validator.validate(context)
        
        assert result.is_valid
        assert result.context_ready


# tests/novel/qa/test_title_validator.py

class TestTitleValidator:
    """Tests for title validation."""
    
    def test_format_chinese_numbered_title(self):
        """Should format Chinese numbered title correctly."""
        validator = TitleValidator(registry=Mock())
        
        result = validator.validate_title(
            raw_title="开端",
            chapter_number=1,
            format_type="numbered",
            language="zh",
        )
        
        assert result.is_valid
        assert result.formatted_title == "第1章：开端"
    
    def test_reject_duplicate_title(self):
        """Should reject duplicate title."""
        registry = Mock()
        registry.get_chapters = Mock(return_value=[])
        
        validator = TitleValidator(registry=registry)
        validator.used_titles = {1: "第1章：开端"}
        
        result = validator.validate_title(
            raw_title="开端",
            chapter_number=2,
            format_type="numbered",
            language="zh",
        )
        
        assert not result.is_valid
        assert any("duplicate" in i.lower() for i in result.issues)
    
    def test_reject_similar_title(self):
        """Should reject very similar title."""
        validator = TitleValidator(registry=Mock())
        validator.used_titles = {1: "第1章：黑暗降临"}
        
        result = validator.validate_title(
            raw_title="黑暗降临",
            chapter_number=2,
            format_type="numbered",
            language="zh",
        )
        
        assert not result.is_valid
        assert any("similar" in i.lower() for i in result.issues)


# tests/novel/recovery/test_retry_handler.py

class TestRetryHandler:
    """Tests for retry handler."""
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Should retry on retryable error."""
        handler = RetryHandler(config=RetryConfig(
            max_attempts=3,
            base_delay_seconds=0.1,
        ))
        
        call_count = 0
        
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RetryableError("Temporary failure")
            return "success"
        
        result = await handler.execute_with_retry(failing_operation)
        
        assert result.success
        assert result.attempts == 3
        assert result.final_content == "success"
    
    @pytest.mark.asyncio
    async def test_no_retry_on_non_retryable(self):
        """Should not retry on non-retryable error."""
        handler = RetryHandler()
        
        async def failing_operation():
            raise NonRetryableError("Permanent failure")
        
        result = await handler.execute_with_retry(failing_operation)
        
        assert not result.success
        assert result.attempts == 1
    
    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Should use exponential backoff."""
        handler = RetryHandler(config=RetryConfig(
            max_attempts=3,
            base_delay_seconds=0.1,
            exponential_base=2.0,
            jitter=False,
        ))
        
        delays = []
        
        async def tracking_operation():
            delays.append(time.time())
            if len(delays) < 3:
                raise RetryableError("Retry")
            return "done"
        
        start = time.time()
        await handler.execute_with_retry(tracking_operation)
        
        # Check delays are approximately exponential
        # First retry: ~0.1s, Second retry: ~0.2s
        assert handler._calculate_delay(1) == pytest.approx(0.1, rel=0.1)
        assert handler._calculate_delay(2) == pytest.approx(0.2, rel=0.1)
```

### 7.2 Integration Tests

```python
# tests/novel/integration/test_generation_pipeline.py

class TestRobustGenerationPipeline:
    """Integration tests for robust generation pipeline."""
    
    @pytest.fixture
    def pipeline(self):
        """Create pipeline with all components."""
        registry = StoryRegistry(novel_id="test", storage_path=Path("data/test"))
        checkpoint_manager = CheckpointManager(Path("data/test/checkpoints"))
        retry_handler = RetryHandler()
        validator = PreGenerationValidator(registry=registry)
        
        return {
            "registry": registry,
            "checkpoint": checkpoint_manager,
            "retry": retry_handler,
            "validator": validator,
        }
    
    @pytest.mark.asyncio
    async def test_full_generation_flow(self, pipeline):
        """Test complete generation flow with validation."""
        registry = pipeline["registry"]
        validator = pipeline["validator"]
        
        # Register prerequisites
        registry.register_character("Alice")
        registry.register_character("Bob")
        
        # Validate pre-generation
        context = PreGenerationContext(
            chapter_number=1,
            expected_characters=["Alice", "Bob"],
            required_plot_threads=[],
            previous_chapter_state=None,
            title_format="Chapter {n}: {title}",
            min_word_count=500,
            max_word_count=5000,
        )
        
        pre_result = validator.validate(context)
        assert pre_result.is_valid
        
        # Simulate generation
        content = "Chapter 1: The Beginning\n\n" + "Alice and Bob met. " * 100
        
        # Register chapter
        success = registry.register_chapter(
            number=1,
            title="Chapter 1: The Beginning",
            content=content,
            quality_score=8.5,
            state_snapshot_id="snap_001",
        )
        
        assert success
        assert registry.chapter_exists(1)
    
    @pytest.mark.asyncio
    async def test_missing_chapter_detection(self, pipeline):
        """Test detection of missing chapters."""
        registry = pipeline["registry"]
        
        # Register chapter 1
        registry.register_chapter(1, "Chapter 1", "Content", 8.0, "snap_1")
        
        # Try to register chapter 3 (skip 2)
        success = registry.register_chapter(3, "Chapter 3", "Content", 8.0, "snap_3")
        
        assert not success  # Should fail
        
        # Check missing detection
        missing = registry.get_missing_chapters(3)
        assert missing == [2]
    
    @pytest.mark.asyncio
    async def test_recovery_from_failure(self, pipeline):
        """Test recovery from generation failure."""
        checkpoint = pipeline["checkpoint"]
        rollback = RollbackManager(
            state_manager=StateCheckpointManager(Path("data/test/states")),
            content_manager=checkpoint,
        )
        
        # Create rollback point
        state = GenerationState(
            novel_id="test",
            current_chapter=5,
            completed_chapters=[1, 2, 3, 4],
            story_state=StoryState(chapter=4, location="Castle"),
            outline={},
            characters={},
            world_context={},
            generation_log=[],
            created_at=datetime.now(),
            checksum="abc123",
        )
        
        rollback_point = rollback.create_rollback_point(
            chapter_number=5,
            reason="Before risky operation",
            state=state,
            content="Chapter 5 content",
        )
        
        # Simulate failure and rollback
        result = rollback.rollback(rollback_point)
        
        assert result is not None
        assert result[0].current_chapter == 5
```

### 7.3 Edge Case Tests

```python
# tests/novel/edge_cases/test_failure_modes.py

class TestFailureModes:
    """Tests for edge cases and failure modes."""
    
    def test_empty_content_detection(self):
        """Should detect empty/short content."""
        verifier = PostGenerationVerifier()
        
        result = verifier.verify(
            content="",  # Empty content
            chapter_number=1,
            expected=Mock(min_word_count=1000),
            story_state=Mock(),
        )
        
        assert not result.passed
        assert any(i.type == "empty_content" for i in result.issues)
    
    def test_duplicate_content_detection(self):
        """Should detect duplicate content."""
        registry = Mock()
        registry.content_exists = Mock(return_value=True)
        
        verifier = PostGenerationVerifier(registry=registry)
        
        result = verifier.verify(
            content="Duplicate content",
            chapter_number=2,
            expected=Mock(min_word_count=100),
            story_state=Mock(),
        )
        
        assert not result.passed
        assert any(i.type == "duplicate_content" for i in result.issues)
    
    def test_hallucinated_event_reference(self):
        """Should detect references to non-existent events."""
        validator = ReferenceValidator(story_registry=Mock())
        validator.registry.get_events = Mock(return_value=[])
        
        content = "Alice remembered the Battle of Shadowfall, where Bob died."
        
        result = validator.validate_references(
            content=content,
            chapter_number=5,
            story_state=Mock(),
        )
        
        # Should flag Battle of Shadowfall as unverified
        assert len(result.invalid_references) > 0 or len(result.unverified_references) > 0
    
    def test_dead_character_appearance(self):
        """Should detect dead character appearing alive."""
        story_state = StoryState(
            chapter=5,
            location="Castle",
            character_states={
                "Bob": CharacterState(
                    name="Bob",
                    status="dead",
                    location="Castle",
                    physical_form="human",
                )
            },
        )
        
        content = """
        Alice walked into the room.
        Bob stood up and greeted her warmly.
        "Welcome back," Bob said with a smile.
        """
        
        verifier = ConsistencyVerifier()
        result = verifier.verify(content, 5, story_state)
        
        assert not result.is_consistent
        assert any(
            i.inconsistency_type == InconsistencyType.DEAD_CHARACTER_APPEARANCE
            for i in result.inconsistencies
        )
    
    def test_character_teleportation(self):
        """Should detect impossible location changes."""
        chapters = [
            Mock(content="Alice was in the Northern Castle.", chapter_number=1),
            Mock(content="Alice appeared in the Southern Port.", chapter_number=2),
        ]
        
        validator = CrossChapterValidator()
        issues = validator.validate_range(1, 2, Mock(get_chapters=Mock(return_value=chapters)))
        
        teleport_issues = [i for i in issues if i.issue_type == "location_teleport"]
        assert len(teleport_issues) > 0
```

---

## 8. Summary

This design provides a comprehensive solution to address all identified failure modes:

| Failure Mode | Solution Component |
|-------------|-------------------|
| Title Duplication | TitleValidator + StoryRegistry |
| Content Discontinuity | ContinuityManager + CrossChapterValidator |
| Hallucinated References | ReferenceValidator + StoryRegistry |
| Missing Chapters | PreGenerationValidator + StoryRegistry |
| Inconsistent Backstory | CharacterConsistencyChecker + PlotContinuityVerifier |

### Key Benefits

1. **Prevention Over Cure**: Validation before generation prevents many issues
2. **Graceful Degradation**: System continues operating under stress
3. **Full Recovery**: Checkpointing enables complete state restoration
4. **Observable**: Comprehensive monitoring and logging
5. **Testable**: Clear test strategy for all components
