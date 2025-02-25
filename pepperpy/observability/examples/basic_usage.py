"""Basic example of using the unified observability system."""

import asyncio
import time

from ..provider import UnifiedObservabilityProvider
from ..types import HealthStatus, LogLevel, MetricType


class ExampleService:
    """Example service demonstrating observability integration."""

    def __init__(self) -> None:
        """Initialize service."""
        self.provider = UnifiedObservabilityProvider()
        self._request_count = 0

    async def initialize(self) -> None:
        """Initialize service."""
        await self.provider.initialize()
        await self.provider.log(
            "Service initialized",
            LogLevel.INFO,
        )

    async def cleanup(self) -> None:
        """Clean up service."""
        await self.provider.log(
            "Service shutting down",
            LogLevel.INFO,
        )
        await self.provider.cleanup()

    async def process_request(
        self,
        request_id: str,
        payload: dict | None = None,
    ) -> dict:
        """Process a request with full observability."""
        start_time = time.time()

        try:
            # Start request span
            span = await self.provider.start_span(
                "process_request",
                attributes={"request_id": request_id},
            )

            try:
                # Log request
                await self.provider.log(
                    f"Processing request {request_id}",
                    LogLevel.INFO,
                    {
                        "request_id": request_id,
                        "payload": payload,
                    },
                )

                # Increment request counter
                self._request_count += 1
                await self.provider.record_metric(
                    "requests_total",
                    1,
                    MetricType.COUNTER,
                    {"status": "started"},
                )

                # Simulate processing
                await asyncio.sleep(0.1)

                # Record processing time
                duration = time.time() - start_time
                await self.provider.record_metric(
                    "request_duration_seconds",
                    duration,
                    MetricType.HISTOGRAM,
                )

                # Return result
                result = {
                    "request_id": request_id,
                    "status": "success",
                    "duration": duration,
                }

                await self.provider.log(
                    f"Request {request_id} completed",
                    LogLevel.INFO,
                    result,
                )

                return result

            finally:
                await self.provider.end_span(span)

        except Exception as e:
            # Record error
            await self.provider.log(
                f"Error processing request {request_id}",
                LogLevel.ERROR,
                {
                    "request_id": request_id,
                    "error": str(e),
                },
            )
            await self.provider.record_metric(
                "requests_total",
                1,
                MetricType.COUNTER,
                {"status": "error"},
            )
            raise

    async def check_health(self) -> dict:
        """Check service health."""
        health = await self.provider.check_health(
            "example_service",
            dependencies=["database", "cache"],
        )

        await self.provider.record_metric(
            "health_status",
            1 if health.status == HealthStatus.HEALTHY else 0,
            MetricType.GAUGE,
        )

        return {
            "status": health.status.value,
            "details": health.details,
        }


async def main():
    """Run example service."""
    # Create and initialize service
    service = ExampleService()
    await service.initialize()

    try:
        # Process some requests
        for i in range(5):
            request_id = f"req_{i}"
            try:
                result = await service.process_request(
                    request_id,
                    {"data": f"payload_{i}"},
                )
                print(f"Request {request_id} result:", result)
            except Exception as e:
                print(f"Request {request_id} failed:", e)

        # Check health
        health = await service.check_health()
        print("Service health:", health)

        # Get metrics
        metrics = await service.provider.get_metrics()
        print("\nMetrics:")
        for metric in metrics:
            print(f"- {metric.name}: {metric.value}")

        # Get recent logs
        start_time = time.time() - 60
        logs = await service.provider.get_logs(
            start_time,
            time.time(),
        )
        print("\nRecent logs:")
        for log in logs:
            print(f"- [{log.level.value}] {log.message}")

    finally:
        await service.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
