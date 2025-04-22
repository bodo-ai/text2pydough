import json
import sys
from collections import defaultdict

def json_to_markdown(metadata: dict) -> str:
    # Map to store: {collection: list of (reverse_name, from_collection, singular, reverse_of)}
    inferred_reverse_relationships = defaultdict(list)

    for collections in metadata.values():
        for collection_name, collection in collections.items():
            for prop_name, prop in collection.get("properties", {}).items():
                if prop["type"] in {"simple_join", "compound"}:
                    target = prop["other_collection_name"]
                    inferred_reverse_relationships[target].append({
                        "name": prop["reverse_relationship_name"],
                        "from": collection_name,
                        "reverse_of": prop_name,
                        "singular": prop.get("no_collisions", False)  # flip side
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
            "address": "The directional address",
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

    for graph_name, collections in metadata.items():
        for collection, info in collections.items():
            markdown.append(f"### The `{collection}` collection contains the following columns:")
            props = info.get("properties", {})
            existing = set(props.keys())

            for prop_name, prop_info in props.items():
                if prop_info["type"] == "table_column":
                    markdown.append(describe_table_column(prop_name, prop_info))
                elif prop_info["type"] in {"simple_join", "compound"}:
                    markdown.append(describe_join(prop_name, prop_info))

            # Include inferred reverse relationships
            for reverse in inferred_reverse_relationships.get(collection, []):
                if reverse["name"] not in existing:
                    markdown.append(describe_inferred_reverse(
                        name=reverse["name"],
                        from_collection=reverse["from"],
                        reverse_of=reverse["reverse_of"],
                        singular=reverse["singular"]
                    ))

            markdown.append("")

    return "\n".join(markdown)

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
