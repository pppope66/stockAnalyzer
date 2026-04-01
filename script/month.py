import pandas as pd
import yfinance as yf
import datetime
import argparse
import sys

def get_price_candles(ticker, start_date, end_date, interval):
    """
    Fetch historical price candle data for any ticker with specified interval
    
    Args:
        ticker (str): Stock ticker symbol
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        interval (str): Data interval ('daily', 'weekly', or 'monthly')
        
    Returns:
        DataFrame: Candle data with open, close, high, low, and percent change
    """
    try:
        # Map interval string to yfinance interval format
        interval_map = {
            'daily': '1d',
            'weekly': '1wk',
            'monthly': '1mo'
        }
        
        yf_interval = interval_map.get(interval.lower())
        if not yf_interval:
            return f"Invalid interval: {interval}. Choose from 'daily', 'weekly', or 'monthly'."
        
        # Fetch ticker data
        print(f"Fetching {interval} data for {ticker} from {start_date} to {end_date}")
        data = yf.download(ticker, start=start_date, end=end_date, interval=yf_interval)
        
        if len(data) == 0:
            return f"No data found for {ticker} in the specified period"
        
        # Reset index to make Date a column
        data = data.reset_index()
        
        # Format Date properly as string before processing
        data['Date'] = data['Date'].dt.strftime('%Y-%m-%d')
        
        # Initialize new columns
        data['Color'] = 'unknown'
        data['Percent_Change'] = 0.0
        data['IntervalCount'] = 1  # Generic name for the count column
        
        # Process each row individually to avoid Series truth value errors
        for i in range(len(data)):
            # Set color as string
            if float(data.loc[i, 'Close']) >= float(data.loc[i, 'Open']):
                data.loc[i, 'Color'] = 'green'
                # For green candles: calculate from Open to High
                data.loc[i, 'Percent_Change'] = round((float(data.loc[i, 'High']) - float(data.loc[i, 'Open'])) / float(data.loc[i, 'Open']) * 100, 2)
            else:
                data.loc[i, 'Color'] = 'red'
                # For red candles: calculate from Open to Low
                data.loc[i, 'Percent_Change'] = round((float(data.loc[i, 'Low']) - float(data.loc[i, 'Open'])) / float(data.loc[i, 'Open']) * 100, 2)
        
        # Format the output
        result = data[['Date', 'Open', 'High', 'Low', 'Close', 'Color', 'Percent_Change', 'IntervalCount']]
        result = result.round(2)
        
        return result
        
    except Exception as e:
        print(f"Error fetching {ticker} data: {e}")
        return f"Error: {e}"

# Example usage
if __name__ == "__main__":
    try:
        # Example commands:
        # All arguments are required:
        #    python month.py --ticker AAPL --start 2020-01-01 --end 2023-12-31 --interval monthly
        #    python month.py -t MSFT -s 2015-01-01 -e 2023-12-31 -i weekly
        #    python month.py -t SPY -s 2022-01-01 -e 2023-01-31 -i daily
        
        # Set up argument parser
        parser = argparse.ArgumentParser(description='Fetch price candle data for any ticker')
        parser.add_argument('--ticker', '-t', required=True, help='Ticker symbol (required)')
        parser.add_argument('--start', '-s', required=True, help='Start date (YYYY-MM-DD) (required)')
        parser.add_argument('--end', '-e', required=True, help='End date (YYYY-MM-DD) (required)')
        parser.add_argument('--interval', '-i', required=True, choices=['daily', 'weekly', 'monthly'], 
                           help='Data interval: daily, weekly, or monthly (required)')
        
        args = parser.parse_args()
        
        # Get data using provided arguments
        ticker_data = get_price_candles(args.ticker, args.start, args.end, args.interval)
        
        # Check if we received data or an error message
        if isinstance(ticker_data, str):
            print(ticker_data)
            sys.exit(1)
        
        # Print first few rows to verify
        print("First 5 rows of data:")
        print(ticker_data.head())
        
        # Save to CSV with ticker name and interval in filename
        output_file = f"{args.ticker.lower()}_{args.interval}_candles_{args.start[:4]}_{args.end[:4]}.csv"
        ticker_data.to_csv(output_file, index=False)
        
        # Read the file, skip the second line, and write back
        with open(output_file, 'r') as file:
            lines = file.readlines()
        
        # Write back all lines except the second line (index 1)
        with open(output_file, 'w') as file:
            file.writelines(lines[0])  # Write header
            file.writelines(lines[2:]) # Write all lines except the second line
            
        print(f"Data saved to {output_file}")
        
        # Print summary of data
        print(f"\nTotal rows: {len(ticker_data)}")
        print(f"Green candles: {len(ticker_data[ticker_data['Color'] == 'green'])}")
        print(f"Red candles: {len(ticker_data[ticker_data['Color'] == 'red'])}")
        
    except Exception as e:
        print(f"Error in main function: {e}")
