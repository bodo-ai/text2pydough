import json
import sys
from pydough import parse_json_metadata_from_file

def generate_markdown_from_metadata(graph):
    """
    Converts a pydough graph metadata object into a formatted Markdown string..
    """
    markdown_output = []

    # Add main header and version
    markdown_output.append(f"# Metadata Overview: {graph.name} (Graph Name)")
    if hasattr(graph, 'version') and graph.version:
        markdown_output.append(f"**Version**: {graph.version}")
    markdown_output.append("")

    # Iterate through each collection (table) in the graph
    for collection_name in graph.get_collection_names():
        collection = graph.get_collection(collection_name)
        markdown_output.append(f"### The `{collection.name}` collection contains the following columns:")

        # Iterate through each property (column or relationship) within the collection
        for prop_name in collection.get_property_names():
            prop = collection.get_property(prop_name)
            if not prop:
                continue

            # Handle scalar properties (regular columns)
            if not prop.is_subcollection:
                description_text = prop.description if prop.description else "No description available."
                markdown_output.append(f"- **{prop.name}**: {description_text}")

                if hasattr(prop, 'synonyms') and prop.synonyms:
                    markdown_output.append(f"  - Synonyms: {', '.join(prop.synonyms)}")
                if hasattr(prop, 'sample_values') and prop.sample_values:
                    sample_values_str = ', '.join(map(str, prop.sample_values))
                    markdown_output.append(f"  - Sample values: {sample_values_str}")
            # Handle sub-collection properties (relationships)
            else:
                description_text = prop.description if prop.description else "No description available."
                reverse_info_suffix = ""

                # Determine the "reverse of" text for relationships
                if hasattr(graph, 'relationships'):
                    for rel_entry in graph.relationships:
                        # If the current property is a 'reverse' relationship itself
                        if rel_entry.get("type") == "reverse" and rel_entry.get("name") == prop.name:
                            is_relevant_reverse = False
                            for sj_rel in graph.relationships:
                                if sj_rel.get("type") == "simple join" and \
                                   sj_rel.get("parent collection") == rel_entry.get("original parent") and \
                                   sj_rel.get("name") == rel_entry.get("original property") and \
                                   sj_rel.get("child collection") == collection.name:
                                    is_relevant_reverse = True
                                    break
                            if is_relevant_reverse:
                                reverse_info_suffix = f" (reverse of `{rel_entry['original parent']}.{rel_entry['original property']}`)"
                                break
                        # If the current property is a 'simple join' relationship
                        elif rel_entry.get("type") == "simple join" and rel_entry.get("name") == prop.name and \
                             rel_entry.get("parent collection") == collection.name and \
                             rel_entry.get("child collection") == prop.child_collection.name:
                            
                            # Find the corresponding reverse relationship
                            for rev_rel_entry in graph.relationships:
                                if rev_rel_entry.get("type") == "reverse" and \
                                   rev_rel_entry.get("original parent") == rel_entry.get("child collection") and \
                                   rev_rel_entry.get("original property") == rel_entry.get("name"):
                                    reverse_info_suffix = f" (reverse of `{rel_entry['child collection']}.{rev_rel_entry['name']}`)"
                                    break
                            if reverse_info_suffix:
                                break

                markdown_output.append(f"- **{prop.name}**: {description_text}{reverse_info_suffix}")

                if hasattr(prop, 'synonyms') and prop.synonyms:
                    if isinstance(prop.synonyms, str):
                        markdown_output.append(f"  - Synonyms: {prop.synonyms}")
                    else:
                        markdown_output.append(f"  - Synonyms: {', '.join(prop.synonyms)}")
        markdown_output.append("") # Add a blank line between collections

    return "\n".join(markdown_output)

# Command-line interface (CLI) usage
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python your_script_name.py <input_json_file_path>")
        sys.exit(1)

    input_file_path = sys.argv[1]

    try:
        # Load JSON to extract graph name for pydough parsing
        with open(input_file_path, 'r', encoding='utf-8') as f:
            metadata_json = json.load(f)

        graph_name = metadata_json[0].get('name', 'default_graph')

        # Parse the metadata file using pydough
        my_graph = parse_json_metadata_from_file(input_file_path, graph_name)

        print(my_graph)

        # Generate the markdown content
        markdown_content = generate_markdown_from_metadata(my_graph)

        # Define output file name
        output_file_name = f"{graph_name}_graph.md"

        # Save the markdown content to a file
        with open(output_file_name, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"Markdown successfully generated and saved to '{output_file_name}'")

    except FileNotFoundError:
        print(f"Error: The file '{input_file_path}' was not found. Please check the path.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{input_file_path}'. Please ensure it's a valid JSON file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")