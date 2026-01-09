---
allowed-tools: Bash(git:*)
description: Stage changes and create a commit with Co-Authored-By trailer
---

## Current State

- Branch: !`git branch --show-current`
- Status: !`git status --short`
- Recent commits: !`git log --oneline -3`

## Instructions

1. Review the changes shown above
2. Stage only the relevant modified files (skip untracked screenshots/html unless requested)
3. Create a commit message following this project's style:
   - Imperative tense ("Add", "Fix", "Update")
   - Brief summary line
   - Optional body with details
   - Always end with: `Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>`
4. Push to origin

Use a HEREDOC for the commit message to preserve formatting.
