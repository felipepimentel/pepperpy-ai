"""Lazy loading utilities for PepperPy modules.

This module provides utilities for lazy loading of modules and classes,
which helps reduce startup time and memory usage by only importing
modules when they are actually needed.
"""

import importlib
import types
from typing import Any, Dict, List, Optional, Tuple, Union


class LazyLoader:
    """Lazy loader for modules and objects.

    This class implements a lazy loader that defers importing modules until
    they are actually accessed. This helps reduce startup time and memory
    usage, especially for large applications with many dependencies.

    Example:
        ```python
        # In __init__.py
        from pepperpy.core.lazy_loader import LazyLoader

        # Create lazy imports
        openai = LazyLoader("pepperpy.llm.providers.openai")
        anthropic = LazyLoader("pepperpy.llm.providers.anthropic")
        ```

        When `openai` is accessed for the first time, the module will be
        imported. Subsequent accesses will use the cached module.
    """

    def __init__(self, module_path: str):
        """Initialize the lazy loader.

        Args:
            module_path: The fully qualified path to the module to load.
        """
        self._module_path = module_path
        self._module: Optional[types.ModuleType] = None

    def __getattr__(self, name: str) -> Any:
        """Get an attribute from the module.

        This method is called when an attribute is accessed on the lazy loader.
        If the module hasn't been loaded yet, it will be loaded first.

        Args:
            name: The name of the attribute to get.

        Returns:
            The attribute from the module.

        Raises:
            AttributeError: If the attribute doesn't exist in the module.
        """
        if self._module is None:
            self._module = importlib.import_module(self._module_path)
        return getattr(self._module, name)

    def __dir__(self) -> List[str]:
        """Get the list of attributes in the module.

        This method is called when dir() is called on the lazy loader.
        If the module hasn't been loaded yet, it will be loaded first.

        Returns:
            The list of attributes in the module.
        """
        if self._module is None:
            self._module = importlib.import_module(self._module_path)
        return dir(self._module)


class LazyObject:
    """Lazy loader for specific objects from modules.

    This class implements a lazy loader that defers importing specific objects
    from modules until they are actually accessed. This is useful for importing
    specific classes or functions without loading the entire module.

    Example:
        ```python
        # In __init__.py
        from pepperpy.core.lazy_loader import LazyObject

        # Create lazy imports for specific objects
        OpenAIProvider = LazyObject("pepperpy.llm.providers.openai", "OpenAIProvider")
        AnthropicProvider = LazyObject("pepperpy.llm.providers.anthropic", "AnthropicProvider")
        ```

        When `OpenAIProvider` is accessed for the first time, the object will be
        imported from the module. Subsequent accesses will use the cached object.
    """

    def __init__(self, module_path: str, object_name: str):
        """Initialize the lazy object loader.

        Args:
            module_path: The fully qualified path to the module containing the object.
            object_name: The name of the object to load from the module.
        """
        self._module_path = module_path
        self._object_name = object_name
        self._object: Any = None

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call the object.

        This method is called when the lazy object is called as a function.
        If the object hasn't been loaded yet, it will be loaded first.

        Args:
            *args: Positional arguments to pass to the object.
            **kwargs: Keyword arguments to pass to the object.

        Returns:
            The result of calling the object.

        Raises:
            TypeError: If the loaded object is not callable.
        """
        if self._object is None:
            module = importlib.import_module(self._module_path)
            self._object = getattr(module, self._object_name)

        if not callable(self._object):
            raise TypeError(
                f"Object '{self._object_name}' from module '{self._module_path}' is not callable"
            )

        return self._object(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Get an attribute from the object.

        This method is called when an attribute is accessed on the lazy object.
        If the object hasn't been loaded yet, it will be loaded first.

        Args:
            name: The name of the attribute to get.

        Returns:
            The attribute from the object.

        Raises:
            AttributeError: If the attribute doesn't exist in the object.
        """
        if self._object is None:
            module = importlib.import_module(self._module_path)
            self._object = getattr(module, self._object_name)
        return getattr(self._object, name)


def lazy_import(
    module_path: str, objects: Optional[List[str]] = None
) -> Union[LazyLoader, Dict[str, LazyObject]]:
    """Import a module or specific objects lazily.

    This function provides a convenient way to import modules or specific
    objects lazily. If `objects` is None, the entire module will be imported
    lazily. If `objects` is a list of strings, only those objects will be
    imported lazily.

    Args:
        module_path: The fully qualified path to the module to import.
        objects: Optional list of object names to import from the module.

    Returns:
        If `objects` is None, a LazyLoader for the module.
        If `objects` is a list, a dictionary mapping object names to LazyObjects.

    Example:
        ```python
        # Import entire module lazily
        openai = lazy_import("pepperpy.llm.providers.openai")

        # Import specific objects lazily
        from_openai = lazy_import("pepperpy.llm.providers.openai", ["OpenAIProvider", "create"])
        OpenAIProvider = from_openai["OpenAIProvider"]
        create = from_openai["create"]
        ```
    """
    if objects is None:
        return LazyLoader(module_path)

    return {obj: LazyObject(module_path, obj) for obj in objects}


def setup_lazy_imports(
    namespace: Dict[str, Any], imports: Dict[str, Union[str, Tuple[str, str]]]
) -> None:
    """Set up lazy imports in a namespace.

    This function sets up lazy imports in a namespace, typically the globals()
    of a module. It takes a dictionary mapping names to module paths or
    (module_path, object_name) tuples and adds the lazy imports to the namespace.

    Args:
        namespace: The namespace to add the lazy imports to, typically globals().
        imports: A dictionary mapping names to module paths or (module_path, object_name) tuples.

    Example:
        ```python
        # In __init__.py
        from pepperpy.core.lazy_loader import setup_lazy_imports

        # Set up lazy imports
        setup_lazy_imports(globals(), {
            "openai": "pepperpy.llm.providers.openai",
            "anthropic": "pepperpy.llm.providers.anthropic",
            "OpenAIProvider": ("pepperpy.llm.providers.openai", "OpenAIProvider"),
            "AnthropicProvider": ("pepperpy.llm.providers.anthropic", "AnthropicProvider"),
        })
        ```
    """
    for name, import_spec in imports.items():
        if isinstance(import_spec, str):
            # Import entire module lazily
            namespace[name] = LazyLoader(import_spec)
        elif isinstance(import_spec, (list, tuple)) and len(import_spec) == 2:
            # Import specific object lazily
            module_path, object_name = import_spec
            namespace[name] = LazyObject(module_path, object_name)
        else:
            raise ValueError(
                f"Invalid import specification for {name}: {import_spec}. "
                "Expected a module path string or a (module_path, object_name) tuple."
            )
