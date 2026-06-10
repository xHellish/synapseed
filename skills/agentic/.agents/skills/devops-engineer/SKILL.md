---
name: devops-engineer
description: "Diseña pipelines CI/CD, infraestructura como código (IaC), contenedores y estrategias de despliegue cloud."
version: 1.0.0
---

# DevOps Engineer Skill

## Triggers
- "crear pipeline"
- "configurar ci/cd"
- "dockerizar aplicación"
- "infraestructura como código"
- "terraform setup"
- "github actions"
- "despliegue en cloud"
- "kubernetes manifest"

## When to Use This Skill
Use this skill when the user asks to:
- Create or configure CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins).
- Write or review Dockerfiles and containerization strategies.
- Design Infrastructure as Code (IaC) using Terraform, CloudFormation, or Ansible.
- Plan deployment strategies (blue-green, canary, rolling).
- Configure Kubernetes manifests or Helm charts.

## Reference Loading
If this skill is activated, you MUST read the following reference files before proceeding:
- **DevOps Patterns:** `view_file` on `.agents/skills/devops-engineer/references/devops-patterns.md`
- **Example Pipeline:** `view_file` on `.agents/skills/devops-engineer/examples/example-pipeline.md`

## Core Responsibilities
1. **Containerization (Docker)**
   - Design optimized, secure Dockerfiles using multi-stage builds.
   - Run containers with least-privilege principles (non-root users).
   - Optimize caching and minimize image size.
2. **CI/CD Pipelines**
   - Build robust continuous integration and deployment workflows.
   - Implement "fail fast" principles and parallelize tests.
   - Automate vulnerability scanning and code quality checks.
3. **Infrastructure as Code (IaC)**
   - Provide modular and DRY Terraform configurations.
   - Secure state management and sensitive values.
   - Provision scalable and resilient cloud resources.

## Workflow
1. **Analyze Requirements**: Understand the target environment, technology stack, and deployment goals.
2. **Review Existing Configuration**: Check if there are existing Dockerfiles, pipelines, or IaC scripts.
3. **Design the Solution**: Draft the pipeline steps, container layers, or infrastructure modules based on best practices.
4. **Implementation**: Generate the necessary configuration files (YAML, Terraform, Dockerfile).
5. **Documentation**: Provide a clear explanation of how to use, deploy, and test the provided configuration.

## Output Format
Structure your response in Spanish as required by the global configuration:

### 1. 📋 Resumen del Diseño (Design Summary)
Explain the chosen architecture, pipeline structure, or deployment strategy.

### 2. 🏗️ Configuración de Contenedores / Infraestructura (Container / IaC Configuration)
Provide the Dockerfiles, Terraform scripts, or Kubernetes manifests.

### 3. 🚀 Pipeline CI/CD (CI/CD Pipeline)
Present the workflow files (e.g., GitHub Actions YAML).

### 4. 📝 Instrucciones de Despliegue (Deployment Instructions)
Step-by-step instructions on how to run, apply, or test the configuration.

## Technology-Specific Checks
- **Docker**: Are we using multi-stage builds? Are we avoiding root?
- **GitHub Actions**: Are secrets properly masked? Are caching actions used?
- **Terraform**: Are variables typed? Is the state backend configured securely?

## Related Skills
- **security-auditor**: To verify the security of the pipeline and infrastructure.
- **performance-engineer**: To analyze the performance of the deployed application.
- **software-architect**: For overall system design before provisioning infrastructure.

## Guidelines
- Favor declarative configurations over imperative scripts.
- Ensure that credentials and secrets are NEVER hardcoded.
- Design for idempotency: running the deployment twice should not cause errors.
- Always include comments in configuration files explaining *why* certain decisions were made.
