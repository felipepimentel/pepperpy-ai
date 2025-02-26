"""Module for filtering sensitive or inappropriate content."""
from typing import List, Optional, Dict, Any, Union, Set
from dataclasses import dataclass
from enum import Enum
import re


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
    """Filters sensitive or inappropriate content."""
    
    def __init__(self):
        self.rules: List[ContentRule] = []
        self._load_default_rules()

    def _load_default_rules(self):
        """Load default content filtering rules."""
        # Note: Using placeholder patterns - in practice, you would use more comprehensive lists
        self.rules.extend([
            ContentRule(
                category=ContentCategory.PERSONAL_INFO,
                patterns=[
                    r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone numbers
                    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Emails
                    r'\b\d{3}[-]?\d{2}[-]?\d{4}\b'  # SSN
                ],
                description="Personal identifying information",
                severity=8,
                action="redact"
            ),
            ContentRule(
                category=ContentCategory.PROFANITY,
                patterns=[
                    r'\b(bad_word1|bad_word2)\b'  # Placeholder
                ],
                description="Profanity and offensive language",
                severity=5,
                action="redact"
            ),
            ContentRule(
                category=ContentCategory.HATE_SPEECH,
                patterns=[
                    r'\b(slur1|slur2)\b'  # Placeholder
                ],
                description="Hate speech and discriminatory language",
                severity=9,
                action="block"
            )
        ])

    def add_rule(self, rule: ContentRule):
        """Add a new content filtering rule."""
        self.rules.append(rule)

    def _find_matches(self, text: str) -> List[FilterMatch]:
        """Find all rule matches in text."""
        matches = []
        
        for rule in self.rules:
            for pattern in rule.patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    matches.append(FilterMatch(
                        rule=rule,
                        text=match.group(),
                        span=match.span(),
                        replacement=self._get_replacement(rule, match.group())
                    ))
        
        return sorted(matches, key=lambda m: m.span[0])

    def _get_replacement(self, rule: ContentRule, text: str) -> str:
        """Get replacement text based on rule action."""
        if rule.action == "redact":
            return "[REDACTED]"
        elif rule.action == "block":
            return "[BLOCKED]"
        return text

    def filter_text(self, text: str) -> FilterResult:
        """Filter sensitive content from text."""
        matches = self._find_matches(text)
        
        if not matches:
            return FilterResult(
                is_clean=True,
                matches=[],
                filtered_text=text
            )
        
        # Apply replacements in reverse order to maintain correct positions
        filtered_text = text
        for match in reversed(matches):
            start, end = match.span
            filtered_text = filtered_text[:start] + match.replacement + filtered_text[end:]
        
        return FilterResult(
            is_clean=False,
            matches=matches,
            filtered_text=filtered_text
        )


class PersonalInfoDetector:
    """Detects and handles personal information."""
    
    def __init__(self):
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',
            'credit_card': r'\b\d{4}[-]?\d{4}[-]?\d{4}[-]?\d{4}\b',
            'address': r'\b\d+\s+[A-Za-z\s,]+\b(?:street|st|avenue|ave|road|rd|boulevard|blvd)\b'
        }

    def detect(self, text: str) -> Dict[str, List[str]]:
        """Detect personal information in text."""
        findings = {}
        
        for info_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            if matches:
                findings[info_type] = [m.group() for m in matches]
        
        return findings

    def redact(self, text: str) -> str:
        """Redact personal information from text."""
        redacted = text
        
        for info_type, pattern in self.patterns.items():
            redacted = re.sub(
                pattern,
                f"[REDACTED {info_type.upper()}]",
                redacted,
                flags=re.IGNORECASE
            )
        
        return redacted


class ContentPolicy:
    """Defines and enforces content policies."""
    
    def __init__(self):
        self.allowed_categories: Set[ContentCategory] = set()
        self.blocked_categories: Set[ContentCategory] = set()
        self.severity_threshold: int = 5
        self.required_actions: Dict[ContentCategory, str] = {}

    def allow_category(self, category: ContentCategory):
        """Allow a content category."""
        self.allowed_categories.add(category)
        if category in self.blocked_categories:
            self.blocked_categories.remove(category)

    def block_category(self, category: ContentCategory):
        """Block a content category."""
        self.blocked_categories.add(category)
        if category in self.allowed_categories:
            self.allowed_categories.remove(category)

    def set_severity_threshold(self, threshold: int):
        """Set severity threshold for content filtering."""
        if not 1 <= threshold <= 10:
            raise ValueError("Severity threshold must be between 1 and 10")
        self.severity_threshold = threshold

    def require_action(self, category: ContentCategory, action: str):
        """Set required action for a category."""
        if action not in ['warn', 'block', 'redact']:
            raise ValueError("Invalid action")
        self.required_actions[category] = action

    def check_content(self, matches: List[FilterMatch]) -> bool:
        """Check if content matches comply with policy."""
        for match in matches:
            # Check if category is explicitly blocked
            if match.rule.category in self.blocked_categories:
                return False
            
            # Check if severity exceeds threshold
            if match.rule.severity > self.severity_threshold:
                return False
            
            # Check if required action is followed
            required_action = self.required_actions.get(match.rule.category)
            if required_action and match.rule.action != required_action:
                return False
        
        return True


class ContentGuard:
    """High-level interface for content filtering and protection."""
    
    def __init__(self,
                 content_filter: Optional[ContentFilter] = None,
                 pii_detector: Optional[PersonalInfoDetector] = None,
                 policy: Optional[ContentPolicy] = None):
        self.filter = content_filter or ContentFilter()
        self.pii_detector = pii_detector or PersonalInfoDetector()
        self.policy = policy or ContentPolicy()

    def check_content(self, text: str) -> Dict[str, Any]:
        """Comprehensive content security check."""
        # Filter sensitive content
        filter_result = self.filter.filter_text(text)
        
        # Detect personal information
        pii_findings = self.pii_detector.detect(text)
        
        # Check policy compliance
        is_compliant = self.policy.check_content(filter_result.matches)
        
        return {
            'is_safe': filter_result.is_clean and not pii_findings and is_compliant,
            'filter_results': {
                'is_clean': filter_result.is_clean,
                'matches': [
                    {
                        'category': m.rule.category.value,
                        'severity': m.rule.severity,
                        'text': m.text,
                        'action': m.rule.action
                    }
                    for m in filter_result.matches
                ]
            },
            'pii_detected': bool(pii_findings),
            'pii_types': list(pii_findings.keys()) if pii_findings else [],
            'is_policy_compliant': is_compliant,
            'filtered_text': filter_result.filtered_text
        }

    def filter_content(self, text: str) -> str:
        """Filter and clean content for safe use."""
        # First filter sensitive content
        filter_result = self.filter.filter_text(text)
        
        # Then redact any remaining personal information
        return self.pii_detector.redact(filter_result.filtered_text)

    def is_content_allowed(self, text: str) -> bool:
        """Check if content is allowed by policy."""
        filter_result = self.filter.filter_text(text)
        return self.policy.check_content(filter_result.matches) 