import os
import sys

# Add the pepperpy directory to the path
sys.path.insert(0, os.path.abspath("."))

# Try importing all modules
modules = [
    "pepperpy.types",
    "pepperpy.errors",
    "pepperpy.utils",
    "pepperpy.config",
    "pepperpy.cli",
    "pepperpy.registry",
    "pepperpy.interfaces",
    "pepperpy.memory",
    "pepperpy.cache",
    "pepperpy.storage",
    "pepperpy.workflows",
    "pepperpy.events",
    "pepperpy.plugins",
    "pepperpy.streaming",
    "pepperpy.http",
    "pepperpy.llm",
    # "pepperpy.rag",  # Skip RAG module as it requires external dependencies
    "pepperpy.data",
]

success = True
for module in modules:
    try:
        __import__(module)
        print(f"✅ Successfully imported {module}")
    except Exception as e:
        success = False
        print(f"❌ Failed to import {module}: {str(e)}")

if success:
    print("\n🎉 All modules imported successfully!")
else:
    print("\n⚠️ Some modules failed to import. See errors above.")
