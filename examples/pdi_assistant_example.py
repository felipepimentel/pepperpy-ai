"""Example of using PepperPy to create a PDI (Personal Development Initiative) assistant."""

import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

try:
    from dotenv import load_dotenv
except ImportError:
    # Mock load_dotenv if not available
    def load_dotenv():
        """Mock function for load_dotenv."""
        print("Warning: dotenv not available, skipping environment loading")

# Commented out actual imports to avoid dependency issues
# from pepperpy.rag import Document, HashEmbeddingFunction, Query
# from pepperpy.rag.providers import AnnoyRAGProvider

# Define Document class for the example
class Document:
    """Document class for the example."""
    
    def __init__(self, id: str, content: str, metadata: Dict[str, Any]):
        self.id = id
        self.content = content
        self.metadata = metadata
        self.embeddings = None


class PDIAssistant:
    """PDI Assistant that helps users track their personal development goals."""

    def __init__(self) -> None:
        """Initialize the PDI assistant."""
        # Load environment variables
        load_dotenv()
        
        # In a real implementation, we would use:
        # self.data_dir = "data/pdi_assistant/rag"
        # self.embedding_function = HashEmbeddingFunction()
        # self.rag_provider = AnnoyRAGProvider(
        #     data_dir=self.data_dir,
        #     embedding_dim=1536,  # Default for OpenAI embeddings
        #     n_trees=10,
        # )
        
        # For this example, we'll use mock data
        self.output_dir = Path("examples/output/pdi_assistant")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.pdis = {}  # Store PDIs in memory for the example

    async def initialize(self) -> None:
        """Initialize the assistant."""
        print("Initializing PDI Assistant (simulation)...")
        # In a real implementation, we would:
        # Remove existing data to start fresh
        # shutil.rmtree(self.data_dir, ignore_errors=True)
        # await self.rag_provider.initialize()
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def shutdown(self) -> None:
        """Shut down the assistant."""
        print("Shutting down PDI Assistant...")
        # In a real implementation, we would:
        # await self.rag_provider.shutdown()

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

        # Save PDI data to output dir
        output_file = self.output_dir / f"pdi_{user_id}.json"
        with open(output_file, "w") as f:
            json.dump(pdi_data, f, indent=2)
        
        # Store in memory for the example
        self.pdis[user_id] = pdi_data

        # In a real implementation, we would:
        # Create document
        # doc = Document(
        #     id=f"pdi:{user_id}",
        #     content=json.dumps(pdi_data),
        #     metadata={"type": "pdi", "user_id": user_id},
        # )
        # Add embeddings
        # doc.embeddings = await self.embedding_function.embed_text(doc.content)
        # Add to RAG provider
        # await self.rag_provider.add_documents([doc])

        return pdi_data

    async def search_pdis(self, query_text: str) -> List[Dict[str, Any]]:
        """Search for PDIs matching a query.

        Args:
            query_text: Text to search for

        Returns:
            List of matching PDIs
        """
        print(f"Searching for PDIs with query: {query_text}")
        
        # In a real implementation, we would:
        # Create query
        # query = Query(text=query_text)
        # query.embeddings = await self.embedding_function.embed_text(query.text)
        # Search
        # result = await self.rag_provider.search(query)
        # Parse results
        # pdis = []
        # for doc in result.documents:
        #     try:
        #         pdi_data = json.loads(doc.content)
        #         pdis.append(pdi_data)
        #     except json.JSONDecodeError:
        #         continue
        
        # For this example, we'll just do a simple text search
        pdis = []
        for pdi_data in self.pdis.values():
            # Simple keyword matching (in a real implementation, this would use embeddings)
            pdi_json = json.dumps(pdi_data).lower()
            if query_text.lower() in pdi_json:
                pdis.append(pdi_data)
        
        return pdis


async def main() -> None:
    """Run the example."""
    print("PDI Assistant Example")
    print("=" * 80)
    
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
        print(f"\nCreated PDI for user {pdi['user_id']}")
        print(f"Goals: {', '.join(pdi['goals'])}")
        print("\nAction Plan:")
        for item in pdi['action_plan']:
            print(f"- {item['skill']}: {item['action']} (Deadline: {item['deadline']})")

        # Search for PDIs
        print("\nSearching for PDIs about Machine Learning...")
        pdis = await assistant.search_pdis("Machine Learning")
        
        if pdis:
            print(f"Found {len(pdis)} matching PDIs")
            for pdi in pdis:
                print(f"\nUser: {pdi['user_id']}")
                print(f"Goals: {', '.join(pdi['goals'])}")
                print("Action Plan:")
                for item in pdi['action_plan']:
                    print(f"- {item['skill']}: {item['action']}")
        else:
            print("No matching PDIs found")
        
        print("\nThis is a demonstration example. In a real implementation:")
        print("1. The assistant would use actual embeddings for semantic search")
        print("2. PDIs would be stored in a vector database for efficient retrieval")
        print("3. Recommendations would be generated based on user progress")
        print("4. Actions would be tracked with completion status")
        print("\nExample completed successfully!")

    finally:
        await assistant.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
