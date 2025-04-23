import json
import sqlalchemy
from sqlalchemy import inspect, create_engine
from typing import Dict, List, Any, Optional

class SQLToPyDoughConverter:
    def __init__(self, database_uri: str):
        """
        Initialize the converter with a database connection URI.
        
        Args:
            database_uri: SQLAlchemy compatible database URI (e.g., 'postgresql://user:password@localhost:5432/mydb')
        """
        self.engine = create_engine(database_uri)
        self.inspector = inspect(self.engine)
        self.metadata = {"Graph": {}}  # Default graph name is "Graph"
    
    def map_sql_type_to_pydough(self, sql_type: Any) -> str:
        """
        Map SQL column types to PyDough type strings.
        
        Args:
            sql_type: SQLAlchemy column type
            
        Returns:
            PyDough type string
        """
        if isinstance(sql_type, sqlalchemy.Integer):
            if isinstance(sql_type, sqlalchemy.SmallInteger):
                return "int16"
            return "int64"
        elif isinstance(sql_type, sqlalchemy.String):
            return "string"
        elif isinstance(sql_type, sqlalchemy.Float):
            return "float64"
        elif isinstance(sql_type, sqlalchemy.Numeric):
            if hasattr(sql_type, "precision") and hasattr(sql_type, "scale"):
                return f"decimal[{sql_type.precision},{sql_type.scale}]"
            return "decimal[10,2]"  # Default precision/scale
        elif isinstance(sql_type, sqlalchemy.Boolean):
            return "bool"
        elif isinstance(sql_type, sqlalchemy.Date):
            return "date"
        elif isinstance(sql_type, sqlalchemy.DateTime):
            return "timestamp[6]"  # Default to microsecond precision
        elif isinstance(sql_type, sqlalchemy.Time):
            return "time[6]"  # Default to microsecond precision
        elif isinstance(sql_type, sqlalchemy.LargeBinary):
            return "binary"
        elif isinstance(sql_type, sqlalchemy.ARRAY):
            element_type = self.map_sql_type_to_pydough(sql_type.item_type)
            return f"array[{element_type}]"
        else:
            return "unknown"
    
    def get_primary_keys(self, table_name: str, schema: Optional[str] = None) -> List[str]:
        """
        Get primary keys for a table.
        
        Args:
            table_name: Name of the table
            schema: Optional schema name
            
        Returns:
            List of primary key column names
        """
        return self.inspector.get_pk_constraint(table_name, schema=schema)["constrained_columns"]
    
    def get_foreign_keys(self, table_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get foreign keys for a table.
        
        Args:
            table_name: Name of the table
            schema: Optional schema name
            
        Returns:
            List of foreign key dictionaries
        """
        return self.inspector.get_foreign_keys(table_name, schema=schema)
    
    def analyze_database(self, schema: Optional[str] = None) -> None:
        """
        Analyze the database schema and build the PyDough metadata structure.
        
        Args:
            schema: Optional schema name to analyze
        """
        # First pass: create all tables as simple_table collections
        for table_name in self.inspector.get_table_names(schema=schema):
            self.add_table_as_collection(table_name, schema)
        
        # Second pass: add relationships based on foreign keys
        for table_name in self.inspector.get_table_names(schema=schema):
            self.add_relationships_for_table(table_name, schema)
    
    def add_table_as_collection(self, table_name: str, schema: Optional[str] = None) -> None:
        """
        Add a table as a simple_table collection to the metadata.
        
        Args:
            table_name: Name of the table
            schema: Optional schema name
        """
        # Get fully qualified table path
        table_path_parts = []
        if schema:
            table_path_parts.append(schema)
        table_path_parts.append(table_name)
        table_path = ".".join(table_path_parts)
        
        # Get columns and primary keys
        columns = self.inspector.get_columns(table_name, schema=schema)
        primary_keys = self.get_primary_keys(table_name, schema)
        
        # Build properties dictionary
        properties = {}
        for column in columns:
            column_name = column["name"]
            properties[column_name] = {
                "type": "table_column",
                "column_name": column_name,
                "data_type": self.map_sql_type_to_pydough(column["type"])
            }
        
        # Determine unique properties (primary keys)
        if len(primary_keys) == 1:
            unique_properties = [primary_keys[0]]
        elif len(primary_keys) > 1:
            unique_properties = [primary_keys]  # List of columns that together form a unique key
        
        # Add to metadata
        self.metadata["Graph"][table_name] = {
            "type": "simple_table",
            "table_path": table_path,
            "unique_properties": unique_properties,
            "properties": properties
        }
    
    def add_relationships_for_table(self, table_name: str, schema: Optional[str] = None) -> None:
        """
        Add relationships (simple_join properties) for a table based on foreign keys.
        
        Args:
            table_name: Name of the table
            schema: Optional schema name
        """
        foreign_keys = self.get_foreign_keys(table_name, schema)
        
        for fk in foreign_keys:
            # Get information about the foreign key
            constrained_columns = fk["constrained_columns"]  # Columns in this table
            referred_table = fk["referred_table"]  # Table being referenced
            referred_columns = fk["referred_columns"]  # Columns in referenced table
            
            # Determine relationship name (simple heuristic)
            if len(constrained_columns) == 1:
                rel_name = referred_table.lower()
                if not rel_name.endswith('s'):
                    rel_name += 's'  # Pluralize
            else:
                rel_name = f"{referred_table.lower()}_by_{'_and_'.join(constrained_columns)}"
            
            # Determine if the relationship is singular (1:1 or many:1)
            # This is a simplification - in a real implementation you'd need to analyze the constraints
            singular = False  # Default to many:many
            
            # Create the simple_join property
            join_property = {
                "type": "simple_join",
                "other_collection_name": referred_table,
                "singular": singular,
                "no_collisions": not singular,  # Simplified assumption
                "keys": {col: [ref_col] for col, ref_col in zip(constrained_columns, referred_columns)},
                "reverse_relationship_name": f"{table_name.lower()}_by_{'_and_'.join(referred_columns)}"
            }
            
            # Add the property to the current table's properties
            if table_name in self.metadata["Graph"]:
                self.metadata["Graph"][table_name]["properties"][rel_name] = join_property
    
    def generate_metadata(self) -> Dict[str, Any]:
        """
        Generate the PyDough metadata JSON structure.
        
        Returns:
            Dictionary containing the PyDough metadata
        """
        return self.metadata
    
    def save_to_file(self, file_path: str) -> None:
        """
        Save the generated metadata to a JSON file.
        
        Args:
            file_path: Path to the output JSON file
        """
        with open(file_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)

# Example usage
if __name__ == "__main__":
    # Replace with your actual database URI
    DB_URI = "sqlite:///TPCH.db"
    
    # Create converter and analyze database
    converter = SQLToPyDoughConverter(DB_URI)
    converter.analyze_database()
    
    # Generate and print metadata
    metadata = converter.generate_metadata()
    print(json.dumps(metadata, indent=2))
    
    # Save to file
    converter.save_to_file("pydough_metadata.json")