#%%
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv
from utils import autocommit, get_git_commit, modified_files, untracked_files, download_database
from dynamic_prompt.generate_pydough_metadata import generate_metadata
from dynamic_prompt.mdgen_v2 import json_to_markdown
env_path = Path.home() / ".env"
env = load_dotenv(dotenv_path=env_path)
import pandas as pd
from pathlib import Path
import dspy
import json
#%%


def prepare_db_markdown_map(df, metadata_base_path, db_base_path):
    db_names = df["db_name"]
    dataset_names = df["dataset_name"]
    db_markdown_map = {}
    for db_name, dataset_name in zip(db_names, dataset_names):
        json_file = os.path.join(metadata_base_path, dataset_name, "metadata", f"{db_name}_graph.json")
        # Only generate if missing
        if not os.path.exists(json_file):
            print(f"[INFO] Generating JSON for: {db_name}")
            url = f"sqlite:///{os.path.join(db_base_path, dataset_name, 'databases', db_name, f'{db_name}.sqlite')}"
            print("DB URL:", url)
            engine = create_engine(url)
            md= generate_metadata(engine,db_name)
            with open(json_file, "w") as f:
                json.dump(md, f, indent=2)

        if db_name not in db_markdown_map:
            with open(json_file, "r") as f:
                data = json.load(f)
                db_markdown_map[db_name] ={
                    "metadata": data,
                    "json_file_path": json_file}

    return db_markdown_map



class Text2Pydough(dspy.Signature):
    """Based on database query described in English, use the context and schema to generate pydough code."""

    query: str = dspy.InputField(desc="Contains the english query")
    context: str = dspy.InputField(desc="Contains a reference description of the pydough language")
    db_schema: str = dspy.InputField(desc="Contains the schema of the database")
    answer: str = dspy.OutputField(desc="Contains the pydough code that will execute the query")


lm = dspy.LM('gemini/gemini-2.5-pro',  api_key=os.getenv("GOOGLE_API_KEY_1"), temperature=0, max_tokens=3000, cache=True)
qa = dspy.ChainOfThought(Text2Pydough)

#%%
df = pd.read_csv("corrected_questions.csv")
defog = "/home/amuller/dataset/"
md_map = prepare_db_markdown_map(df, defog, defog)

#%%
# read query file

context = Path("cheatsheet_8_1.md").read_text()

for i, row in df.iterrows():
    query = row["question"]
    db_name = row["db_name"]
    assert db_name in md_map, f"{db_name} not in {md_map.keys()}"
    schema = json_to_markdown(md_map[db_name]["metadata"])

    with dspy.context(lm=lm):
        response = qa(query=query, context=context, db_schema=schema )
        print("Query: ", query)
        print("Response: " , response.answer)
        # generated result
        # now we have to validate it by executing the generated pydough code

    break

#%%

# %%
