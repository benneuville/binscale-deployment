# process_output.py
import sys
import pandas as pd

# Read the CSV file
df = pd.read_csv(sys.argv[1], quotechar='"')
df.columns = df.columns.str.strip('"')

# Check if the initial DataFrame is empty
if df.empty:
    print("Input CSV file is empty.")
else:
    # Filter the data
    filtered_df = df[df['message'].str.contains("latency is", na=False) & df['kubernetes.pod.name'].str.contains("latency-")]

    # Check if the filtered DataFrame is empty
    if filtered_df.empty:
        print("No matching data found.")
    else:
        # Save the filtered DataFrame to a specific CSV file
        filtered_df.to_csv('python/input/result.csv', index=False)
        print("Filtered data saved to 'result.csv'.")

print(df.head())
