# DevOps Patterns & Best Practices

## 1. Containerization (Docker)

### Multi-Stage Builds
Always use multi-stage builds to keep final images small and secure. Build the application in a heavy "builder" stage, and copy only the compiled artifacts to a minimal runtime image (like Alpine or distroless).

### Non-Root User
Never run applications as the `root` user inside a container. Create a dedicated user and group, and switch to it using the `USER` directive.

### Image Caching
Order Dockerfile instructions from least likely to change to most likely to change. Install dependencies before copying the application source code to maximize layer caching.

### Minimal Base Images
Use specific and minimal base image tags (e.g., `node:18-alpine` instead of `node:latest`). Avoid `latest` to ensure reproducible builds.

## 2. CI/CD Pipeline Principles

### Fail Fast
Put the fastest and most critical checks at the beginning of the pipeline (e.g., linting, unit tests, secret scanning). If they fail, the pipeline stops immediately, saving time and resources.

### Isolated Environments
Deploy to isolated environments (Preview, Staging, Production) to ensure changes are thoroughly tested before reaching users.

### Artifact Immutability
Build the Docker image or artifact exactly once during the CI phase, tag it with a unique identifier (like the Git commit SHA), and promote that same exact artifact through all deployment environments.

## 3. Infrastructure as Code (IaC)

### DRY (Don't Repeat Yourself)
Use modules and variables to reuse infrastructure configurations. Avoid copying and pasting resource definitions.

### State Management
Always use remote state backends (e.g., AWS S3 with DynamoDB locking, Terraform Cloud) for team collaboration and state protection. Never commit state files to version control.

### Principle of Least Privilege
When provisioning IAM roles or service accounts for deployments, grant only the exact permissions needed for the infrastructure to function, rather than wide-open admin access.
