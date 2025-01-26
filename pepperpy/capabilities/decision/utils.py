"""Decision utilities."""
import random
from typing import Any, List

class ProbabilityCalculator:
    """Helper class for probability calculations."""
    
    def apply_temperature(
        self,
        scores: List[float],
        temperature: float
    ) -> List[float]:
        """Apply temperature to scores."""
        if temperature == 0:
            return scores
        return [score / temperature for score in scores]
    
    def normalize(self, scores: List[float]) -> List[float]:
        """Normalize scores to probabilities."""
        total = sum(scores)
        if total == 0:
            # If all scores are zero, use uniform distribution
            return [1.0 / len(scores)] * len(scores)
        return [score / total for score in scores]
    
    def sample(
        self,
        options: List[Any],
        scores: List[float],
        temperature: float = 1.0
    ) -> Any:
        """Sample an option based on scores and temperature."""
        if not options:
            return None
            
        # Apply temperature and normalize
        scores = self.apply_temperature(scores, temperature)
        probs = self.normalize(scores)
        
        # Sample based on probabilities
        r = random.random()
        cumsum = 0
        for option, prob in zip(options, probs):
            cumsum += prob
            if r <= cumsum:
                return option
                
        return options[-1] 