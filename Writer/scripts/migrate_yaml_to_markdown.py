#!/usr/bin/env python3
"""Migrate YAML memory files to Markdown format for memsearch.

This script converts all YAML files in data/openviking/memory/
to Markdown format with YAML frontmatter.
"""

import sys
from pathlib import Path

import yaml


def yaml_to_markdown(yaml_path: Path, output_path: Path) -> bool:
    """Convert a single YAML file to Markdown.
    
    Args:
        yaml_path: Path to source YAML file
        output_path: Path to target Markdown file
        
    Returns:
        True if conversion succeeded
    """
    try:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            print(f"  Skipping empty file: {yaml_path}")
            return False

        # Extract value and metadata
        value = data.get("value", data)
        metadata = data.get("metadata", {})

        # Build frontmatter
        key = "/" + str(yaml_path.relative_to(yaml_path.parents[2])).replace("\\", "/")
        key = key.rsplit(".", 1)[0]  # Remove extension

        frontmatter = {
            "key": key,
            "namespace": data.get("namespace", "default"),
        }
        if metadata:
            frontmatter["metadata"] = metadata

        # Build Markdown content
        lines = ["---"]
        lines.append(yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True).strip())
        lines.append("---")
        lines.append("")

        if isinstance(value, dict):
            # Extract title
            title = value.get("name", value.get("title", key.split("/")[-1]))
            lines.append(f"# {title}")
            lines.append("")

            # Process each field
            for k, v in value.items():
                if k in ("name", "title"):
                    continue

                section_title = k.replace("_", " ").title()
                lines.append(f"## {section_title}")
                lines.append("")

                if isinstance(v, str):
                    lines.append(v)
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, str):
                            lines.append(f"- {item}")
                        elif isinstance(item, dict):
                            # Format dict items
                            for sub_k, sub_v in item.items():
                                lines.append(f"- **{sub_k}**: {sub_v}")
                        else:
                            lines.append(f"- {item}")
                elif isinstance(v, dict):
                    for sub_k, sub_v in v.items():
                        if isinstance(sub_v, list):
                            lines.append(f"- **{sub_k}**: {', '.join(str(x) for x in sub_v)}")
                        else:
                            lines.append(f"- **{sub_k}**: {sub_v}")
                else:
                    lines.append(str(v))
                lines.append("")
        else:
            lines.append(str(value))

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return True

    except Exception as e:
        print(f"  Error converting {yaml_path}: {e}")
        return False


def main():
    """Run the migration."""
    base_path = Path("data/openviking/memory")

    if not base_path.exists():
        print(f"Error: Directory not found: {base_path}")
        sys.exit(1)

    # Find all YAML files
    yaml_files = list(base_path.rglob("*.yaml"))

    if not yaml_files:
        print("No YAML files found to migrate.")
        sys.exit(0)

    print(f"Found {len(yaml_files)} YAML files to migrate")
    print()

    success_count = 0
    fail_count = 0

    for yaml_path in yaml_files:
        # Compute output path
        relative = yaml_path.relative_to(base_path)
        output_path = base_path / relative.with_suffix(".md")

        print(f"Converting: {relative}")

        if yaml_to_markdown(yaml_path, output_path):
            success_count += 1
            print(f"  -> {output_path.relative_to(base_path)}")
        else:
            fail_count += 1

    print()
    print(f"Migration complete: {success_count} succeeded, {fail_count} failed")
    print(f"Markdown files created in: {base_path}")


if __name__ == "__main__":
    main()
