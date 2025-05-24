import logging
import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Union

import comtypes.client
from .area_methods import AreaMethods
from .frame_methods import FrameMethods
from .group_methods import GroupMethods
from .design_optimization import DesignOptimization
from .config_manager import ModelConfig

logger = logging.getLogger(__name__)

class CustomSAP2000Model(AreaMethods, FrameMethods, GroupMethods, DesignOptimization):
    """
    Custom SAP2000 model class that extends the base SAP2000 model with additional functionality.
    """
    def __init__(self, sap_model, config: ModelConfig):
        self._model = sap_model
        self.config = config

    def load_section_names(self) -> Dict[str, List[Dict[str, Union[str, float]]]]:
        """
        Loads and parses the AISC16.xml file to get all section names and properties
        using the section types and filter criteria from config.
        
        Returns:
            Dict mapping section types (W, L, C, etc.) to lists of filtered dictionaries, where each 
            dictionary contains section properties (name, nominal_depth, depth, weight, area)
        """
        xml_path = os.path.join(os.path.dirname(__file__), 'data', 'AISC16.xml')
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Get section types and filter criteria from config
        section_types = self.config.section_candidates.section_types
        depth_range = tuple(self.config.section_candidates.filter.depth_range)
        weight_range = tuple(self.config.section_candidates.filter.weight_range)
        
        # Handle XML namespace
        # Extract namespace from root tag
        ns = {'ns': root.tag.split('}')[0].strip('{')} if '}' in root.tag else ''
        
        # Dictionary to store section names by type
        section_names = {
            'W': [],  # Wide flange sections (from STEEL_I_SECTION)
            'L': [],  # Angle sections
            'C': [],  # Channel sections
            'WT': [], # Tee sections
            'HSS': [] # Hollow structural sections
        }
        
        # Parse each section type
        section_mappings = {
            'STEEL_I_SECTION': ['W'],  # W sections from I sections
            'STEEL_ANGLE': ['L'],  # Angle sections
            'STEEL_CHANNEL': ['C'],  # Channel sections
            #'STEEL_TEE': ['WT'],  # Tee sections
            #'STEEL_BOX': ['HSS'],  # Box sections
            #'STEEL_PIPE': ['HSS']  # Pipe sections (also HSS)
        }
        
        for xml_type, designations in section_mappings.items():
            # Find all sections of this type, handling potential namespace
            xpath = f".//{xml_type}" if not ns else f".//ns:{xml_type}"
            for section in root.findall(xpath, namespaces=ns):
                # Find elements, handling potential namespace
                label_elem = section.find('LABEL' if not ns else 'ns:LABEL', namespaces=ns)
                designation_elem = section.find('DESIGNATION' if not ns else 'ns:DESIGNATION', namespaces=ns)
                
                if label_elem is not None and designation_elem is not None:
                    label = label_elem.text
                    designation = designation_elem.text
                    
                    # Extract additional properties
                    depth_elem = section.find('D' if not ns else 'ns:D', namespaces=ns)
                    area_elem = section.find('A' if not ns else 'ns:A', namespaces=ns)
                    
                    # Create section dictionary with properties
                    section_dict = {
                        'name': label,
                        'nominal_depth': None,
                        'depth': float(depth_elem.text) if depth_elem is not None else None,
                        'weight': None,
                        'area': float(area_elem.text) if area_elem is not None else None
                    }
                    
                    # Extract nominal depth and weight from section name (e.g., W24X162 -> depth=24, weight=162)
                    if 'X' in label:
                        parts = label.split('X')
                        if len(parts) == 2:
                            # Extract the numeric part after the designation letter (e.g., W24 -> 24)
                            prefix = parts[0]
                            for i, char in enumerate(prefix):
                                if char.isdigit():
                                    section_dict['nominal_depth'] = float(prefix[i:])
                                    break
                            
                            # Extract weight (e.g., 162)
                            try:
                                section_dict['weight'] = float(parts[1])
                            except ValueError:
                                pass
                    
                    # Store in appropriate category if designation matches
                    if designation in designations:
                        section_names[designation].append(section_dict)
        
        # Initial log before filtering
        for section_type, sections in section_names.items():
            logger.info(f"Parsed {len(sections)} {section_type} sections initially.")
            
        # Filter sections based on provided criteria
        filtered_section_names = {}
        for section_type, sections in section_names.items():
            # Filter by section type
            if section_types is not None and section_type not in section_types:
                continue

            filtered_list = []
            keep_rate = 30
            keeping_idx = 0
            for section in sections:
                keeping_idx += 1
                # Filter by depth range
                if depth_range is not None:
                    min_depth, max_depth = depth_range
                    if section['depth'] is None or not (min_depth <= section['depth'] <= max_depth):
                        continue
                
                # Filter by weight range
                if weight_range is not None:
                    min_weight, max_weight = weight_range
                    if section['weight'] is None or not (min_weight <= section['weight'] <= max_weight):
                        continue
                if keeping_idx % keep_rate != 0:
                    continue
                
                filtered_list.append(section)
            
            if filtered_list:
                filtered_section_names[section_type] = filtered_list
                logger.info(f"Filtered to {len(filtered_list)} {section_type} sections.")
        
        # Calculate and log percentiles for the *filtered* depth and weight
        for section_type, sections in filtered_section_names.items():
            if sections:
                # Extract non-None depth and weight values
                depths = [s['depth'] for s in sections if s['depth'] is not None]
                weights = [s['weight'] for s in sections if s['weight'] is not None]
                
                # Sort values for percentile calculation
                depths.sort()
                weights.sort()
                
                # Calculate percentiles
                if depths:
                    p10_depth_idx = int(0.1 * len(depths))
                    p50_depth_idx = int(0.5 * len(depths))
                    p90_depth_idx = int(0.9 * len(depths))
                    
                    p10_depth = depths[p10_depth_idx]
                    p50_depth = depths[p50_depth_idx]
                    p90_depth = depths[p90_depth_idx]
                    
                    logger.info(f"Filtered {section_type} depth percentiles - P10: {p10_depth:.2f}, P50: {p50_depth:.2f}, P90: {p90_depth:.2f}")
                
                if weights:
                    p10_weight_idx = int(0.1 * len(weights))
                    p50_weight_idx = int(0.5 * len(weights))
                    p90_weight_idx = int(0.9 * len(weights))
                    
                    p10_weight = weights[p10_weight_idx]
                    p50_weight = weights[p50_weight_idx]
                    p90_weight = weights[p90_weight_idx]
                    
                    logger.info(f"Filtered {section_type} weight percentiles - P10: {p10_weight:.2f}, P50: {p50_weight:.2f}, P90: {p90_weight:.2f}")
            
        return filtered_section_names

    def __getattr__(self, name):
        """
        Forward any unknown attribute access to the underlying model.
        """
        return getattr(self._model, name) 