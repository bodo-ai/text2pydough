# How to Generate Metadata with the Scripts

This guide explains how to configure credentials and run the scripts to generate metadata (JSON and Markdown) for different databases.

---

## 1. Configure `creds.json`

Before running the scripts, configure the `creds.json` file with the required database credentials.  
Each top-level key (e.g., `"example"`) represents a user or namespace, and within it each project corresponds to a database.  
An example is provided for the three currently supported engines: **SQLite, MySQL, and Snowflake**.

**Important:**  
Update `json_path` and `md_path` with the correct output paths and de `bd_name` or "path" for the sqlite db.
It is recommended to place them in the same directory as the scripts.

```json
{
  "example": {
    "tpch": {
      "engine": "sqlite",
      "db_name": "/my/path/to/graph/database/tpch.db",
      "graph_name": "tpch",
      "json_path": "/my/path/to/graph/tpch_graph.json",
      "md_path": "/my/path/to/graph/tpch.md"
    }
  }
}
```

## 2. Prepare the Environment

Before running the scripts, ensure you have the required dependencies.  
Use `generator-env.yaml` file to create the environment easily.

### Create the Conda environment  
```bash
conda env create -f generator-env.yaml
```
### Activate the environment  
```bash
conda activate generator-env
```

Alternatively, install the specific dependencies manually if preferred or with the `requirements.txt`.

## 3. Generate the Metadata

The process has two steps:

- Generate the JSON file.  
- Generate the Markdown file.

### 3.1 Generate the JSON

Use the following command:

```bash
python generate_json.py --user <user> --project <project_name>

<user>: the name of the main dictionary in creds.json (eg., "example").

<project_name>: the project name assigned to that user (eg., "tpch").
```

#### 3.1.1 Table selection

During execution, you will be prompted to select the tables you want to include.  
This can be done by table names or by their index in the list (starting from 1).

#### 3.1.2 Recommendations before generating

Ensure the target database has properly defined Primary Keys (PKs) and Foreign Keys (FKs).  
After generation, verify that each collection has the correct unique properties.  
Validate the relationships created, ensuring the correctness of singular and always matches values, or manually add them and the relationships if not inferred.

### 3.2 Generate the Markdown

Once the JSON is created, run:

```bash
python generate_md.py --user <user> --project <project_name>
```

#### 3.2.1 Recommendations before generating

Fill in additional json first (descriptions, synonyms, etc.).  
If this is not done, the script will generate only the basic structure and won’t include extra information that could be useful for an LLM.
