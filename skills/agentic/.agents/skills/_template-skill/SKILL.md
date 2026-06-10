---
name: _template
version: 1.0.0
description: Template for creating new agent skills. Use create_skill.py to scaffold from this template. NOT a real skill.
---

# [Skill Title]

<!--
  HOW TO USE THIS TEMPLATE:
  1. Run: python .agents/scripts/create_skill.py <skill-name> "<description>"
  2. Fill in all sections marked with [brackets] or <!-- comments -->
  3. Replace all placeholder text before using
  4. Add reference files to references/
  5. Add an output example to examples/
  6. Run: python .agents/scripts/validate_skills.py
  
  DIRECTORY STRUCTURE:
  your-skill/
  ├── SKILL.md           ← This file (required)
  ├── references/        ← Deep-dive reference documents (required directory)
  │   └── your-ref.md   ← Load these files during execution
  └── examples/          ← Sample outputs for format reference (required directory)
      └── example-output.md
-->

> **Language rule**: [Configure in `.agents/config.yaml` → `response_language`. Default: Always respond in Spanish.]

You are a [role title — e.g., "senior backend engineer", "DevOps specialist"]. Your role is to [primary responsibility — one sentence explaining the core value this skill provides].

## Triggers

<!-- List 4-8 trigger phrases in the workspace's primary language that users would naturally say to activate this skill -->
- "[trigger phrase 1]"
- "[trigger phrase 2]"
- "[trigger phrase 3]"
- "[trigger phrase 4]"

## When to Use This Skill

<!-- List 4-6 concrete use cases. Start each with "User asks/wants/needs" for consistency -->
- User asks to [use case 1]
- User wants to [use case 2]
- User needs [use case 3]
- User asks about [use case 4]

## Reference Loading

<!-- Specify which files to load and when. This section is critical for quality output. -->
Before starting any task, read the relevant reference files:
- **Required**: `references/[main-reference].md` — [one-line description of what this file contains]
- **On demand**: `examples/[example-file].md` — Load when generating output to match the expected format

## Core Responsibilities

<!-- Define 4-6 numbered responsibilities. Each should have a clear action and scope. -->

### 1. [Responsibility Name]
<!-- What this skill does in this area. Be specific about inputs, outputs, and approach. -->
[Description of what to do and how]

### 2. [Responsibility Name]
[Description of what to do and how]

### 3. [Responsibility Name]
[Description of what to do and how]

## Workflow

<!-- Define a 5-6 step process. Use verb: description format. -->
1. **[Step 1]**: [What to do and why]
2. **[Step 2]**: [What to do and why]
3. **[Step 3]**: [What to do and why]
4. **[Step 4]**: [What to do and why]
5. **[Step 5]**: [What to do and why]

## Output Format

<!-- Define the exact structure the agent must follow when responding. Use Spanish section names. -->
Always structure responses as:
1. **[Sección 1]**: [Description of what goes here]
2. **[Sección 2]**: [Description of what goes here]
3. **[Sección 3]**: [Description of what goes here]

## Technology-Specific Checks

<!-- Optional but recommended: add technology-specific checks if the skill has different behavior per language/stack. Remove this section if not applicable. -->

### Python
- [Python-specific check 1]
- [Python-specific check 2]

### JavaScript/TypeScript
- [JS/TS-specific check 1]
- [JS/TS-specific check 2]

### Go
- [Go-specific check 1 — or remove this subsection if not applicable]

### Java
- [Java-specific check 1 — or remove this subsection if not applicable]

## Related Skills

<!-- List 2-4 skills that complement or are triggered after this one. Explain the handoff scenario. -->
- **[skill-name]**: [When to hand off — e.g., "After completing X, use skill-Y to do Z"]
- **[skill-name]**: [When to combine — e.g., "Run concurrently with skill-Y when scope includes Z"]

## Guidelines

<!-- List 5-7 behavioral rules for the agent. Be specific and actionable. -->
- [Guideline 1 — e.g., "Always provide before/after examples when proposing changes"]
- [Guideline 2 — e.g., "Prioritize high-impact, low-effort improvements first"]
- [Guideline 3 — e.g., "Explain WHY something is a problem, not just WHAT"]
- [Guideline 4]
- [Guideline 5]
