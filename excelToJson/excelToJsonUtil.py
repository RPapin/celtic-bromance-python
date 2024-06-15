import pandas as pd
import json

# Read the Excel file into a pandas DataFrame
excel_file_path = 'RP.xlsx'
df = pd.read_excel(excel_file_path)

# Define the new column names
new_column_names = {
    'Steam id64 (17 digits)': 'Steam id ',
    'First name / Prénom': 'First name',
    'Surname / Nom': 'Surname',
    'Race number / Numéro de course ': 'Race number',
    'Nationality / Nationalité': 'Nationality'
}
# Rename the columns in the DataFrame
df.rename(columns=new_column_names, inplace=True)
# Add new columns with fixed data
df = df.assign(
    available=True,
    isConnected=False,
    swapCar=2,
    teamWith=1,
    isAdmin=False,
    teamWithVictim=1
)
# Convert the DataFrame to a dictionary
data_dict = df.to_dict(orient='records')

# Convert the dictionary to a JSON string
json_data = json.dumps(data_dict, indent=4, ensure_ascii=False)

# Write the JSON string to a file
json_file_path = 'output.json'
with open(json_file_path, 'w', encoding='utf-8') as json_file:
    json_file.write(json_data)

print("Excel file has been successfully converted to JSON format and saved as", json_file_path)