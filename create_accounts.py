import pandas as pd


df = pd.read_csv('./Villages.csv')

# Get the unique district names
districts = df['New District Name'].unique()


print("Unique Districts:")
for district in districts:
    print(district)


# Verify that no two districts have the same name
if len(districts) != len(set(districts)):
    print("Error: Duplicate district names found!")
else:
    print("No duplicate district names found.")