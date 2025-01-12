from typing import List
from compass.tools.screen_parser.models import ScreenData, BoundingBox

# Constants
IOU_THRESHOLD = 0.9  # Threshold for overlap detection
CONTAINMENT_THRESHOLD = 0.8  # Threshold for containment detection

def calculate_box_area(box: BoundingBox) -> float:
    """Calculate area of a bounding box"""
    return (box.bbox[2] - box.bbox[0]) * (box.bbox[3] - box.bbox[1])

def calculate_intersection_area(box1: BoundingBox, box2: BoundingBox) -> float:
    """Calculate intersection area between two bounding boxes"""
    x1 = max(box1.bbox[0], box2.bbox[0])
    y1 = max(box1.bbox[1], box2.bbox[1])
    x2 = min(box1.bbox[2], box2.bbox[2])
    y2 = min(box1.bbox[3], box2.bbox[3])
    return max(0, x2 - x1) * max(0, y2 - y1)

def calculate_iou(box1: BoundingBox, box2: BoundingBox) -> float:
    """
    Calculate Intersection over Union (IoU) between two bounding boxes
    
    Args:
        box1: First bounding box
        box2: Second bounding box
        
    Returns:
        float: IoU value
    """
    intersection = calculate_intersection_area(box1, box2)
    box1_area = calculate_box_area(box1)
    box2_area = calculate_box_area(box2)
    
    # Calculate union and containment ratios
    union = box1_area + box2_area - intersection + 1e-6
    ratio1 = intersection / box1_area if box1_area > 0 else 0
    ratio2 = intersection / box2_area if box2_area > 0 else 0
    
    return max(intersection / union, ratio1, ratio2)

def is_contained(inner: BoundingBox, outer: BoundingBox) -> bool:
    """Check if one box is contained within another"""
    intersection = calculate_intersection_area(inner, outer)
    inner_area = calculate_box_area(inner)
    return (intersection / inner_area) > CONTAINMENT_THRESHOLD if inner_area > 0 else False

def remove_overlapping_boxes(icon_data: ScreenData, text_data: ScreenData) -> ScreenData:
    """
    Remove overlapping boxes with intelligent handling of text and icon overlaps.
    
    Args:
        icon_data: ScreenData containing icon detection results
        text_data: ScreenData containing text detection results
        
    Returns:
        ScreenData with overlap conflicts resolved
    """
    # Create new ScreenData instance with original image
    merged = ScreenData(image_data=icon_data.image_data)
    
    # Process text boxes first
    for text_box in text_data.text_elements:
        merged.add_text_element(
            bbox=text_box.bbox,
            text=text_box.text,
            confidence=text_box.confidence
        )

    # Process icon boxes and handle overlaps
    for icon_box in icon_data.icon_elements:
        should_add_icon = True
        
        for text_box in merged.text_elements[:]:  # Copy list for safe modification
            if is_contained(text_box, icon_box):
                # Text is inside icon - merge them
                merged.elements.remove(text_box)
                merged.add_text_element(
                    bbox=icon_box.bbox,
                    text=text_box.text,
                    confidence=max(icon_box.confidence, text_box.confidence)
                )
                should_add_icon = False
                break
            elif is_contained(icon_box, text_box):
                # Icon is inside text - skip icon
                should_add_icon = False
                break
            elif calculate_iou(icon_box, text_box) > IOU_THRESHOLD:
                # Significant overlap - keep the larger box
                if calculate_box_area(icon_box) <= calculate_box_area(text_box):
                    should_add_icon = False
                    break

        if should_add_icon:
            merged.add_icon_element(
                bbox=icon_box.bbox,
                confidence=icon_box.confidence,
                caption=icon_box.caption
            )

    return merged 