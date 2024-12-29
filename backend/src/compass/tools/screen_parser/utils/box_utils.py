from dataclasses import dataclass
from typing import List, Optional
from screen_parser.detectors.text import TextDetectionOutput
from screen_parser.detectors.icon import IconDetectionOutput

@dataclass
class UnifiedBox:
    bbox: tuple[float, float, float, float]
    box_type: str  # 'text' or 'icon'
    content: Optional[str]
    interactivity: bool

def remove_overlapping_boxes(
    icon_output: IconDetectionOutput,
    text_output: TextDetectionOutput,
    iou_threshold: float = 0.9
) -> List[UnifiedBox]:
    """
    Remove overlapping boxes with intelligent handling of text and icon overlaps.
    
    Args:
        icon_output: Detection results from icon detector
        text_output: Detection results from text detector
        iou_threshold: Threshold for overlap detection (default: 0.9)
        
    Returns:
        List of unified boxes with overlap conflicts resolved
    """
    def calculate_box_area(box: tuple) -> float:
        return (box[2] - box[0]) * (box[3] - box[1])

    def calculate_intersection_area(box1: tuple, box2: tuple) -> float:
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        return max(0, x2 - x1) * max(0, y2 - y1)

    def calculate_iou(box1: tuple, box2: tuple) -> float:
        intersection = calculate_intersection_area(box1, box2)
        box1_area = calculate_box_area(box1)
        box2_area = calculate_box_area(box2)
        
        # Calculate union and containment ratios
        union = box1_area + box2_area - intersection + 1e-6
        ratio1 = intersection / box1_area if box1_area > 0 else 0
        ratio2 = intersection / box2_area if box2_area > 0 else 0
        
        return max(intersection / union, ratio1, ratio2)

    def is_contained(inner: tuple, outer: tuple, threshold: float = 0.8) -> bool:
        intersection = calculate_intersection_area(inner, outer)
        inner_area = calculate_box_area(inner)
        return (intersection / inner_area) > threshold if inner_area > 0 else False

    # Convert detection outputs to unified format
    unified_boxes: List[UnifiedBox] = []
    
    # Add text boxes
    for text_box in text_output.boxes:
        unified_boxes.append(UnifiedBox(
            bbox=text_box.bbox,
            box_type='text',
            content=text_box.text,
            interactivity=False
        ))

    # Process icon boxes and handle overlaps
    for icon_box in icon_output.boxes:
        should_add_icon = True
        
        for text_box in unified_boxes[:]:  # Copy list for safe modification
            if text_box.box_type == 'text':
                if is_contained(text_box.bbox, icon_box.bbox):
                    # Text is inside icon - merge them
                    unified_boxes.remove(text_box)
                    unified_boxes.append(UnifiedBox(
                        bbox=icon_box.bbox,
                        box_type='text',
                        content=text_box.content,
                        interactivity=True
                    ))
                    should_add_icon = False
                    break
                elif is_contained(icon_box.bbox, text_box.bbox):
                    # Icon is inside text - skip icon
                    should_add_icon = False
                    break
                elif calculate_iou(icon_box.bbox, text_box.bbox) > iou_threshold:
                    # Significant overlap - keep the larger box
                    if calculate_box_area(icon_box.bbox) <= calculate_box_area(text_box.bbox):
                        should_add_icon = False
                        break

        if should_add_icon:
            unified_boxes.append(UnifiedBox(
                bbox=icon_box.bbox,
                box_type='icon',
                content=None,
                interactivity=True
            ))

    return unified_boxes 