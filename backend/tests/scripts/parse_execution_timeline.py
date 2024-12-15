import re
import matplotlib.pyplot as plt
from datetime import datetime
import os
import numpy as np

def parse_log_file(log_id):
    """Parse the log file and extract method execution times."""
    log_path = f"logs/{log_id}/app.log"
    
    # Regular expression to match the timing lines
    pattern = r"Method (\w+) took ([\d.]+)ms between times (\d+):(\d+)\.(\d+) to (\d+):(\d+)\.(\d+)"
    
    executions = []
    
    with open(log_path, 'r') as f:
        for line in f:
            match = re.search(pattern, line)
            if match:
                method_name = match.group(1)
                duration_ms = float(match.group(2))
                
                # Parse start and end times
                start_min, start_sec, start_ms = map(int, match.groups()[2:5])
                end_min, end_sec, end_ms = map(int, match.groups()[5:8])
                
                # Convert to total seconds
                start_time = start_min * 60 + start_sec + start_ms / 1000
                end_time = end_min * 60 + end_sec + end_ms / 1000
                
                executions.append({
                    'method': method_name,
                    'start': start_time,
                    'end': end_time,
                    'duration': duration_ms
                })
    
    return executions

def plot_execution_timeline(executions, log_id):
    """Create a timeline plot of method executions."""
    # Create figure and axis
    fig, ax = plt.figure(figsize=(15, 4)), plt.gca()
    
    # Get unique methods
    methods = sorted(set(e['method'] for e in executions))
    method_to_y = {method: i for i, method in enumerate(methods)}
    
    # Create color map for methods
    colors = plt.cm.tab10(np.linspace(0, 1, len(methods)))
    method_to_color = dict(zip(methods, colors))
    
    # Find the minimum start time to normalize the x-axis
    min_time = min(e['start'] for e in executions)
    
    # Calculate y-axis limits
    y_min = -0.4
    y_max = len(methods) - 0.6
    
    # Plot horizontal lines and vertical boundaries for each execution
    for execution in executions:
        y = method_to_y[execution['method']]
        # Normalize times relative to start
        start = execution['start'] - min_time
        end = execution['end'] - min_time
        
        # Horizontal bar for duration
        ax.bar(
            x=start,
            width=end-start,
            bottom=y-0.4,
            height=0.8,
            alpha=0.7,
            align='edge',
            color=method_to_color[execution['method']]
        )
        
        # Vertical lines for start and end spanning full height
        ax.vlines(
            x=[start, end],
            ymin=y_min,
            ymax=y_max,
            linestyles='dashed',
            colors='gray',
            alpha=0.3
        )
    
    # Set y-axis limits
    ax.set_ylim(y_min, y_max)
    
    # Customize the plot
    ax.set_yticks(range(len(methods)))
    ax.set_yticklabels(methods)
    
    # Format x-axis to show seconds with 2 decimal places
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x:.2f}s"))
    
    ax.set_xlabel('Time (seconds from start)')
    ax.set_title(f'Method Execution Timeline - Log {log_id}')
    ax.grid(True, axis='x', linestyle='--', alpha=0.7)
    
    # Save in the log folder instead of test_output
    output_dir = f"logs/{log_id}"
    output_path = f"{output_dir}/execution_timeline.png"
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    
    return output_path

def main(log_id):
    """Main function to parse log and create visualization."""
    executions = parse_log_file(log_id)
    output_path = plot_execution_timeline(executions, log_id)
    print(f"Timeline plot saved to: {output_path}")

if __name__ == "__main__":
    main("20241206-1226-3916")