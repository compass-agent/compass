from typing import List, Optional, Literal
from pydantic import BaseModel, Field, validator
import yaml
import os
import logging

logger = logging.getLogger(__name__)

class MaterialSteel(BaseModel):
    name: str
    type: Literal["STEEL"]

class Materials(BaseModel):
    steel: MaterialSteel

class Restraints(BaseModel):
    base_restraints: List[bool] = Field(..., min_items=6, max_items=6)
    auto_detect_columns: bool = True

class LoadPattern(BaseModel):
    name: str
    type: Literal["DEAD", "LIVE"]

class AreaLoads(BaseModel):
    dead: float
    live: float

class FloorLoads(BaseModel):
    floor: AreaLoads
    roof: AreaLoads

class ExclusionPoint(BaseModel):
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None

    @validator('x', 'y', 'z')
    def validate_coordinates(cls, v):
        if v is not None and v < 0:
            raise ValueError("Coordinates cannot be negative")
        return v

class Loads(BaseModel):
    patterns: List[LoadPattern]
    area_loads: FloorLoads
    load_direction_type: Literal["GLOBAL_X", "GLOBAL_Y", "GLOBAL_Z", "DECK_ORIENTED"]
    exclusion_areas: List[ExclusionPoint]

class SectionFilter(BaseModel):
    depth_range: List[float] = Field(..., min_items=2, max_items=2)
    weight_range: List[float] = Field(..., min_items=2, max_items=2)

    @validator('depth_range', 'weight_range')
    def validate_ranges(cls, v):
        if v[0] >= v[1]:
            raise ValueError("First value must be less than second value")
        if any(x < 0 for x in v):
            raise ValueError("Range values cannot be negative")
        return v

class SectionCandidates(BaseModel):
    section_types: List[Literal["W", "HSS", "PIPE", "L", "WT", "C", "MC"]]
    filter: SectionFilter

class ObjectiveWeights(BaseModel):
    weight_minimization: float = Field(..., ge=0.0, le=1.0)
    connection_compatibility: float = Field(..., ge=0.0, le=1.0)
    floor_consistency: float = Field(..., ge=0.0, le=1.0)

class Design(BaseModel):
    code: Literal["AISC 360-16"]  # Add more codes as needed
    maximum_allowed_usage_ratio: float = Field(..., ge=0.0, le=1.0)
    objective_weights: ObjectiveWeights
    max_groups: int = Field(..., ge=1)
    beam_column_segregation: bool
    group_by_floor: bool

class ModelConfig(BaseModel):
    """Main configuration model that represents the entire config.yaml structure"""
    general: dict = Field(..., description="General settings including units and model path")
    materials: Materials
    restraints: Restraints
    loads: Loads
    section_candidates: SectionCandidates
    design: Design

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'ModelConfig':
        """Load configuration from a YAML file"""
        try:
            with open(yaml_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return cls(**config_dict)
        except Exception as e:
            logger.error(f"Error loading config from {yaml_path}: {str(e)}")
            raise

    def to_yaml(self, yaml_path: str) -> None:
        """Save configuration to a YAML file"""
        try:
            config_dict = self.model_dump()
            with open(yaml_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error saving config to {yaml_path}: {str(e)}")
            raise

    def validate_config(self) -> bool:
        """Additional validation beyond Pydantic's built-in validation"""
        # Add any custom validation logic here
        return True
