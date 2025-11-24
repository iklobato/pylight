<!--
Sync Impact Report:
Version change: 0.0.0 → 1.0.0
Modified principles: All principles replaced with new clean-code and architecture standards
Added sections: Clean Code Principles, Architecture Standards, Naming Conventions, Error Handling, Testing Standards, Documentation Standards, Code Organization, Commit Conventions
Removed sections: Template placeholder sections
Templates requiring updates:
  ✅ plan-template.md - Constitution Check section will reference new principles
  ✅ spec-template.md - No direct constitution references, but aligns with testing standards
  ✅ tasks-template.md - No direct constitution references, but aligns with testing standards
Follow-up TODOs: None
-->

# Pylight Constitution

## Core Principles

### I. Clean Code (NON-NEGOTIABLE)

Code MUST prioritize clarity over cleverness. Solutions MUST be as simple as possible while meeting requirements. Functions MUST be small, deterministic, typed, and single-responsibility. Explicit naming is mandatory—avoid abbreviations and unclear variable names. Duplication MUST be eliminated through appropriate abstraction. Dead abstractions (unused interfaces, wrappers, or layers) MUST be removed. Code MUST be readable by developers of varying experience levels without extensive documentation.

**Rationale**: Maintainable code reduces technical debt, accelerates development, and minimizes bugs. Simple solutions are easier to test, debug, and extend.

### II. SOLID Principles (Pragmatic Application)

Apply SOLID principles ONLY when they reduce complexity. Do NOT introduce extra layers, wrappers, or indirection unless they provide real value. Single Responsibility Principle: Each class/function has one reason to change. Open/Closed Principle: Open for extension, closed for modification—but only when extension is likely. Liskov Substitution: Subtypes must be substitutable—prefer composition over inheritance. Interface Segregation: Clients should not depend on interfaces they don't use. Dependency Inversion: High-level modules should not depend on low-level modules—use dependency injection ONLY where it meaningfully improves testability and decoupling.

**Rationale**: SOLID principles prevent architectural rot, but over-application creates unnecessary complexity. Balance is key.

### III. Layered Architecture (Minimal Essential Layers)

Structure projects with minimal but essential layers: domain, application, infrastructure, presentation. The domain layer MUST never depend on infrastructure. Domain contains business logic and entities. Application contains use cases and orchestration. Infrastructure contains external adapters (databases, APIs, file systems). Presentation contains UI/API controllers. Additional layers (e.g., shared utilities) are permitted only when truly required. Do NOT introduce extra modules, wrappers, or indirection unless they provide real value.

**Rationale**: Clear separation of concerns enables testability, maintainability, and independent evolution of layers. Minimal layers reduce cognitive load and unnecessary abstractions.

### IV. Naming Conventions (MANDATORY)

Use PascalCase for classes. Use camelCase for methods and variables. Use UPPER_SNAKE_CASE for constants. Follow language-conventional file naming (e.g., snake_case for Python, PascalCase for TypeScript classes). Names MUST be descriptive and self-documenting. Avoid abbreviations except for widely understood acronyms (e.g., API, HTTP, ID).

**Rationale**: Consistent naming reduces cognitive overhead and enables faster code navigation. Self-documenting names reduce the need for comments.

### V. Project Structure (Clean Folder Layout)

Maintain a clean folder layout with ONLY directories that are truly required: `src/domain`, `src/application`, `src/infrastructure`, `src/presentation`, `src/shared` (only if needed), `tests`, `docs`. Do NOT create organizational-only directories. Each directory MUST have a clear purpose. Avoid deep nesting—prefer flat structures when possible.

**Rationale**: Clear structure enables developers to locate code quickly. Minimal structure reduces decision fatigue and maintenance overhead.

### VI. Composition Over Inheritance

Classes MUST be purpose-specific. Prefer composition over inheritance. Use inheritance ONLY when there is a clear "is-a" relationship and shared behavior is substantial. Avoid deep inheritance hierarchies. Use interfaces/protocols for polymorphism when appropriate.

**Rationale**: Composition provides flexibility and reduces coupling. Deep inheritance hierarchies become brittle and difficult to maintain.

### VII. Dependency Injection (Selective Use)

Rely on dependency injection ONLY where it meaningfully improves testability and decoupling. Do NOT wrap simple operations in pointless abstractions. Do NOT create dependency injection containers for trivial cases. Use constructor injection for required dependencies. Use setter injection or method injection only when constructor injection is impractical.

**Rationale**: Dependency injection improves testability, but overuse creates unnecessary complexity. Use it where it provides real value.

### VIII. Error Handling (Fail Fast, Domain-Specific Errors)

Code MUST fail fast—validate inputs early and reject invalid states immediately. NEVER swallow exceptions silently. Use domain-specific error types instead of generic exceptions. Avoid "magic values"—use named constants or enums. NEVER wrap simple operations in pointless abstractions. Propagate errors to appropriate handlers—do not catch exceptions unless you can handle them meaningfully.

**Rationale**: Fail-fast behavior surfaces bugs early. Domain-specific errors provide clear diagnostic information. Proper error handling prevents silent failures and improves debuggability.

### IX. Testing Standards (Arrange-Act-Assert, Comprehensive Coverage)

Tests MUST follow Arrange-Act-Assert pattern. Tests MUST cover domain rules, use cases, controllers, and infrastructure adapters. Tests MUST NOT rely on unnecessary mocking layers—mock only external dependencies (databases, APIs, file systems). Unit tests MUST be fast, isolated, and deterministic. Integration tests MUST verify component interactions. Test names MUST clearly describe what is being tested and the expected outcome.

**Rationale**: Comprehensive testing prevents regressions and enables confident refactoring. Clear test structure improves readability and maintenance.

### X. Documentation Standards (Intent and Behavior)

Documentation MUST explain intent and behavior clearly. Comments MUST focus on "why," not "what." Code should be self-documenting through clear naming. Document complex algorithms, business rules, and non-obvious decisions. Keep documentation up-to-date with code changes. API documentation MUST be complete and accurate.

**Rationale**: Good documentation accelerates onboarding and reduces misunderstanding. "Why" comments provide context that code cannot express.

### XI. Code Organization (Strict Ordering)

Enforce strict ordering: imports (standard library, third-party, local), constants, types, classes, and helpers. Always use formatters and linters. Generated code MUST be complete, runnable, real, and never boilerplate for its own sake. Group related code together. Separate concerns clearly.

**Rationale**: Consistent organization improves readability and reduces merge conflicts. Automated tooling ensures consistency across the codebase.

### XII. AI-Generated Code Standards

AI-generated code MUST follow all rules in this constitution. AI-generated code MUST avoid complexity that does not serve the problem. AI-generated code MUST always return the simplest, cleanest, and most organized version possible. Review AI-generated code for compliance before committing.

**Rationale**: AI tools can generate complex or over-engineered solutions. Human review ensures code meets project standards.

## Code Quality Gates

### Linting and Formatting

All code MUST pass linting checks before commit. Use project-standard formatters (e.g., black, isort for Python). Configure linters to enforce naming conventions, import ordering, and code style. CI/CD pipelines MUST enforce linting and formatting checks.

### Type Safety

Use type hints for all function signatures and class attributes. Enable static type checking (e.g., mypy for Python, TypeScript strict mode). Fix type errors before merging. Use type-safe patterns—avoid `Any` except when absolutely necessary.

### Code Review Requirements

All code changes MUST be reviewed before merging. Reviewers MUST verify constitution compliance. Reviewers MUST check for unnecessary complexity, dead code, and violations of clean code principles. Complexity MUST be justified in code review comments.

## Development Workflow

### Commit Conventions

Commits MUST be atomic—each commit should represent a single logical change. Commit messages MUST be descriptive and follow conventional prefixes: `feat:` for new features, `fix:` for bug fixes, `refactor:` for code refactoring, `docs:` for documentation, `test:` for test additions or changes. NEVER mix unrelated changes in a single commit. Commit messages MUST explain the "why" when the change is non-obvious.

**Rationale**: Atomic commits enable easier debugging, rollback, and code archaeology. Conventional prefixes enable automated changelog generation.

### Refactoring Discipline

Refactor continuously to eliminate duplication and reduce complexity. Refactor in dedicated commits—do not mix refactoring with feature work unless the refactoring is necessary for the feature. Remove dead code immediately. Update tests when refactoring changes behavior.

## Governance

This constitution supersedes all other coding practices and style guides. All code MUST comply with these principles. Amendments to this constitution require:

1. Documentation of the proposed change and rationale
2. Review and approval by project maintainers
3. Update to version number following semantic versioning:
   - MAJOR: Backward incompatible governance/principle removals or redefinitions
   - MINOR: New principle/section added or materially expanded guidance
   - PATCH: Clarifications, wording, typo fixes, non-semantic refinements
4. Propagation of changes to dependent templates and documentation
5. Communication to all contributors

All pull requests and code reviews MUST verify compliance with this constitution. Complexity that violates principles MUST be justified in code review. Use this constitution as the primary reference for all development decisions.

**Version**: 1.0.0 | **Ratified**: 2025-01-27 | **Last Amended**: 2025-01-27
