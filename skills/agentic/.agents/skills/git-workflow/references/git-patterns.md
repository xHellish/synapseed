# Git Patterns & Best Practices

## 1. Branching Strategies

### Trunk-Based Development (Recommended)
Trunk-Based Development is a model where all developers merge their code into a central branch (`main` or `trunk`) multiple times a day.
- **Pros**: Reduces merge conflicts, enables Continuous Integration, promotes smaller commits.
- **Rules**:
  - Branches should be short-lived (less than a couple of days).
  - Commits should be small and logical.
  - Rely on feature toggles (feature flags) to hide incomplete work instead of keeping long-running feature branches.

### GitHub Flow
A lightweight, branch-based workflow centered around Pull Requests.
- **Workflow**:
  1. Create a branch off `main` (e.g., `feature/login`).
  2. Commit changes.
  3. Open a Pull Request.
  4. Discuss and review code.
  5. Merge and deploy immediately.
- **Best For**: Web applications and continuous deployment environments.

### Git Flow
A strict branching model with multiple long-running branches (`main`, `develop`) and specific types of temporary branches (`feature/`, `release/`, `hotfix/`).
- **Pros**: High control over releases, good for packaged software with specific release schedules.
- **Cons**: Can lead to "merge hell", slows down integration, overhead of managing multiple branches.
- **Recommendation**: Avoid for most modern SaaS/Web applications unless specifically required by compliance or strict scheduled releases.

## 2. Conventional Commits

Conventional Commits is a lightweight convention on top of commit messages. It provides an easy set of rules for creating an explicit commit history, which makes it easier to write automated tools on top of.

**Format:**
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Common Types:**
- `feat`: A new feature (correlates with MINOR in Semantic Versioning).
- `fix`: A bug fix (correlates with PATCH in Semantic Versioning).
- `docs`: Documentation only changes.
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc.).
- `refactor`: A code change that neither fixes a bug nor adds a feature.
- `perf`: A code change that improves performance.
- `test`: Adding missing tests or correcting existing tests.
- `chore`: Changes to the build process or auxiliary tools and libraries.

**Breaking Changes:**
Any commit type can include a `BREAKING CHANGE` footer or a `!` after the type/scope to indicate a breaking change (correlates with MAJOR in Semantic Versioning).
Example: `feat(api)!: rename user endpoint`

## 3. Release Automation & Semantic Versioning

By combining Conventional Commits with a CI tool, we can automate the release process.
- **Semantic Release**: Analyzes commits since the last release.
  - If a `feat` is found -> Bumps MINOR (1.1.0 -> 1.2.0)
  - If a `fix` is found -> Bumps PATCH (1.1.0 -> 1.1.1)
  - If a `BREAKING CHANGE` is found -> Bumps MAJOR (1.1.0 -> 2.0.0)
- The tool automatically generates a `CHANGELOG.md`, creates a Git tag, and publishes the release (e.g., to npm, GitHub Releases, Docker Hub).
