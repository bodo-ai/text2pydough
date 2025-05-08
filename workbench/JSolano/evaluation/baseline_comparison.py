# %%

import pandas as pd
import numpy as np

column_names_old = ['question','sql','db_name','response','execution_time','extracted_python_code','usage','comparison_result','exception']
column_names_new = ['question_new','sql_new','db_name_new','response_new','execution_time_new','extracted_python_code_new','usage_new','comparison_result_new','exception_new']
columns_to_eval = ['comparison_result', 'exception']

baseline = pd.read_csv('defog_baseline.csv')
new_run = pd.read_csv('test_execution_2025_05_02-13_56_18.csv')

baseline_array = np.array(baseline)
new_array = np.array(new_run)

df_baseline = pd.DataFrame(baseline_array, columns=column_names_old)
df_new_run = pd.DataFrame(new_array, columns=column_names_old)

df_new_run.columns = column_names_new

df_baseline.index += 1
df_new_run.index += 1


for i in column_names_old:
    df_baseline[i] = df_baseline[i].fillna("NaN")
for i in column_names_new:
    df_new_run[i] = df_new_run[i].fillna("NaN")

df = pd.concat([df_baseline, df_new_run], axis=1)

df['changed'] = ((df['comparison_result'] != df['comparison_result_new']) 
                        | (df['exception'].str.split().str[0] != df['exception_new'].str.split().str[0]))

df['change_reason'] = np.where(df['changed']==True & (df['comparison_result'] != df['comparison_result_new']), 'DataFrame match changed from' + df['comparison_result'] + 'to' + df['comparison_result_new'], '')

df.to_csv('comparison_result.csv')

# %%
