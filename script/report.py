import pandas as pd
import os
import sys
import numpy as np
from datetime import datetime
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

def generate_market_report(input_file, output_file=None):
    """
    Generate a detailed analysis report from the market trend data
    
    Args:
        input_file (str): Path to input CSV file
        output_file (str, optional): Path to output report file. If None, will use input name with .report extension
    
    Returns:
        str: Path to the generated report file
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
        
        ticker = input_file.split('_')[0]

        # Check if the column is Month_Count (old format) or IntervalCount (new format)
        count_column = 'Month_Count' if 'Month_Count' in df.columns else 'IntervalCount'
        
        # Convert numeric columns to float
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Percent_Change', count_column]
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col])
        
        # Determine output filename if not provided
        if output_file is None:
            output_file = os.path.splitext(input_file)[0] + '.report'
        
        print(f"Generating report: {output_file}")
        
        # Filter data for analysis
        green_trends = df[df['Color'] == 'green']
        red_trends = df[df['Color'] == 'red']
        
        # Calculate total intervals
        total_intervals = df[count_column].sum()
        green_intervals = green_trends[count_column].sum()
        red_intervals = red_trends[count_column].sum()
        
        # Calculate performance metrics
        avg_green_pct = green_trends['Percent_Change'].mean()
        avg_red_pct = red_trends['Percent_Change'].mean()
        avg_all_pct = df['Percent_Change'].mean()
        
        # Calculate interval performance
        # Weighted average based on interval count
        interval_return = (df['Percent_Change'] * df[count_column]).sum() / total_intervals
        
        # Calculate trend duration metrics
        median_trend_length = df[count_column].median()
        median_green_length = green_trends[count_column].median() if len(green_trends) > 0 else 0
        median_red_length = red_trends[count_column].median() if len(red_trends) > 0 else 0
        
        # Create trend length distribution
        length_bins = [(1, 3), (4, 6), (7, 12), (13, 24), (25, float('inf'))]
        length_distribution = {}
        
        for low, high in length_bins:
            bin_name = f"{low}-{high if high != float('inf') else '+'}"
            count = len(df[(df[count_column] >= low) & (df[count_column] <= high)])
            length_distribution[bin_name] = count
        
        # Generate correlation between length and percentage
        correlation = df[[count_column, 'Percent_Change']].corr().iloc[0, 1]
        
        # Write the report
        with open(output_file, 'w') as report:
            report.write(f"=== {ticker} Market Trend Analysis Report ===\n")
            report.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            report.write(f"Data source: {input_file}\n")
            report.write(f"Analysis period: {df.iloc[0]['Date']} to {df.iloc[-1]['Date']}\n")
            report.write(f"Interval type: {interval_type}\n\n")
            
            # Basic Statistics
            report.write("=== Basic Statistics ===\n")
            report.write(f"Total trends identified: {len(df)}\n")
            report.write(f"Upward trends (green): {len(green_trends)}\n")
            report.write(f"Downward trends (red): {len(red_trends)}\n")
            report.write(f"Total {interval_display} analyzed: {total_intervals}\n")
            report.write(f"{interval_display.capitalize()} in uptrends: {green_intervals} ({green_intervals/total_intervals*100:.1f}%)\n")
            report.write(f"{interval_display.capitalize()} in downtrends: {red_intervals} ({red_intervals/total_intervals*100:.1f}%)\n\n")
            
            # Duration Statistics
            report.write("=== Duration Statistics ===\n")
            report.write(f"Average trend duration: {df[count_column].mean():.1f} {interval_display}\n")
            report.write(f"Median trend duration: {median_trend_length:.1f} {interval_display}\n")
            report.write(f"Average uptrend duration: {green_trends[count_column].mean():.1f} {interval_display}\n")
            report.write(f"Median uptrend duration: {median_green_length:.1f} {interval_display}\n")
            report.write(f"Average downtrend duration: {red_trends[count_column].mean():.1f} {interval_display}\n")
            report.write(f"Median downtrend duration: {median_red_length:.1f} {interval_display}\n")
            report.write(f"Longest uptrend: {green_trends[count_column].max() if len(green_trends) > 0 else 0} {interval_display}\n")
            report.write(f"Longest downtrend: {red_trends[count_column].max() if len(red_trends) > 0 else 0} {interval_display}\n\n")
            
            # Performance Statistics
            report.write("=== Performance Statistics ===\n")
            report.write(f"Average percentage change (all trends): {avg_all_pct:.2f}%\n")
            report.write(f"Average percentage change (uptrends): +{avg_green_pct:.2f}%\n")
            report.write(f"Average percentage change (downtrends): {avg_red_pct:.2f}%\n")
            report.write(f"Maximum uptrend gain: +{green_trends['Percent_Change'].max() if len(green_trends) > 0 else 0:.2f}%\n")
            report.write(f"Maximum downtrend loss: {red_trends['Percent_Change'].min() if len(red_trends) > 0 else 0:.2f}%\n")
            report.write(f"Average {interval_type} return: {interval_return:.2f}%\n\n")
            
            # Trend Length Distribution
            report.write("=== Trend Length Distribution ===\n")
            for bin_name, count in length_distribution.items():
                report.write(f"{bin_name} {interval_display}: {count} trends ({count/len(df)*100:.1f}%)\n")
            report.write("\n")
            
            # Additional Insights
            report.write("=== Additional Insights ===\n")
            report.write(f"Trend change frequency: {len(df)/total_intervals:.2f} changes per {interval_type[:-1]}\n")
            report.write(f"Correlation between trend length and percentage change: {correlation:.2f}\n")
            if correlation > 0:
                report.write("Positive correlation suggests longer trends tend to have larger percentage moves\n")
            else:
                report.write("Negative correlation suggests shorter trends tend to have larger percentage moves\n")
            
            # Top Trends
            report.write("\n=== Notable Trends ===\n")
            # Top 5 uptrends by percentage gain
            if len(green_trends) > 0:
                top_gains = green_trends.nlargest(5, 'Percent_Change')
                report.write("Top 5 Uptrends by Percentage Gain:\n")
                for i, row in top_gains.iterrows():
                    report.write(f"  {row['Date']}: +{row['Percent_Change']:.2f}% over {int(row[count_column])} {interval_display}\n")
            
            # Top 5 downtrends by percentage loss
            if len(red_trends) > 0:
                top_losses = red_trends.nsmallest(5, 'Percent_Change')
                report.write("\nTop 5 Downtrends by Percentage Loss:\n")
                for i, row in top_losses.iterrows():
                    report.write(f"  {row['Date']}: {row['Percent_Change']:.2f}% over {int(row[count_column])} {interval_display}\n")
            
            # Percentage Distribution Analysis
            report.write("\n=== Percentage Change Distribution ===\n")
            
            # For uptrends
            if len(green_trends) > 0:
                report.write("\nUptrend Percentage Distribution:\n")
                up_bins = [(0, 10), (10, 20), (20, 30), (30, 40), (40, 50), (50, float('inf'))]
                
                for low, high in up_bins:
                    bin_count = len(green_trends[(green_trends['Percent_Change'] >= low) & 
                                               (green_trends['Percent_Change'] < high if high != float('inf') else True)])
                    bin_percent = (bin_count / len(green_trends) * 100) if len(green_trends) > 0 else 0
                    
                    if high == float('inf'):
                        report.write(f"  {low}%+ : {bin_count} trends ({bin_percent:.1f}% of uptrends)\n")
                    else:
                        report.write(f"  {low}%-{high}% : {bin_count} trends ({bin_percent:.1f}% of uptrends)\n")
            
            # For downtrends
            if len(red_trends) > 0:
                report.write("\nDowntrend Percentage Distribution:\n")
                # Note: red trends have negative percentages, so bins need to be defined differently
                down_bins = [(0, -10), (-10, -20), (-20, -30), (-30, -40), (-40, -50), (-50, float('-inf'))]
                
                for high, low in down_bins:  # Note the order is reversed for downtrends
                    bin_count = len(red_trends[(red_trends['Percent_Change'] <= high) & 
                                             (red_trends['Percent_Change'] > low if low != float('-inf') else True)])
                    bin_percent = (bin_count / len(red_trends) * 100) if len(red_trends) > 0 else 0
                    
                    if low == float('-inf'):
                        report.write(f"  {high}%- : {bin_count} trends ({bin_percent:.1f}% of downtrends)\n")
                    else:
                        report.write(f"  {high}% to {low}% : {bin_count} trends ({bin_percent:.1f}% of downtrends)\n")
            
            report.write("\n")
        
        print(f"Report successfully generated: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"Error generating report: {e}")
        return None

def print_usage():
    print("Usage: python generate_market_report.py <input_file> [output_file]")
    print("Example: python generate_market_report.py spy_monthly_candles_merged_v2_2007_2025.csv my_report.txt")
    print("Example: python generate_market_report.py aapl_weekly_candles_merged_v2_2010_2023.csv aapl_weekly_report.txt")
    print("Example: python generate_market_report.py msft_daily_candles_merged_v2_2022_2023.csv")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate a market trend analysis report from CSV data")
    parser.add_argument("input_file", help="Path to input CSV file")
    parser.add_argument("output_file", nargs="?", help="Path to output report file (optional)", default=None)
    
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    args = parser.parse_args()
    generate_market_report(args.input_file, args.output_file) 