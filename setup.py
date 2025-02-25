"""Setup configuration for the pepperpy package."""

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
DESCRIPTION = "A modern Python framework for building AI-powered applications"
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
    install_requires=read_requirements("requirements.txt"),
    extras_require={
        "dev": [
            "black>=23.3.0",
            "isort>=5.12.0",
            "mypy>=1.3.0",
            "pylint>=2.17.3",
            "flake8>=6.0.0",
            "pytest>=7.3.1",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.10.0",
        ],
        "docs": [
            "sphinx>=6.2.1",
            "sphinx-rtd-theme>=1.2.0",
            "sphinx-autodoc-typehints>=1.23.0",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Typing :: Typed",
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
