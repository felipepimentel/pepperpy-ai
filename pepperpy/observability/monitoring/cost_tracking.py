"""Cost tracking module for API usage costs."""

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel


class CostAlertLevel(str, Enum):
    """Cost alert levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class CostEvent:
    """Represents a cost event.

    Attributes:
        provider: Provider of the service (e.g., "openai", "anthropic")
        service: Service used (e.g., "gpt-4", "claude-3")
        cost: Cost of the usage
        usage_type: Type of usage (e.g., "tokens", "requests")
        usage_amount: Amount of usage
        timestamp: When the usage occurred
        metadata: Additional metadata about the usage
    """

    provider: str
    service: str
    cost: float
    usage_type: str
    usage_amount: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary.

        Returns:
            Dictionary representation of the event
        """
        return {
            "provider": self.provider,
            "service": self.service,
            "cost": self.cost,
            "usage_type": self.usage_type,
            "usage_amount": self.usage_amount,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class BudgetAlert(BaseModel):
    """Represents a budget alert.

    Attributes:
        level: Alert level
        threshold: Threshold that triggered the alert
        current_cost: Current cost
        budget: Budget limit
        message: Alert message
        timestamp: When the alert was triggered
    """

    level: CostAlertLevel
    threshold: float
    current_cost: float
    budget: float
    message: str
    timestamp: datetime = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the alert to a dictionary.

        Returns:
            Dictionary representation of the alert
        """
        return {
            "level": self.level.value,
            "threshold": self.threshold,
            "current_cost": self.current_cost,
            "budget": self.budget,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
        }


class CostTracker:
    """Tracks API usage costs.

    This class provides methods for tracking API usage costs,
    including recording cost events and calculating total costs.
    """

    def __init__(self):
        """Initialize the cost tracker."""
        self.events: List[CostEvent] = []
        self._event_handlers: List[Callable[[CostEvent], None]] = []

    def add_event(self, event: CostEvent) -> None:
        """Add a cost event to the tracker.

        Args:
            event: Cost event to add
        """
        self.events.append(event)

        # Notify event handlers
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                # Log the error but continue with other handlers
                print(f"Error in cost event handler: {e}")

    def add_event_handler(self, handler: Callable[[CostEvent], None]) -> None:
        """Add an event handler.

        Args:
            handler: Function that takes a cost event and processes it
        """
        self._event_handlers.append(handler)

    def track_usage(
        self,
        provider: str,
        service: str,
        cost: float,
        usage_type: str,
        usage_amount: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CostEvent:
        """Track API usage.

        Args:
            provider: Provider of the service
            service: Service used
            cost: Cost of the usage
            usage_type: Type of usage
            usage_amount: Amount of usage
            metadata: Additional metadata about the usage

        Returns:
            The recorded cost event
        """
        event = CostEvent(
            provider=provider,
            service=service,
            cost=cost,
            usage_type=usage_type,
            usage_amount=usage_amount,
            metadata=metadata or {},
        )

        self.add_event(event)
        return event

    def get_total_cost(
        self,
        provider: Optional[str] = None,
        service: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> float:
        """Get total cost for the specified criteria.

        Args:
            provider: Provider to filter by (optional)
            service: Service to filter by (optional)
            start_time: Start time to filter by (optional)
            end_time: End time to filter by (optional)

        Returns:
            Total cost
        """
        # Filter events based on criteria
        filtered_events = self.events

        if provider:
            filtered_events = [e for e in filtered_events if e.provider == provider]
        if service:
            filtered_events = [e for e in filtered_events if e.service == service]
        if start_time:
            filtered_events = [e for e in filtered_events if e.timestamp >= start_time]
        if end_time:
            filtered_events = [e for e in filtered_events if e.timestamp <= end_time]

        # Calculate total cost
        return sum(event.cost for event in filtered_events)

    def get_cost_by_provider(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> Dict[str, float]:
        """Get costs grouped by provider.

        Args:
            start_time: Start time to filter by (optional)
            end_time: End time to filter by (optional)

        Returns:
            Dictionary mapping providers to their total costs
        """
        # Filter events based on time range
        filtered_events = self.events
        if start_time:
            filtered_events = [e for e in filtered_events if e.timestamp >= start_time]
        if end_time:
            filtered_events = [e for e in filtered_events if e.timestamp <= end_time]

        # Group costs by provider
        costs_by_provider: Dict[str, float] = {}
        for event in filtered_events:
            if event.provider not in costs_by_provider:
                costs_by_provider[event.provider] = 0
            costs_by_provider[event.provider] += event.cost

        return costs_by_provider

    def get_cost_by_service(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> Dict[str, float]:
        """Get costs grouped by service.

        Args:
            start_time: Start time to filter by (optional)
            end_time: End time to filter by (optional)

        Returns:
            Dictionary mapping services to their total costs
        """
        # Filter events based on time range
        filtered_events = self.events
        if start_time:
            filtered_events = [e for e in filtered_events if e.timestamp >= start_time]
        if end_time:
            filtered_events = [e for e in filtered_events if e.timestamp <= end_time]

        # Group costs by service
        costs_by_service: Dict[str, float] = {}
        for event in filtered_events:
            service_key = f"{event.provider}/{event.service}"
            if service_key not in costs_by_service:
                costs_by_service[service_key] = 0
            costs_by_service[service_key] += event.cost

        return costs_by_service

    def generate_report(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate a comprehensive cost report.

        Args:
            start_time: Start time to filter by (optional)
            end_time: End time to filter by (optional)

        Returns:
            Dictionary containing the cost report
        """
        # Filter events based on time range
        filtered_events = self.events
        if start_time:
            filtered_events = [e for e in filtered_events if e.timestamp >= start_time]
        if end_time:
            filtered_events = [e for e in filtered_events if e.timestamp <= end_time]

        # Calculate total cost
        total_cost = sum(event.cost for event in filtered_events)

        # Group costs by provider and service
        costs_by_provider = self.get_cost_by_provider(start_time, end_time)
        costs_by_service = self.get_cost_by_service(start_time, end_time)

        return {
            "total_cost": total_cost,
            "by_provider": costs_by_provider,
            "by_service": costs_by_service,
            "total_events": len(filtered_events),
            "time_range": {
                "start": start_time.isoformat() if start_time else None,
                "end": end_time.isoformat() if end_time else None,
            },
        }


class CostMonitor:
    """Monitors API usage costs.

    This class provides utilities for monitoring API usage costs,
    including budget tracking and alerts.
    """

    def __init__(self, tracker: Optional[CostTracker] = None):
        """Initialize the cost monitor.

        Args:
            tracker: Cost tracker to use (optional)
        """
        self.tracker = tracker or CostTracker()
        self.budget: Optional[float] = None
        self.alert_thresholds: List[float] = [0.5, 0.8, 0.9, 0.95, 1.0]
        self._alert_handlers: List[Callable[[BudgetAlert], None]] = []
        self._triggered_alerts: Dict[float, bool] = {}

    def set_budget(self, budget: float) -> None:
        """Set the budget limit.

        Args:
            budget: Budget limit
        """
        self.budget = budget
        # Reset triggered alerts
        self._triggered_alerts = {
            threshold: False for threshold in self.alert_thresholds
        }

    def set_alert_thresholds(self, thresholds: List[float]) -> None:
        """Set the alert thresholds.

        Args:
            thresholds: List of thresholds (as fractions of the budget)
        """
        self.alert_thresholds = sorted(thresholds)
        # Reset triggered alerts
        self._triggered_alerts = {
            threshold: False for threshold in self.alert_thresholds
        }

    def add_alert_handler(self, handler: Callable[[BudgetAlert], None]) -> None:
        """Add an alert handler.

        Args:
            handler: Function that takes a budget alert and processes it
        """
        self._alert_handlers.append(handler)

    def check_budget(self) -> Optional[BudgetAlert]:
        """Check if the current cost exceeds any threshold.

        Returns:
            Budget alert if a threshold is exceeded, None otherwise
        """
        if self.budget is None:
            return None

        current_cost = self.tracker.get_total_cost()
        cost_ratio = current_cost / self.budget

        # Check thresholds in descending order
        for threshold in sorted(self.alert_thresholds, reverse=True):
            if cost_ratio >= threshold and not self._triggered_alerts.get(
                threshold, False
            ):
                # Mark this threshold as triggered
                self._triggered_alerts[threshold] = True

                # Determine alert level
                level = CostAlertLevel.INFO
                if threshold >= 1.0:
                    level = CostAlertLevel.CRITICAL
                elif threshold >= 0.8:
                    level = CostAlertLevel.WARNING

                # Create alert
                alert = BudgetAlert(
                    level=level,
                    threshold=threshold,
                    current_cost=current_cost,
                    budget=self.budget,
                    message=f"Cost threshold {threshold:.0%} reached: ${current_cost:.2f} of ${self.budget:.2f}",
                )

                # Notify alert handlers
                for handler in self._alert_handlers:
                    try:
                        handler(alert)
                    except Exception as e:
                        # Log the error but continue with other handlers
                        print(f"Error in budget alert handler: {e}")

                return alert

        return None

    def track_usage(
        self,
        provider: str,
        service: str,
        cost: float,
        usage_type: str,
        usage_amount: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CostEvent:
        """Track API usage and check budget.

        Args:
            provider: Provider of the service
            service: Service used
            cost: Cost of the usage
            usage_type: Type of usage
            usage_amount: Amount of usage
            metadata: Additional metadata about the usage

        Returns:
            The recorded cost event
        """
        # Track the usage
        event = self.tracker.track_usage(
            provider, service, cost, usage_type, usage_amount, metadata
        )

        # Check budget
        self.check_budget()

        return event

    def get_budget_status(self) -> Dict[str, Any]:
        """Get the current budget status.

        Returns:
            Dictionary containing the budget status
        """
        if self.budget is None:
            return {
                "budget": None,
                "current_cost": 0,
                "remaining": None,
                "percentage_used": 0,
            }

        current_cost = self.tracker.get_total_cost()
        remaining = self.budget - current_cost
        percentage_used = (current_cost / self.budget) * 100

        return {
            "budget": self.budget,
            "current_cost": current_cost,
            "remaining": remaining,
            "percentage_used": percentage_used,
        }


class CostOptimizer:
    """Optimizes API usage costs.

    This class provides utilities for optimizing API usage costs,
    including cost-based routing and usage recommendations.
    """

    def __init__(self, tracker: Optional[CostTracker] = None):
        """Initialize the cost optimizer.

        Args:
            tracker: Cost tracker to use (optional)
        """
        self.tracker = tracker or CostTracker()
        self.service_costs: Dict[str, Dict[str, float]] = {}

    def register_service_cost(
        self, provider: str, service: str, cost_per_unit: float
    ) -> None:
        """Register the cost per unit for a service.

        Args:
            provider: Provider of the service
            service: Service name
            cost_per_unit: Cost per unit (e.g., per 1000 tokens)
        """
        if provider not in self.service_costs:
            self.service_costs[provider] = {}
        self.service_costs[provider][service] = cost_per_unit

    def get_cheapest_service(
        self, providers: Optional[List[str]] = None, min_tier: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get the cheapest service that meets the requirements.

        Args:
            providers: List of providers to consider (optional)
            min_tier: Minimum service tier required (optional)

        Returns:
            Dictionary with provider and service information, or None if no service meets the requirements
        """
        if not self.service_costs:
            return None

        cheapest_cost = float("inf")
        cheapest_service = None

        for provider, services in self.service_costs.items():
            # Skip if provider not in the list
            if providers and provider not in providers:
                continue

            for service, cost in services.items():
                # Skip if service doesn't meet minimum tier
                if min_tier and not self._meets_min_tier(service, min_tier):
                    continue

                if cost < cheapest_cost:
                    cheapest_cost = cost
                    cheapest_service = {
                        "provider": provider,
                        "service": service,
                        "cost_per_unit": cost,
                    }

        return cheapest_service

    def _meets_min_tier(self, service: str, min_tier: str) -> bool:
        """Check if a service meets the minimum tier requirement.

        This is a simple implementation that assumes service names include tier information.
        In a real implementation, this would use a more sophisticated approach.

        Args:
            service: Service name
            min_tier: Minimum service tier required

        Returns:
            True if the service meets the minimum tier requirement, False otherwise
        """
        # Simple implementation - just check if the service name includes the tier
        return min_tier.lower() in service.lower()

    def estimate_cost(
        self, provider: str, service: str, usage_amount: float
    ) -> Optional[float]:
        """Estimate the cost for a given usage.

        Args:
            provider: Provider of the service
            service: Service name
            usage_amount: Amount of usage

        Returns:
            Estimated cost, or None if the service cost is not registered
        """
        if (
            provider not in self.service_costs
            or service not in self.service_costs[provider]
        ):
            return None

        cost_per_unit = self.service_costs[provider][service]
        return cost_per_unit * usage_amount

    def get_usage_recommendations(self) -> Dict[str, Any]:
        """Get usage recommendations based on historical data.

        Returns:
            Dictionary containing usage recommendations
        """
        # Get costs by service
        costs_by_service = self.tracker.get_cost_by_service()

        # Get total cost
        total_cost = sum(costs_by_service.values())

        # Calculate percentage of total cost for each service
        service_percentages = {
            service: (cost / total_cost) * 100 if total_cost > 0 else 0
            for service, cost in costs_by_service.items()
        }

        # Identify high-cost services (>20% of total)
        high_cost_services = {
            service: percentage
            for service, percentage in service_percentages.items()
            if percentage > 20
        }

        # Generate recommendations
        recommendations = []

        if high_cost_services:
            for service, percentage in high_cost_services.items():
                provider, service_name = service.split("/", 1)

                # Try to find a cheaper alternative
                cheaper_alternative = self.get_cheapest_service([provider])

                if (
                    cheaper_alternative
                    and cheaper_alternative["service"] != service_name
                ):
                    recommendations.append({
                        "service": service,
                        "percentage_of_total": percentage,
                        "recommendation": f"Consider using {cheaper_alternative['service']} instead",
                        "potential_savings": "Unknown",  # Would require usage data to estimate
                    })

        return {
            "total_cost": total_cost,
            "high_cost_services": high_cost_services,
            "recommendations": recommendations,
        }
