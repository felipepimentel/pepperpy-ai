---
title: Git Synchronization
version: "1.0"
scope: "Pepperpy Project"
description: |
  A guide for synchronizing local and remote repositories.
  Use this prompt when:
  - Updating local repository
  - Pushing local changes
  - Resolving conflicts
  - Managing branches
  - Preparing for deployment
  
  The prompt helps maintain a clean and synchronized
  codebase across all environments.
---

Synchronize local and remote repositories:

1. Preparation:
   - Check current branch:
     ```bash
     git status
     ```
   - Review uncommitted changes
   - Stash if needed:
     ```bash
     git stash save "Temporary stash before sync"
     ```

2. Update Local Repository:
   - Fetch remote changes:
     ```bash
     git fetch origin
     ```
   - Pull with rebase:
     ```bash
     git pull --rebase origin main
     ```
   - Resolve any conflicts

3. Push Local Changes:
   - Review outgoing changes:
     ```bash
     git status
     ```
   - Push to remote:
     ```bash
     git push origin main
     ```

4. Post-Sync Tasks:
   - Apply stashed changes if any:
     ```bash
     git stash pop
     ```
   - Verify synchronization:
     ```bash
     git status
     ```
   - Update `.product/kanban.md` with:
     - Branch name
     - Changes summary
     - Conflict resolutions
     - Timestamp 