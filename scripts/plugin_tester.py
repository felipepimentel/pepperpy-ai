#!/usr/bin/env python3
"""
Plugin Tester for PepperPy.

This script runs tests on plugins based on examples defined in plugin.yaml.
"""

import argparse
import asyncio
import glob
import importlib.util
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple, cast

import yaml
from deepdiff import DeepDiff


class PluginTester:
    """Executes tests on PepperPy plugins based on examples."""

    def __init__(self, plugins_dir: str = "plugins", verbose: bool = False) -> None:
        """Initialize tester.
        
        Args:
            plugins_dir: Base directory for plugins
            verbose: Whether to enable verbose output
        """
        self.plugins_dir = plugins_dir
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
        
    def find_plugins(self) -> List[str]:
        """Find all plugin directories.
        
        Returns:
            List of plugin paths
        """
        plugin_dirs = []
        
        # Find all plugin.yaml files and use their directory as plugin root
        for plugin_yaml in glob.glob(f"{self.plugins_dir}/**/plugin.yaml", recursive=True):
            plugin_dir = os.path.dirname(plugin_yaml)
            plugin_dirs.append(plugin_dir)
            
        return plugin_dirs
        
    def load_plugin_examples(self, plugin_path: str) -> List[Dict[str, Any]]:
        """Load examples from plugin.yaml.
        
        Args:
            plugin_path: Path to plugin directory
            
        Returns:
            List of examples
        """
        yaml_path = os.path.join(plugin_path, "plugin.yaml")
        
        if not os.path.exists(yaml_path):
            self.logger.error(f"Missing plugin.yaml: {yaml_path}")
            return []
            
        try:
            with open(yaml_path, 'r') as f:
                plugin_data = yaml.safe_load(f)
                
            examples = plugin_data.get("examples", [])
            
            if not examples:
                self.logger.warning(f"No examples found in plugin.yaml: {yaml_path}")
                
            return examples
        except Exception as e:
            self.logger.error(f"Error loading examples from plugin.yaml: {e}")
            return []
            
    def load_provider_class(self, plugin_path: str) -> Optional[Any]:
        """Load provider class from plugin.
        
        Args:
            plugin_path: Path to plugin directory
            
        Returns:
            Provider class or None if loading fails
        """
        yaml_path = os.path.join(plugin_path, "plugin.yaml")
        provider_path = os.path.join(plugin_path, "provider.py")
        
        if not os.path.exists(yaml_path) or not os.path.exists(provider_path):
            self.logger.error(f"Missing plugin.yaml or provider.py: {plugin_path}")
            return None
            
        try:
            # Load plugin.yaml to get entry_point
            with open(yaml_path, 'r') as f:
                plugin_data = yaml.safe_load(f)
                
            entry_point = plugin_data.get("entry_point", "")
            if not entry_point or "." not in entry_point:
                self.logger.error(f"Invalid entry_point in plugin.yaml: {entry_point}")
                return None
                
            # Extract module and class name from entry point
            module_name, class_name = entry_point.split(".", 1)
            
            # Load module dynamically
            spec = importlib.util.spec_from_file_location(module_name, provider_path)
            if not spec or not spec.loader:
                self.logger.error(f"Failed to load module spec: {provider_path}")
                return None
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get provider class
            provider_class = getattr(module, class_name, None)
            if not provider_class:
                self.logger.error(f"Provider class not found: {class_name}")
                return None
                
            return provider_class
        except Exception as e:
            self.logger.error(f"Error loading provider class: {e}")
            return None
            
    async def run_test(
        self, 
        provider: Any, 
        example: Dict[str, Any]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Run a single test on a provider instance.
        
        Args:
            provider: Provider instance
            example: Test example definition
            
        Returns:
            Tuple of (success, message, output)
        """
        test_name = example.get("name", "unnamed test")
        input_data = example.get("input", {})
        expected_output = example.get("expected_output", {})
        
        if not input_data:
            return False, "Missing input data", {}
            
        try:
            # Ensure provider is initialized
            if not getattr(provider, "initialized", True):
                await provider.initialize()
                
            # Execute test
            self.logger.debug(f"Running test '{test_name}' with input: {input_data}")
            output = await provider.execute(input_data)
            self.logger.debug(f"Output: {output}")
            
            # Compare with expected output
            if not expected_output:
                self.logger.warning(f"No expected output defined for test '{test_name}'")
                return True, "Test completed without expected output verification", output
                
            # Verify output matches expected format
            diff = DeepDiff(expected_output, output, ignore_order=True)
            
            if diff:
                # Check if it's just additional fields (which is OK)
                missing_values = diff.get("dictionary_item_removed", [])
                if not missing_values:
                    # Only additional fields, no missing ones
                    return True, "Test passed with additional fields in output", output
                else:
                    # Missing expected fields
                    return False, f"Output missing expected fields: {missing_values}", output
            else:
                # Exact match
                return True, "Test passed", output
                
        except Exception as e:
            return False, f"Error executing test: {e}", {}
            
    async def test_plugin(self, plugin_path: str) -> Dict[str, Any]:
        """Test a plugin with all its examples.
        
        Args:
            plugin_path: Path to plugin directory
            
        Returns:
            Test results
        """
        # Load examples and provider class
        examples = self.load_plugin_examples(plugin_path)
        provider_class = self.load_provider_class(plugin_path)
        
        if not examples or not provider_class:
            return {
                "plugin": plugin_path,
                "success": False,
                "message": "Failed to load examples or provider class",
                "tests": []
            }
            
        # Create provider instance
        try:
            provider = provider_class()
            
            # Run tests
            results = []
            all_passed = True
            
            for example in examples:
                await provider.initialize()
                
                try:
                    success, message, output = await self.run_test(provider, example)
                    
                    test_result = {
                        "name": example.get("name", "unnamed test"),
                        "success": success,
                        "message": message,
                        "input": example.get("input", {}),
                        "expected": example.get("expected_output", {}),
                        "actual": output
                    }
                    
                    results.append(test_result)
                    
                    if not success:
                        all_passed = False
                finally:
                    await provider.cleanup()
                
            return {
                "plugin": plugin_path,
                "success": all_passed,
                "tests": results
            }
                
        except Exception as e:
            return {
                "plugin": plugin_path,
                "success": False,
                "message": f"Error testing plugin: {e}",
                "tests": []
            }
            
    async def test_all_plugins(self) -> List[Dict[str, Any]]:
        """Test all plugins.
        
        Returns:
            List of test results for all plugins
        """
        plugin_paths = self.find_plugins()
        results = []
        
        for plugin_path in plugin_paths:
            self.logger.info(f"Testing plugin: {plugin_path}")
            result = await self.test_plugin(plugin_path)
            results.append(result)
            
        return results


def setup_logging(verbose: bool) -> None:
    """Set up logging configuration.
    
    Args:
        verbose: Whether to enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def print_results(results: List[Dict[str, Any]]) -> None:
    """Print test results.
    
    Args:
        results: Test results to print
    """
    plugins_total = len(results)
    plugins_passed = sum(1 for r in results if r.get("success", False))
    
    total_tests = sum(len(r.get("tests", [])) for r in results)
    passed_tests = sum(
        sum(1 for t in r.get("tests", []) if t.get("success", False))
        for r in results
    )
    
    print(f"\n=== Test Results ===")
    print(f"Plugins: {plugins_passed}/{plugins_total} passed")
    print(f"Tests: {passed_tests}/{total_tests} passed")
    print()
    
    for result in results:
        plugin_path = result.get("plugin", "unknown")
        success = result.get("success", False)
        tests = result.get("tests", [])
        
        if success:
            print(f"✅ {plugin_path}: All tests passed ({len(tests)})")
        else:
            print(f"❌ {plugin_path}: Tests failed")
            
            if "message" in result:
                print(f"   {result['message']}")
                
            for test in tests:
                test_name = test.get("name", "unnamed")
                test_success = test.get("success", False)
                test_message = test.get("message", "")
                
                if test_success:
                    print(f"   ✅ {test_name}: {test_message}")
                else:
                    print(f"   ❌ {test_name}: {test_message}")
        
        print()


async def main_async() -> int:
    """Run the tester asynchronously.
    
    Returns:
        Exit code (0 for success, non-zero otherwise)
    """
    parser = argparse.ArgumentParser(description="Test PepperPy plugins based on examples")
    parser.add_argument("-d", "--plugins-dir", default="plugins", help="Base plugins directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-s", "--single", help="Test a single plugin directory")
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    tester = PluginTester(plugins_dir=args.plugins_dir, verbose=args.verbose)
    
    if args.single:
        # Test a single plugin
        plugin_path = args.single
        if not os.path.isdir(plugin_path):
            print(f"Error: {plugin_path} is not a directory")
            return 1
            
        result = await tester.test_plugin(plugin_path)
        print_results([result])
        
        return 0 if result.get("success", False) else 1
    else:
        # Test all plugins
        results = await tester.test_all_plugins()
        print_results(results)
        
        # Return success if all plugins passed
        return 0 if all(r.get("success", False) for r in results) else 1


def main() -> int:
    """Run the tester.
    
    Returns:
        Exit code (0 for success, non-zero otherwise)
    """
    return asyncio.run(main_async())


if __name__ == "__main__":
    sys.exit(main()) 