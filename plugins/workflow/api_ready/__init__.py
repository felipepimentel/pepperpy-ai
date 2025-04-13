"""API Ready workflow plugin package.

This package provides a workflow for evaluating APIs for production readiness,
checking them against industry best practices across multiple categories:
- Security
- Performance 
- Reliability
- Documentation
- Standards compliance
- Observability

The workflow can also enhance existing APIs by adding agent-ready features
like discovery endpoints, authentication, and observability.
"""

from .provider import APIReadyProvider, ReadinessLevel, ReadinessCategory, ReadinessFinding, APIReadinessReport

__all__ = [
    "APIReadyProvider",
    "ReadinessLevel",
    "ReadinessCategory", 
    "ReadinessFinding",
    "APIReadinessReport"
] 