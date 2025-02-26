"""Module for tracking and monitoring API usage costs."""
from typing import Dict, Optional, List
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
import asyncio
import json


@dataclass
class CostEntry:
    """Represents a single API cost entry."""
    timestamp: datetime
    api_name: str
    operation: str
    tokens: int
    cost: Decimal
    metadata: Optional[dict] = None


class CostTracker:
    """Tracks API usage costs."""
    
    def __init__(self):
        self.entries: List[CostEntry] = []
        self._lock = asyncio.Lock()

    async def record_cost(self, entry: CostEntry):
        """Record a new cost entry."""
        async with self._lock:
            self.entries.append(entry)

    def get_total_cost(self, api_name: Optional[str] = None) -> Decimal:
        """Get total cost, optionally filtered by API."""
        total = Decimal('0')
        for entry in self.entries:
            if api_name is None or entry.api_name == api_name:
                total += entry.cost
        return total

    def get_cost_by_operation(self, api_name: str) -> Dict[str, Decimal]:
        """Get costs broken down by operation for an API."""
        costs = {}
        for entry in self.entries:
            if entry.api_name == api_name:
                costs[entry.operation] = costs.get(entry.operation, Decimal('0')) + entry.cost
        return costs


class BudgetAlert:
    """Manages budget alerts for API costs."""
    
    def __init__(self, cost_tracker: CostTracker):
        self.cost_tracker = cost_tracker
        self.alerts: Dict[str, Decimal] = {}  # api_name -> threshold
        self._handlers: List[callable] = []

    def set_threshold(self, api_name: str, threshold: Decimal):
        """Set a budget threshold for an API."""
        self.alerts[api_name] = threshold

    def add_handler(self, handler: callable):
        """Add an alert handler function."""
        self._handlers.append(handler)

    async def check_thresholds(self):
        """Check if any thresholds have been exceeded."""
        for api_name, threshold in self.alerts.items():
            current_cost = self.cost_tracker.get_total_cost(api_name)
            if current_cost > threshold:
                await self._trigger_alert(api_name, current_cost, threshold)

    async def _trigger_alert(self, api_name: str, current_cost: Decimal, threshold: Decimal):
        """Trigger alert handlers."""
        alert_data = {
            'api_name': api_name,
            'current_cost': str(current_cost),
            'threshold': str(threshold),
            'timestamp': datetime.now().isoformat()
        }
        
        for handler in self._handlers:
            try:
                await handler(alert_data)
            except Exception as e:
                # Log error but continue with other handlers
                print(f"Error in alert handler: {e}")


class CostOptimizer:
    """Analyzes and optimizes API usage costs."""
    
    def __init__(self, cost_tracker: CostTracker):
        self.cost_tracker = cost_tracker

    def analyze_usage_patterns(self, api_name: str) -> Dict[str, Any]:
        """Analyze usage patterns to identify optimization opportunities."""
        entries = [e for e in self.cost_tracker.entries if e.api_name == api_name]
        
        if not entries:
            return {}
        
        total_tokens = sum(e.tokens for e in entries)
        total_cost = sum(e.cost for e in entries)
        avg_cost_per_token = total_cost / total_tokens if total_tokens > 0 else Decimal('0')
        
        # Group by operation
        op_stats = {}
        for entry in entries:
            if entry.operation not in op_stats:
                op_stats[entry.operation] = {'count': 0, 'tokens': 0, 'cost': Decimal('0')}
            stats = op_stats[entry.operation]
            stats['count'] += 1
            stats['tokens'] += entry.tokens
            stats['cost'] += entry.cost
        
        return {
            'total_tokens': total_tokens,
            'total_cost': str(total_cost),
            'avg_cost_per_token': str(avg_cost_per_token),
            'operations': {
                op: {
                    'count': stats['count'],
                    'tokens': stats['tokens'],
                    'cost': str(stats['cost']),
                    'avg_tokens_per_call': stats['tokens'] / stats['count']
                }
                for op, stats in op_stats.items()
            }
        }

    def get_optimization_recommendations(self, api_name: str) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations."""
        analysis = self.analyze_usage_patterns(api_name)
        recommendations = []
        
        if not analysis:
            return recommendations
        
        # Check for high token usage operations
        for op, stats in analysis.get('operations', {}).items():
            avg_tokens = stats['avg_tokens_per_call']
            if avg_tokens > 1000:  # Example threshold
                recommendations.append({
                    'type': 'high_token_usage',
                    'operation': op,
                    'avg_tokens': avg_tokens,
                    'suggestion': 'Consider chunking large requests or implementing caching'
                })
        
        # Check for frequent low-token operations
        for op, stats in analysis.get('operations', {}).items():
            if stats['count'] > 1000 and stats['avg_tokens_per_call'] < 100:
                recommendations.append({
                    'type': 'high_frequency_low_tokens',
                    'operation': op,
                    'call_count': stats['count'],
                    'suggestion': 'Consider batching multiple small requests'
                })
        
        return recommendations 