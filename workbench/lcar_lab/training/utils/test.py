import pandas as pd
import random

# 1. Leer el CSV a un DataFrame
def load_csv(file_path):
    df = pd.read_csv(file_path)
    return df

# 2. Crear un DataFrame filtrado
def filter_dataframe(df):
    filtered_df = df[(df['dataframe_match'] == True) & (df['dataset_name'] == 'spider_data')]
    return filtered_df

# 3. Obtener valores únicos para las columnas específicas
def get_unique_values(filtered_df):
    unique_db_names = filtered_df['db_name'].unique()
    unique_difficulties = filtered_df['difficulty'].unique()
    unique_complexities = filtered_df['complexity'].unique()
    return unique_db_names, unique_difficulties, unique_complexities

# 4. Crear el DataFrame '500_spider_test'
def create_500_spider_test(df, unique_db_names, unique_difficulties, unique_complexities):
    # Filtrar por condiciones iniciales
    spider_test_df = df[(df['dataframe_match'] == False) & (df['dataset_name'] == 'spider_data')]

    # Aplicar filtros únicos (simular un filtrado aleatorio para cumplir con el requisito de 500 filas)
    filtered_spider_test = spider_test_df[
        (spider_test_df['db_name'].isin(unique_db_names)) &
        (spider_test_df['difficulty'].isin(unique_difficulties)) &
        (spider_test_df['complexity'].isin(unique_complexities))
    ]

    # Seleccionar 500 filas al azar si hay más de 500, o todas si hay menos
    selected_rows = filtered_spider_test.sample(n=min(500, len(filtered_spider_test)), random_state=42)
    return selected_rows

# 5. Función para guardar un DataFrame a un CSV
def save_to_csv(df, output_path):
    reformatted_questions = df[['question', 'ground_truth_sql', 'dataset_name', 'db_name']] \
        .rename(columns={'ground_truth_sql': 'sql'}) \
        .to_dict(orient='records')
        
    final_csv = pd.DataFrame(reformatted_questions)

    final_csv.to_csv(output_path, index=False)

# Uso de las funciones
file_path = '/home/gerald8525/repositories/mount-folder/datasets/Finetuning/labeling/labeled_data/spider/training_ready/labeled_training_data_with_schema_133702.csv'
output_path = '/home/gerald8525/repositories/output.csv'
df = load_csv(file_path)

filtered_df = filter_dataframe(df)
unique_db_names, unique_difficulties, unique_complexities = get_unique_values(filtered_df)
print(f"Unique DB names: {unique_db_names}")
print(f"Unique difficulties: {unique_difficulties}")    
print(f"Unique complexities: {unique_complexities}")

spider_test_df = create_500_spider_test(df, unique_db_names, unique_difficulties, unique_complexities)
save_to_csv(spider_test_df, output_path)