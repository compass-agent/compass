import cv2

# The path to your original image
image_path = r"C:\Users\mksad\Projects\compass\resources\sap_screenshot.png"
# The path where the new image with bounding boxes will be saved
output_path = r"C:\Users\mksad\Projects\compass\resources\sap_screenshot_with_boxes.png"

# The bounding box data you provided
bounding_boxes = [
    {
        "bbox": (675.0, 63.0, 703.0, 96.0),
        "caption": "0: zy view (0.99)"
    },
    {
        "bbox": (705.0, 63.0, 733.0, 96.0),
        "caption": "1: zy view (0.81)"
    }
]

# Load the image
image = cv2.imread(image_path)

if image is not None:
    # Loop over the bounding boxes
    for box_info in bounding_boxes:
        # Get coordinates and caption
        x1, y1, x2, y2 = [int(c) for c in box_info["bbox"]]
        caption = box_info["caption"]

        # Draw the bounding box
        # cv2.rectangle(image, start_point, end_point, color, thickness)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green box, thickness 2

        # Add the caption
        # cv2.putText(image, text, org, fontFace, fontScale, color, thickness)
        cv2.putText(image, caption, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # Save the new image
    cv2.imwrite(output_path, image)
    print(f"Successfully created image with bounding boxes at: {output_path}")
else:
    print(f"Error: Could not read the image at {image_path}")



