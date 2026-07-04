# AGENTS

# Project Agent Guide

## Project Information

- Project Name: {PROJECT_NAME}
- Description: {PROJECT_DESCRIPTION}
- Tech Stack: {TECH_STACK}
- Version: {PROJECT_VERSION}

---

## Operating Model

This project follows an Architect → Builder workflow.

- The Architect plans, organizes and reviews.
- The Builder implements the approved sprint.
- Project files are the single source of truth.
- Conversations are temporary. Documentation is permanent.

---

## Development Workflow

Project
→ Phase
→ Module
→ Sprint
→ Implementation
→ Review
→ Next Sprint

Only one sprint should be active at a time.

---

## Read Order

Before making changes read:

1. AGENTS.md
2. Current Phase
3. Current Module
4. Current Sprint handoff
5. Relevant documentation (only if required)

Do not read unrelated files.

---

## Builder Rules

- Implement only the active sprint.
- Do not expand scope.
- Do not invent business rules.
- Do not redesign architecture.
- Do not modify unrelated files.
- Stop and report blockers instead of guessing.

---

## Token Optimization

The Builder should focus on implementation only.

Skip unless explicitly requested:

- Unit Tests
- Integration Tests
- Documentation updates
- Validation reports
- Deployment steps
- Long explanations
- Full project scans

Manual testing and validation are performed by the user.

---

## Sprint Workflow

Each sprint contains:

- handoff.md

The handoff defines:

- Goal
- Scope
- Files to modify
- Constraints
- Acceptance criteria

---

## After Implementation

Return only:

- Files Created
- Files Modified
- Errors (if any)
- Manual Steps (if any)