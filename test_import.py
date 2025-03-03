#!/usr/bin/env python
try:
    import feedparser
    print("feedparser imported successfully")
except ImportError as e:
    print(f"Error importing feedparser: {e}")
