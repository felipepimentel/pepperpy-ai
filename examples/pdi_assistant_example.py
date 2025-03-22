"""Example of using PepperPy to create a PDI (Personal Development Initiative) assistant."""

import asyncio
import json
import shutil
from datetime import datetime, timedelta
from typing import Any, Dict, List

from pepperpy.rag import Document, HashEmbeddingFunction, Query
from pepperpy.rag.providers import AnnoyRAGProvider


class PDIAssistant:
    """PDI Assistant that helps users track their personal development goals."""

    def __init__(self) -> None:
        self.data_dir = "data/pdi_assistant/rag"
        self.embedding_function = HashEmbeddingFunction()
        self.rag_provider = AnnoyRAGProvider(
            data_dir=self.data_dir,
            embedding_dim=1536,  # Default for OpenAI embeddings
            n_trees=10,
        )

    async def initialize(self) -> None:
        """Initialize the assistant."""
        # Remove existing data to start fresh
        shutil.rmtree(self.data_dir, ignore_errors=True)
        await self.rag_provider.initialize()

    async def shutdown(self) -> None:
        """Shut down the assistant."""
        await self.rag_provider.shutdown()

    async def create_pdi(
        self,
        user_id: str,
        goals: List[str],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a PDI for a user.

        Args:
            user_id: ID of the user
            goals: List of goals for the PDI
            **kwargs: Additional arguments

        Returns:
            Created PDI data
        """
        # Create PDI document
        pdi_data = {
            "user_id": user_id,
            "goals": goals,
            "created_at": datetime.now().isoformat(),
        }

        # Add action plan
        action_plan = [
            {
                "skill": "Machine Learning",
                "action": "Complete ML course on Coursera",
                "deadline": (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d"),
            },
            {
                "skill": "Deep Learning",
                "action": "Read Deep Learning book by Ian Goodfellow",
                "deadline": (datetime.now() + timedelta(days=240)).strftime("%Y-%m-%d"),
            },
        ]
        pdi_data["action_plan"] = action_plan

        # Add recommendations (empty for now)
        pdi_data["recommendations"] = []

        # Create document
        doc = Document(
            id=f"pdi:{user_id}",
            content=json.dumps(pdi_data),
            metadata={"type": "pdi", "user_id": user_id},
        )

        # Add embeddings
        doc.embeddings = await self.embedding_function.embed_text(doc.content)

        # Add to RAG provider
        await self.rag_provider.add_documents([doc])

        return pdi_data

    async def search_pdis(self, query_text: str) -> List[Dict[str, Any]]:
        """Search for PDIs matching a query.

        Args:
            query_text: Text to search for

        Returns:
            List of matching PDIs
        """
        # Create query
        query = Query(text=query_text)
        query.embeddings = await self.embedding_function.embed_text(query.text)

        # Search
        result = await self.rag_provider.search(query)

        # Parse results
        pdis = []
        for doc in result.documents:
            try:
                pdi_data = json.loads(doc.content)
                pdis.append(pdi_data)
            except json.JSONDecodeError:
                continue

        return pdis


async def main() -> None:
    """Run the example."""
    # Create assistant
    assistant = PDIAssistant()
    await assistant.initialize()

    try:
        # Create PDI
        pdi = await assistant.create_pdi(
            user_id="user123",
            goals=["Improve Python skills", "Learn AI/ML"],
        )

        # Print results
        print(f"Created PDI for user {pdi['user_id']}")
        print(f"Goals: {pdi['goals']}")
        print(f"Action Plan: {pdi['action_plan']}")
        print(f"Recommendations: {pdi['recommendations']}")

        # Search for PDIs
        print("\nSearching for PDIs about Machine Learning...")
        pdis = await assistant.search_pdis("Machine Learning")
        for pdi in pdis:
            print(f"\nFound PDI for user {pdi['user_id']}")
            print(f"Goals: {pdi['goals']}")
            print(f"Action Plan: {pdi['action_plan']}")

    finally:
        await assistant.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
