# Agent Engineering Practices Prompt

This document outlines the best practices for AI agents interacting with this codebase. All agents should adhere to these guidelines to ensure code quality, consistency, and safety.

## 1. Understand First, Act Second

Before making any changes, thoroughly understand the context.

- **Analyze Existing Code:** Read and analyze relevant files to understand the existing code, conventions, and architectural patterns.
- **Use Project Conventions:** Rigorously adhere to the project's established conventions (naming, formatting, libraries, frameworks).
- **Clarify Ambiguity:** If the request is ambiguous or requires significant architectural changes, ask for clarification before proceeding.

## 2. Write High-Quality Code

All code modifications meet high standards.

- **Mimic Style:** Match the style, structure, and architectural patterns of the existing code in the project.
- **Add Tests:** All new features and bug fixes must be accompanied by corresponding unit or integration tests to ensure correctness and prevent regressions.
- **Comment Sparingly:** Only add comments to explain the *why* behind complex logic, not the *what*. Focus on writing self-documenting code.
- **No Hardcoded Secrets:** Never hardcode API keys, passwords, or other sensitive information. Use configuration files or environment variables.

## 3. Verify and Validate

Ensure all changes are safe and correct before finishing.

- **Run Tests:** Execute the project's test suite to ensure that your changes have not introduced any regressions.
- **Run Linters/Builds:** Run any static analysis, type checking, or build commands (e.g., `tsc`, `npm run lint`, `ruff check .`) to verify code quality and standards.
- **Explain Critical Commands:** Before executing any shell command that modifies the file system or system state, explain its purpose and potential impact.

## 4. Communicate Effectively

Interaction should be clear, concise, and professional.

- **Be Direct:** Get straight to the point.
- **Propose, Don't Assume:** For significant actions, propose a plan first.
