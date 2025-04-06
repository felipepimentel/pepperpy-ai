#!/usr/bin/env python3
"""
Repository Analyzer Plugin Setup.

This script handles installation of the repository analyzer plugin
and its dependencies. It can be used for standalone installation
outside of the main PepperPy framework.
"""

from setuptools import find_namespace_packages, setup

# Read requirements
with open("requirements.txt") as f:
    requirements = [
        line.strip() for line in f if line.strip() and not line.startswith("#")
    ]

# Extract extras from requirements
extras_require = {
    "git": [],
    "reporting": [],
    "code_analysis": [],
    "code_quality": [],
    "all": [],
}

base_requirements = []

for req in requirements:
    if ";" in req:  # This is an extra
        pkg, condition = req.split(";", 1)
        pkg = pkg.strip()
        if "extra ==" in condition:
            extra_name = condition.split("==")[1].strip().strip('"').strip("'")
            extras_require[extra_name].append(pkg)
            extras_require["all"].append(pkg)
        else:
            base_requirements.append(req)
    else:
        base_requirements.append(req)

setup(
    name="pepperpy-repository-analyzer",
    version="0.3.0",
    description="Repository analysis plugin for PepperPy",
    author="PepperPy Team",
    author_email="info@pepperpy.io",
    packages=find_namespace_packages(include=["plugins.workflow.repository_analyzer*"]),
    python_requires=">=3.9",
    install_requires=base_requirements,
    extras_require=extras_require,
    entry_points={
        "pepperpy.plugins": [
            "workflow.repository_analyzer = plugins.workflow.repository_analyzer.simplified_adapter:SimpleRepositoryAnalyzerAdapter",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
