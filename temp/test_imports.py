import os
import sys

# Add the temp directory to the path
sys.path.insert(0, os.path.abspath("."))

# Try importing all modules
modules = [
    "types",
    "errors",
    "utils",
    "config",
    "cli",
    "registry",
    "interfaces",
    "memory",
    "cache",
    "storage",
    "workflows",
    "events",
    "plugins",
    "streaming",
    "http",
    "llm",
    "rag",
    "data",
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
