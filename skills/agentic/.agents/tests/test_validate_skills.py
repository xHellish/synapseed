import json
from pathlib import Path
import pytest
import sys
import os

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validate_skills import parse_frontmatter, validate_manifest


def test_parse_frontmatter():
    content = """---
name: test-skill
version: 1.0.0
description: A test skill
---
## Triggers
"""
    result = parse_frontmatter(content)
    assert result.get("name") == "test-skill"
    assert result.get("version") == "1.0.0"
    assert result.get("description") == "A test skill"

def test_parse_frontmatter_empty():
    content = "No frontmatter here"
    result = parse_frontmatter(content)
    assert result == {}

def test_validate_manifest_missing_skills():
    manifest_data = {}
    skills_on_disk = set()
    errors = validate_manifest(manifest_data, skills_on_disk)
    assert len(errors) == 1
    assert "missing top-level 'skills' array" in errors[0]

def test_validate_manifest_missing_required_fields():
    manifest_data = {
        "skills": [
            {
                "name": "test-skill",
                "version": "1.0.0"
                # Missing description, languages, etc.
            }
        ]
    }
    skills_on_disk = {"test-skill"}
    errors = validate_manifest(manifest_data, skills_on_disk)
    assert any("Missing field: 'description'" in e for e in errors)
    assert any("Missing field: 'languages'" in e for e in errors)