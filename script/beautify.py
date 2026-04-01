import pandas as pd
import os
import sys

def beautify_output(input_file, output_file):
    """
    Read merged candle data and create a beautified tab-separated output
    
    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output text file
    """
    try:
        # Check if input file exists
        if not os.path.exists(input_file):
            print(f"Error: Input file '{input_file}' not found!")
            return
            
        # Read the CSV file
        print(f"Reading input file: {input_file}")
        df = pd.read_csv(input_file)
        print(f"Read {len(df)} rows from input file")
        
        # Convert numeric columns to float for proper formatting
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Percent_Change', 'Month_Count']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col])
        
        # Format the date column
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        
        # Create header string
        header = "Date\tOpen\tHigh\tLow\tClose\tColor\t%Change\tMonths"
        
        # Create the output file
        print(f"Creating output file: {output_file}")
        with open(output_file, 'w') as f:
            # Write header
            f.write(header + '\n')
            f.write('-' * 80 + '\n')  # Separator line
            
            # Write each row
            for _, row in df.iterrows():
                formatted_row = (
                    f"{row['Date']}\t"
                    f"{row['Open']:,.2f}\t"
                    f"{row['High']:,.2f}\t"
                    f"{row['Low']:,.2f}\t"
                    f"{row['Close']:,.2f}\t"
                    f"{row['Color']:<5}\t"
                    f"{row['Percent_Change']:+.2f}%\t"
                    f"{int(row['Month_Count'])}"
                )
                f.write(formatted_row + '\n')
            
            # Write summary statistics
            f.write('\n' + '-' * 80 + '\n')
            f.write("Summary Statistics:\n")
            f.write(f"Total Trends: {len(df)}\n")
            
            green_trends = df[df['Color'] == 'green']
            red_trends = df[df['Color'] == 'red']
            
            f.write(f"Green Trends: {len(green_trends)}\n")
            f.write(f"Red Trends: {len(red_trends)}\n")
            f.write(f"Average Green Trend Duration: {green_trends['Month_Count'].mean():.1f} months\n")
            f.write(f"Average Red Trend Duration: {red_trends['Month_Count'].mean():.1f} months\n")
            f.write(f"Longest Green Trend: {int(green_trends['Month_Count'].max())} months\n")
            f.write(f"Longest Red Trend: {int(red_trends['Month_Count'].max())} months\n")
            
        print(f"Beautified output saved to {output_file}")
        
        # Print the first few lines as preview
        print("\nPreview of formatted output:")
        with open(output_file, 'r') as f:
            for i, line in enumerate(f):
                if i < 5:  # Print first 5 lines
                    print(line.rstrip())
                else:
                    break
            
    except Exception as e:
        print(f"Error: {e}")

def print_usage():
    print("Usage: python beautify.py <input_file> <output_file>")
    print("Example: python beautify.py spy_monthly_candles_merged_2007_2025.csv spy_trends.txt")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Error: Incorrect number of arguments")
        print_usage()
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    beautify_output(input_file, output_file) 