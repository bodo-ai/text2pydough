import pandas as pd
import os
import sqlite3 as sql

# Mapping configuration for db_name to SQLite files
def process_csv(input_csv_path, output_csv_path, db_base_path):
    # Read the CSV file
    data = pd.read_csv(input_csv_path)

    # Verify that the required columns are present
    required_columns = {"question", "sql", "db_name"}
    if not required_columns.issubset(data.columns):
        raise ValueError(f"The CSV file must contain the columns: {', '.join(required_columns)}")

    # Copy original data and initialize new columns
    data["ground_truth_json"] = None
    data["sql_error"] = None

    for index, row in data.iterrows():
        question = row["question"]
        sql_query = row["sql"]
        db_name = row["db_name"]

        db_path = os.path.join(db_base_path, f"{db_name}.db")

        # Connect to the database
        try:
            with sql.connect(db_path) as connection:
                # Execute the query
                df = pd.read_sql_query(sql_query, connection)

                # Convert results to JSON (empty JSON if no results)
                ground_truth_json = df.to_json(orient="records", date_format="iso") if not df.empty else "[]"
                sql_error = None

        except Exception as e:
            ground_truth_json = None
            sql_error = str(e)

        # Update the new columns in the DataFrame
        data.at[index, "ground_truth_json"] = ground_truth_json
        data.at[index, "sql_error"] = sql_error

    # Save the updated DataFrame to a CSV file
    data.to_csv(output_csv_path, index=False)

def main():
    input_csv_path = "Corrected_questions_Gerald_7_4.csv"  # Input CSV file path
    output_csv_path = "Corrected_questions_Gerald_7_4_gtj.csv"  # Output CSV file path
    db_base_path = "./test_data/databases/Defog/"  # Base folder where the databases are located

    # Process the CSV
    process_csv(input_csv_path, output_csv_path, db_base_path)

if __name__ == "__main__":
    main()
