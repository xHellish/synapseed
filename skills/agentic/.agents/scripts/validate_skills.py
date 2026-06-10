#!/usr/bin/env python3
"""
validate_skills.py — Validador de integridad del catálogo de Agent Skills.

Uso:
    python .agents/scripts/validate_skills.py

Verifica:
  1. Cada carpeta en .agents/skills/ (excepto _template-skill) tiene un SKILL.md
  2. Cada SKILL.md tiene el frontmatter YAML requerido: name, version, description
  3. Cada SKILL.md tiene las secciones obligatorias: Triggers, When to Use, Workflow, Related Skills
  4. Cada skill está registrada en .agents/manifest.json con los campos requeridos
  5. Los archivos de referencia listados en manifest.json existen en disco
  6. Las carpetas examples/ existen en cada skill

Retorna código de salida 0 si todo es válido, 1 si hay errores.
"""

import json
import re
import sys
from pathlib import Path

# ── Configuración ────────────────────────────────────────────────────────────

WORKSPACE_ROOT = Path(__file__).parent.parent.parent
AGENTS_DIR = WORKSPACE_ROOT / ".agents"
SKILLS_DIR = AGENTS_DIR / "skills"
MANIFEST_PATH = AGENTS_DIR / "manifest.json"
TEMPLATE_SKILL = "_template-skill"

REQUIRED_FRONTMATTER_FIELDS = {"name", "version", "description"}
REQUIRED_SKILL_SECTIONS = [
    "## Triggers",
    "## When to Use This Skill",
    "## Reference Loading",
    "## Workflow",
    "## Related Skills",
]
REQUIRED_MANIFEST_SKILL_FIELDS = {
    "name", "version", "description", "languages", "skillFile", "references", "triggers"
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def error(msg: str) -> None:
    print(f"  [ERROR] {msg}")

def warn(msg: str) -> None:
    print(f"  [WARN]  {msg}")

def ok(msg: str) -> None:
    print(f"  [OK]    {msg}")

def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter fields (simple key: value parser)."""
    fields = {}
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return fields
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields

# ── Validaciones ──────────────────────────────────────────────────────────────

def validate_skill_directory(skill_dir: Path) -> list[str]:
    """Validate a single skill directory. Returns list of error messages."""
    errors = []
    skill_name = skill_dir.name

    # 1. SKILL.md must exist
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        errors.append(f"[{skill_name}] Missing SKILL.md")
        return errors  # Can't continue without it

    content = skill_md.read_text(encoding="utf-8")

    # 2. Frontmatter validation
    frontmatter = parse_frontmatter(content)
    for field in REQUIRED_FRONTMATTER_FIELDS:
        if field not in frontmatter or not frontmatter[field]:
            errors.append(f"[{skill_name}] SKILL.md missing frontmatter field: '{field}'")

    # Version format check (semver)
    version = frontmatter.get("version", "")
    if version and not re.match(r"^\d+\.\d+\.\d+$", version):
        errors.append(f"[{skill_name}] Version '{version}' is not valid semver (X.Y.Z)")

    # 3. Required sections
    for section in REQUIRED_SKILL_SECTIONS:
        if section not in content:
            errors.append(f"[{skill_name}] SKILL.md missing section: '{section}'")

    # 4. references/ directory
    refs_dir = skill_dir / "references"
    if not refs_dir.exists():
        errors.append(f"[{skill_name}] Missing references/ directory")

    # 5. examples/ directory (warning only)
    examples_dir = skill_dir / "examples"
    if not examples_dir.exists():
        errors.append(f"[{skill_name}] Missing examples/ directory (recommended)")

    return errors


def validate_manifest(manifest_data: dict, skills_on_disk: set[str]) -> list[str]:
    """Validate manifest.json contents. Returns list of error messages."""
    errors = []

    if "skills" not in manifest_data:
        errors.append("manifest.json missing top-level 'skills' array")
        return errors

    manifest_skill_names = set()
    for skill in manifest_data["skills"]:
        skill_name = skill.get("name", "<unnamed>")
        manifest_skill_names.add(skill_name)

        # Required fields
        for field in REQUIRED_MANIFEST_SKILL_FIELDS:
            if field not in skill:
                errors.append(f"[manifest:{skill_name}] Missing field: '{field}'")

        # Verify skillFile exists on disk
        skill_file = skill.get("skillFile", "")
        if skill_file:
            full_path = WORKSPACE_ROOT / skill_file
            if not full_path.exists():
                errors.append(f"[manifest:{skill_name}] skillFile not found: {skill_file}")

        # Verify reference files exist
        for ref in skill.get("references", []):
            ref_path = WORKSPACE_ROOT / ref
            if not ref_path.exists():
                errors.append(f"[manifest:{skill_name}] Reference file not found: {ref}")

        # Validate triggers is non-empty
        triggers = skill.get("triggers", [])
        if not triggers:
            errors.append(f"[manifest:{skill_name}] 'triggers' array is empty")

    # Check that all disk skills are in manifest
    for skill_name in skills_on_disk:
        if skill_name not in manifest_skill_names:
            errors.append(
                f"[manifest] Skill '{skill_name}' exists on disk but is not registered in manifest.json"
            )

    # Check that all manifest skills exist on disk
    for skill_name in manifest_skill_names:
        if skill_name not in skills_on_disk:
            errors.append(
                f"[manifest] Skill '{skill_name}' is in manifest.json but has no directory in skills/"
            )

    return errors

# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    print("[*] Validating Agentic Workspace skill catalog...\n")
    total_errors = 0
    total_warnings = 0

    # ── 1. Validate each skill directory ────────────────────────────────────
    print("[DIR] Checking skill directories...")
    if not SKILLS_DIR.exists():
        error(f"Skills directory not found: {SKILLS_DIR}")
        return 1

    skills_on_disk = set()
    all_dir_errors = []

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name.startswith(TEMPLATE_SKILL):
            continue
        skills_on_disk.add(skill_dir.name)
        dir_errors = validate_skill_directory(skill_dir)
        if dir_errors:
            for e in dir_errors:
                all_dir_errors.append(e)
        else:
            ok(f"{skill_dir.name}")

    if all_dir_errors:
        for e in all_dir_errors:
            # Treat missing examples/ as a warning
            if "examples/" in e:
                warn(e)
                total_warnings += 1
            else:
                error(e)
                total_errors += 1
    print()

    # ── 2. Validate manifest.json ────────────────────────────────────────────
    print("[JSON] Checking manifest.json...")
    if not MANIFEST_PATH.exists():
        error(f"manifest.json not found at {MANIFEST_PATH}")
        total_errors += 1
    else:
        try:
            manifest_data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            manifest_errors = validate_manifest(manifest_data, skills_on_disk)
            if manifest_errors:
                for e in manifest_errors:
                    error(e)
                    total_errors += 1
            else:
                ok("manifest.json is valid")
        except json.JSONDecodeError as exc:
            error(f"manifest.json is not valid JSON: {exc}")
            total_errors += 1
    print()

    # ── 3. Summary ───────────────────────────────────────────────────────────
    print("-" * 50)
    if total_errors == 0 and total_warnings == 0:
        print(f"[OK] All {len(skills_on_disk)} skills are valid. Catalog is healthy.")
        return 0
    elif total_errors == 0:
        print(f"[WARN] {total_warnings} warning(s) found. No blocking errors.")
        return 0
    else:
        print(f"[ERROR] {total_errors} error(s) and {total_warnings} warning(s) found.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
