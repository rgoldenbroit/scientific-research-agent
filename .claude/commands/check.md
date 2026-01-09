---
allowed-tools: Bash(python3:*), Bash(cd:*)
description: Run syntax and import checks on modified Python files before committing
---

## Check Modified Files

Run these checks on recently modified Python files in the scientific-research-agent directory:

1. **Syntax check**: `python3 -m py_compile <file>`
2. **Import check**: `python3 -c "import sys; sys.path.insert(0, '.'); exec(open('<file>').read())"` (catch import errors)

Files to check: !`git diff --name-only HEAD | grep '\.py$' | head -10`

Report any errors found. This catches obvious bugs before deployment.
