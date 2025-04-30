# %%

import pandas as pd
import numpy as np

column_names = ['question','sql','db_name','response','execution_time','extracted_python_code','usage','comparison_result','exception']
columns_to_eval = ['extracted_python_code', 'comparison_result', 'exception']

baseline = pd.read_csv('defog_baseline.csv')
new_run = pd.read_csv('defog_new.csv')

baseline_array = np.array(baseline)
new_array = np.array(new_run)

df_baseline = pd.DataFrame(baseline_array, columns=column_names)
df_new_run = pd.DataFrame(new_array, columns=column_names)

df_baseline.index += 1
df_new_run.index += 1


for i in column_names:
    df_baseline[i] = df_baseline[i].fillna("NaN")
    df_new_run[i] = df_new_run[i].fillna("NaN")

df_result = df_baseline.eq(df_new_run)

df_result = df_result[columns_to_eval]

equal_rows = df_result[(( df_result.comparison_result == True) & (df_result.exception == True))].index
df_result.drop(equal_rows, axis='index', inplace=True)

filter_rows_by_values(df_result, columns_to_eval, 'True')

df_result.to_csv('comparison_result.csv')

# %%
