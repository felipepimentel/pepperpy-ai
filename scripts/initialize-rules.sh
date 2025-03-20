#!/bin/bash
#
# PepperPy Rules Initialization Script
#
# This script:
# 1. Backs up existing rules
# 2. Moves the new rules into place
# 3. Sets up the auto-generated directory
# 4. Runs the initial rule scan

set -e

# Configuration
RULES_DIR=".cursor/rules"
NEW_RULES_DIR=".cursor/rules/new"
BACKUP_DIR=".cursor/rules/backup-$(date +%Y%m%d-%H%M%S)"
AUTO_GENERATED_DIR=".cursor/rules/auto-generated"

# Functions
log() {
  echo "[$(date +%H:%M:%S)] $1"
}

# Check if new rules directory exists
if [ ! -d "$NEW_RULES_DIR" ]; then
  log "Error: New rules directory not found: $NEW_RULES_DIR"
  exit 1
fi

# Create backup directory
log "Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Backup existing rules
if [ -d "$RULES_DIR" ] && [ "$(ls -A $RULES_DIR)" ]; then
  log "Backing up existing rules to $BACKUP_DIR"
  for file in "$RULES_DIR"/*.mdc; do
    if [ -f "$file" ]; then
      log "  Backing up: $(basename "$file")"
      cp "$file" "$BACKUP_DIR/"
    fi
  done
fi

# Remove existing rules (but not the new rules directory)
log "Removing existing rules"
find "$RULES_DIR" -maxdepth 1 -name "*.mdc" -type f -delete

# Move new rules into place
log "Moving new rules into place"
for file in "$NEW_RULES_DIR"/*.mdc; do
  if [ -f "$file" ]; then
    log "  Moving: $(basename "$file")"
    cp "$file" "$RULES_DIR/"
  fi
done

# Create auto-generated directory
log "Setting up auto-generated directory"
mkdir -p "$AUTO_GENERATED_DIR"

# Run initial rule scan
log "Running initial rule scan"
python scripts/rules-updater.py scan

log "Rules initialization complete!"
log "New rules are now in place: $RULES_DIR"
log "Old rules are backed up in: $BACKUP_DIR"
log "Auto-generated rules are in: $AUTO_GENERATED_DIR" 