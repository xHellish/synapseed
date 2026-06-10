import os
import sys
import shutil
import json
from pathlib import Path

def create_skill(name, description):
    """Creates a new skill from the template."""
    base_dir = Path(__file__).parent.parent
    skills_dir = base_dir / "skills"
    template_dir = skills_dir / "_template-skill"
    new_skill_dir = skills_dir / name

    if new_skill_dir.exists():
        print(f"Error: Skill '{name}' already exists.")
        sys.exit(1)

    if not template_dir.exists():
        print("Error: Template skill directory not found.")
        sys.exit(1)

    print(f"Creating skill '{name}'...")
    shutil.copytree(template_dir, new_skill_dir)

    skill_md_path = new_skill_dir / "SKILL.md"
    if skill_md_path.exists():
        content = skill_md_path.read_text(encoding="utf-8")
        content = content.replace("name: _template", f"name: {name}")
        content = content.replace("description: Template for creating new agent skills", f"description: {description}")
        skill_md_path.write_text(content, encoding="utf-8")

    manifest_path = base_dir / "manifest.json"
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            
            new_skill = {
                "name": name,
                "version": "1.0.0",
                "description": description,
                "languages": ["Any"],
                "skillFile": f".agents/skills/{name}/SKILL.md",
                "references": [],
                "triggers": [name.replace("-", " ")]
            }
            manifest["skills"].append(new_skill)
            
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            print(f"Added '{name}' to manifest.json")
        except Exception as e:
             print(f"Warning: Could not update manifest.json: {e}")

    print(f"Successfully created skill '{name}' in {new_skill_dir}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_skill.py <skill-name> <description>")
        sys.exit(1)
    
    skill_name = sys.argv[1]
    skill_desc = sys.argv[2]
    create_skill(skill_name, skill_desc)