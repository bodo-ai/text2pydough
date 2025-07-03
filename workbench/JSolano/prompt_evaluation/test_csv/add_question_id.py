import csv

input_file = 'corrected_questions_ArGer.csv'
output_file = 'corrected_questions_ArGer_with_id.csv'

with open(input_file, 'r', newline='', encoding='utf-8') as infile, open(output_file, 'w', newline='', encoding='utf-8') as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)
    
    header = next(reader)
    # Insert 'question_id' as the first column
    new_header = ['question_id'] + header
    writer.writerow(new_header)
    
    for idx, row in enumerate(reader, start=1):
        new_row = [idx] + row
        writer.writerow(new_row) 