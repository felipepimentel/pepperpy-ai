pepperpy
├── agents # Handles the creation and management of agents, including their configurations, types, and lifecycle services.
│   ├── __init__.py
│   ├── agent.py
│   ├── types.py
│   ├── config.py
│   ├── builder.py
│   └── service.py
├── lifecycle # Manages the lifecycle of agents, including initialization, state management, and termination processes.
│   ├── __init__.py
│   ├── initializer.py
│   ├── state_manager.py
│   └── terminator.py
├── context # Handles contextual data for agents, including state management, history tracking, and hierarchical state dependencies.
│   ├── __init__.py
│   ├── manager.py
│   ├── history.py
│   ├── state.py
│   └── complex_state_manager.py
├── profile # Encapsulates agent profiles, goals, and preferences, supporting dynamic behavior and custom configurations.
│   ├── __init__.py
│   ├── goals # Manages the definition and tracking of agent goals, including instructions and objectives.
│   │   ├── __init__.py
│   │   ├── goal_manager.py
│   │   ├── objective_tracker.py
│   │   └── instruction_processor.py
│   ├── profile_manager.py
│   └── preferences.py
├── memory # Provides short-term and long-term memory capabilities, including vectorized operations and memory management.
│   ├── __init__.py
│   ├── short_term # Handles transient memory storage for short-lived agent contexts and sessions.
│   │   ├── __init__.py
│   │   ├── context.py
│   │   └── session.py
│   ├── long_term # Manages persistent memory storage and retrieval for agents.
│   │   ├── __init__.py
│   │   ├── storage.py
│   │   └── retriever.py
│   ├── memory_manager.py
│   └── vector_support.py
├── decision # Implements decision-making engines and criteria for agent actions and behaviors.
│   ├── __init__.py
│   ├── engine # Core decision logic and policy implementations.
│   │   ├── __init__.py
│   │   ├── core.py
│   │   └── policy.py
│   ├── criteria # Evaluation criteria and rules for decision-making processes.
│       ├── __init__.py
│       ├── evaluator.py
│       └── rules.py
├── data # Manages data ingestion, transformation, storage, and indexing for agents.
│   ├── __init__.py
│   ├── vector # Handles vector embeddings and indexing for efficient data retrieval.
│   │   ├── __init__.py
│   │   ├── embeddings.py
│   │   └── indexer.py
│   ├── processing # Handles data transformation and validation processes.
│   │   ├── __init__.py
│   │   ├── transformer.py
│   │   └── validator.py
│   ├── dynamic_sources # Loads and processes dynamic data sources and algorithms for agent ingestion.
│       ├── __init__.py
│       ├── algorithms # Contains various ingestion algorithms and a base class for extensibility.
│       │   ├── __init__.py
│       │   ├── algorithm_a.py
│       │   ├── algorithm_b.py
│       │   └── base_algorithm.py
│       ├── ingest.py
│       ├── update.py
│       └── vector_linker.py
├── events # Handles event-driven communication, including dispatchers, handlers, and event type definitions.
│   ├── __init__.py
│   ├── dispatcher.py
│   ├── handler.py
│   └── types.py
├── orchestrator # Coordinates workflows and strategies for agent behavior and execution.
│   ├── __init__.py
│   ├── strategy # Implements strategies for orchestrating agent actions and workflows.
│   │   ├── __init__.py
│   │   ├── selector.py
│   │   ├── executor.py
│   │   └── evaluator.py
│   ├── pipeline # Manages execution pipelines, including their construction, validation, and execution.
│       ├── __init__.py
│       ├── builder.py
│       ├── executor.py
│       └── validator.py
├── reasoning # Implements reasoning frameworks (e.g., ReAct, CoT, ToT) and evaluation metrics for logical processes.
│   ├── __init__.py
│   ├── frameworks # Contains different reasoning frameworks and their implementations.
│   │   ├── __init__.py
│   │   ├── react # Reasoning framework for reactive agents.
│   │   │   ├── __init__.py
│   │   │   ├── thought.py
│   │   │   ├── action.py
│   │   │   └── observation.py
│   │   ├── cot # Chain-of-thought framework implementation.
│   │   │   ├── __init__.py
│   │   │   └── processor.py
│   │   └── tot # Tree-of-thought framework implementation.
│       │   ├── __init__.py
│       │   └── processor.py
│   ├── evaluation # Provides reasoning evaluation metrics and analysis tools.
│       ├── __init__.py
│       ├── metrics.py
│       └── analyzer.py
├── tools # Provides utilities for extensions, external functions, and data integration.
│   ├── __init__.py
│   ├── extensions # Manages API extensions and discovery utilities.
│   │   ├── __init__.py
│   │   ├── registry.py
│   │   └── discovery.py
│   ├── functions # Executes external functions and clients for extended operations.
│   │   ├── __init__.py
│   │   ├── function.py
│   │   └── client_executor.py
│   ├── datastore # Provides connectors and interfaces for external data stores.
│       ├── __init__.py
│       ├── datastore.py
│       └── connector.py
├── learning # Supports learning strategies, RAG workflows, and fine-tuning operations.
│   ├── __init__.py
│   ├── strategies # Implements various learning strategies, such as retrieval-based and in-context learning.
│   │   ├── __init__.py
│   │   ├── in_context.py
│   │   ├── retrieval_based.py
│   │   └── fine_tuning.py
│   ├── examples # Manages few-shot learning examples and storage.
│   │   ├── __init__.py
│   │   ├── store.py
│   │   └── manager.py
│   ├── rag_workflows # Implements workflows for retrieval-augmented generation.
│       ├── __init__.py
│       ├── pipeline.py
│       ├── retriever.py
│       └── evaluator.py
├── monitoring # Tracks agent performance and logs decision-making processes for analysis and auditing.
│   ├── __init__.py
│   ├── performance_metrics # Collects, aggregates, and reports performance metrics.
│   │   ├── __init__.py
│   │   ├── collector.py
│   │   ├── aggregator.py
│   │   └── reporter.py
│   ├── decision_audit # Logs and visualizes decision-making processes for auditing.
│       ├── __init__.py
│       ├── logger.py
│       ├── tracer.py
│       └── visualizer.py
├── runtime # Manages the execution environment and runtime state for the system.
│   ├── __init__.py
│   ├── environment.py
│   ├── executor.py
│   └── state_manager.py
├── security # Provides security features like validation, sanitization, and rate limiting.
│   ├── __init__.py
│   ├── validator.py
│   ├── sanitizer.py
│   └── rate_limiter.py
└── common # Contains shared utilities, error handling, and logging functionalities.
    ├── __init__.py
    ├── logger.py
    ├── errors.py
    └── utils.py
