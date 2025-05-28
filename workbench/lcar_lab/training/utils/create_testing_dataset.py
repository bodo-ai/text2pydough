import argparse
import math
import pandas as pd

# Read CSV file
def load_csv(file_path):
    df = pd.read_csv(file_path)
    return df


# Function to create a testing dataset
def create_testing_dataset(df):
    # 1. Conjuntos de entrenamiento y tamaño de test
    training_df = df[df["dataframe_match"] == True]
    test_size = int(len(training_df) * 0.15)
    print(f"Creating testing dataset with size: {test_size}")

    # 2. Split de entrenamiento por dataset
    spider_train = training_df[training_df["dataset_name"] == "spider_data"]
    kaggle_train = training_df[training_df["dataset_name"] == "kaggleDBQA"]

    # 3. Asignar test_size a cada dataset
    total_train = len(training_df)
    spider_test_size = round(test_size * len(spider_train) / total_train)
    kaggle_test_size = test_size - spider_test_size
    print(f" - spider_data test size: {spider_test_size}")
    print(f" - kaggleDBQA   test size: {kaggle_test_size}")

    # 4. Candidatos
    testing_df = df[df["dataframe_match"] == False]

    def sample_db_and_difficulty(train_subset, test_subset, target_n, min_count=30):
        # 4.1. Filtrar dbs con suficiente tamaño
        db_counts = train_subset["db_name"].value_counts()
        valid_dbs = db_counts[db_counts > min_count].index.tolist()
        if not valid_dbs:
            return pd.DataFrame([], columns=test_subset.columns)

        # 4.2. Proporción raw por db
        raw_db = {db: target_n * (db_counts[db] / db_counts.loc[valid_dbs].sum())
                  for db in valid_dbs}
        floor_db = {db: math.floor(cnt) for db, cnt in raw_db.items()}

        # 4.3. Ajuste residuales db
        rem_db = target_n - sum(floor_db.values())
        resid_db = {db: raw_db[db] - floor_db[db] for db in valid_dbs}
        for db, _ in sorted(resid_db.items(), key=lambda x: x[1], reverse=True)[:rem_db]:
            floor_db[db] += 1

        # 4.4. Para cada db, repartir por difficulty
        pieces = []
        for db, n_db in floor_db.items():
            if n_db <= 0:
                continue
            # subset de entrenamiento y test para esta db
            train_db = train_subset[train_subset["db_name"] == db]
            test_db  = test_subset[test_subset["db_name"] == db]

            # 4.4.1. proporciones de difficulty dentro de esta db
            diff_counts = train_db["difficulty"].value_counts()
            diffs = diff_counts.index.tolist()
            raw_diff = {d: n_db * (diff_counts[d] / diff_counts.sum()) for d in diffs}
            floor_diff = {d: math.floor(c) for d, c in raw_diff.items()}

            # 4.4.2. ajustar residuales difficulty
            rem_diff = n_db - sum(floor_diff.values())
            resid_diff = {d: raw_diff[d] - floor_diff[d] for d in diffs}
            for d, _ in sorted(resid_diff.items(), key=lambda x: x[1], reverse=True)[:rem_diff]:
                floor_diff[d] += 1

            # 4.4.3. muestreo por difficulty
            for d, n_d in floor_diff.items():
                if n_d <= 0:
                    continue
                candidate = test_db[test_db["difficulty"] == d]
                take = min(n_d, len(candidate))
                if take > 0:
                    pieces.append(candidate.sample(n=take, random_state=42))

        return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame([], columns=test_subset.columns)

    # 5. Sample para cada dataset
    spider_test = sample_db_and_difficulty(
        spider_train,
        testing_df[testing_df["dataset_name"] == "spider_data"],
        spider_test_size,
        min_count=30
    )
    kaggle_test = sample_db_and_difficulty(
        kaggle_train,
        testing_df[testing_df["dataset_name"] == "kaggleDBQA"],
        kaggle_test_size,
        min_count=30
    )

    # 6. Unión final
    final_test = pd.concat([spider_test, kaggle_test], ignore_index=True)
    print(f"Final testing dataset size: {len(final_test)}")
    return final_test


# Save the DataFrame to a CSV file
def save_to_csv(df, output_path):
    reformatted_questions = df \
        .rename(columns={'ground_truth_sql': 'sql'}) \
        .to_dict(orient='records')
        
    final_csv = pd.DataFrame(reformatted_questions)

    final_csv.to_csv(output_path, index=False)

# Example usage
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_csv')
    parser.add_argument('output_csv')
    args = parser.parse_args()

    df = load_csv(args.input_csv)

    testing_dataset = create_testing_dataset(df)
    save_to_csv(testing_dataset, args.output_csv)