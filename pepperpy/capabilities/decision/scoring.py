"""Decision scoring utilities."""
from typing import Any, Dict, List, Optional

class RuleScorer:
    """Helper class for rule-based scoring."""
    
    def __init__(self, rule_evaluator: Any, rules: List[Dict[str, Any]]):
        """Initialize rule scorer."""
        self.rule_evaluator = rule_evaluator
        self.rules = rules
    
    def calculate_score(
        self,
        rule: Dict[str, Any],
        option: Any,
        context: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """Calculate score for a single rule."""
        if not self.rule_evaluator.evaluate_rule(rule, context):
            return 0.0
            
        if weights:
            return self.rule_evaluator.calculate_rule_score(rule, option, weights)
        return self.rule_evaluator.calculate_rule_score(rule, option)

class ScoreCalculator:
    """Helper class for calculating scores."""
    
    def __init__(self, rule_evaluator: Any, rules: List[Dict[str, Any]]):
        """Initialize score calculator."""
        self.rule_scorer = RuleScorer(rule_evaluator, rules)
        self.rules = rules
    
    def calculate_base_score(
        self,
        option: Any,
        context: Dict[str, Any]
    ) -> float:
        """Calculate base score without weights."""
        if not isinstance(option, dict):
            return 1.0
            
        return sum(
            self.rule_scorer.calculate_score(rule, option, context)
            for rule in self.rules
        )
    
    def calculate_weighted_score(
        self,
        option: Any,
        context: Dict[str, Any],
        weights: Dict[str, float]
    ) -> float:
        """Calculate weighted score."""
        if not isinstance(option, dict):
            return 0.0
            
        return sum(
            self.rule_scorer.calculate_score(rule, option, context, weights)
            for rule in self.rules
        )
    
    def find_first_match(
        self,
        options: List[Any],
        context: Dict[str, Any]
    ) -> Optional[Any]:
        """Find first option with non-zero score."""
        if not options:
            return None
            
        for option in options:
            if self.calculate_base_score(option, context) > 0:
                return option
                
        return options[0]
    
    def find_highest_score(
        self,
        options: List[Any],
        context: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None
    ) -> Optional[Any]:
        """Find option with highest score."""
        if not options:
            return None
            
        if weights:
            scores = {
                option: self.calculate_weighted_score(option, context, weights)
                for option in options
            }
        else:
            scores = {
                option: self.calculate_base_score(option, context)
                for option in options
            }
            
        return max(scores.items(), key=lambda x: x[1])[0] 