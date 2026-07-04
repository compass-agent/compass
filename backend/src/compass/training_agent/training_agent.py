import logging
import base64
import json
from typing import Dict, List, Protocol
import numpy as np
import cv2
from compass.tools.screen_parser.detectors.template_matcher.template_detector import TemplateDetector
from compass.tools.screen_parser.models import ScreenData, BoundingBox
from compass.tools.screen_parser.utils.box_utils import calculate_iou
from compass.database.models import Agent, Session, Template, Page
from dataclasses import dataclass
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from sqlalchemy.sql import func
import uuid

logger = logging.getLogger(__name__)

IOU_THRESHOLD = 0.9  # Using same threshold as box_utils

Base = declarative_base()

@dataclass
class Detection:
    """Represents a single detection with its properties"""
    id: str
    bbox: List[float]
    confidence: float
    caption: str | None
    source: str  # e.g., 'template', 'yolo'

class DetectionFilter(Protocol):
    """Protocol for detection filters"""
    def filter(self, detection: Detection, context: Dict) -> bool:
        """Return True if detection should be kept"""
        pass

class EmptyImageFilter(DetectionFilter):
    def filter(self, detection: Detection, context: Dict) -> bool:
        threshold = 10.0  # Can be made configurable
        image_data = context['image_data']
        return not self._is_empty_image(image_data, detection.bbox, threshold)
        
    def _is_empty_image(self, image_data: str, bbox: List[float], threshold: float) -> bool:
        """
        Check if cropped image region is empty (uniform color/low variation)
        
        Args:
            image_data: Base64 encoded image
            bbox: Bounding box coordinates [x1, y1, x2, y2]
            threshold: Threshold for std deviation (default 10.0)
                      Lower values = more strict (catches more uniform regions)
            
        Returns:
            bool: True if image is considered empty/uniform
        """
        # Decode and crop image
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        x1, y1, x2, y2 = map(int, bbox)
        cropped = img[y1:y2, x1:x2]
        
        # Convert to grayscale
        gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        
        # Calculate standard deviation of pixel values
        std_dev = np.std(gray)
        
        return std_dev < threshold

class SmallBoxFilter(DetectionFilter):
    def filter(self, detection: Detection, context: Dict) -> bool:
        if detection.source == 'template':  # Skip filter for templates
            return True
        return self._get_box_area(detection.bbox) >= context['min_area_threshold']
        
    def _get_box_area(self, bbox: List[float]) -> float:
        """Calculate area of bounding box"""
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return width * height

class OverlapFilter(DetectionFilter):
    def filter(self, detection: Detection, context: Dict) -> bool:
        if detection.source == 'template':  # Skip filter for templates
            return True
            
        template_detections = context['template_detections']
        for template_detection in template_detections:
            # Create BoundingBox objects for IOU calculation
            box1 = BoundingBox(bbox=tuple(detection.bbox), element_type="icon", confidence=detection.confidence)
            box2 = BoundingBox(bbox=tuple(template_detection.bbox), element_type="icon", confidence=template_detection.confidence)
            
            if calculate_iou(box1, box2) > context['iou_threshold']:
                return False
        return True

class TrainingAgent:
    def __init__(self):
        """Initialize training agent with detectors and filters"""
        # YOLO icon detection needs torch/ultralytics, which are excluded
        # from the packaged app to keep it small. Template matching still
        # works without it.
        self.yolo_detector = None
        try:
            from compass.training_agent.detectors.icon.yolo_detector import YOLOIconDetector
            self.yolo_detector = YOLOIconDetector()
        except Exception as e:
            logger.warning(f"YOLO icon detection unavailable (optional): {e}")


        self.filters = [
            EmptyImageFilter(),
            SmallBoxFilter(),
            OverlapFilter()
        ]
        self._seed_default_agents()

    def _seed_default_agents(self) -> None:
        """Create baseline Agent Hub rows for fresh installs.

        Older versions only stored pages/templates by agent name, so the Agent
        table may be empty even when training data exists. These defaults make
        the Agent Hub usable immediately while preserving any existing page
        names as lightweight agent rows when listed.
        """
        try:
            with Session() as session:
                if session.query(Agent).count() > 0:
                    return

                session.add(Agent(
                    name="structural-engineer",
                    description="Structural engineering assistant with SAP2000 integration",
                    prompt="You are a structural engineering expert with SAP2000 automation capabilities.",
                    general_tools=[],
                    software_integrations=[{
                        "id": "SAP2000",
                        "name": "SAP2000",
                        "scripting": True,
                        "desktop": False,
                        "config": {},
                    }],
                    configuration={},
                ))
                session.add(Agent(
                    name="Generic",
                    description="General purpose desktop automation agent",
                    prompt="You are a helpful AI assistant.",
                    general_tools=[
                        {"id": "fileEditor", "name": "File Editor", "config": {"rootDir": "", "restricted": True}},
                        {"id": "commandLine", "name": "Command Line", "config": {"access": "full"}},
                    ],
                    software_integrations=[],
                    configuration={},
                ))
                session.commit()
        except Exception as e:
            logger.warning(f"Could not seed default agents: {e}")

    @staticmethod
    def _normalize_agent_payload(data: Dict) -> Dict:
        """Accept both renderer camelCase and database snake_case payloads."""
        data = data or {}
        return {
            "name": (data.get("name") or "").strip(),
            "description": data.get("description") or "",
            "prompt": data.get("prompt") or "",
            "general_tools": data.get("generalTools", data.get("general_tools", [])) or [],
            "software_integrations": data.get(
                "softwareIntegrations",
                data.get("software_integrations", []),
            ) or [],
            "configuration": data.get("configuration") or {},
        }

    @staticmethod
    def _agent_with_counts(session, agent: Agent) -> Dict:
        data = agent.to_dict()
        data["pagesCount"] = session.query(Page).filter_by(agent_name=agent.name).count()
        data["templatesCount"] = session.query(Template).filter_by(agent_name=agent.name).count()
        return data

    @staticmethod
    def _unique_agent_name(session, desired_name: str) -> str:
        base_name = (desired_name or "Imported Agent").strip() or "Imported Agent"
        name = base_name
        counter = 2
        while session.query(Agent).filter_by(name=name).first() is not None:
            name = f"{base_name} {counter}"
            counter += 1
        return name

    def list_agents(self) -> List[Dict]:
        """List configured agents, including legacy page-only agents."""
        try:
            self._seed_default_agents()
            with Session() as session:
                agents = session.query(Agent).order_by(Agent.updated_at.desc()).all()
                result = [self._agent_with_counts(session, agent) for agent in agents]

                known_names = {agent["name"] for agent in result}
                legacy_page_names = [
                    row[0]
                    for row in session.query(Page.agent_name).distinct().all()
                    if row[0] and row[0] not in known_names
                ]
                for name in legacy_page_names:
                    pages_count = session.query(Page).filter_by(agent_name=name).count()
                    templates_count = session.query(Template).filter_by(agent_name=name).count()
                    result.append({
                        "agentId": name,
                        "name": name,
                        "description": "",
                        "prompt": "",
                        "generalTools": [],
                        "softwareIntegrations": [],
                        "configuration": {},
                        "pagesCount": pages_count,
                        "templatesCount": templates_count,
                        "last_modified": None,
                    })
                return result
        except Exception as e:
            logger.error(f"Failed to list agents: {e}", exc_info=True)
            raise

    def create_agent(self, data: Dict) -> Dict:
        """Create an Agent Hub configuration."""
        payload = self._normalize_agent_payload(data)
        if not payload["name"]:
            raise ValueError("Agent name is required")

        try:
            with Session() as session:
                if session.query(Agent).filter_by(name=payload["name"]).first():
                    raise ValueError(f"Agent '{payload['name']}' already exists")

                agent = Agent(**payload)
                session.add(agent)
                session.commit()
                session.refresh(agent)
                return self._agent_with_counts(session, agent)
        except Exception as e:
            logger.error(f"Failed to create agent: {e}", exc_info=True)
            raise

    def update_agent(self, agent_id: str, data: Dict) -> Dict:
        """Update an Agent Hub configuration."""
        payload = self._normalize_agent_payload(data)
        try:
            with Session() as session:
                agent = (
                    session.query(Agent).filter_by(id=agent_id).first()
                    or session.query(Agent).filter_by(name=agent_id).first()
                )
                if not agent:
                    raise ValueError("Agent not found")

                old_name = agent.name
                new_name = payload["name"] or old_name
                if new_name != old_name and session.query(Agent).filter_by(name=new_name).first():
                    raise ValueError(f"Agent '{new_name}' already exists")

                agent.name = new_name
                agent.description = payload["description"]
                agent.prompt = payload["prompt"]
                agent.general_tools = payload["general_tools"]
                agent.software_integrations = payload["software_integrations"]
                agent.configuration = payload["configuration"]
                agent.updated_at = datetime.utcnow()

                if new_name != old_name:
                    session.query(Page).filter_by(agent_name=old_name).update({"agent_name": new_name})
                    session.query(Template).filter_by(agent_name=old_name).update({"agent_name": new_name})

                session.commit()
                session.refresh(agent)
                return self._agent_with_counts(session, agent)
        except Exception as e:
            logger.error(f"Failed to update agent: {e}", exc_info=True)
            raise

    def delete_agent(self, agent_id: str) -> Dict:
        """Delete an agent and all pages/templates associated with its name."""
        try:
            with Session() as session:
                agent = (
                    session.query(Agent).filter_by(id=agent_id).first()
                    or session.query(Agent).filter_by(name=agent_id).first()
                )
                if not agent:
                    raise ValueError("Agent not found")

                agent_name = agent.name
                pages_deleted = session.query(Page).filter_by(agent_name=agent_name).count()
                templates_deleted = session.query(Template).filter_by(agent_name=agent_name).count()
                session.query(Template).filter_by(agent_name=agent_name).delete()
                session.query(Page).filter_by(agent_name=agent_name).delete()
                session.delete(agent)
                session.commit()
                return {
                    "agentId": agent_id,
                    "agentName": agent_name,
                    "pagesDeleted": pages_deleted,
                    "templatesDeleted": templates_deleted,
                }
        except Exception as e:
            logger.error(f"Failed to delete agent: {e}", exc_info=True)
            raise

    def export_agent(self, agent_id: str) -> Dict:
        """Export agent configuration and training data as base64 JSON."""
        try:
            with Session() as session:
                agent = (
                    session.query(Agent).filter_by(id=agent_id).first()
                    or session.query(Agent).filter_by(name=agent_id).first()
                )
                if not agent:
                    raise ValueError("Agent not found")

                pages = session.query(Page).filter_by(agent_name=agent.name).all()
                templates = session.query(Template).filter_by(agent_name=agent.name).all()
                payload = {
                    "version": 1,
                    "agent": agent.to_dict(),
                    "pages": [{
                        "name": page.name,
                        "image": page.base64_image,
                        "created_at": page.created_at.isoformat() if page.created_at else None,
                    } for page in pages],
                    "templates": [{
                        "id": template.id,
                        "page_name": template.page_name,
                        "caption": template.caption,
                        "base64_image": template.base64_image,
                        "created_at": template.created_at.isoformat() if template.created_at else None,
                    } for template in templates],
                }
                content = base64.b64encode(
                    json.dumps(payload, indent=2).encode("utf-8")
                ).decode("utf-8")
                safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in agent.name)
                return {
                    "content": content,
                    "filename": f"{safe_name}.agent",
                }
        except Exception as e:
            logger.error(f"Failed to export agent: {e}", exc_info=True)
            raise

    def import_agent(self, import_data: str) -> Dict:
        """Import agent configuration and optional pages/templates."""
        try:
            payload = json.loads(import_data)
            agent_data = payload.get("agent", payload)
            pages = payload.get("pages", [])
            templates = payload.get("templates", [])

            with Session() as session:
                normalized = self._normalize_agent_payload(agent_data)
                normalized["name"] = self._unique_agent_name(session, normalized["name"])
                agent = Agent(**normalized)
                session.add(agent)
                session.flush()

                for page in pages:
                    image = page.get("image") or page.get("base64_image")
                    if image:
                        session.add(Page(
                            agent_name=agent.name,
                            name=page.get("name") or "",
                            base64_image=image,
                        ))

                for template in templates:
                    image = template.get("base64_image") or template.get("image")
                    if image:
                        session.add(Template(
                            id=str(uuid.uuid4()),
                            agent_name=agent.name,
                            page_name=template.get("page_name") or template.get("pageName") or "",
                            caption=template.get("caption") or "",
                            base64_image=image,
                        ))

                session.commit()
                session.refresh(agent)
                return self._agent_with_counts(session, agent)
        except Exception as e:
            logger.error(f"Failed to import agent: {e}", exc_info=True)
            raise

    def delete_page(self, page_id: int) -> Dict:
        """Delete a training page and its templates."""
        try:
            with Session() as session:
                page = session.query(Page).filter_by(id=page_id).first()
                if not page:
                    raise ValueError("Page not found")

                templates_deleted = session.query(Template).filter_by(
                    agent_name=page.agent_name,
                    page_name=page.name,
                ).count()
                session.query(Template).filter_by(
                    agent_name=page.agent_name,
                    page_name=page.name,
                ).delete()
                session.delete(page)
                session.commit()
                return {
                    "pageId": page_id,
                    "templatesDeleted": templates_deleted,
                    "message": f"Deleted page '{page.name or 'Untitled'}'",
                }
        except Exception as e:
            logger.error(f"Failed to delete page: {e}", exc_info=True)
            raise
        
    def get_screenshots(self, agent_name: str) -> List[Dict]:
        """Get all pages for an agent"""
        try:
            with Session() as session:
                pages = session.query(Page).filter_by(
                    agent_name=agent_name
                ).order_by(Page.created_at.desc()).all()
                
                return [{
                    'id': p.id,
                    'image': p.base64_image,
                    'name': p.name,  # Include page name
                    'created_at': p.created_at.isoformat()
                } for p in pages]
        except Exception as e:
            logger.error(f"Failed to get pages: {e}")
            raise

    def get_agent_names(self) -> List[Dict]:
        """Get all unique agent names with their latest modification time"""
        try:
            return self.list_agents()
        except Exception as e:
            logger.error(f"Failed to get agent names: {e}")
            raise

    def save_page(self, image_data: str, agent_name: str, page_name: str = "") -> int:
        """
        Save page to database if it doesn't exist
        
        Args:
            image_data: Base64 encoded image
            agent_name: Name of the agent
            page_name: Name of the page
            
        Returns:
            id: ID of saved or existing page
        """
        try:
            with Session() as session:
                # Check if page already exists
                existing = session.query(Page).filter_by(
                    base64_image=image_data,
                    agent_name=agent_name
                ).first()
                
                if existing:
                    if page_name and existing.name != page_name:
                        existing.name = page_name
                        existing.updated_at = datetime.utcnow()
                        session.commit()
                    return existing.id  # Return ID before session closes
                
                # Create new page
                page = Page(
                    base64_image=image_data,
                    agent_name=agent_name,
                    name=page_name
                )
                session.add(page)
                session.commit()
                page_id = page.id  # Get ID before session closes
                return page_id
                
        except Exception as e:
            logger.error(f"Failed to save page: {e}")
            raise

    def save_template(self, image_data: str, templates: List[dict], agent_name: str = "FreeCAD", page_name: str = "") -> None:
        """Save multiple templates to database, ensuring screenshot exists first"""
        try:
            # First save the full screenshot once
            self.save_page(image_data, agent_name, page_name)
            
            # Then save each template
            for template in templates:
                caption = template.get('caption', '')
                bbox = template.get('bbox', [])
                
                cropped_image = self._crop_and_encode_image(image_data, bbox)
                
                with Session() as session:
                    existing_template = session.query(Template).filter_by(
                        base64_image=cropped_image,
                        agent_name=agent_name
                    ).first()
                    
                    if existing_template:
                        existing_template.caption = caption
                        existing_template.page_name = page_name
                        logger.info(f"Updated existing template caption to: {caption}")
                    else:
                        template_obj = Template(
                            base64_image=cropped_image,
                            caption=caption,
                            agent_name=agent_name,
                            page_name=page_name
                        )
                        session.add(template_obj)
                        logger.info(f"Saved new template with caption: {caption}")
                    
                    session.commit()
                
        except Exception as e:
            logger.error(f"Failed to save templates: {e}")
            raise

    def _calculate_size_context(self, template_detections: List[Detection], 
                              yolo_detections: List[Detection]) -> float:
        """Calculate median area and minimum threshold"""
        all_boxes = [d.bbox for d in template_detections + yolo_detections]
        if not all_boxes:
            return 0
            
        box_areas = [SmallBoxFilter()._get_box_area(bbox) for bbox in all_boxes]
        median_area = np.median(box_areas)
        return median_area * 0.2  # 20% of median area

    def process_screenshot(self, image_data: str, agent_name: str) -> Dict:
        """Process screenshot using detection pipeline"""
        self.template_detector = TemplateDetector(agent_name=agent_name)
        
        # Run detectors
        screen_data = ScreenData(image_data=image_data)
        template_results = self.template_detector.detect(screen_data)
        yolo_icon_elements = (
            self.yolo_detector.detect(screen_data).icon_elements
            if self.yolo_detector is not None else []
        )

        # Convert to Detection objects
        all_detections = []

        # Use template IDs for template matches
        for t in template_results.icon_elements:
            all_detections.append(Detection(
                id=t.template_id,  # Use the actual template ID from database
                bbox=t.bbox,
                confidence=t.confidence,
                caption=t.caption,
                source='template'
            ))

        # Use UUID for YOLO detections
        for y in yolo_icon_elements:
            all_detections.append(Detection(
                id=str(uuid.uuid4()),  # Generate unique UUID for each YOLO detection
                bbox=y.bbox,
                confidence=y.confidence,
                caption=None,
                source='yolo'
            ))
        
        # Create filter context
        context = {
            'image_data': image_data,
            'template_detections': all_detections[:len(template_results.icon_elements)],
            'min_area_threshold': self._calculate_size_context(
                all_detections[:len(template_results.icon_elements)],
                all_detections[len(template_results.icon_elements):]
            ),
            'iou_threshold': 0.3
        }
        
        # Apply filters to YOLO detections
        filtered_detections = [d for d in all_detections if (
            d.source == 'template' or 
            all(f.filter(d, context) for f in self.filters)
        )]
        
        # Convert back to dictionary format
        return {
            'detections': [
                {
                    'id': d.id,
                    'bbox': d.bbox,
                    'confidence': d.confidence,
                    'caption': d.caption,
                    'source': d.source  # Include source in response
                } for d in filtered_detections
            ],
            'image': image_data
        }
    
    def _crop_and_encode_image(self, image_data: str, bbox: List[float]) -> str:
        """
        Crop image to bbox region and return base64 encoded result
        
        Args:
            image_data: Base64 encoded full image
            bbox: Bounding box coordinates [x1, y1, x2, y2]
            
        Returns:
            Base64 encoded cropped image
        """
        # Decode base64 image
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert bbox coordinates to integers
        x1, y1, x2, y2 = map(int, bbox)
        
        # Crop image
        cropped = img[y1:y2, x1:x2]
        
        # Encode cropped image to base64
        _, buffer = cv2.imencode('.png', cropped)
        cropped_b64 = base64.b64encode(buffer).decode('utf-8')
        
        return cropped_b64

    def get_templates(self, agent_name: str) -> List[Dict]:
        """Retrieve all templates for a given agent."""
        with Session() as session:
            templates = session.query(Template).filter_by(agent_name=agent_name).all()
            return [template.to_dict() for template in templates]

    def save_templates(self, data: Dict) -> List[Dict]:
        """
        Save templates with UUID handling.
        - Updates existing templates if ID exists (updates caption/image)
        - Creates new templates with new UUIDs for entries without IDs
        - Creates new templates with provided UUIDs for YOLO detections that were captioned
        """
        templates = data['templates']
        agent_name = data['agent_name']
        page_name = data['page_name']
        image_data = data['image']
        results = []

        with Session() as session:
            try:
                for template_data in templates:
                    try:
                        # Crop image for this template
                        bbox = template_data['bbox']
                        cropped_image = self._crop_and_encode_image(
                            image_data, 
                            bbox
                        )

                        template_id = template_data.get('id')
                        
                        if template_id:
                            # Check if template exists for this agent
                            existing_template = session.query(Template).filter_by(
                                id=template_id,
                                agent_name=agent_name
                            ).first()
                            
                            if existing_template:
                                # Update existing template
                                existing_template.caption = template_data['caption']
                                existing_template.base64_image = cropped_image
                                existing_template.page_name = page_name
                                existing_template.updated_at = datetime.utcnow()
                                message = 'Template updated'
                            else:
                                # Create new template with provided UUID (from YOLO detection)
                                new_template = Template(
                                    id=template_id,
                                    agent_name=agent_name,
                                    page_name=page_name,
                                    caption=template_data['caption'],
                                    base64_image=cropped_image
                                )
                                session.add(new_template)
                                message = 'New template created with provided ID'
                        else:
                            # Create new template with new UUID (user-created box)
                            new_id = str(uuid.uuid4())
                            new_template = Template(
                                id=new_id,
                                agent_name=agent_name,
                                page_name=page_name,
                                caption=template_data['caption'],
                                base64_image=cropped_image
                            )
                            session.add(new_template)
                            template_id = new_id
                            message = 'New template created with new ID'

                        results.append({
                            'success': True,
                            'message': message,
                            'id': template_id
                        })

                    except Exception as e:
                        logger.error(f"Failed to save template: {str(e)}")
                        results.append({
                            'success': False,
                            'message': f"Failed to save template: {str(e)}"
                        })

                session.commit()
                return results

            except Exception as e:
                logger.error(f"Database error: {str(e)}")
                session.rollback()
                raise
