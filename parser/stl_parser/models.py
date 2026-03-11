"""
STL Parser Data Models

This module defines Pydantic models for representing STL statements and their components.
All models are based on the STL v1.0 Core Specification and Supplement.
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import re


class AnchorType(str, Enum):
    """9 canonical anchor types from STL specification.

    SEMANTIC LAYER:
        CONCEPT: Abstract ideas, theories, properties, categories
        RELATIONAL: Logical or semantic relations

    ENTITY LAYER:
        EVENT: Actions, processes, temporal events
        ENTITY: Physical or perceivable objects
        NAME: Uniquely identified named entities

    STRUCTURAL LAYER:
        AGENT: Active or cognitive subjects
        QUESTION: Points of inquiry, unresolved tension
        VERIFIER: Evaluation, testing, validation mechanisms
        PATH_SEGMENT: Intermediate states, transitions
    """

    CONCEPT = "Concept"
    RELATIONAL = "Relational"
    EVENT = "Event"
    ENTITY = "Entity"
    NAME = "Name"
    AGENT = "Agent"
    QUESTION = "Question"
    VERIFIER = "Verifier"
    PATH_SEGMENT = "PathSegment"


class PathType(str, Enum):
    """6 primary path types based on semantic function."""

    SEMANTIC = "Semantic"  # Definitional, categorical
    ACTION = "Action"  # Agency and intentionality
    COGNITIVE = "Cognitive"  # Epistemic relations
    CAUSAL = "Causal"  # Cause-effect mechanisms
    INFERENTIAL = "Inferential"  # Logical reasoning
    REFLEXIVE = "Reflexive"  # Self-reference


class Anchor(BaseModel):
    """Represents an STL anchor: [Name] or [Namespace:Name].

    Args:
        name: Anchor name (alphanumeric + underscore + Unicode)
        namespace: Optional namespace for disambiguation
        type: Optional anchor type classification

    Example:
        >>> a1 = Anchor(name="Concept")
        >>> a2 = Anchor(name="Energy", namespace="Physics")
        >>> a3 = Anchor(name="ChineseConcept")    ")
    """

    name: str
    namespace: Optional[str] = None
    type: Optional[AnchorType] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate anchor name according to spec.

        Rules:
        - Alphanumeric + underscore + Unicode letters/digits
        - No special characters except _ and :
        - Maximum 64 characters (recommended)
        - Cannot be empty

        Raises:
            ValueError: If name violates constraints
        """
        if not v:
            raise ValueError("Anchor name cannot be empty")

        # Allow Unicode letters, digits, underscore, and hyphen
        # \w matches [A-Za-z0-9_] plus Unicode word characters
        # Hyphen (-) allowed after first char; safe inside bracket-delimited anchors
        if not re.match(r"^[\w\u4e00-\u9fff\u0600-\u06ff][\w\u4e00-\u9fff\u0600-\u06ff\-]*$", v, re.UNICODE):
            raise ValueError(
                f"Anchor name '{v}' must be alphanumeric + underscore + hyphen "
                "(other special characters not allowed)"
            )

        if len(v) > 64:
            raise ValueError(f"Anchor name too long: {len(v)} > 64 characters")

        # Check for reserved names
        reserved = ["NULL", "UNDEFINED", "ANY", "NONE", "TRUE", "FALSE", "SYSTEM", "GLOBAL", "LOCAL"]
        if v in reserved:
            raise ValueError(f"Anchor name '{v}' is reserved")

        return v

    @field_validator("namespace")
    @classmethod
    def validate_namespace(cls, v: Optional[str]) -> Optional[str]:
        """Validate namespace format."""
        if v is None:
            return v

        # Namespace can contain dots for hierarchy
        if not re.match(r"^[\w\.][\w\.]*$", v, re.UNICODE):
            raise ValueError(f"Invalid namespace format: {v}")

        return v

    def __str__(self) -> str:
        """String representation in STL format."""
        if self.namespace:
            return f"[{self.namespace}:{self.name}]"
        return f"[{self.name}]"

    def __hash__(self) -> int:
        """Hash for use in sets and dicts."""
        return hash((self.namespace, self.name))


class Modifier(BaseModel):
    """All standard modifier fields from STL specification.

    Fields are organized by category:
    - Temporal: time, duration, frequency, tense
    - Spatial: location, domain, scope
    - Logical: certainty, confidence, necessity, rule
    - Provenance: source, author, timestamp, version
    - Affective: emotion, intensity, valence
    - Value: value, alignment, priority
    - Causal: cause, effect, strength, conditionality
    - Cognitive: intent, focus, perspective
    - Mood: mood, modality

    All fields are optional. Type validation is performed automatically.
    """

    # Temporal Modifiers
    time: Optional[str] = Field(None, description="Temporal context (Past/Present/Future or ISO 8601)")
    duration: Optional[str] = Field(None, description="Duration in ISO 8601 format")
    frequency: Optional[str] = Field(None, description="Frequency (Once/Daily/Weekly/Recurring)")
    tense: Optional[str] = Field(None, description="Grammatical tense (Past/Present/Future)")

    # Spatial Modifiers
    location: Optional[str] = Field(None, description="Geographic location or identifier")
    domain: Optional[str] = Field(None, description="Domain identifier")
    scope: Optional[str] = Field(None, description="Scope (Global/Local/Regional/Organizational)")

    # Logical Modifiers
    certainty: Optional[float] = Field(None, ge=0.0, le=1.0, description="Certainty level [0.0-1.0]")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence level [0.0-1.0]")
    necessity: Optional[str] = Field(
        None, description="Modal necessity (Possible/Contingent/Necessary/Impossible)"
    )
    rule: Optional[str] = Field(
        None, description="Rule type (causal/correlative/logical/definitional/empirical)"
    )

    # Provenance Modifiers
    source: Optional[str] = Field(None, description="Source reference (URI)")
    author: Optional[str] = Field(None, description="Author or creator")
    timestamp: Optional[str] = Field(None, description="Timestamp in ISO 8601")
    version: Optional[str] = Field(None, description="Version identifier")

    # Affective Modifiers
    emotion: Optional[str] = Field(
        None, description="Emotion (Joy/Fear/Anger/Empathy/Neutral/Hope/Sadness)"
    )
    intensity: Optional[float] = Field(None, ge=0.0, le=1.0, description="Intensity level [0.0-1.0]")
    valence: Optional[str] = Field(None, description="Valence (Positive/Negative/Neutral/Mixed)")

    # Value Modifiers
    value: Optional[str] = Field(None, description="Value orientation (Good/Neutral/Bad/Evil/Beneficial)")
    alignment: Optional[str] = Field(None, description="Alignment (Positive/Negative/Neutral/Mixed)")
    priority: Optional[Any] = Field(None, description="Priority (High/Medium/Low or 1-10)")

    # Causal Modifiers
    cause: Optional[str] = Field(None, description="Cause description")
    effect: Optional[str] = Field(None, description="Effect description")
    strength: Optional[float] = Field(None, ge=0.0, le=1.0, description="Causal strength [0.0-1.0]")
    conditionality: Optional[str] = Field(
        None, description="Conditionality (Sufficient/Necessary/Both/Neither)"
    )

    # Cognitive Modifiers
    intent: Optional[str] = Field(None, description="Intent (Explain/Predict/Evaluate/Compare/Describe)")
    focus: Optional[str] = Field(None, description="Focus (Subject/Predicate/Relationship/Context)")
    perspective: Optional[str] = Field(
        None, description="Perspective (FirstPerson/SecondPerson/ThirdPerson/Objective)"
    )

    # Mood Modifiers
    mood: Optional[str] = Field(
        None, description="Mood (Assertion/Question/Request/Doubt/Conditional/Imperative)"
    )
    modality: Optional[str] = Field(None, description="Modality (Indicative/Subjunctive/Imperative)")

    # Custom fields (for extensions)
    custom: Dict[str, Any] = Field(default_factory=dict, description="Custom extension fields")

    model_config = {"extra": "allow"}  # Allow additional fields for extensions


class Statement(BaseModel):
    """Represents one STL statement: [A] -> [B] ::mod(...).

    Args:
        source: Source anchor
        target: Target anchor
        arrow: Arrow symbol (-> or ->)
        modifiers: Optional modifiers
        path_type: Optional path type classification
        line: Optional line number in source text
        column: Optional column number in source text

    Example:
        >>> stmt = Statement(
        ...     source=Anchor(name="A"),
        ...     target=Anchor(name="B"),
        ...     modifiers=Modifier(confidence=0.95)
        ... )
    """

    source: Anchor
    target: Anchor
    arrow: str = Field(default="\u2192", pattern=r"^(\u2192|->)$")
    modifiers: Optional[Modifier] = None
    path_type: Optional[PathType] = None
    line: Optional[int] = None
    column: Optional[int] = None

    def __str__(self) -> str:
        """String representation in STL format."""
        s = f"{self.source} -> {self.target}"

        if self.modifiers:
            mod_dict = self.modifiers.model_dump(exclude_none=True, exclude={"custom"})
            # Include custom fields — validation and transport are separate concerns
            if self.modifiers.custom:
                mod_dict.update(self.modifiers.custom)
            if mod_dict:
                # Sort keys for deterministic output
                sorted_keys = sorted(mod_dict.keys())

                mod_parts = []
                for k in sorted_keys:
                    v = mod_dict[k]
                    if isinstance(v, bool):
                        mod_parts.append(f"{k}={str(v).lower()}")
                    elif isinstance(v, str):
                        mod_parts.append(f'{k}="{v}"')
                    else:
                        mod_parts.append(f"{k}={v}")

                mod_str = ", ".join(mod_parts)
                s += f" ::mod({mod_str})"

        return s

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Statement):
            return NotImplemented
        # Compare all significant attributes for equality
        return (
            self.source == other.source
            and self.target == other.target
            and self.arrow == other.arrow
            and self.modifiers == other.modifiers
            and self.path_type == other.path_type
            # line and column are metadata, not part of semantic equality
        )

    def __hash__(self) -> int:
        # Generate a hash based on the string representation, which is now deterministic
        # and includes all relevant semantic information.
        return hash(str(self))


class ParseError(BaseModel):
    """Represents a parsing error.

    Args:
        code: Error code (E001-E199)
        message: Error message
        line: Optional line number
        column: Optional column number
        suggestion: Optional suggestion for fixing
    """

    code: str = Field(..., pattern=r"^E\d{3}$")
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None


class ParseWarning(BaseModel):
    """Represents a parsing warning.

    Args:
        code: Warning code (W001-W099)
        message: Warning message
        line: Optional line number
        column: Optional column number
    """

    code: str = Field(..., pattern=r"^W\d{3}$")
    message: str
    line: Optional[int] = None
    column: Optional[int] = None


class ParseResult(BaseModel):
    """Result of parsing STL text.

    Args:
        statements: List of parsed statements
        errors: List of errors encountered
        warnings: List of warnings encountered
        is_valid: Whether parsing was successful

    Example:
        >>> result = ParseResult(
        ...     statements=[stmt1, stmt2],
        ...     errors=[],
        ...     warnings=[warning1],
        ...     is_valid=True
        ... )
    """

    statements: List[Statement] = Field(default_factory=list)
    errors: List[ParseError] = Field(default_factory=list)
    warnings: List[ParseWarning] = Field(default_factory=list)
    is_valid: bool = True
    extraction_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata from auto-extraction process")

    def to_json(self, **kwargs: Any) -> str:
        """Serialize to JSON.

        Args:
            **kwargs: Additional arguments passed to model_dump_json()

        Returns:
            JSON string representation
        """
        return self.model_dump_json(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation
        """
        return self.model_dump()

    def to_stl(self) -> str:
        """Serialize back to STL text.

        Returns:
            STL text representation
        """
        return "\n".join(str(stmt) for stmt in self.statements)

    # --------------------------------------------------
    # Query convenience methods (delegate to query.py)
    # --------------------------------------------------

    def find(self, **kwargs: Any) -> Optional["Statement"]:
        """Find the first statement matching all conditions.

        Uses Django-style lookups: ``source="A"``, ``confidence__gt=0.8``.
        See :func:`stl_parser.query.find` for full documentation.
        """
        from .query import find as _find
        return _find(self, **kwargs)

    def find_all(self, **kwargs: Any) -> List["Statement"]:
        """Find all statements matching all conditions.

        See :func:`stl_parser.query.find_all` for full documentation.
        """
        from .query import find_all as _find_all
        return _find_all(self, **kwargs)

    def filter(self, **kwargs: Any) -> "ParseResult":
        """Filter to a new ParseResult containing only matching statements.

        See :func:`stl_parser.query.filter_statements` for full documentation.
        """
        from .query import filter_statements as _filter
        return _filter(self, **kwargs)

    def select(self, field: str) -> List[Any]:
        """Extract a single field value from every statement.

        See :func:`stl_parser.query.select` for full documentation.
        """
        from .query import select as _select
        return _select(self, field)

    def __getitem__(self, key):
        """Dict-like access to statements.

        - ``result[0]`` → Statement by index
        - ``result["Name"]`` → all statements where source.name == Name
        - ``result[1:3]`` → slice of statements
        """
        if isinstance(key, int):
            return self.statements[key]
        if isinstance(key, slice):
            return self.statements[key]
        if isinstance(key, str):
            from .query import find_all as _find_all
            return _find_all(self, source=key)
        raise TypeError(f"ParseResult indices must be int, slice, or str, not {type(key).__name__}")
