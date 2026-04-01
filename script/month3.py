import pandas as pd
import os
import sys
import argparse
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

def merge_candles_with_percentage(input_file, threshold):
    """
    Merge candles based on color and percentage threshold
    Merges if:
    1. Adjacent candles have same color, OR
    2. Current candle has |%| > threshold% and next candle has |%| < threshold%
    
    Args:
        input_file (str): Path to input CSV file (required)
        threshold (float): Percentage threshold for merging (0-100)
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
        print(f"Read {len(df)} rows from input file")
        print(f"Using threshold: {threshold}%")
        
        # Check if the column is Month_Count (old format) or IntervalCount (new format)
        count_column = 'Month_Count' if 'Month_Count' in df.columns else 'IntervalCount'
        
        # Convert numeric columns to float
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Percent_Change', count_column]
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col])

        # Initialize list for merged candles
        merged_candles = []
        i = 0
        
        while i < len(df):
            current_group = {
                'Date': df.iloc[i]['Date'],
                'Open': df.iloc[i]['Open'],
                'High': df.iloc[i]['High'],
                'Low': df.iloc[i]['Low'],
                'Close': df.iloc[i]['Close'],
                'Color': df.iloc[i]['Color'],
                'Percent_Change': df.iloc[i]['Percent_Change'],
                interval_column: df.iloc[i][count_column]
            }
            
            while i + 1 < len(df):
                current_pct = abs(current_group['Percent_Change'])
                next_pct = abs(df.iloc[i + 1]['Percent_Change'])
                
                # Check merge conditions
                should_merge = (
                    df.iloc[i + 1]['Color'] == current_group['Color'] or
                    (current_pct > threshold and next_pct < threshold)
                )
                
                if should_merge:
                    # Update High and Low
                    current_group['High'] = max(current_group['High'], df.iloc[i + 1]['High'])
                    current_group['Low'] = min(current_group['Low'], df.iloc[i + 1]['Low'])
                    current_group['Close'] = df.iloc[i + 1]['Close']  # Take latest close
                    current_group[interval_column] += df.iloc[i + 1][count_column]
                    
                    # Recalculate percent change
                    if current_group['Color'] == 'green':
                        current_group['Percent_Change'] = round(
                            (current_group['High'] - current_group['Open']) / current_group['Open'] * 100, 2
                        )
                    else:
                        current_group['Percent_Change'] = round(
                            (current_group['Low'] - current_group['Open']) / current_group['Open'] * 100, 2
                        )
                    
                    i += 1  # Move to next row
                else:
                    break
            
            merged_candles.append(current_group)
            i += 1
        
        # Convert to DataFrame
        result = pd.DataFrame(merged_candles)
        
        # Create output filename based on input filename
        base, ext = os.path.splitext(input_file)
        if '_merged_v2' in base:
            output_file = f"{base}{ext}"  # Keep the same name if already has _merged_v2
        else:
            output_file = f"{base}_merged_v2{ext}"
        
        # Save to new CSV
        result.to_csv(output_file, index=False)
        print(f"\nSaved merged data to {output_file}")
        
        # Print summary statistics with appropriate interval name
        print(f"\nTotal merged candles: {len(result)}")
        green_candles = result.loc[result['Color'] == 'green']
        red_candles = result.loc[result['Color'] == 'red']
        print(f"Green trends: {len(green_candles)}")
        print(f"Red trends: {len(red_candles)}")
        print(f"Average {interval_display} in green trends: {green_candles[interval_column].mean():.1f}")
        print(f"Average {interval_display} in red trends: {red_candles[interval_column].mean():.1f}")
        print(f"Longest green trend: {int(green_candles[interval_column].max())} {interval_display}")
        print(f"Longest red trend: {int(red_candles[interval_column].max())} {interval_display}")
        
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    # Example commands:
    # Required input file and threshold:
    #    python month3.py -i spy_monthly_candles_merged_2007_2025.csv -t 6
    #    python month3.py --input aapl_weekly_candles_2010_2023.csv --threshold 8
    #    python month3.py --input msft_daily_candles_2022_2023.csv --threshold 5
    
    parser = argparse.ArgumentParser(description='Merge candles based on color and percentage threshold')
    parser.add_argument('--input', '-i', required=True, help='Input CSV file path (required)')
    parser.add_argument('--threshold', '-t', type=float, required=True, 
                        help='Percentage threshold for merging (0-100)')
    
    args = parser.parse_args()
    
    if not args.input:
        print("Error: Input file is required")
        parser.print_help()
        sys.exit(1)
    
    # Validate threshold is within range
    if args.threshold < 0 or args.threshold > 100:
        print("Error: Threshold must be between 0 and 100")
        parser.print_help()
        sys.exit(1)
    
    merge_candles_with_percentage(args.input, args.threshold) 