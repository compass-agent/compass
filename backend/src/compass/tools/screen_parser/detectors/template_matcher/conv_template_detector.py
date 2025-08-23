import cv2
import numpy as np
import base64
from typing import List, Tuple, Optional, Dict
import io
from PIL import Image
import logging
import torch
import torch.nn.functional as F
from pathlib import Path
import yaml
from compass.database.models import Session, Template
from compass.tools.screen_parser.models import ScreenData
from sklearn.cluster import KMeans
import warnings

logger = logging.getLogger(__name__)

class ConvTemplateDetector:
    """
    Convolution-based template detector that processes all templates simultaneously
    using grouped convolutions for different template sizes.
    """
    
    def __init__(self, agent_name: Optional[str] = None, device: str = 'cpu'):
        """
        Initialize convolution template detector
        
        Args:
            agent_name: Optional agent name to filter templates
            device: 'cpu' or 'cuda' for computation
        """
        config = self._load_config()
        
        if not config.get('enabled', False):
            raise RuntimeError("Template matching is not enabled in config")
            
        self.threshold = config.get('threshold', 0.8)
        self.agent_name = agent_name if agent_name is not None else "structural-engineer"
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")
        
        # Load and group templates by size
        self.template_groups = self._load_and_group_templates()
        logger.info(f"Loaded {sum(group['num_templates'] for group in self.template_groups)} templates "
                   f"in {len(self.template_groups)} size groups for agent '{self.agent_name}'")
    
    @staticmethod
    def _load_config() -> dict:
        """Load template matching configuration from config file"""
        config_path = Path(__file__).parent.parent.parent / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config.get('template_matching', {})
    
    def _load_and_group_templates(self) -> List[Dict]:
        """
        Load templates from database and group them by similar sizes
        
        Returns:
            List of template groups, each containing templates of similar sizes
        """
        # First, load all templates and their sizes
        template_data = []
        
        with Session() as session:
            db_templates = session.query(Template).filter(Template.agent_name == self.agent_name).all()
            
            for template in db_templates:
                try:
                    # Convert base64 to numpy array
                    img_bytes = base64.b64decode(str(template.base64_image))
                    img = Image.open(io.BytesIO(img_bytes))
                    img_array = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                    
                    template_data.append({
                        'image': img_array,
                        'caption': template.caption,
                        'id': template.id,
                        'height': img_array.shape[0],
                        'width': img_array.shape[1]
                    })
                except Exception as e:
                    logger.warning(f"Failed to load template {template.id}: {e}")
                    continue
        
        if not template_data:
            logger.warning("No templates loaded")
            return []
        
        # Group templates by size using clustering
        return self._cluster_templates_by_size(template_data)
    
    def _cluster_templates_by_size(self, template_data: List[Dict]) -> List[Dict]:
        """
        Cluster templates into groups based on their sizes
        
        Args:
            template_data: List of template dictionaries with size info
            
        Returns:
            List of template groups
        """
        if len(template_data) <= 3:
            # If we have very few templates, put them all in one group
            max_h = max(t['height'] for t in template_data)
            max_w = max(t['width'] for t in template_data)
            return [self._create_template_group(template_data, max_h, max_w)]
        
        # Extract size features for clustering
        sizes = np.array([[t['height'], t['width']] for t in template_data])
        
        # Determine number of clusters (max 3, but could be fewer)
        n_clusters = min(3, len(template_data))
        
        # Use size variance to determine if clustering is beneficial
        size_variance = np.var(sizes, axis=0).sum()
        if size_variance < 100:  # Low variance, use single group
            max_h = max(t['height'] for t in template_data)
            max_w = max(t['width'] for t in template_data)
            return [self._create_template_group(template_data, max_h, max_w)]
        
        # Perform K-means clustering
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
            cluster_labels = kmeans.fit_predict(sizes)
        
        # Group templates by cluster
        groups = []
        for cluster_id in range(n_clusters):
            cluster_templates = [t for i, t in enumerate(template_data) if cluster_labels[i] == cluster_id]
            if cluster_templates:
                # Find max dimensions for this cluster
                max_h = max(t['height'] for t in cluster_templates)
                max_w = max(t['width'] for t in cluster_templates)
                groups.append(self._create_template_group(cluster_templates, max_h, max_w))
        
        return groups
    
    def _create_template_group(self, templates: List[Dict], target_h: int, target_w: int) -> Dict:
        """
        Create a template group with padded templates, convolution kernel, and pre-calculated statistics for NCC.
        
        Args:
            templates: List of template dictionaries
            target_h: Target height for padding
            target_w: Target width for padding
            
        Returns:
            Dictionary containing the group information
        """
        # Pad all templates to target size and stack them
        padded_templates = []
        template_info = []
        template_means = []
        template_norms = []
        
        for template in templates:
            img = template['image']
            h, w = img.shape[:2]
            
            # Calculate padding
            pad_h = target_h - h
            pad_w = target_w - w
            
            # Pad the template (pad bottom and right)
            padded = cv2.copyMakeBorder(
                img, 0, pad_h, 0, pad_w, 
                cv2.BORDER_CONSTANT, value=[0, 0, 0]
            )
            
            # Convert to grayscale for template matching
            if len(padded.shape) == 3:
                padded = cv2.cvtColor(padded, cv2.COLOR_BGR2GRAY)

            padded_templates.append(padded)
            template_info.append({
                'caption': template['caption'],
                'id': template['id'],
                'original_h': h,
                'original_w': w
            })

            # Pre-calculate statistics for NCC using the PADDED template for consistency
            template_padded_float = padded.astype(np.float32)
            mean = np.mean(template_padded_float)
            template_means.append(mean)
            
            # Calculate de-meaned L2 norm
            de_meaned_template = template_padded_float - mean
            norm = np.sqrt(np.sum(de_meaned_template**2))
            template_norms.append(norm)

        # Stack templates to create kernel [num_templates, height, width]
        kernel = np.stack(padded_templates, axis=0)
        
        return {
            'kernel': kernel,
            'template_info': template_info,
            'template_means': np.array(template_means, dtype=np.float32),
            'template_norms': np.array(template_norms, dtype=np.float32),
            'target_h': target_h,
            'target_w': target_w,
            'num_templates': len(templates)
        }
    
    def detect(self, screen_data: ScreenData, agent_name: Optional[str] = None) -> ScreenData:
        """
        Detect icons in screen using a convolution-based template matching approach.
        
        Args:
            screen_data: ScreenData object containing the screenshot
            agent_name: Optional agent name (not used, kept for interface compatibility)
            
        Returns:
            ScreenData object with detected icons
        """
        # Convert screen to grayscale numpy array
        img_bytes = base64.b64decode(screen_data.image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        screen_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if screen_bgr is None:
            raise ValueError("Failed to decode screen image")
        screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
        
        result = ScreenData(image_data=screen_data.image_data)
        
        all_detections = []

        # Process each template group on the full image
        for group in self.template_groups:
            # Skip if image is smaller than template
            if screen_gray.shape[0] < group['target_h'] or screen_gray.shape[1] < group['target_w']:
                continue
                
            detections = self._process_template_group(screen_gray, group)
            all_detections.extend(detections)
        
        # Apply NMS across all detections
        if all_detections:
            final_detections = self._apply_global_nms(all_detections)
            
            # Add to result
            for detection in final_detections:
                result.add_icon_element(
                    bbox=detection['bbox'],
                    confidence=detection['confidence'],
                    caption=detection['caption'],
                    template_id=detection['template_id']
                )
        
        logger.info(f"Found {len(result.icon_elements)} icon matches using convolution")
        return result
    
    def _process_template_group(self, screen: np.ndarray, group: Dict) -> List[Dict]:
        """
        Process a single template group using convolution to compute Normalized Cross-Correlation.
        
        Args:
            screen: Grayscale screen image (as numpy array)
            group: Template group dictionary containing kernels and pre-calculated stats
            
        Returns:
            List of detection dictionaries
        """
        kernel = group['kernel']  # [num_templates, height, width]
        template_info = group['template_info']
        template_means = group['template_means'] # [num_templates]
        template_norms = group['template_norms'] # [num_templates]
        h, w = group['target_h'], group['target_w']
        n_templates = group['num_templates']
        n_pixels = h * w
        
        # --- 1. Convert to torch tensors for efficient computation (use float for performance) ---
        screen_tensor = torch.from_numpy(screen).float().unsqueeze(0).unsqueeze(0).to(self.device)
        kernel_tensor = torch.from_numpy(kernel).float().unsqueeze(1).to(self.device)
        
        # Reshape template stats for broadcasting
        template_means_t = torch.from_numpy(template_means).float().view(1, n_templates, 1, 1).to(self.device)
        template_norms_t = torch.from_numpy(template_norms).float().view(1, n_templates, 1, 1).to(self.device)

        # --- 2. Calculate local image statistics using convolution with a 'ones' kernel ---
        ones_kernel = torch.ones(1, 1, h, w, device=self.device, dtype=torch.float32)
        
        with torch.no_grad():
            # Calculate local sum of image pixels
            local_sum_map = F.conv2d(screen_tensor, ones_kernel, padding='valid')
            local_mean_map = local_sum_map / n_pixels

            # Calculate local sum of squared image pixels
            screen_sq_tensor = screen_tensor**2
            local_sum_sq_map = F.conv2d(screen_sq_tensor, ones_kernel, padding='valid')

            # Calculate local image standard deviation
            image_variance = (local_sum_sq_map / n_pixels) - (local_mean_map**2)
            image_variance = torch.clamp(image_variance, min=0) 
            image_std_map = torch.sqrt(image_variance)
            image_norm_map = image_std_map * np.sqrt(n_pixels)

            # --- 3. Calculate main cross-correlation ---
            cross_corr_map = F.conv2d(screen_tensor, kernel_tensor, padding='valid')

            # --- 4. Assemble the NCC Numerator ---
            numerator = cross_corr_map - n_pixels * template_means_t * local_mean_map

            # --- 5. Assemble the NCC Denominator ---
            # norm(T) * norm(I)
            denominator = template_norms_t * image_norm_map
            
            # --- 6. Calculate final NCC score ---
            ncc_map = torch.zeros_like(denominator)
            stable_mask = denominator > 1e-6 
            ncc_map[stable_mask] = numerator[stable_mask] / denominator[stable_mask]

        ncc_map_np = ncc_map.squeeze(0).cpu().numpy() # [num_templates, H', W']
        
        # --- 7. Find detections for each template ---
        detections = []
        
        for template_idx, template_data in enumerate(template_info):
            response_map = ncc_map_np[template_idx]
            
            # Find peaks above threshold
            locations = np.where(response_map >= self.threshold)
            
            for y, x in zip(locations[0], locations[1]):
                # Use original template size for bounding box
                h_orig, w_orig = template_data['original_h'], template_data['original_w']
                
                detections.append({
                    'bbox': (float(x), float(y), float(x + w_orig), float(y + h_orig)),
                    'confidence': float(response_map[y, x]),
                    'caption': template_data['caption'],
                    'template_id': template_data['id'],
                    'template_idx': template_idx
                })
        
        return detections
    
    def _apply_global_nms(self, detections: List[Dict], iou_threshold: float = 0.5) -> List[Dict]:
        """
        Apply Non-Maximum Suppression across all detections
        
        Args:
            detections: List of detection dictionaries
            iou_threshold: IoU threshold for NMS
            
        Returns:
            Filtered list of detections
        """
        if not detections:
            return []
        
        # Sort by confidence (descending)
        detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        
        # Convert to arrays for efficient computation
        boxes = np.array([d['bbox'] for d in detections])
        scores = np.array([d['confidence'] for d in detections])
        
        # Apply NMS
        keep_indices = []
        indices = np.arange(len(detections))
        
        while len(indices) > 0:
            # Pick the detection with highest confidence
            current_idx = indices[0]
            keep_indices.append(current_idx)
            
            if len(indices) == 1:
                break
            
            # Calculate IoU with remaining detections
            current_box = boxes[current_idx]
            other_boxes = boxes[indices[1:]]
            
            # Calculate intersection
            x1 = np.maximum(current_box[0], other_boxes[:, 0])
            y1 = np.maximum(current_box[1], other_boxes[:, 1])
            x2 = np.minimum(current_box[2], other_boxes[:, 2])
            y2 = np.minimum(current_box[3], other_boxes[:, 3])
            
            intersection = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
            
            # Calculate union
            current_area = (current_box[2] - current_box[0]) * (current_box[3] - current_box[1])
            other_areas = (other_boxes[:, 2] - other_boxes[:, 0]) * (other_boxes[:, 3] - other_boxes[:, 1])
            union = current_area + other_areas - intersection
            
            # Calculate IoU
            iou = intersection / (union + 1e-6)
            
            # Keep detections with IoU below threshold
            indices = indices[1:][iou < iou_threshold]
        
        return [detections[i] for i in keep_indices]


if __name__ == "__main__":
    # Test the detector
    import sys
    import time
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.append(str(project_root))
    
    from compass.tools.screen_parser.models import ScreenData
    
    # Test with SAP screenshot
    image_path = r"C:\Users\mksad\Projects\compass\resources\sap_screenshot.png"
    
    print("Testing convolution-based template detector")
    detector = ConvTemplateDetector(agent_name="SAP")
    
    print(f"Loaded {len(detector.template_groups)} template groups")
    
    print(f"\nRunning detection on: {image_path}")
    
    # Load screen data
    screen_data = ScreenData.from_path(image_path)
    
    # Run detection
    start_time = time.time()
    result = detector.detect(screen_data)
    end_time = time.time()
    
    print(f"Detection completed in {end_time - start_time:.3f}s")
    print(f"Found {len(result.icon_elements)} icon matches")
    
    if result.icon_elements:
        print("\nDetected icons:")
        for i, icon in enumerate(result.icon_elements):
            bbox = icon.bbox
            print(f"  {i+1}. {icon.caption} at ({bbox[0]:.0f}, {bbox[1]:.0f}, {bbox[2]:.0f}, {bbox[3]:.0f}) "
                  f"(confidence: {icon.confidence:.3f})")
    else:
        print("No icons detected.")