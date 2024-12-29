import json
import base64
import os
from pathlib import Path

def create_screenshot_report(log_id):
    """Create an HTML report of all screenshots from all message files for a given log ID."""
    
    log_path = Path(f"logs/{log_id}")
    html_content = []
    
    # HTML header with enhanced styling and JavaScript
    html_content.append(f"""
    <html>
    <head>
        <style>
            .screenshot-container {{ margin: 20px 0; padding: 20px; border: 1px solid #ccc; }}
            .caption {{ font-family: Arial, sans-serif; margin: 10px 0; }}
            img {{ max-width: 100%; height: auto; }}
            .message-section {{ margin: 20px 0; }}
            .collapsible {{ 
                background-color: #eee;
                color: #444;
                cursor: pointer;
                padding: 18px;
                width: 100%;
                border: none;
                text-align: left;
                outline: none;
                font-size: 15px;
                font-weight: bold;
            }}
            .active, .collapsible:hover {{
                background-color: #ccc;
            }}
            .content {{
                padding: 0 18px;
                display: none;
                overflow: hidden;
                background-color: #f1f1f1;
            }}
        </style>
    </head>
    <body>
        <h1>Screenshots Report - Log ID: {log_id}</h1>
    """)
    
    # Find all message files
    message_files = sorted([f for f in os.listdir(log_path) if f.startswith("messages_") and f.endswith(".json")])
    
    for message_file in message_files:
        # Start a new section for each message file
        html_content.append(f"""
            <div class="message-section">
                <button type="button" class="collapsible">{message_file}</button>
                <div class="content">
        """)
        
        # Read the messages file
        with open(log_path / message_file, 'r') as f:
            messages = json.load(f)
        
        # Track if we found any images in this file
        images_found = False
        
        # Process each message
        for msg_idx, message in enumerate(messages):
            content = message.get('content', [])
            
            for content_idx, item in enumerate(content):
                # Handle tool results
                if item.get('type') == 'tool_result':
                    for result in item.get('content', []):
                        if result.get('type') == 'image':
                            images_found = True
                            img_data = result.get('source', {}).get('data', '')
                            html_content.append(f"""
                                <div class="screenshot-container">
                                    <img src="data:image/png;base64,{img_data}">
                                    <p class="caption">Message Index: {msg_idx}, Content Index: {content_idx}</p>
                                </div>
                            """)
                
                # Handle direct images
                elif item.get('type') == 'image':
                    images_found = True
                    img_data = item.get('source', {}).get('data', '')
                    html_content.append(f"""
                        <div class="screenshot-container">
                            <img src="data:image/png;base64,{img_data}">
                            <p class="caption">Message Index: {msg_idx}, Content Index: {content_idx}</p>
                        </div>
                    """)
        
        # If no images were found, add a message
        if not images_found:
            html_content.append("<p>No images found in this message file.</p>")
        
        # Close the section
        html_content.append("</div></div>")
    
    # Add JavaScript for collapsible functionality
    html_content.append("""
        <script>
        var coll = document.getElementsByClassName("collapsible");
        var i;

        for (i = 0; i < coll.length; i++) {
            coll[i].addEventListener("click", function() {
                this.classList.toggle("active");
                var content = this.nextElementSibling;
                if (content.style.display === "block") {
                    content.style.display = "none";
                } else {
                    content.style.display = "block";
                }
            });
        }
        </script>
        </body>
        </html>
    """)
    
    # Save the HTML file
    output_path = log_path / "screenshots_report.html"
    with open(output_path, 'w') as f:
        f.write("\n".join(html_content))
    
    print(f"Report generated at: {output_path}")

if __name__ == "__main__":
    # Example usage
    create_screenshot_report("20241215-1735-0158")
