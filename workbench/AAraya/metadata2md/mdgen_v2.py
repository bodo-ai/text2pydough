import json
import sys
from collections import defaultdict

def json_to_markdown(metadata: list) -> str:
    graph = metadata[0]
    graph_name = graph.get("name", "Unknown")
    version = graph.get("version", "Unknown")
    collections = {col["name"]: col for col in graph.get("collections", [])}
    relationships = graph.get("relationships", [])

    # Track where to insert join/reverse relationships
    rel_map = defaultdict(list)

    # Index joins to help with reverse placement
    join_lookup = {}
    for rel in relationships:
        if rel["type"] == "simple join":
            parent = rel["parent collection"]
            child = rel["child collection"]
            name = rel["name"]
            join_lookup[(parent, name)] = child
            rel_map[parent].append({
                "field": name,
                "from": parent,
                "to": child,
                "description": rel.get("description", ""),
                "synonyms": rel.get("synonyms", []),
                "type": "join"
            })

    for rel in relationships:
        if rel["type"] == "reverse":
            original_parent = rel["original parent"]
            original_property = rel["original property"]
            reverse_name = rel["name"]
            # Look up the child collection using the original join
            child = join_lookup.get((original_parent, original_property))
            if child:
                rel_map[child].append({
                    "field": reverse_name,
                    "from": original_parent,
                    "to": child,
                    "description": rel.get("description", ""),
                    "synonyms": rel.get("synonyms", []),
                    "type": "reverse"
                })

    md = [f"# Metadata Overview: {graph_name} (Graph Name)", f"**Version**: {version}\n"]

    for cname, col in collections.items():
        md.append(f"### The `{cname}` collection contains the following columns:")
        props = col.get("properties", [])

        for prop in props:
            if prop["type"] != "table column":
                continue
            line = f"- **{prop['name']}**: {prop.get('description', 'No description.')}"
            md.append(line)
            if "synonyms" in prop:
                md.append(f"  - Synonyms: {', '.join(prop['synonyms'])}")
            if "sample values" in prop:
                values = ', '.join([repr(x) for x in prop['sample values']])
                md.append(f"  - Sample values: {values}")

        # Add relationships assigned to this collection
        for rel in rel_map.get(cname, []):
            md.append(f"- **{rel['field']}**: {rel['description']} (reverse of `{rel['from']}.{rel['field']}`)" if rel["type"] == "reverse" else f"- **{rel['field']}**: {rel['description']}")
            if rel.get("synonyms"):
                md.append(f"  - Synonyms: {', '.join(rel['synonyms'])}")

        md.append("")

    return "\n".join(md)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python mdgen.py <input.json> <output.md>")
        sys.exit(1)

    input_file, output_file = sys.argv[1], sys.argv[2]

    with open(input_file, "r") as f:
        metadata = json.load(f)

    markdown = json_to_markdown(metadata)

    with open(output_file, "w") as f:
        f.write(markdown)

    print(f"✅ Markdown written to {output_file}")
