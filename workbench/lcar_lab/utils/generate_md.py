import sys
import json
import argparse
from pathlib import Path
from generate_mark_down import generate_markdown_from_metadata
from pydough import parse_json_metadata_from_file

# Path to credentials file
CREDENTIALS_PATH = Path(__file__).parent / "creds.json"


def main():
    """
    Using this command:
    python generate_md.py --user <user> --project <project_name>
    """
    parser = argparse.ArgumentParser(
        description="Generate Markdown from existing metadata using creds.json"
    )
    parser.add_argument("--user", required=True, help="User ID (e.g., email)")
    parser.add_argument("--project", required=True, help="Project key in creds.json")
    args = parser.parse_args()

    try:
        # Load credentials
        creds = json.loads(CREDENTIALS_PATH.read_text(encoding="utf-8"))

        if args.user not in creds:
            raise KeyError(f"User '{args.user}' not found in credentials file.")
        if args.project not in creds[args.user]:
            raise KeyError(
                f"Project '{args.project}' not found for user '{args.user}'."
            )

        project_cfg = creds[args.user][args.project]
        json_path = Path(project_cfg["json_path"])
        md_path = Path(project_cfg["md_path"])
        graph_name = project_cfg.get("graph_name", "default_graph")

        # Parse metadata using PyDough
        graph = parse_json_metadata_from_file(json_path, graph_name)

        # Generate markdown from parsed graph
        markdown_content = generate_markdown_from_metadata(graph)

        # Save markdown to file
        md_path.parent.mkdir(parents=True, exist_ok=True)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"Markdown written to {md_path}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
