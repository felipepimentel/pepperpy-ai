#!/usr/bin/env python3
"""
Benchmark script for AI Gateway multiport system.

This script tests performance of all gateway services and advanced features.
"""

import argparse
import asyncio
import json
import logging
import statistics
import sys
import time
from typing import Any

import aiohttp
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("benchmark")


class AIGatewayBenchmark:
    """Benchmark tool for AI Gateway multiport system."""

    def __init__(
        self,
        config_path: str | None = None,
        concurrency: int = 10,
        duration: int = 60,
        warmup: int = 10,
    ):
        """Initialize benchmark.

        Args:
            config_path: Path to configuration file
            concurrency: Number of concurrent requests
            duration: Test duration in seconds
            warmup: Warmup period in seconds
        """
        self.config_path = config_path
        self.config = {}
        self.services = []
        self.concurrency = concurrency
        self.duration = duration
        self.warmup = warmup
        self.results = {}

    async def load_config(self) -> dict[str, Any]:
        """Load configuration from file.

        Returns:
            Configuration dictionary
        """
        try:
            if not self.config_path:
                logger.error("No configuration path provided")
                return {}

            with open(self.config_path) as f:
                self.config = yaml.safe_load(f)

            # Extract services information
            multiport_config = self.config.get("multiport", {})
            self.services = multiport_config.get("services", [])

            if not self.services:
                logger.warning("No multiport services found in configuration")

            return self.config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}

    async def benchmark_chat_completion(self, host: str, port: int) -> dict[str, Any]:
        """Benchmark chat completion endpoint.

        Args:
            host: Host of the service
            port: Port of the service

        Returns:
            Benchmark results
        """
        url = f"http://{host}:{port}/v1/chat/completions"

        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Tell me a short joke."},
            ],
            "max_tokens": 50,
            "temperature": 0.7,
        }

        results = {
            "successful_requests": 0,
            "failed_requests": 0,
            "latencies": [],
            "start_time": time.time(),
            "end_time": 0,
            "errors": {},
        }

        headers = {"Content-Type": "application/json"}

        # Create client session
        async with aiohttp.ClientSession() as session:
            # Warmup
            if self.warmup > 0:
                logger.info(f"Warming up for {self.warmup} seconds...")
                warmup_end = time.time() + self.warmup

                while time.time() < warmup_end:
                    try:
                        await session.post(url, json=payload, headers=headers)
                    except Exception as e:
                        logger.debug(f"Warmup error: {e}")

                    await asyncio.sleep(0.5)

                logger.info("Warmup completed")

            # Run benchmark tasks
            tasks = []
            start_time = time.time()
            end_time = start_time + self.duration

            logger.info(
                f"Starting benchmark for {self.duration} seconds with {self.concurrency} concurrent requests"
            )

            for _ in range(self.concurrency):
                tasks.append(
                    asyncio.create_task(
                        self._run_benchmark_worker(
                            session, url, payload, headers, end_time, results
                        )
                    )
                )

            await asyncio.gather(*tasks)

            results["end_time"] = time.time()

            # Calculate statistics
            total_requests = results["successful_requests"] + results["failed_requests"]
            duration = results["end_time"] - results["start_time"]

            if results["latencies"]:
                avg_latency = statistics.mean(results["latencies"])
                p50_latency = statistics.median(results["latencies"])
                p95_latency = (
                    results["latencies"][int(0.95 * len(results["latencies"])) - 1]
                    if len(results["latencies"]) > 20
                    else None
                )
                p99_latency = (
                    results["latencies"][int(0.99 * len(results["latencies"])) - 1]
                    if len(results["latencies"]) > 100
                    else None
                )
                min_latency = min(results["latencies"])
                max_latency = max(results["latencies"])
            else:
                avg_latency = p50_latency = p95_latency = p99_latency = min_latency = (
                    max_latency
                ) = 0

            # Add calculated metrics to results
            results["total_requests"] = total_requests
            results["requests_per_second"] = total_requests / duration
            results["average_latency"] = avg_latency
            results["p50_latency"] = p50_latency
            results["p95_latency"] = p95_latency
            results["p99_latency"] = p99_latency
            results["min_latency"] = min_latency
            results["max_latency"] = max_latency
            results["success_rate"] = (
                results["successful_requests"] / total_requests
                if total_requests > 0
                else 0
            )

            return results

    async def _run_benchmark_worker(
        self,
        session: aiohttp.ClientSession,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
        end_time: float,
        results: dict[str, Any],
    ) -> None:
        """Worker for benchmark tasks.

        Args:
            session: HTTP session
            url: URL to benchmark
            payload: Request payload
            headers: Request headers
            end_time: End time for benchmark
            results: Results dictionary to update
        """
        while time.time() < end_time:
            start = time.time()

            try:
                timeout = aiohttp.ClientTimeout(total=30)
                async with session.post(
                    url, json=payload, headers=headers, timeout=timeout
                ) as response:
                    latency = time.time() - start
                    results["latencies"].append(latency)

                    if response.status == 200:
                        results["successful_requests"] += 1
                    else:
                        results["failed_requests"] += 1
                        error_key = f"HTTP {response.status}"
                        results["errors"][error_key] = (
                            results["errors"].get(error_key, 0) + 1
                        )

            except Exception as e:
                results["failed_requests"] += 1
                error_type = type(e).__name__
                results["errors"][error_type] = results["errors"].get(error_type, 0) + 1

    async def benchmark_function_calling(self, host: str, port: int) -> dict[str, Any]:
        """Benchmark function calling endpoint.

        Args:
            host: Host of the service
            port: Port of the service

        Returns:
            Benchmark results
        """
        url = f"http://{host}:{port}/v1/functions/call"

        payload = {"function": "calculator", "parameters": {"expression": "2+2*5"}}

        results = {
            "successful_requests": 0,
            "failed_requests": 0,
            "latencies": [],
            "start_time": time.time(),
            "end_time": 0,
            "errors": {},
        }

        headers = {"Content-Type": "application/json"}

        # Create client session
        async with aiohttp.ClientSession() as session:
            # Warmup
            if self.warmup > 0:
                logger.info(f"Warming up for {self.warmup} seconds...")
                warmup_end = time.time() + self.warmup

                while time.time() < warmup_end:
                    try:
                        await session.post(url, json=payload, headers=headers)
                    except Exception as e:
                        logger.debug(f"Warmup error: {e}")

                    await asyncio.sleep(0.5)

                logger.info("Warmup completed")

            # Run benchmark tasks
            tasks = []
            start_time = time.time()
            end_time = start_time + self.duration

            logger.info(
                f"Starting benchmark for {self.duration} seconds with {self.concurrency} concurrent requests"
            )

            for _ in range(self.concurrency):
                tasks.append(
                    asyncio.create_task(
                        self._run_benchmark_worker(
                            session, url, payload, headers, end_time, results
                        )
                    )
                )

            await asyncio.gather(*tasks)

            results["end_time"] = time.time()

            # Calculate statistics
            total_requests = results["successful_requests"] + results["failed_requests"]
            duration = results["end_time"] - results["start_time"]

            if results["latencies"]:
                avg_latency = statistics.mean(results["latencies"])
                p50_latency = statistics.median(results["latencies"])
                p95_latency = (
                    results["latencies"][int(0.95 * len(results["latencies"])) - 1]
                    if len(results["latencies"]) > 20
                    else None
                )
                p99_latency = (
                    results["latencies"][int(0.99 * len(results["latencies"])) - 1]
                    if len(results["latencies"]) > 100
                    else None
                )
                min_latency = min(results["latencies"])
                max_latency = max(results["latencies"])
            else:
                avg_latency = p50_latency = p95_latency = p99_latency = min_latency = (
                    max_latency
                ) = 0

            # Add calculated metrics to results
            results["total_requests"] = total_requests
            results["requests_per_second"] = total_requests / duration
            results["average_latency"] = avg_latency
            results["p50_latency"] = p50_latency
            results["p95_latency"] = p95_latency
            results["p99_latency"] = p99_latency
            results["min_latency"] = min_latency
            results["max_latency"] = max_latency
            results["success_rate"] = (
                results["successful_requests"] / total_requests
                if total_requests > 0
                else 0
            )

            return results

    async def benchmark_rag_query(self, host: str, port: int) -> dict[str, Any]:
        """Benchmark RAG query endpoint.

        Args:
            host: Host of the service
            port: Port of the service

        Returns:
            Benchmark results
        """
        url = f"http://{host}:{port}/v1/rag/query"

        payload = {"query": "What is AI Gateway?", "top_k": 3}

        results = {
            "successful_requests": 0,
            "failed_requests": 0,
            "latencies": [],
            "start_time": time.time(),
            "end_time": 0,
            "errors": {},
        }

        headers = {"Content-Type": "application/json"}

        # Create client session
        async with aiohttp.ClientSession() as session:
            # Warmup
            if self.warmup > 0:
                logger.info(f"Warming up for {self.warmup} seconds...")
                warmup_end = time.time() + self.warmup

                while time.time() < warmup_end:
                    try:
                        await session.post(url, json=payload, headers=headers)
                    except Exception as e:
                        logger.debug(f"Warmup error: {e}")

                    await asyncio.sleep(0.5)

                logger.info("Warmup completed")

            # Run benchmark tasks
            tasks = []
            start_time = time.time()
            end_time = start_time + self.duration

            logger.info(
                f"Starting benchmark for {self.duration} seconds with {self.concurrency} concurrent requests"
            )

            for _ in range(self.concurrency):
                tasks.append(
                    asyncio.create_task(
                        self._run_benchmark_worker(
                            session, url, payload, headers, end_time, results
                        )
                    )
                )

            await asyncio.gather(*tasks)

            results["end_time"] = time.time()

            # Calculate statistics
            total_requests = results["successful_requests"] + results["failed_requests"]
            duration = results["end_time"] - results["start_time"]

            if results["latencies"]:
                avg_latency = statistics.mean(results["latencies"])
                p50_latency = statistics.median(results["latencies"])
                p95_latency = (
                    results["latencies"][int(0.95 * len(results["latencies"])) - 1]
                    if len(results["latencies"]) > 20
                    else None
                )
                p99_latency = (
                    results["latencies"][int(0.99 * len(results["latencies"])) - 1]
                    if len(results["latencies"]) > 100
                    else None
                )
                min_latency = min(results["latencies"])
                max_latency = max(results["latencies"])
            else:
                avg_latency = p50_latency = p95_latency = p99_latency = min_latency = (
                    max_latency
                ) = 0

            # Add calculated metrics to results
            results["total_requests"] = total_requests
            results["requests_per_second"] = total_requests / duration
            results["average_latency"] = avg_latency
            results["p50_latency"] = p50_latency
            results["p95_latency"] = p95_latency
            results["p99_latency"] = p99_latency
            results["min_latency"] = min_latency
            results["max_latency"] = max_latency
            results["success_rate"] = (
                results["successful_requests"] / total_requests
                if total_requests > 0
                else 0
            )

            return results

    async def run_benchmarks(self) -> dict[str, Any]:
        """Run all benchmarks.

        Returns:
            Benchmark results
        """
        logger.info(f"Starting benchmarks with configuration: {self.config_path}")

        # Load configuration
        await self.load_config()

        if not self.services:
            logger.error("No services configured for benchmark")
            return {"status": "error", "message": "No services configured"}

        # Find API service
        api_service = next(
            (s for s in self.services if s.get("type", "api") == "api"), None
        )
        if not api_service:
            logger.error("No API service found for benchmark")
            return {"status": "error", "message": "No API service found"}

        host = api_service.get("host", "localhost")
        port = api_service.get("port")

        if not port:
            logger.error("API service missing port configuration")
            return {"status": "error", "message": "API service missing port"}

        # Run benchmarks for different endpoints
        logger.info(f"Running benchmarks for API service at {host}:{port}")

        # Chat completion benchmark
        logger.info("Starting chat completion benchmark")
        chat_results = await self.benchmark_chat_completion(host, port)
        self.results["chat_completion"] = chat_results
        logger.info(
            f"Chat completion benchmark completed: {chat_results['requests_per_second']:.2f} req/s, "
            + f"Avg latency: {chat_results['average_latency']:.2f}s, "
            + f"Success rate: {chat_results['success_rate'] * 100:.2f}%"
        )

        # Function calling benchmark if enabled
        if self.config.get("function_calling", {}).get("enabled", False):
            logger.info("Starting function calling benchmark")
            function_results = await self.benchmark_function_calling(host, port)
            self.results["function_calling"] = function_results
            logger.info(
                f"Function calling benchmark completed: {function_results['requests_per_second']:.2f} req/s, "
                + f"Avg latency: {function_results['average_latency']:.2f}s, "
                + f"Success rate: {function_results['success_rate'] * 100:.2f}%"
            )

        # RAG benchmark if enabled
        if self.config.get("rag", {}).get("enabled", False):
            logger.info("Starting RAG query benchmark")
            rag_results = await self.benchmark_rag_query(host, port)
            self.results["rag_query"] = rag_results
            logger.info(
                f"RAG query benchmark completed: {rag_results['requests_per_second']:.2f} req/s, "
                + f"Avg latency: {rag_results['average_latency']:.2f}s, "
                + f"Success rate: {rag_results['success_rate'] * 100:.2f}%"
            )

        # Add benchmark metadata
        self.results["metadata"] = {
            "timestamp": time.time(),
            "concurrency": self.concurrency,
            "duration": self.duration,
            "warmup": self.warmup,
            "config_path": self.config_path,
        }

        return self.results

    def save_results(self, output_path: str) -> None:
        """Save benchmark results to file.

        Args:
            output_path: Path to save results
        """
        try:
            with open(output_path, "w") as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"Results saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")

    def print_results(self) -> None:
        """Print benchmark results to console."""
        if not self.results:
            print("No benchmark results available")
            return

        print("\n===== AI Gateway Benchmark Results =====\n")

        metadata = self.results.get("metadata", {})
        timestamp = metadata.get("timestamp", 0)

        print(
            f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}"
        )
        print(f"Concurrency: {metadata.get('concurrency', 0)}")
        print(f"Duration: {metadata.get('duration', 0)} seconds")
        print(f"Warmup: {metadata.get('warmup', 0)} seconds")
        print(f"Configuration: {metadata.get('config_path', 'N/A')}")
        print()

        # Print chat completion results
        chat_results = self.results.get("chat_completion")
        if chat_results:
            print("=== Chat Completion Benchmark ===")
            print(f"Total requests: {chat_results.get('total_requests', 0)}")
            print(f"Successful requests: {chat_results.get('successful_requests', 0)}")
            print(f"Failed requests: {chat_results.get('failed_requests', 0)}")
            print(
                f"Requests per second: {chat_results.get('requests_per_second', 0):.2f}"
            )
            print(
                f"Average latency: {chat_results.get('average_latency', 0):.2f} seconds"
            )
            print(
                f"Median latency (P50): {chat_results.get('p50_latency', 0):.2f} seconds"
            )
            print(
                f"P95 latency: {chat_results.get('p95_latency', 0):.2f} seconds"
                if chat_results.get("p95_latency")
                else "P95 latency: N/A"
            )
            print(
                f"P99 latency: {chat_results.get('p99_latency', 0):.2f} seconds"
                if chat_results.get("p99_latency")
                else "P99 latency: N/A"
            )
            print(f"Min latency: {chat_results.get('min_latency', 0):.2f} seconds")
            print(f"Max latency: {chat_results.get('max_latency', 0):.2f} seconds")
            print(f"Success rate: {chat_results.get('success_rate', 0) * 100:.2f}%")

            if chat_results.get("errors"):
                print("\nErrors:")
                for error, count in chat_results.get("errors", {}).items():
                    print(f"  {error}: {count}")

            print()

        # Print function calling results
        function_results = self.results.get("function_calling")
        if function_results:
            print("=== Function Calling Benchmark ===")
            print(f"Total requests: {function_results.get('total_requests', 0)}")
            print(
                f"Successful requests: {function_results.get('successful_requests', 0)}"
            )
            print(f"Failed requests: {function_results.get('failed_requests', 0)}")
            print(
                f"Requests per second: {function_results.get('requests_per_second', 0):.2f}"
            )
            print(
                f"Average latency: {function_results.get('average_latency', 0):.2f} seconds"
            )
            print(
                f"Median latency (P50): {function_results.get('p50_latency', 0):.2f} seconds"
            )
            print(
                f"P95 latency: {function_results.get('p95_latency', 0):.2f} seconds"
                if function_results.get("p95_latency")
                else "P95 latency: N/A"
            )
            print(
                f"P99 latency: {function_results.get('p99_latency', 0):.2f} seconds"
                if function_results.get("p99_latency")
                else "P99 latency: N/A"
            )
            print(f"Min latency: {function_results.get('min_latency', 0):.2f} seconds")
            print(f"Max latency: {function_results.get('max_latency', 0):.2f} seconds")
            print(f"Success rate: {function_results.get('success_rate', 0) * 100:.2f}%")

            if function_results.get("errors"):
                print("\nErrors:")
                for error, count in function_results.get("errors", {}).items():
                    print(f"  {error}: {count}")

            print()

        # Print RAG query results
        rag_results = self.results.get("rag_query")
        if rag_results:
            print("=== RAG Query Benchmark ===")
            print(f"Total requests: {rag_results.get('total_requests', 0)}")
            print(f"Successful requests: {rag_results.get('successful_requests', 0)}")
            print(f"Failed requests: {rag_results.get('failed_requests', 0)}")
            print(
                f"Requests per second: {rag_results.get('requests_per_second', 0):.2f}"
            )
            print(
                f"Average latency: {rag_results.get('average_latency', 0):.2f} seconds"
            )
            print(
                f"Median latency (P50): {rag_results.get('p50_latency', 0):.2f} seconds"
            )
            print(
                f"P95 latency: {rag_results.get('p95_latency', 0):.2f} seconds"
                if rag_results.get("p95_latency")
                else "P95 latency: N/A"
            )
            print(
                f"P99 latency: {rag_results.get('p99_latency', 0):.2f} seconds"
                if rag_results.get("p99_latency")
                else "P99 latency: N/A"
            )
            print(f"Min latency: {rag_results.get('min_latency', 0):.2f} seconds")
            print(f"Max latency: {rag_results.get('max_latency', 0):.2f} seconds")
            print(f"Success rate: {rag_results.get('success_rate', 0) * 100:.2f}%")

            if rag_results.get("errors"):
                print("\nErrors:")
                for error, count in rag_results.get("errors", {}).items():
                    print(f"  {error}: {count}")

        print("\n===== End of Benchmark Results =====\n")


async def main() -> int:
    """Main entry point for benchmark script.

    Returns:
        Exit code
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Benchmark AI Gateway multiport system"
    )
    parser.add_argument(
        "--config", "-c", help="Path to configuration file", required=True
    )
    parser.add_argument(
        "--concurrency",
        "-n",
        help="Number of concurrent requests",
        type=int,
        default=10,
    )
    parser.add_argument(
        "--duration", "-d", help="Test duration in seconds", type=int, default=60
    )
    parser.add_argument(
        "--warmup", "-w", help="Warmup period in seconds", type=int, default=10
    )
    parser.add_argument(
        "--output", "-o", help="Output file path for results", default=None
    )
    parser.add_argument(
        "--verbose", "-v", help="Enable verbose output", action="store_true"
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create benchmark instance
    benchmark = AIGatewayBenchmark(
        config_path=args.config,
        concurrency=args.concurrency,
        duration=args.duration,
        warmup=args.warmup,
    )

    # Run benchmarks
    results = await benchmark.run_benchmarks()

    # Save results if output path provided
    if args.output:
        benchmark.save_results(args.output)

    # Print results
    benchmark.print_results()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
