import random

from locust import HttpUser, between, task


class AIGatewayUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Initialize user session."""
        self.api_key = "test-key"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Common test prompts
        self.prompts = [
            "What is artificial intelligence?",
            "How does machine learning work?",
            "Explain neural networks",
            "What is deep learning?",
            "Describe reinforcement learning",
        ]

        # Test documents for RAG
        self.documents = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]

        # Test functions for function calling
        self.functions = ["get_weather", "search_products", "calculate_price"]

    @task(3)
    def chat_completion(self):
        """Test chat completion endpoint."""
        payload = {
            "model": random.choice(["gpt-4", "claude-3"]),
            "messages": [{"role": "user", "content": random.choice(self.prompts)}],
        }
        self.client.post("/v1/chat/completions", json=payload, headers=self.headers)

    @task(2)
    def rag_query(self):
        """Test RAG endpoint."""
        payload = {
            "query": random.choice(self.prompts),
            "document": random.choice(self.documents),
            "model": "gpt-4",
        }
        self.client.post("/v1/rag/query", json=payload, headers=self.headers)

    @task(2)
    def function_call(self):
        """Test function calling endpoint."""
        payload = {
            "function": random.choice(self.functions),
            "arguments": {"param1": "value1", "param2": "value2"},
        }
        self.client.post("/v1/functions/execute", json=payload, headers=self.headers)

    @task(1)
    def multimodal_request(self):
        """Test multimodal endpoint."""
        payload = {
            "model": "gpt-4-vision",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What's in this image?"},
                        {"type": "image_url", "url": "https://example.com/test.jpg"},
                    ],
                }
            ],
        }
        self.client.post("/v1/chat/multimodal", json=payload, headers=self.headers)

    @task(1)
    def guardrails_check(self):
        """Test content filtering endpoint."""
        payload = {
            "text": random.choice([
                "Safe content for testing",
                "Potentially unsafe content",
                "Neutral content",
            ])
        }
        self.client.post("/v1/guardrails/check", json=payload, headers=self.headers)
