"""Example demonstrating dependency management between plugins.

This example shows how to create plugins with dependencies, how to validate
dependencies, and how to resolve the load order based on dependencies.
"""

import asyncio

from pepperpy.plugins import (
    DependencyType,
    PepperpyPlugin,
    get_load_order,
)


# Example base plugin
class BaseUtilsPlugin(PepperpyPlugin):
    """Base utility plugin providing fundamental operations."""

    __metadata__ = {
        "name": "base_utils",
        "version": "1.0.0",
        "description": "Base utility functions",
        "author": "PepperPy Team",
        "provider_type": "utils",  # Provider type is required
    }

    def initialize(self) -> None:
        """Initialize plugin."""
        super().initialize()
        print(f"✅ Initialized {self.__metadata__['name']}")

    async def async_cleanup(self) -> None:
        """Clean up plugin."""
        await super().async_cleanup()
        print(f"🧹 Cleaned up {self.__metadata__['name']}")

    def add(self, a, b):
        """Add two numbers."""
        return a + b

    def multiply(self, a, b):
        """Multiply two numbers."""
        return a * b


# Plugin that requires the base utils plugin
class MathPlugin(PepperpyPlugin):
    """Advanced math operations plugin."""

    __metadata__ = {
        "name": "math_plugin",
        "version": "1.0.0",
        "description": "Advanced math operations",
        "author": "PepperPy Team",
        "provider_type": "math",  # Provider type is required
    }

    # Declare dependency on BaseUtilsPlugin
    __dependencies__ = {
        "base_utils": DependencyType.REQUIRED,
    }

    def __init__(self, config=None):
        """Initialize plugin."""
        super().__init__(config)
        self.base_utils = None

    def initialize(self) -> None:
        """Initialize plugin."""
        # Validate dependencies first
        if not self.validate_dependencies():
            print(f"⚠️ Warning: {self.__metadata__['name']} has unmet dependencies")

        # Set base utils plugin
        from pepperpy.plugins.registry import get_plugin

        self.base_utils = get_plugin("base_utils")
        if not self.base_utils:
            raise RuntimeError("Required plugin 'base_utils' not found")

        # Register some resources
        self.register_resource(
            resource_key="calculation_history",
            resource=[],
            resource_type="memory",
            metadata={"description": "History of calculations"},
        )

        super().initialize()
        print(f"✅ Initialized {self.__metadata__['name']}")

    async def async_cleanup(self) -> None:
        """Clean up plugin."""
        await super().async_cleanup()
        print(f"🧹 Cleaned up {self.__metadata__['name']}")

    def square(self, x):
        """Square a number using the base utils."""
        if not self.base_utils:
            raise RuntimeError("Base utils plugin not initialized")
        return self.base_utils.multiply(x, x)

    def cube(self, x):
        """Cube a number using the base utils."""
        if not self.base_utils:
            raise RuntimeError("Base utils plugin not initialized")
        return self.base_utils.multiply(self.base_utils.multiply(x, x), x)

    def add_calculation(self, op, value):
        """Add calculation to history."""
        history = self.get_resource("calculation_history")
        history.append({"op": op, "value": value})


# Plugin that enhances the math plugin
class AdvancedMathPlugin(PepperpyPlugin):
    """Very advanced math operations plugin."""

    __metadata__ = {
        "name": "advanced_math",
        "version": "1.0.0",
        "description": "Very advanced math operations",
        "author": "PepperPy Team",
        "provider_type": "math_advanced",  # Provider type is required
    }

    # This plugin requires math_plugin and is enhanced by base_utils
    __dependencies__ = {
        "math_plugin": DependencyType.REQUIRED,
        "base_utils": DependencyType.ENHANCES,
    }

    def __init__(self, config=None):
        """Initialize plugin."""
        super().__init__(config)
        self.math_plugin = None

    def initialize(self) -> None:
        """Initialize plugin."""
        # Validate dependencies
        if not self.validate_dependencies():
            print(f"⚠️ Warning: {self.__metadata__['name']} has unmet dependencies")

        # Get math plugin
        from pepperpy.plugins.registry import get_plugin

        self.math_plugin = get_plugin("math_plugin")
        if not self.math_plugin:
            raise RuntimeError("Required plugin 'math_plugin' not found")

        # Register a scoped resource
        with self.scoped_resource(
            resource_key="temp_calculations",
            resource={},
            resource_type="memory",
        ) as calculations:
            calculations["initialized_at"] = "now"

        super().initialize()
        print(f"✅ Initialized {self.__metadata__['name']}")

    async def async_cleanup(self) -> None:
        """Clean up plugin."""
        await super().async_cleanup()
        print(f"🧹 Cleaned up {self.__metadata__['name']}")

    def factorial(self, n):
        """Calculate factorial using lower-level plugins."""
        if not self.math_plugin or not hasattr(self.math_plugin, "base_utils"):
            raise RuntimeError("Math plugin or base_utils not initialized")

        result = 1
        for i in range(2, n + 1):
            result = self.math_plugin.base_utils.multiply(result, i)

        # Record calculation
        if not self.math_plugin:
            raise RuntimeError("Math plugin not initialized")
        self.math_plugin.add_calculation("factorial", n)
        return result


# Plugin that has a conflict with another plugin
class LegacyMathPlugin(PepperpyPlugin):
    """Legacy math operations that conflict with the new math plugin."""

    __metadata__ = {
        "name": "legacy_math",
        "version": "0.5.0",
        "description": "Legacy math operations",
        "author": "PepperPy Team",
        "provider_type": "math_legacy",  # Provider type is required
    }

    # This plugin conflicts with the math_plugin
    __dependencies__ = {
        "math_plugin": DependencyType.CONFLICTS,
    }

    def initialize(self) -> None:
        """Initialize plugin."""
        if not self.validate_dependencies():
            print(f"⚠️ Warning: {self.__metadata__['name']} has conflicts")

        super().initialize()
        print(f"✅ Initialized {self.__metadata__['name']}")


async def main():
    """Run the example."""
    print("🚀 Starting plugin dependencies example")

    # Register plugins to the dependency system
    from pepperpy.plugins.dependencies import add_plugin

    add_plugin("base_utils")
    add_plugin("math_plugin")
    add_plugin("advanced_math")
    add_plugin("legacy_math")

    # Register dependencies
    from pepperpy.plugins.dependencies import add_dependency

    # MathPlugin depends on BaseUtilsPlugin
    add_dependency("math_plugin", "base_utils", DependencyType.REQUIRED)

    # AdvancedMathPlugin depends on MathPlugin and is enhanced by BaseUtilsPlugin
    add_dependency("advanced_math", "math_plugin", DependencyType.REQUIRED)
    add_dependency("advanced_math", "base_utils", DependencyType.ENHANCES)

    # LegacyMathPlugin conflicts with MathPlugin
    add_dependency("legacy_math", "math_plugin", DependencyType.CONFLICTS)

    # Resolve dependency order
    try:
        load_order = get_load_order(["advanced_math", "base_utils", "math_plugin"])
        print(f"✨ Load order: {load_order}")
    except Exception as e:
        print(f"❌ Error resolving dependencies: {e}")

    # Check for missing dependencies
    from pepperpy.plugins.dependencies import check_missing_dependencies

    missing = check_missing_dependencies("advanced_math")
    if missing:
        print(f"⚠️ Missing dependencies for advanced_math: {missing}")
    else:
        print("✅ No missing dependencies for advanced_math")

    # Check for conflicts
    from pepperpy.plugins.dependencies import check_conflicts

    conflicts = check_conflicts("legacy_math")
    if conflicts:
        print(f"⚠️ Conflicts for legacy_math: {conflicts}")
    else:
        print("✅ No conflicts for legacy_math")

    # Initialize plugins in correct order
    base_utils = BaseUtilsPlugin()
    math_plugin = MathPlugin()
    advanced_math = AdvancedMathPlugin()

    # Create registry with the plugins
    from pepperpy.plugins.registry import register_plugin as reg_plugin

    reg_plugin("base_utils", BaseUtilsPlugin)
    reg_plugin("math_plugin", MathPlugin)
    reg_plugin("advanced_math", AdvancedMathPlugin)

    # Mark as loaded in dependency system
    from pepperpy.plugins.dependencies import mark_loaded

    mark_loaded("base_utils")
    mark_loaded("math_plugin")
    mark_loaded("advanced_math")

    # Initialize plugins
    base_utils.initialize()
    math_plugin.initialize()
    advanced_math.initialize()

    # Use the plugins
    print("\n📊 Running calculations:")
    square_result = math_plugin.square(5)
    cube_result = math_plugin.cube(3)
    factorial_result = advanced_math.factorial(5)

    print(f"Square of 5: {square_result}")
    print(f"Cube of 3: {cube_result}")
    print(f"Factorial of 5: {factorial_result}")

    # Get resource and show calculation history
    history = math_plugin.get_resource("calculation_history")
    print(f"\n📜 Calculation history: {history}")

    # Clean up all plugins
    print("\n🧹 Cleaning up...")
    await advanced_math.async_cleanup()
    await math_plugin.async_cleanup()
    await base_utils.async_cleanup()

    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
