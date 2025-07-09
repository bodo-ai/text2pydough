import json
import sys


def convert_metadata(original_json: dict) -> list[dict]:
    new_json: list[dict] = []
    for graph_name, original_graph in original_json.items():
        new_collections: list[dict] = []
        new_relationships: list[dict] = []
        for collection_name, original_collection in original_graph.items():
            new_properties: list[dict] = []
            for property_name, original_property in original_collection["properties"].items():
                original_type: str = original_property["type"]
                if original_type == "table_column":
                    original_data_type: str = original_property["data_type"]
                    new_data_type: str
                    if original_data_type.startswith("int") or original_data_type.startswith("float") or original_data_type.startswith("decimal"):
                        new_data_type = "numeric"
                    elif original_data_type.startswith("date") or original_data_type.startswith("timestamp"):
                        new_data_type = "datetime"
                    elif original_data_type in ("string", "binary"):
                        new_data_type = "string"
                    elif original_data_type == "bool":
                        new_data_type = "bool"
                    else:
                        raise NotImplementedError(f"Unhandled data type: {original_data_type}")
                    new_property: dict = {
                        "name": property_name,
                        "type": "table column",
                        "data type": new_data_type,
                        "column name":  original_property["column_name"],
                        "description": "",
                        "synonyms": [""],
                        "sample values": [""],
                        "extra semantic info": {}
                    }
                    new_properties.append(new_property)
                else:
                    if original_type not in ("simple_join", "general_join", "cartesian_product"):
                        raise NotImplementedError(f"Unhandled property type: {original_type}")
                    new_type: str
                    join_info: dict = {}
                    if original_type == "simple_join":
                        new_type = "simple join"
                        join_info["keys"] = original_property["keys"]
                        join_info["singular"] = original_property["singular"]
                    elif original_type == "general_join":
                        new_type = "general join"
                        join_info["condition"] = original_property["condition"]
                        join_info["singular"] = original_property["singular"]
                    else:
                        new_type = "cartesian product"
                    forward_property: dict = {
                        "name": property_name,
                        "type": new_type,
                        "parent collection": collection_name,
                        "child collection": original_property["other_collection_name"],
                        **join_info,
                        "always matches": original_property["always_matches"] if "always_matches" in original_property else True,
                        "description": "",
                        "synonyms": [""],
                        "extra semantic info": {}
                    }
                    reverse_property: dict = {
                        "name": original_property["reverse_relationship_name"],
                        "type": "reverse",
                        "original parent":  collection_name,
                        "original property": property_name,
                        "singular": original_property["no_collisions"],
                        "always matches": original_property["always_matches"] if "always_matches" in original_property else True,
                        "description": "",
                        "synonyms": [""],
                        "extra semantic info": {}
                    }
                    new_relationships.append(forward_property)
                    new_relationships.append(reverse_property)
            new_collection: dict = {
                "name": collection_name,
                "type": "simple table",
                "table path": original_collection["table_path"],
                "unique properties": original_collection.get("unique_properties", []),
                "properties": new_properties,
                "description": "",
                "synonyms": [""],
                "extra semantic info": {}
            }
            new_collections.append(new_collection)
        new_graph = {
            "name": graph_name,
            "version": "V2",
            "collections": new_collections,
            "relationships": new_relationships,
            "additional definitions": [],
            "verified pydough analysis": [],
            "extra semantic info": {},
        }
        new_json.append(new_graph)
    return new_json


if __name__ == "__main__":
    assert len(sys.argv) == 2
    print(sys.argv)
    path = sys.argv[1]
    with open(path, 'r') as f:
        original_json: dict = json.load(f)
    print(json.dumps(convert_metadata(original_json), indent=1))