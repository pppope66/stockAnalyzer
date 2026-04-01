import pandas as pd
import plotly.graph_objects as go
import argparse
import os
import sys
import numpy as np

def create_candlestick_chart(csv_filename):
    """
    Creates an interactive candlestick chart from CSV data with annotations
    for month count and percentage change.
    
    Args:
        csv_filename (str): Path to the CSV file
    """
    try:
        # Check if file exists
        if not os.path.exists(csv_filename):
            print(f"Error: File '{csv_filename}' not found!")
            return
            
        # Read the CSV file
        print(f"Reading data from: {csv_filename}")
        df = pd.read_csv(csv_filename)
        
        # Ensure required columns exist
        required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Color', 'Percent_Change', 'Month_Count']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Error: Missing required columns: {', '.join(missing_columns)}")
            return
            
        # Convert numeric columns
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Percent_Change', 'Month_Count']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col])
            
        # Convert date column for labels only
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Create a sequence column for linear spacing
        df['Position'] = range(len(df))
        
        # Create figure
        fig = go.Figure()
        
        # Add candlestick trace with wider bars using position for x-axis
        fig.add_trace(go.Candlestick(
            x=df['Position'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            increasing_line_color='green',
            decreasing_line_color='red',
            increasing_line_width=4,
            decreasing_line_width=4,
            name='Price',
            text=[
                f"Date: {row['Date'].strftime('%Y-%m-%d')}<br>" +
                f"Open: {row['Open']:.2f}<br>" +
                f"High: {row['High']:.2f}<br>" +
                f"Low: {row['Low']:.2f}<br>" +
                f"Close: {row['Close']:.2f}<br>" +
                f"Months: {int(row['Month_Count'])}<br>" +
                f"Change: {row['Percent_Change']:+.2f}%"
                for _, row in df.iterrows()
            ],
            hoverinfo='text'
        ))
        
        # Only create month count annotations
        month_count_annotations = []
        annotation_positions = []
        
        # Use a fixed minimum spacing to ensure readability
        min_vertical_distance = 25  # Fixed pixel spacing (larger value)
        
        # Create month count annotations with percentage info
        for i, row in df.iterrows():
            # Start annotation just above its bar
            base_y = row['High'] + (df['High'].max() - df['Low'].min()) * 0.03  # Start 3% above bar
            text_y = base_y
            
            # Keep adjusting position until no overlap or max attempts reached
            overlap = True
            attempts = 0
            max_attempts = 20  # More attempts to find non-overlapping position
            
            while overlap and attempts < max_attempts:
                overlap = False
                attempts += 1
                
                # Check against all existing annotations
                for pos in annotation_positions:
                    # Expand horizontal check range slightly
                    if abs(pos['x'] - row['Position']) <= 2:
                        # Use fixed minimum distance for clearer separation
                        if abs(pos['y'] - text_y) < min_vertical_distance:
                            text_y = pos['y'] + min_vertical_distance
                            overlap = True
                            break
            
            # Track the position we're using
            annotation_positions.append({
                'x': row['Position'],
                'y': text_y
            })
            
            # Calculate arrow length based on distance to bar
            arrow_length = text_y - row['High']
            
            # Add month count annotation with percentage
            month_count_annotations.append(dict(
                x=row['Position'],
                y=text_y,
                text=f"{int(row['Month_Count'])}m ({row['Percent_Change']:+.2f}%)",
                showarrow=True,
                arrowhead=2,
                arrowsize=0.8,
                arrowwidth=1.5,
                ax=0,
                ay=-arrow_length,  # Dynamic arrow length pointing to bar top
                font=dict(
                    size=10,
                    color='green' if row['Color'] == 'green' else 'red'
                ),
                bordercolor='green' if row['Color'] == 'green' else 'red',
                borderwidth=1,
                borderpad=4,
                bgcolor='white'
            ))
        
        # Calculate required chart height for layout
        max_annotation_y = max(pos['y'] for pos in annotation_positions) if annotation_positions else df['High'].max()
        chart_top = max_annotation_y + (df['High'].max() - df['Low'].min()) * 0.05
        
        # Update layout to accommodate annotations
        fig.update_layout(
            title=f"Candlestick Chart: {os.path.basename(csv_filename)}",
            xaxis_title="Date",
            yaxis_title="Price",
            xaxis=dict(
                tickmode='array',
                tickvals=df['Position'].tolist(),
                ticktext=df['Date'].dt.strftime('%Y-%m-%d').tolist(),
                tickangle=45
            ),
            yaxis=dict(
                range=[
                    df['Low'].min() - (df['High'].max() - df['Low'].min()) * 0.05,  # 5% padding below
                    chart_top  # Dynamic top based on highest annotation
                ]
            ),
            xaxis_rangeslider_visible=True,
            width=1200,
            height=800,
            annotations=month_count_annotations,
            bargap=0.05,
            bargroupgap=0.01
        )
        
        # Save as HTML file with custom JavaScript for bar selection and keyboard navigation
        output_file = f"{os.path.splitext(os.path.basename(csv_filename))[0]}_chart.html"
        
        # Create custom JavaScript for bar selection and keyboard navigation
        custom_js = """
        <script>
        // Store the selected bar index
        var selectedBarIndex = null;
        var numBars = %d;
        var barPositions = %s;
        var tryCount = 0;
        
        // Function to show hover info for a specific bar
        function showHoverInfo(index) {
            console.log("Attempting to select bar:", index);
            if (index >= 0 && index < numBars) {
                var myPlot = document.getElementById('plotly-chart');
                if (!myPlot) {
                    console.log("Plot element not found");
                    return;
                }
                
                // Get the x-coordinate for the bar
                var xCoord = barPositions[index];
                
                try {
                    // Try multiple hover approaches 
                    // Method 1: Using Fx.hover
                    Plotly.Fx.hover('plotly-chart', [{
                        curveNumber: 0,
                        pointNumber: index
                    }]);
                    
                    // Method 2: Using direct event dispatch (fallback)
                    var plotArea = myPlot.querySelector('.cartesianlayer');
                    if (plotArea) {
                        var evt = new MouseEvent('mouseover', {
                            bubbles: true,
                            cancelable: true,
                            view: window
                        });
                        
                        // Try to find the actual bar element
                        var bars = myPlot.querySelectorAll('.point');
                        if (bars && bars.length > index) {
                            bars[index].dispatchEvent(evt);
                        } else {
                            plotArea.dispatchEvent(evt);
                        }
                    }
                    
                    console.log("Bar " + index + " selected");
                    selectedBarIndex = index;
                } catch (e) {
                    console.error("Error selecting bar:", e);
                }
            }
        }
        
        // Function to handle keyboard navigation
        function handleKeyDown(event) {
            if (selectedBarIndex === null) {
                // If no bar is selected, select the first one on arrow key
                if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
                    selectedBarIndex = 0;
                    showHoverInfo(selectedBarIndex);
                }
                return;
            }
            
            // Handle arrow keys
            if (event.key === 'ArrowLeft' && selectedBarIndex > 0) {
                showHoverInfo(selectedBarIndex - 1);
            } else if (event.key === 'ArrowRight' && selectedBarIndex < numBars - 1) {
                showHoverInfo(selectedBarIndex + 1);
            }
        }
        
        // Function to try selecting the first bar
        function trySelectFirstBar() {
            tryCount++;
            console.log("Trying to select first bar, attempt:", tryCount);
            
            showHoverInfo(0);
            
            // Try again a few times with increasing delays
            if (tryCount < 5) {
                setTimeout(trySelectFirstBar, tryCount * 500);
            }
        }
        
        // Function to set up the plot and attach event handlers
        function setupPlot() {
            var myPlot = document.getElementById('plotly-chart');
            if (!myPlot) {
                console.log("Plot not found, trying again in 200ms");
                setTimeout(setupPlot, 200);
                return;
            }
            
            console.log("Plot found, setting up event handlers");
            
            // Add click handler for the plot
            myPlot.on('plotly_click', function(data) {
                if (data.points && data.points.length > 0) {
                    var point = data.points[0];
                    showHoverInfo(point.pointNumber);
                }
            });
            
            // Add handler for when plot is fully rendered
            myPlot.on('plotly_afterplot', function() {
                console.log("Plot fully rendered, selecting first bar");
                setTimeout(trySelectFirstBar, 100);
            });
            
            // Add keyboard event listener
            document.addEventListener('keydown', handleKeyDown);
            
            // Start trying to select the first bar
            setTimeout(trySelectFirstBar, 300);
        }
        
        // Watch for when the DOM is fully loaded
        document.addEventListener('DOMContentLoaded', function() {
            console.log("DOM loaded, setting up plot");
            setupPlot();
        });
        
        // Also try when window is fully loaded
        window.addEventListener('load', function() {
            console.log("Window loaded, setting up plot");
            setupPlot();
        });
        
        // One more fallback to ensure we catch when Plotly is ready
        if (window.Plotly) {
            console.log("Plotly detected, setting up plot");
            setupPlot();
        } else {
            // Check periodically for Plotly
            var plotlyCheckInterval = setInterval(function() {
                if (window.Plotly) {
                    console.log("Plotly detected during interval check");
                    clearInterval(plotlyCheckInterval);
                    setupPlot();
                }
            }, 100);
        }
        </script>
        """ % (len(df), df['Position'].tolist())
        
        # Generate HTML with custom div ID and the custom JavaScript
        html_content = fig.to_html(include_plotlyjs=True, full_html=True, div_id='plotly-chart')
        html_content = html_content.replace('</body>', custom_js + '</body>')
        
        # Write the HTML file
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"Interactive chart saved as: {output_file}")
        
        # Show the plot in browser
        import webbrowser
        webbrowser.open('file://' + os.path.realpath(output_file))
        
    except Exception as e:
        print(f"Error creating chart: {e}")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Create an interactive candlestick chart from CSV data')
    parser.add_argument('filename', help='Path to the CSV file')
    
    args = parser.parse_args()
    create_candlestick_chart(args.filename)

if __name__ == "__main__":
    main() 