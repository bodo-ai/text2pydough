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

    # Iterate through each collection in the graph
    for collection_name in graph.get_collection_names():
        collection = graph.get_collection(collection_name)
        markdown_output.append(f"### The `{collection.name}` collection contains the following columns:")

        # Iterate through each property within the collection
        for prop_name in collection.get_property_names():
            prop = collection.get_property(prop_name)
            if not prop:
                continue

            # Handle properties
            if not prop.is_subcollection:
                description_text = prop.description if prop.description else "No description available."
                markdown_output.append(f"- **{prop.name}**: {description_text}")

                if hasattr(prop, 'synonyms') and prop.synonyms:
                    markdown_output.append(f"  - Synonyms: {', '.join(prop.synonyms)}")
                if hasattr(prop, 'sample_values') and prop.sample_values:
                    sample_values_str = ', '.join(map(str, prop.sample_values))
                    markdown_output.append(f"  - Sample values: {sample_values_str}")
            # Handle relationships
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