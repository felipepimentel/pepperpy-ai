"""PDI Assistant Example.

This example demonstrates how to use PepperPy to create a PDI (Individual Development Plan)
assistant that helps users track and evolve their development plans.

Example:
    $ python examples/pdi_assistant_example.py
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from mock_rag_provider import MockRAGProvider
from mock_storage_provider import MockStorageProvider

from pepperpy.agents import Agent
from pepperpy.rag import Query, RAGProvider
from pepperpy.storage import StorageProvider


@dataclass
class PDI:
    """Individual Development Plan."""

    user_id: str
    goals: List[str]
    skills: List[str]
    action_plan: List[Dict[str, str]]
    resources: List[Dict[str, str]]
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    def to_json(self) -> str:
        """Convert PDI to JSON string."""
        return json.dumps(
            {
                "user_id": self.user_id,
                "goals": self.goals,
                "skills": self.skills,
                "action_plan": self.action_plan,
                "resources": self.resources,
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat(),
            }
        )

    @classmethod
    def from_json(cls, data: str) -> "PDI":
        """Create PDI from JSON string."""
        obj = json.loads(data)
        return cls(
            user_id=obj["user_id"],
            goals=obj["goals"],
            skills=obj["skills"],
            action_plan=obj["action_plan"],
            resources=obj["resources"],
            created_at=datetime.fromisoformat(obj["created_at"]),
            updated_at=datetime.fromisoformat(obj["updated_at"]),
        )


class PDIAssistant:
    """PDI Assistant using PepperPy modules."""

    def __init__(
        self,
        agent: Optional[Agent] = None,
        rag_provider: Optional[RAGProvider] = None,
        storage_provider: Optional[StorageProvider] = None,
    ):
        """Initialize PDI Assistant."""
        self.agent = agent or Agent("pdi_assistant")
        self.rag = rag_provider or MockRAGProvider()
        self.storage = storage_provider or MockStorageProvider()

    async def analyze_profile(self, profile: Dict) -> Dict:
        """Analyze user profile to identify development needs."""
        self.agent.add_memory(
            content=f"User profile: {json.dumps(profile)}", metadata={"type": "profile"}
        )
        return {
            "user_id": profile.get("id"),
            "goals": ["Improve Python skills", "Learn AI/ML"],
            "skills": ["Python", "Git", "SQL"],
        }

    async def identify_skills(self, data: Dict) -> Dict:
        """Identify skills to develop based on goals."""
        goals = data.get("goals", [])
        skills = data.get("skills", [])
        self.agent.add_memory(
            content=f"Goals: {goals}, Current skills: {skills}",
            metadata={"type": "skills"},
        )
        return {
            **data,
            "skills_to_develop": ["Machine Learning", "Deep Learning", "TensorFlow"],
        }

    async def create_action_plan(self, data: Dict) -> Dict:
        """Create action plan based on skills to develop."""
        skills = data.get("skills_to_develop", [])
        self.agent.add_memory(
            content=f"Skills to develop: {skills}", metadata={"type": "action_plan"}
        )
        return {
            **data,
            "action_plan": [
                {
                    "skill": "Machine Learning",
                    "action": "Complete ML course on Coursera",
                    "deadline": "2024-06-30",
                },
                {
                    "skill": "Deep Learning",
                    "action": "Read Deep Learning book by Ian Goodfellow",
                    "deadline": "2024-08-31",
                },
            ],
        }

    async def find_resources(self, data: Dict) -> Dict:
        """Find learning resources for action plan."""
        action_plan = data.get("action_plan", [])
        resources = []
        for item in action_plan:
            query = Query(
                text=f"Find resources for learning {item['skill']}",
                metadata={"type": "learning_resource"},
            )
            results = await self.rag.search(query, limit=5)
            resources.extend(
                [
                    {
                        "skill": item["skill"],
                        "title": doc.content,
                        "url": doc.metadata.get("url", ""),
                    }
                    for doc in results.documents
                ]
            )
        return {**data, "resources": resources}

    async def create_pdi(self, user_profile: Dict) -> PDI:
        """Create a new PDI for user."""
        data = await self.analyze_profile(user_profile)
        data = await self.identify_skills(data)
        data = await self.create_action_plan(data)
        data = await self.find_resources(data)

        pdi = PDI(
            user_id=data["user_id"],
            goals=data["goals"],
            skills=data["skills"],
            action_plan=data["action_plan"],
            resources=data["resources"],
        )
        await self.storage.write(f"pdi/{pdi.user_id}", pdi.to_json())
        return pdi

    async def update_progress(self, user_id: str, skill: str, progress: str) -> None:
        """Update progress for a skill in user's PDI."""
        data = await self.storage.read(f"pdi/{user_id}")
        pdi = PDI.from_json(data.decode("utf-8"))
        self.agent.add_memory(
            content=f"Progress update for {skill}: {progress}",
            metadata={"type": "progress", "user_id": user_id},
        )
        # Update PDI with progress
        pdi.updated_at = datetime.now()
        await self.storage.write(f"pdi/{user_id}", pdi.to_json())

    async def get_recommendations(self, user_id: str) -> List[Dict[str, str]]:
        """Get recommendations based on PDI progress."""
        data = await self.storage.read(f"pdi/{user_id}")
        pdi = PDI.from_json(data.decode("utf-8"))
        query = Query(
            text="Get recommendations for PDI progress",
            metadata={"type": "recommendation"},
        )
        results = await self.rag.search(query, limit=5)
        return [
            {
                "title": doc.content,
                "type": doc.metadata.get("type", "general"),
                "priority": doc.metadata.get("priority", "medium"),
            }
            for doc in results.documents
        ]


async def main():
    """Run PDI Assistant example."""
    assistant = PDIAssistant()

    # Create PDI for user
    user_profile = {
        "id": "user123",
        "name": "John Doe",
        "role": "Software Engineer",
        "interests": ["AI/ML", "Python", "Cloud Computing"],
    }
    pdi = await assistant.create_pdi(user_profile)
    print(f"Created PDI for user {pdi.user_id}")
    print(f"Goals: {pdi.goals}")
    print(f"Action Plan: {pdi.action_plan}")

    # Update progress
    await assistant.update_progress(
        pdi.user_id, "Machine Learning", "Completed first week of Coursera course"
    )

    # Get recommendations
    recommendations = await assistant.get_recommendations(pdi.user_id)
    print(f"Recommendations: {recommendations}")


if __name__ == "__main__":
    asyncio.run(main())
