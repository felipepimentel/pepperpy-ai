"""Setup script for pepperpy package."""

from setuptools import find_packages, setup


# Read requirements from requirements.txt
def read_requirements(filename: str) -> list[str]:
    """Read requirements from a file.

    Args:
        filename: Path to requirements file

    Returns:
        List of requirements
    """
    with open(filename) as f:
        reqs = []
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                reqs.append(line)
        return reqs


# Read long description from README
def read_long_description() -> str:
    """Read long description from README file.

    Returns:
        README contents
    """
    with open("README.md", encoding="utf-8") as f:
        return f.read()


# Project metadata
NAME = "pepperpy"
VERSION = "0.1.0"
DESCRIPTION = "A Python framework for building AI-powered applications"
AUTHOR = "Your Name"
AUTHOR_EMAIL = "your.email@example.com"
URL = "https://github.com/yourusername/pepperpy"
LICENSE = "MIT"

# Setup configuration
setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    license=LICENSE,
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "pytest>=8.0.2",
        "pytest-asyncio>=0.23.5",
        "pytest-cov>=4.1.0",
        "pytest-mock>=3.12.0",
        "pytest-timeout>=2.2.0",
        "pytest-xdist>=3.5.0",
    ],
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    project_urls={
        "Documentation": "https://pepperpy.readthedocs.io/",
        "Source": URL,
        "Tracker": f"{URL}/issues",
    },
    entry_points={
        "console_scripts": [
            "pepperpy=pepperpy.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
