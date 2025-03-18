#!/bin/bash
# Consolidate duplicate modules in the PepperPy framework
# As part of TASK-013 Phase 2

set -e

# Activate the virtual environment
source .venv/bin/activate

echo "Starting module consolidation process..."

# Capabilities consolidation
echo "Consolidating capabilities modules..."
python scripts/refactor.py --directory pepperpy --verbose consolidate-modules \
  --sources core/capabilities.py capabilities.py \
  --target core/capabilities.py \
  --backup

# Registry consolidation
echo "Consolidating registry modules..."
python scripts/refactor.py --directory pepperpy --verbose consolidate-modules \
  --sources core/registry.py registry.py llm/registry.py providers/registry.py \
  --target core/registry.py \
  --backup

# Dependency Injection consolidation
echo "Consolidating dependency injection modules..."
python scripts/refactor.py --directory pepperpy --verbose consolidate-modules \
  --sources core/dependency_injection.py di.py \
  --target core/di.py \
  --backup

# Config consolidation
echo "Consolidating config modules..."
python scripts/refactor.py --directory pepperpy --verbose consolidate-modules \
  --sources config.py core/config.py infra/config.py \
  --target config.py \
  --backup

# Providers consolidation
echo "Consolidating providers modules..."
python scripts/refactor.py --directory pepperpy --verbose consolidate-modules \
  --sources core/providers.py providers/base.py \
  --target core/providers.py \
  --backup

# Remove composition.py file (keeping only the directory)
if [ -f "pepperpy/core/composition.py" ]; then
  echo "Backing up and removing composition.py (keeping only the directory)..."
  cp pepperpy/core/composition.py pepperpy/core/composition.py.bak
  rm pepperpy/core/composition.py
fi

echo "Module consolidation complete!"
echo "Please run tests to verify that everything works correctly."
echo "Backup files with .bak extension have been created for all modified files." 