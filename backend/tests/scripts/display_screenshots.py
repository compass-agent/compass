import json
import base64
import io
from PIL import Image
import matplotlib.pyplot as plt

def display_screenshots(log_id):
    """Display all screenshots from messages.json for a given log ID."""
    
    # Read the messages file
    with open(f"logs/{log_id}/messages.json", 'r') as f:
        messages = json.load(f)
    
    # Iterate through messages to find screenshots
    for idx, message in enumerate(messages):
        content = message.get('content', [])
        
        # Check each content item
        for item in content:
            # Handle both direct tool results and nested tool results
            if item.get('type') == 'tool_result':
                for result in item.get('content', []):
                    if result.get('type') == 'image':
                        # Get image data
                        img_data = result.get('source', {}).get('data', '')
                        
                        # Convert base64 to image
                        img_bytes = base64.b64decode(img_data)
                        img = Image.open(io.BytesIO(img_bytes))
                        
                        # Print image info
                        print(f"\nImage at index {idx}")
                        print(f"Size: {img.size}")
                        
                        # Display image
                        plt.figure(figsize=(10, 8))
                        plt.imshow(img)
                        plt.axis('off')
                        plt.show()
            
            # Direct image in content
            elif item.get('type') == 'image':
                img_data = item.get('source', {}).get('data', '')
                
                # Convert base64 to image
                img_bytes = base64.b64decode(img_data)
                img = Image.open(io.BytesIO(img_bytes))
                
                # Print image info
                print(f"\nImage at index {idx}")
                print(f"Size: {img.size}")
                
                # Display image
                plt.figure(figsize=(10, 8))
                plt.imshow(img)
                plt.axis('off')
                plt.show()

if __name__ == "__main__":
    # Example usage
    display_screenshots("20241208-0634-4043") 