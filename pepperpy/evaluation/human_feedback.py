"""Module for incorporating human feedback in agent evaluation."""
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import json


class FeedbackType(Enum):
    """Types of human feedback."""
    RATING = "rating"
    RANKING = "ranking"
    COMPARISON = "comparison"
    FREE_TEXT = "free_text"
    CORRECTION = "correction"


@dataclass
class FeedbackItem:
    """Individual piece of feedback."""
    id: str
    type: FeedbackType
    content: Any
    timestamp: datetime
    evaluator_id: str
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[dict] = None


@dataclass
class FeedbackRequest:
    """Request for human feedback."""
    id: str
    type: FeedbackType
    items: List[Any]
    instructions: str
    deadline: Optional[datetime] = None
    metadata: Optional[dict] = None


class FeedbackCollector:
    """Manages collection of human feedback."""
    
    def __init__(self):
        self.feedback: Dict[str, List[FeedbackItem]] = {}  # item_id -> feedback
        self.pending_requests: Dict[str, FeedbackRequest] = {}

    def create_request(self, request: FeedbackRequest) -> str:
        """Create a new feedback request."""
        self.pending_requests[request.id] = request
        return request.id

    def submit_feedback(self, feedback: FeedbackItem):
        """Submit feedback for an item."""
        if feedback.context and 'item_id' in feedback.context:
            item_id = feedback.context['item_id']
            if item_id not in self.feedback:
                self.feedback[item_id] = []
            self.feedback[item_id].append(feedback)

    def get_feedback(self, item_id: str) -> List[FeedbackItem]:
        """Get all feedback for an item."""
        return self.feedback.get(item_id, [])

    def get_pending_requests(self) -> List[FeedbackRequest]:
        """Get all pending feedback requests."""
        now = datetime.now()
        return [
            req for req in self.pending_requests.values()
            if not req.deadline or req.deadline > now
        ]


class FeedbackAnalyzer:
    """Analyzes collected feedback."""
    
    def analyze_ratings(self, feedback_items: List[FeedbackItem]) -> Dict[str, Any]:
        """Analyze numerical ratings."""
        if not feedback_items:
            return {}
        
        ratings = [
            float(item.content)
            for item in feedback_items
            if item.type == FeedbackType.RATING and isinstance(item.content, (int, float))
        ]
        
        if not ratings:
            return {}
        
        return {
            'count': len(ratings),
            'average': sum(ratings) / len(ratings),
            'min': min(ratings),
            'max': max(ratings),
            'distribution': self._get_distribution(ratings)
        }

    def analyze_rankings(self, feedback_items: List[FeedbackItem]) -> Dict[str, Any]:
        """Analyze ranking feedback."""
        if not feedback_items:
            return {}
        
        rankings = [
            item.content
            for item in feedback_items
            if item.type == FeedbackType.RANKING and isinstance(item.content, list)
        ]
        
        if not rankings:
            return {}
        
        # Calculate average rank for each item
        item_ranks = {}
        for ranking in rankings:
            for rank, item_id in enumerate(ranking, 1):
                if item_id not in item_ranks:
                    item_ranks[item_id] = []
                item_ranks[item_id].append(rank)
        
        return {
            'count': len(rankings),
            'average_ranks': {
                item_id: sum(ranks) / len(ranks)
                for item_id, ranks in item_ranks.items()
            }
        }

    def analyze_comparisons(self, feedback_items: List[FeedbackItem]) -> Dict[str, Any]:
        """Analyze pairwise comparisons."""
        if not feedback_items:
            return {}
        
        comparisons = [
            item.content
            for item in feedback_items
            if item.type == FeedbackType.COMPARISON and isinstance(item.content, dict)
        ]
        
        if not comparisons:
            return {}
        
        # Count wins for each item
        wins = {}
        total_comparisons = {}
        
        for comp in comparisons:
            winner = comp.get('winner')
            loser = comp.get('loser')
            if winner and loser:
                wins[winner] = wins.get(winner, 0) + 1
                total_comparisons[winner] = total_comparisons.get(winner, 0) + 1
                total_comparisons[loser] = total_comparisons.get(loser, 0) + 1
        
        return {
            'count': len(comparisons),
            'win_rates': {
                item_id: wins.get(item_id, 0) / total_comparisons[item_id]
                for item_id in total_comparisons
            }
        }

    def analyze_text_feedback(self, feedback_items: List[FeedbackItem]) -> Dict[str, Any]:
        """Analyze free-text feedback."""
        if not feedback_items:
            return {}
        
        text_feedback = [
            item.content
            for item in feedback_items
            if item.type == FeedbackType.FREE_TEXT and isinstance(item.content, str)
        ]
        
        if not text_feedback:
            return {}
        
        # Simple analysis - in practice, you would use NLP
        return {
            'count': len(text_feedback),
            'average_length': sum(len(text) for text in text_feedback) / len(text_feedback)
        }

    def _get_distribution(self, values: List[float]) -> Dict[str, int]:
        """Get distribution of values in bins."""
        bins = {}
        for value in values:
            bin_key = str(round(value))
            bins[bin_key] = bins.get(bin_key, 0) + 1
        return bins


class FeedbackManager:
    """High-level interface for feedback management."""
    
    def __init__(self):
        self.collector = FeedbackCollector()
        self.analyzer = FeedbackAnalyzer()

    def request_feedback(self,
                        items: List[Any],
                        feedback_type: FeedbackType,
                        instructions: str,
                        deadline: Optional[datetime] = None) -> str:
        """Create a new feedback request."""
        request = FeedbackRequest(
            id=f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            type=feedback_type,
            items=items,
            instructions=instructions,
            deadline=deadline
        )
        return self.collector.create_request(request)

    def submit_feedback(self,
                       feedback_type: FeedbackType,
                       content: Any,
                       evaluator_id: str,
                       item_id: str,
                       metadata: Optional[dict] = None):
        """Submit feedback for an item."""
        feedback = FeedbackItem(
            id=f"fb_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            type=feedback_type,
            content=content,
            timestamp=datetime.now(),
            evaluator_id=evaluator_id,
            context={'item_id': item_id},
            metadata=metadata
        )
        self.collector.submit_feedback(feedback)

    def analyze_feedback(self, item_id: str) -> Dict[str, Any]:
        """Analyze all feedback for an item."""
        feedback_items = self.collector.get_feedback(item_id)
        
        return {
            'ratings': self.analyzer.analyze_ratings(feedback_items),
            'rankings': self.analyzer.analyze_rankings(feedback_items),
            'comparisons': self.analyzer.analyze_comparisons(feedback_items),
            'text_feedback': self.analyzer.analyze_text_feedback(feedback_items)
        }

    def export_feedback(self, format: str = 'json') -> str:
        """Export all feedback data."""
        data = {
            'feedback': {
                item_id: [
                    {
                        'id': fb.id,
                        'type': fb.type.value,
                        'content': fb.content,
                        'timestamp': fb.timestamp.isoformat(),
                        'evaluator_id': fb.evaluator_id,
                        'context': fb.context,
                        'metadata': fb.metadata
                    }
                    for fb in feedback_items
                ]
                for item_id, feedback_items in self.collector.feedback.items()
            }
        }
        
        if format == 'json':
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}") 