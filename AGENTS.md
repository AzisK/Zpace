# Zpace

A tool to discover what's hogging your disk space.

App documentation in this document is only for the CLI. Only the Project Structure section explains how this monorepo organizes other builds (MacOS and Windows).

# Project Structure

This is a **monorepo** with multiple apps sharing a common core:

```
zpace/
├── zpace/              # Python CLI (current)
├── apps/
│   ├── macos/          # SwiftUI macOS app
│   └── windows/        # WinUI 3 / .NET 10 Windows app
└── core/               # (future) Rust core library
```

## App-Specific Context

When working on a specific app, focus on that app's directory and conventions:

| App | Language | Build Command | Notes |
|-----|----------|---------------|-------|
| CLI | Python | `uv run zpace` | Main app, TDD required |
| macOS | Swift/SwiftUI | `cd apps/macos && swift run` | Requires Xcode for full .app bundle |
| Windows | C#/.NET 10 | `dotnet build` | Requires VS 2026 + Windows |

## macOS App Notes

- Uses Xcode project (Zpace.xcodeproj) for proper .app bundle
- Open in Xcode: `open apps/macos/Zpace.xcodeproj`
- Build and run with Cmd+R in Xcode

## Windows App Notes

- Uses WinUI 3 with Windows App SDK 1.8
- Requires Windows + Visual Studio 2026 to build
- See `apps/windows/README.md` for setup

## Future Architecture

Long-term plan: Rust core library with FFI bindings to each frontend:
- Swift calls Rust via C FFI for macOS
- C# calls Rust via P/Invoke for Windows
- Python calls Rust via PyO3 for CLI

# Core Philosophy

TEST-DRIVEN DEVELOPMENT IS NON-NEGOTIABLE. Every single line of production code must be written in response to a failing test. No exceptions.

I follow Test-Driven Development (TDD) with a strong emphasis on behavior-driven testing and functional programming principles. All work should be done in small, incremental changes that maintain a working state throughout development.

# Architecture
See [ARCHITECTURE.md](ARCHITECTURE.md) for codebase structure.

# Commands

```bash
uv sync                      # Install dependencies
uv run zpace                 # Run the app locally
uv run pytest -v             # Run tests
uv run ruff check .          # Lint
uv run ruff format --check . # Check formatting
uv run mypy .                # Type check

# Run all checks
uv run pytest -v && uv run ruff check . && uv run ruff format --check . && uv run mypy .
```

# Conventions

- Python 3.8+ (tested through 3.14 and PyPy)
- Uses `uv` for package management
- Tests: `test_unit.py`, `test_integration.py`
- Error handling: Use explicit exceptions with meaningful messages; avoid bare `except` clauses

# Understand First, Plan and Act at the End

Before making any changes, thoroughly understand the context and plan it. Act at the very end only.

- Analyze Existing Code: Read and analyze relevant files to understand the existing code, conventions, and architectural patterns.
- Use Project Conventions: Rigorously adhere to the project's established conventions (naming, formatting, libraries, frameworks).
- Clarify Ambiguity: If the request is ambiguous or requires significant architectural changes, ask for clarification before proceeding.
- Plan First: Plan the file approach, architecture, file structure and code pattern before making any code changes

# Write High-Quality Code

All code modifications meet high standards.

- Mimic Style: Match the style, structure, and architectural patterns of the existing code in the project.
- Comment Sparingly: Only add comments to explain the *why* behind complex logic, not the *what*. Focus on writing self-documenting code.

# Working with AI Agents

**Core principle**: Think deeply, follow TDD strictly, capture learnings while context is fresh.

**Quick reference:**
- ALWAYS FOLLOW TDD - no production code without failing test
- Assess refactoring after every green (but only if adds value)
- Update AGENTS.md when introducing meaningful changes
- Ask "What do I wish I'd known at the start?" after significant changes
- Document gotchas, patterns, decisions, edge cases while context is fresh
