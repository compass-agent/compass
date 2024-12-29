import cv2
from PIL import Image

def visualize_boxes(image_path, boxes_df, output_path=None):
    """
    Visualize bounding boxes on the image
    
    Args:
        image_path (str): Path to input image
        boxes_df (pd.DataFrame): DataFrame with box coordinates and metadata
        output_path (str, optional): Path to save annotated image
        
    Returns:
        PIL.Image if output_path is None, else saves to file
    """
    # Read image
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Colors for different types (RGB)
    colors = {
        'icon': (255, 0, 0),    # Red
        'text': (0, 255, 0)     # Green
    }
    
    # Draw boxes
    for _, row in boxes_df.iterrows():
        x1, y1, x2, y2 = map(int, [row['x1'], row['y1'], row['x2'], row['y2']])
        box_type = row['type']
        color = colors.get(box_type, (0, 0, 255))
        
        # Draw rectangle
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        
        # Add label if text exists
        if row['text']:
            label = f"{box_type}: {row['text']}"
            cv2.putText(image, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.25, color, 2)
    
    # Convert to PIL Image
    image_pil = Image.fromarray(image)
    
    if output_path:
        image_pil.save(output_path)
        return None
    return image_pil 