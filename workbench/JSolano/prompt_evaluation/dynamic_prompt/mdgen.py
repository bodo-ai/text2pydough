import json
import sys
from collections import defaultdict

def json_to_markdown(metadata: dict) -> str:
    inferred_reverse_relationships = defaultdict(list)
    fields_per_collection = {}

    # Index reverse relationships and scalar fields
    for collections in metadata.values():
        for collection_name, collection in collections.items():
            props = collection.get("properties", {})
            fields_per_collection[collection_name] = [
                name for name, p in props.items() if p["type"] == "table_column"
            ]
            for prop_name, prop in props.items():
                if prop["type"] in {"simple_join", "compound"}:
                    inferred_reverse_relationships[prop["other_collection_name"]].append({
                        "name": prop["reverse_relationship_name"],
                        "from": collection_name,
                        "reverse_of": prop_name,
                        "singular": prop.get("no_collisions", False)
                    })

    def describe_table_column(name, col):
        desc = col.get("description") or get_column_description(name)
        return f"- **{name}**: {desc}"

    def describe_join(name, col):
        other = col.get("other_collection_name", "unknown")
        reverse = col.get("reverse_relationship_name", "unknown")
        plural = not col.get("singular", True)
        if plural:
            return f"- **{name}**: A list of all {other} associated with this record (reverse of `{other}.{reverse}`)."
        else:
            return f"- **{name}**: The corresponding {other} for this record (reverse of `{other}.{reverse}`)."

    def describe_inferred_reverse(name, from_collection, reverse_of, singular):
        if singular:
            return f"- **{name}**: The corresponding {from_collection} for this record (reverse of `{from_collection}.{reverse_of}`)."
        else:
            return f"- **{name}**: A list of all {from_collection} associated with this record (reverse of `{from_collection}.{reverse_of}`)."
  
    def get_column_description(name):
        name_map = {
            "key": "A unique identifier",
            "name": "The name",
            "comment": "Additional comments or notes",
            "address": "The address",
            "phone": "The phone number",
            "email": "The email",
        }
        if name in name_map:
            return name_map[name]
        elif name.endswith("_key"):
            ref = name.replace("_key", "")
            return f"A foreign key referencing the `{ref}s` collection."
        else:
            return f"{name.replace('_', ' ').capitalize()}."

    markdown = []

    # Main section: document each collection
    for graph_name, collections in metadata.items():
        markdown.append(f"### The high-level graph `{graph_name}` collection contains the following columns:")
        for collection_name in collections.keys():
            markdown.append(f"- **{collection_name}**: A list of {collection_name}.")
        
        markdown.append("")

        for collection, info in collections.items():
            markdown.append(f"### The `{collection}` collection contains the following columns:")
            props = info.get("properties", {})
            existing = set(props.keys())

            for prop_name, prop_info in props.items():
                if prop_info["type"] == "table_column":
                    markdown.append(describe_table_column(prop_name, prop_info))
                elif prop_info["type"] in {"simple_join", "compound"}:
                    markdown.append(describe_join(prop_name, prop_info))

            # Add inferred reverse relationships if missing
            for reverse in inferred_reverse_relationships.get(collection, []):
                if reverse["name"] not in existing:
                    markdown.append(describe_inferred_reverse(
                        name=reverse["name"],
                        from_collection=reverse["from"],
                        reverse_of=reverse["reverse_of"],
                        singular=reverse["singular"]
                    ))

            markdown.append("")

    # Extra section: auto-generated example queries
    markdown.append("### Example Relationship Queries (Auto-generated)")
    markdown.append("")

    for graph_name, collections in metadata.items():
        for collection, info in collections.items():
            props = info.get("properties", {})
            scalar_fields = fields_per_collection.get(collection, [])[:6]
            scalar_fields_str = ", ".join(scalar_fields) if scalar_fields else "..."

            # Direct relationships
            for prop_name, prop_info in props.items():
                if prop_info["type"] in {"simple_join", "compound"}:
                    is_plural = not prop_info.get("singular", True)
                    other = prop_info["other_collection_name"]
                    if is_plural:
                        markdown.append(f"To get all `{other}` from each `{collection}`:")
                    else:
                        markdown.append(f"To get the corresponding `{other}` for each `{collection}`:")
                    markdown.append(f"```python\n{collection}.{prop_name}.CALCULATE({scalar_fields_str})\n```")
                    markdown.append("")

            # Reverse relationships
            for reverse in inferred_reverse_relationships.get(collection, []):
                from_coll = reverse["from"]
                reverse_name = reverse["name"]
                singular = reverse["singular"]
                reverse_fields = fields_per_collection.get(from_coll, [])[:6]
                reverse_str = ", ".join(reverse_fields) if reverse_fields else "..."
                if singular:
                    markdown.append(f"To get the corresponding `{from_coll}` for each `{collection}`:")
                else:
                    markdown.append(f"To get all `{from_coll}` from each `{collection}`:")
                markdown.append(f"```python\n{collection}.{reverse_name}.CALCULATE({reverse_str})\n```")
                markdown.append("")

    return "\n".join(markdown)

# CLI usage
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python mdgeneration.py <input.json> <output.md>")
        sys.exit(1)

    input_file, output_file = sys.argv[1], sys.argv[2]

    with open(input_file, "r") as f:
        metadata = json.load(f)

    markdown = json_to_markdown(metadata)

    with open(output_file, "w") as f:
        f.write(markdown)

    print(f"Markdown written to {output_file}")