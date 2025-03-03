"""Module for filtering sensitive or inappropriate content."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class ContentCategory(Enum):
    """Categories of sensitive content."""

    PROFANITY = "profanity"
    HATE_SPEECH = "hate_speech"
    PERSONAL_INFO = "personal_info"
    EXPLICIT = "explicit"
    VIOLENCE = "violence"
    HARMFUL = "harmful"


@dataclass
class ContentRule:
    """Rule for identifying sensitive content."""

    category: ContentCategory
    patterns: List[str]
    description: str
    severity: int  # 1-10
    action: str  # 'warn', 'block', 'redact'
    metadata: Optional[dict] = None


@dataclass
class FilterMatch:
    """Match found by content filter."""

    rule: ContentRule
    text: str
    span: tuple[int, int]
    replacement: Optional[str] = None


@dataclass
class FilterResult:
    """Result of content filtering."""

    is_clean: bool
    matches: List[FilterMatch]
    filtered_text: str
    metadata: Optional[dict] = None


class ContentFilter:
    """Filter for detecting and handling sensitive content."""

    def __init__(self):
        self.rules: List[ContentRule] = []
        self._load_default_rules()

    def _load_default_rules(self):
        """Load default content filtering rules."""
        # Profanity rules
        self.rules.append(
            ContentRule(
                category=ContentCategory.PROFANITY,
                patterns=[r"\b(bad_word1|bad_word2)\b"],
                description="Common profanity",
                severity=3,
                action="redact",
            ),
        )

        # Personal information rules
        self.rules.append(
            ContentRule(
                category=ContentCategory.PERSONAL_INFO,
                patterns=[
                    r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",  # US Phone
                    r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b",  # SSN
                ],
                description="Personal identifiable information",
                severity=8,
                action="redact",
            ),
        )

        # Add more default rules for other categories
        self.rules.append(
            ContentRule(
                category=ContentCategory.HATE_SPEECH,
                patterns=[r"\b(hate_term1|hate_term2)\b"],
                description="Hate speech terms",
                severity=9,
                action="block",
            ),
        )

        self.rules.append(
            ContentRule(
                category=ContentCategory.EXPLICIT,
                patterns=[r"\b(explicit_term1|explicit_term2)\b"],
                description="Sexually explicit content",
                severity=7,
                action="block",
            ),
        )

    def add_rule(self, rule: ContentRule):
        """Add a custom content filtering rule."""
        self.rules.append(rule)

    def _find_matches(self, text: str) -> List[FilterMatch]:
        """Find all content matches in the given text."""
        matches = []
        for rule in self.rules:
            for pattern in rule.patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    matches.append(
                        FilterMatch(
                            rule=rule,
                            text=match.group(),
                            span=match.span(),
                            replacement=self._get_replacement(rule, match.group()),
                        ),
                    )
        return matches

    def _get_replacement(self, rule: ContentRule, text: str) -> str:
        """Get replacement text based on the rule action."""
        if rule.action == "redact":
            return "[REDACTED]"
        return text

    def filter_text(self, text: str) -> FilterResult:
        """Filter the given text for sensitive content."""
        matches = self._find_matches(text)

        # Sort matches by their position in reverse order
        # to avoid index shifting when replacing text
        matches.sort(key=lambda m: m.span[0], reverse=True)

        filtered_text = text
        for match in matches:
            if match.rule.action == "redact":
                start, end = match.span
                filtered_text = (
                    filtered_text[:start] + match.replacement + filtered_text[end:]
                )

        return FilterResult(
            is_clean=len(matches) == 0,
            matches=matches,
            filtered_text=filtered_text,
            metadata={
                "categories": list(set(m.rule.category for m in matches)),
                "severity": max([m.rule.severity for m in matches]) if matches else 0,
            },
        )


class PersonalInfoDetector:
    """Detector for personal identifiable information."""

    def __init__(self):
        self.patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "ssn": r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b",
            "credit_card": r"\b(?:\d{4}[-.\s]?){3}\d{4}\b",
            "address": r"\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b",
        }

    def detect(self, text: str) -> Dict[str, List[str]]:
        """Detect personal information in the given text."""
        results = {}
        for name, pattern in self.patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                results[name] = matches
        return results

    def redact(self, text: str) -> str:
        """Redact personal information from the given text."""
        redacted = text
        for name, pattern in self.patterns.items():
            redacted = re.sub(pattern, f"[REDACTED {name.upper()}]", redacted)
        return redacted


class ContentPolicy:
    """Policy for content filtering."""

    def __init__(self):
        self.allowed_categories: Set[ContentCategory] = set()
        self.blocked_categories: Set[ContentCategory] = set()
        self.severity_threshold = 5
        self.required_actions: Dict[ContentCategory, str] = {}

    def allow_category(self, category: ContentCategory):
        """Allow a specific content category."""
        self.allowed_categories.add(category)
        if category in self.blocked_categories:
            self.blocked_categories.remove(category)

    def block_category(self, category: ContentCategory):
        """Block a specific content category."""
        self.blocked_categories.add(category)
        if category in self.allowed_categories:
            self.allowed_categories.remove(category)

    def set_severity_threshold(self, threshold: int):
        """Set the severity threshold (1-10)."""
        self.severity_threshold = max(1, min(10, threshold))

    def require_action(self, category: ContentCategory, action: str):
        """Require a specific action for a category."""
        self.required_actions[category] = action

    def check_content(self, matches: List[FilterMatch]) -> bool:
        """Check if content matches are allowed by the policy."""
        for match in matches:
            # Check if category is explicitly blocked
            if match.rule.category in self.blocked_categories:
                return False

            # Check severity threshold
            if match.rule.severity >= self.severity_threshold:
                return False

            # Check required actions
            if (
                match.rule.category in self.required_actions
                and match.rule.action != self.required_actions[match.rule.category]
            ):
                return False

        return True


class ContentGuard:
    """Guard for content filtering and policy enforcement."""

    def __init__(
        self,
        content_filter: Optional[ContentFilter] = None,
        pii_detector: Optional[PersonalInfoDetector] = None,
        policy: Optional[ContentPolicy] = None,
    ):
        self.content_filter = content_filter or ContentFilter()
        self.pii_detector = pii_detector or PersonalInfoDetector()
        self.policy = policy or ContentPolicy()

    def check_content(self, text: str) -> Dict[str, Any]:
        """Check content against filters and policies."""
        # Run content filter
        filter_result = self.content_filter.filter_text(text)

        # Detect PII
        pii_result = self.pii_detector.detect(text)

        # Check against policy
        is_allowed = self.policy.check_content(filter_result.matches)

        return {
            "is_allowed": is_allowed,
            "is_clean": filter_result.is_clean,
            "filtered_text": filter_result.filtered_text,
            "matches": [
                {
                    "category": m.rule.category.value,
                    "text": m.text,
                    "severity": m.rule.severity,
                    "action": m.rule.action,
                }
                for m in filter_result.matches
            ],
            "pii_detected": {k: len(v) for k, v in pii_result.items()},
            "metadata": filter_result.metadata,
        }

    def filter_content(self, text: str) -> str:
        """Filter content according to rules."""
        filter_result = self.content_filter.filter_text(text)
        return filter_result.filtered_text

    def is_content_allowed(self, text: str) -> bool:
        """Check if content is allowed by policy."""
        filter_result = self.content_filter.filter_text(text)
        return self.policy.check_content(filter_result.matches)
