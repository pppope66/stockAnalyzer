import pandas as pd
import argparse
import os
import sys
import re

def detect_interval(filename):
    """
    Detect the interval type from the filename
    
    Args:
        filename (str): Input filename
        
    Returns:
        tuple: (interval_type, interval_column_name, interval_display_name)
    """
    filename_lower = filename.lower()
    
    if 'daily' in filename_lower:
        return ('daily', 'IntervalCount', 'days')
    elif 'weekly' in filename_lower:
        return ('weekly', 'IntervalCount', 'weeks')
    else:
        # Default to monthly if not specified or if "monthly" is in the name
        return ('monthly', 'IntervalCount', 'months')

def merge_price_candles(input_file):
    """
    Merge adjacent price candles of the same color from CSV input
    
    Args:
        input_file (str): Path to input CSV file
        
    Returns:
        DataFrame: Merged candle data with consecutive trends combined
    """
    try:
        # Check if input file exists
        if not os.path.exists(input_file):
            print(f"Error: Input file '{input_file}' not found!")
            return None
            
        # Detect interval from filename
        interval_type, interval_column, interval_display = detect_interval(input_file)
        print(f"Detected interval type: {interval_type}")
            
        # Read the CSV file
        print(f"Reading input file: {input_file}")
        df = pd.read_csv(input_file)
        
        # Check if the column is Month_Count (old format) or IntervalCount (new format)
        count_column = 'Month_Count' if 'Month_Count' in df.columns else 'IntervalCount'
        
        # Convert numeric columns to float
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Percent_Change', count_column]
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col])
        
        # Initialize lists to store merged candle data
        merged_candles = []
        current_group = {
            'Date': df.iloc[0]['Date'],
            'Open': df.iloc[0]['Open'],
            'High': df.iloc[0]['High'],
            'Low': df.iloc[0]['Low'],
            'Close': df.iloc[0]['Close'],
            'Color': df.iloc[0]['Color'],
            interval_column: df.iloc[0][count_column]
        }

        # Merge adjacent candles of same color
        for i in range(1, len(df)):
            if df.iloc[i]['Color'] == current_group['Color']:
                # Update High and Low for the merged candle
                current_group['High'] = max(current_group['High'], df.iloc[i]['High'])
                current_group['Low'] = min(current_group['Low'], df.iloc[i]['Low'])
                current_group['Close'] = df.iloc[i]['Close']  # Update to latest close
                current_group[interval_column] += df.iloc[i][count_column]
            else:
                # Calculate percent change for the current group
                if current_group['Color'] == 'green':
                    current_group['Percent_Change'] = round(
                        (current_group['High'] - current_group['Open']) / current_group['Open'] * 100, 2
                    )
                else:
                    current_group['Percent_Change'] = round(
                        (current_group['Low'] - current_group['Open']) / current_group['Open'] * 100, 2
                    )
                
                # Add current group to merged candles
                merged_candles.append(current_group)
                
                # Start new group
                current_group = {
                    'Date': df.iloc[i]['Date'],
                    'Open': df.iloc[i]['Open'],
                    'High': df.iloc[i]['High'],
                    'Low': df.iloc[i]['Low'],
                    'Close': df.iloc[i]['Close'],
                    'Color': df.iloc[i]['Color'],
                    interval_column: df.iloc[i][count_column]
                }

        # Add the last group
        if current_group['Color'] == 'green':
            current_group['Percent_Change'] = round(
                (current_group['High'] - current_group['Open']) / current_group['Open'] * 100, 2
            )
        else:
            current_group['Percent_Change'] = round(
                (current_group['Low'] - current_group['Open']) / current_group['Open'] * 100, 2
            )
        merged_candles.append(current_group)

        # Convert merged candles to DataFrame
        result = pd.DataFrame(merged_candles)
        
        # Round numeric columns
        result = result.round(2)
        
        return result, interval_type, interval_display
        
    except Exception as e:
        print(f"Error in merge_price_candles: {e}")
        return None, None, None

def get_output_filename(input_file):
    """Generate appropriate output filename based on input filename"""
    base, ext = os.path.splitext(input_file)
    if '_merged' in base:
        # If input already has '_merged', don't add it again
        return input_file
    else:
        return f"{base}_merged{ext}"

if __name__ == "__main__":
    try:
        # Example commands:
        # Basic usage with explicit input file:
        #    python month2.py --input spy_monthly_candles_2007_2025.csv
        #    python month2.py -i spy_weekly_candles_2010_2023.csv
        #    python month2.py -i aapl_daily_candles_2022_2023.csv
        # 
        # Specify output file (optional):
        #    python month2.py -i aapl_monthly_candles_2010_2023.csv -o aapl_merged.csv
        
        # Set up argument parser
        parser = argparse.ArgumentParser(description='Merge adjacent price candles of the same color')
        parser.add_argument('--input', '-i', required=True, help='Input CSV file path')
        parser.add_argument('--output', '-o', help='Output CSV file path (optional, will be auto-generated if not provided)')
        
        args = parser.parse_args()
        
        # Merge the candles
        merged_data, interval_type, interval_display = merge_price_candles(args.input)
        
        if merged_data is None:
            print("Failed to merge candles")
            sys.exit(1)
            
        # Determine output filename
        output_file = args.output if args.output else get_output_filename(args.input)
        
        # Save merged data to new CSV
        merged_data.to_csv(output_file, index=False)
        print(f"Merged data saved to {output_file}")
        
        # Get the interval column name
        interval_column = 'IntervalCount'
        
        # Print summary statistics
        print(f"\nTotal merged candles: {len(merged_data)}")
        green_candles = merged_data.loc[merged_data['Color'] == 'green']
        red_candles = merged_data.loc[merged_data['Color'] == 'red']
        print(f"Green trends: {len(green_candles)}")
        print(f"Red trends: {len(red_candles)}")
        print(f"Average {interval_display} in green trends: {green_candles[interval_column].mean():.1f}")
        print(f"Average {interval_display} in red trends: {red_candles[interval_column].mean():.1f}")
        
        # Print longest trends
        print(f"\nLongest green trend: {int(green_candles[interval_column].max())} {interval_display}")
        print(f"Longest red trend: {int(red_candles[interval_column].max())} {interval_display}")
        
    except Exception as e:
        print(f"Error: {e}") 