"""Hallucination detection module for LLM outputs."""

import abc
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel


class HallucinationType(str, Enum):
    """Types of hallucinations in LLM outputs."""

    FACTUAL = "factual"  # Factually incorrect information
    LOGICAL = "logical"  # Logically inconsistent reasoning
    MATHEMATICAL = "mathematical"  # Mathematical errors
    CONTEXTUAL = "contextual"  # Inconsistent with provided context
    FABRICATION = "fabrication"  # Completely made up information
    CITATION = "citation"  # False or incorrect citations
    SELF_CONTRADICTION = "self_contradiction"  # Contradicts itself
    INSTRUCTION = "instruction"  # Fails to follow instructions
    OTHER = "other"  # Other types of hallucinations


@dataclass
class HallucinationEvent:
    """Represents a hallucination detection event.

    Attributes:
        hallucination_type: Type of hallucination detected
        confidence: Confidence score of the detection (0-1)
        model_id: Identifier of the model that produced the hallucination
        provider: Provider of the model
        input_text: Input text that led to the hallucination
        output_text: Output text containing the hallucination
        hallucinated_span: Specific span of text that contains the hallucination
        timestamp: When the hallucination was detected
        metadata: Additional metadata about the hallucination
    """

    hallucination_type: HallucinationType
    confidence: float
    model_id: str
    provider: str
    input_text: str
    output_text: str
    hallucinated_span: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary.

        Returns:
            Dictionary representation of the event
        """
        return {
            "hallucination_type": self.hallucination_type.value,
            "confidence": self.confidence,
            "model_id": self.model_id,
            "provider": self.provider,
            "input_text": self.input_text,
            "output_text": self.output_text,
            "hallucinated_span": self.hallucinated_span,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class HallucinationDetection(BaseModel):
    """Result of a hallucination detection.

    Attributes:
        detected: Whether a hallucination was detected
        hallucination_type: Type of hallucination detected
        confidence: Confidence score of the detection (0-1)
        hallucinated_span: Specific span of text that contains the hallucination
        explanation: Explanation of why this is considered a hallucination
    """

    detected: bool
    hallucination_type: Optional[HallucinationType] = None
    confidence: float = 0.0
    hallucinated_span: Optional[str] = None
    explanation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the detection to a dictionary.

        Returns:
            Dictionary representation of the detection
        """
        return {
            "detected": self.detected,
            "hallucination_type": self.hallucination_type.value
            if self.hallucination_type
            else None,
            "confidence": self.confidence,
            "hallucinated_span": self.hallucinated_span,
            "explanation": self.explanation,
        }


class BaseHallucinationDetector(abc.ABC):
    """Base class for hallucination detectors.

    This abstract class defines the interface for hallucination detectors.
    """

    @abc.abstractmethod
    def detect(
        self,
        input_text: str,
        output_text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> HallucinationDetection:
        """Detect hallucinations in the output text.

        Args:
            input_text: Input text that led to the output
            output_text: Output text to check for hallucinations
            context: Additional context for detection (optional)

        Returns:
            Hallucination detection result
        """
        pass

    @abc.abstractmethod
    def get_supported_types(self) -> Set[HallucinationType]:
        """Get the types of hallucinations this detector can detect.

        Returns:
            Set of supported hallucination types
        """
        pass


class HallucinationDetector(BaseHallucinationDetector):
    """Hallucination detector that combines multiple detection strategies.

    This class provides a comprehensive hallucination detection by combining
    multiple detection strategies, such as fact-checking, logical consistency
    checking, and context consistency checking.
    """

    def __init__(self):
        """Initialize the hallucination detector."""
        self._detectors: List[Tuple[BaseHallucinationDetector, float]] = []

    def add_detector(
        self, detector: BaseHallucinationDetector, weight: float = 1.0
    ) -> None:
        """Add a detector with a weight.

        Args:
            detector: Hallucination detector to add
            weight: Weight of the detector in the ensemble (default: 1.0)
        """
        self._detectors.append((detector, weight))

    def detect(
        self,
        input_text: str,
        output_text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> HallucinationDetection:
        """Detect hallucinations in the output text.

        Args:
            input_text: Input text that led to the output
            output_text: Output text to check for hallucinations
            context: Additional context for detection (optional)

        Returns:
            Hallucination detection result
        """
        if not self._detectors:
            return HallucinationDetection(detected=False)

        # Run all detectors
        detections = []
        total_weight = 0.0

        for detector, weight in self._detectors:
            try:
                detection = detector.detect(input_text, output_text, context)
                detections.append((detection, weight))
                total_weight += weight
            except Exception as e:
                # Log the error but continue with other detectors
                print(f"Error in hallucination detector: {e}")

        if not detections:
            return HallucinationDetection(detected=False)

        # Normalize weights
        normalized_weights = [weight / total_weight for _, weight in detections]

        # Calculate weighted average confidence
        weighted_confidence = sum(
            detection.confidence * weight
            for (detection, _), weight in zip(detections, normalized_weights)
        )

        # Determine if a hallucination was detected (majority vote)
        detected = (
            sum(1 for detection, _ in detections if detection.detected)
            > len(detections) / 2
        )

        # Get the most confident hallucination type
        hallucination_type = None
        hallucinated_span = None
        explanation = None

        if detected:
            # Find the detection with the highest confidence
            best_detection = max(
                [d for d, _ in detections if d.detected],
                key=lambda d: d.confidence,
                default=None,
            )

            if best_detection:
                hallucination_type = best_detection.hallucination_type
                hallucinated_span = best_detection.hallucinated_span
                explanation = best_detection.explanation

        return HallucinationDetection(
            detected=detected,
            hallucination_type=hallucination_type,
            confidence=weighted_confidence,
            hallucinated_span=hallucinated_span,
            explanation=explanation,
        )

    def get_supported_types(self) -> Set[HallucinationType]:
        """Get the types of hallucinations this detector can detect.

        Returns:
            Set of supported hallucination types
        """
        supported_types = set()
        for detector, _ in self._detectors:
            supported_types.update(detector.get_supported_types())
        return supported_types


class HallucinationMonitor:
    """Monitors hallucinations in LLM outputs.

    This class provides utilities for monitoring hallucinations in LLM outputs,
    including tracking hallucination events and generating reports.
    """

    def __init__(self, detector: Optional[BaseHallucinationDetector] = None):
        """Initialize the hallucination monitor.

        Args:
            detector: Hallucination detector to use (optional)
        """
        self.detector = detector or HallucinationDetector()
        self.events: List[HallucinationEvent] = []
        self._event_handlers: List[Callable[[HallucinationEvent], None]] = []

    def add_event(self, event: HallucinationEvent) -> None:
        """Add a hallucination event to the monitor.

        Args:
            event: Hallucination event to add
        """
        self.events.append(event)

        # Notify event handlers
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                # Log the error but continue with other handlers
                print(f"Error in hallucination event handler: {e}")

    def add_event_handler(self, handler: Callable[[HallucinationEvent], None]) -> None:
        """Add an event handler.

        Args:
            handler: Function that takes a hallucination event and processes it
        """
        self._event_handlers.append(handler)

    def monitor(
        self,
        input_text: str,
        output_text: str,
        model_id: str,
        provider: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[HallucinationEvent]:
        """Monitor output for hallucinations.

        Args:
            input_text: Input text that led to the output
            output_text: Output text to check for hallucinations
            model_id: Identifier of the model that produced the output
            provider: Provider of the model
            context: Additional context for detection (optional)
            metadata: Additional metadata about the output (optional)

        Returns:
            Hallucination event if a hallucination was detected, None otherwise
        """
        # Detect hallucinations
        detection = self.detector.detect(input_text, output_text, context)

        # Return None if no hallucination was detected
        if not detection.detected:
            return None

        # Create event
        event = HallucinationEvent(
            hallucination_type=detection.hallucination_type or HallucinationType.OTHER,
            confidence=detection.confidence,
            model_id=model_id,
            provider=provider,
            input_text=input_text,
            output_text=output_text,
            hallucinated_span=detection.hallucinated_span,
            metadata=metadata or {},
        )

        # Add event
        self.add_event(event)

        return event

    def get_hallucination_rate(
        self,
        provider: Optional[str] = None,
        model_id: Optional[str] = None,
        hallucination_type: Optional[HallucinationType] = None,
    ) -> float:
        """Get the hallucination rate for the specified criteria.

        Args:
            provider: Provider to filter by (optional)
            model_id: Model ID to filter by (optional)
            hallucination_type: Hallucination type to filter by (optional)

        Returns:
            Hallucination rate (0-1)
        """
        # This is a simplified implementation that assumes all outputs are monitored
        # In a real implementation, we would track both hallucination events and total outputs

        # Filter events based on criteria
        filtered_events = self.events

        if provider:
            filtered_events = [e for e in filtered_events if e.provider == provider]
        if model_id:
            filtered_events = [e for e in filtered_events if e.model_id == model_id]
        if hallucination_type:
            filtered_events = [
                e for e in filtered_events if e.hallucination_type == hallucination_type
            ]

        # Calculate hallucination rate
        # This is a placeholder - in a real implementation, we would divide by the total number of outputs
        return len(filtered_events) / max(len(self.events), 1)

    def get_hallucination_by_type(self) -> Dict[str, int]:
        """Get the number of hallucinations by type.

        Returns:
            Dictionary mapping hallucination types to their counts
        """
        hallucinations_by_type: Dict[str, int] = {}

        for event in self.events:
            hallucination_type = event.hallucination_type.value
            if hallucination_type not in hallucinations_by_type:
                hallucinations_by_type[hallucination_type] = 0
            hallucinations_by_type[hallucination_type] += 1

        return hallucinations_by_type

    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive hallucination report.

        Returns:
            Dictionary containing the hallucination report
        """
        # Calculate overall hallucination rate
        overall_rate = len(self.events) / max(len(self.events), 1)  # Placeholder

        # Get hallucinations by type
        by_type = self.get_hallucination_by_type()

        # Get hallucinations by model
        by_model: Dict[str, int] = {}
        for event in self.events:
            model_key = f"{event.provider}/{event.model_id}"
            if model_key not in by_model:
                by_model[model_key] = 0
            by_model[model_key] += 1

        # Get average confidence
        avg_confidence = sum(event.confidence for event in self.events) / max(
            len(self.events), 1
        )

        return {
            "total_hallucinations": len(self.events),
            "overall_rate": overall_rate,
            "by_type": by_type,
            "by_model": by_model,
            "avg_confidence": avg_confidence,
            "time_range": {
                "start": min(event.timestamp for event in self.events).isoformat()
                if self.events
                else None,
                "end": max(event.timestamp for event in self.events).isoformat()
                if self.events
                else None,
            },
        }
