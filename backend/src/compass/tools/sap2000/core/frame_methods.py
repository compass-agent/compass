import logging
from typing import Dict, List
from collections import defaultdict
import traceback

logger = logging.getLogger(__name__)

class FrameMethods:
    def get_beams_info(self, tolerance: float = 1.0) -> Dict[float, List[str]]:
        """
        Groups all beams in the model by their approximate length.

        Args:
            tolerance: Tolerance for length matching (default 1.0 ft)
            
        Returns:
            Dictionary mapping lengths to lists of beam frame names
            e.g. {24.0: ['beam1', 'beam2', ...], 10.0: ['beam3', ...]}
        """
        try:
            # Get all frame objects
            number_frames, frame_names, ret = self._model.FrameObj.GetNameList()
            if ret != 0 or not frame_names:
                logger.error("Failed to get frame names from model")
                return {}
                
            # Dictionary to store beams grouped by length
            beams_by_length = {}
            
            # Process each frame
            for frame in frame_names:
                # Get frame endpoints
                point_i, point_j, ret = self._model.FrameObj.GetPoints(frame)
                if ret != 0:
                    continue
                    
                # Get coordinates
                x_i, y_i, z_i, ret_i = self._model.PointObj.GetCoordCartesian(point_i)
                x_j, y_j, z_j, ret_j = self._model.PointObj.GetCoordCartesian(point_j)
                
                if ret_i != 0 or ret_j != 0:
                    continue
                
                # Determine if frame is beam (horizontal)
                is_beam = abs(z_i - z_j) <= 0.1
                
                if is_beam:
                    # Calculate beam length
                    dx = x_j - x_i
                    dy = y_j - y_i
                    frame_length = (dx**2 + dy**2)**0.5
                    
                    # Round length to the nearest foot (or tolerance level)
                    rounded_length = round(frame_length / tolerance) * tolerance
                    
                    # Add to the dictionary
                    if rounded_length not in beams_by_length:
                        beams_by_length[rounded_length] = []
                        
                    beams_by_length[rounded_length].append(frame)
            
            # Log summary
            beam_counts = {length: len(beams) for length, beams in beams_by_length.items()}
            logger.info(f"Beam length distribution: {beam_counts}")
            
            return beams_by_length
            
        except Exception as e:
            logger.error(f"Error in get_beams_info: {str(e)}")
            return {}

    def get_columns_info(self, tolerance: float = 1.0) -> Dict[str, List[str]]:
        """
        Groups all columns in the model by their location (corner, edge, interior).

        Args:
            tolerance: Tolerance for coordinate comparison (default 1.0 ft)
            
        Returns:
            Dictionary mapping location types to lists of column frame names
            e.g. {'corner': ['column1', ...], 'edge': ['column2', ...], 'interior': ['column3', ...]}
        """
        try:
            # Get all frame objects
            number_frames, frame_names, ret = self._model.FrameObj.GetNameList()
            if ret != 0 or not frame_names:
                logger.error("Failed to get frame names from model")
                return {}
                
            # Dictionary to store columns grouped by location
            columns_by_location = {
                'corner': [],
                'edge': [],
                'interior': []
            }
            
            # Get all points in the model to determine building bounds
            number_points, point_names, ret = self._model.PointObj.GetNameList()
            if ret != 0 or not point_names:
                logger.error("Failed to get point names from model")
                return {}
            
            # Collect all X and Y coordinates
            x_coords = []
            y_coords = []
            for point in point_names:
                x, y, z, ret = self._model.PointObj.GetCoordCartesian(point)
                if ret == 0:
                    x_coords.append(x)
                    y_coords.append(y)
            
            # If no points found, return empty
            if not x_coords or not y_coords:
                logger.error("Failed to determine building bounds - no valid points found")
                return {}
                
            # Calculate actual bounds
            x_min = min(x_coords)
            x_max = max(x_coords)
            y_min = min(y_coords)
            y_max = max(y_coords)
            
            logger.info(f"Building bounds: X=[{x_min}, {x_max}], Y=[{y_min}, {y_max}]")
                
            # Process each frame
            for frame in frame_names:
                # Get frame endpoints
                point_i, point_j, ret = self._model.FrameObj.GetPoints(frame)
                if ret != 0:
                    continue
                    
                # Get coordinates
                x_i, y_i, z_i, ret_i = self._model.PointObj.GetCoordCartesian(point_i)
                x_j, y_j, z_j, ret_j = self._model.PointObj.GetCoordCartesian(point_j)
                
                if ret_i != 0 or ret_j != 0:
                    continue
                
                # Determine if frame is column (vertical)
                is_column = abs(z_i - z_j) > 0.1
                
                if is_column:
                    # Use lower Z point for column position check
                    x, y = (x_i, y_i) if z_i <= z_j else (x_j, y_j)
                    
                    # Check column position using calculated bounds
                    is_corner = (abs(x - x_min) < tolerance or abs(x - x_max) < tolerance) and \
                                (abs(y - y_min) < tolerance or abs(y - y_max) < tolerance)
                    
                    is_edge = (abs(x - x_min) < tolerance or abs(x - x_max) < tolerance or \
                              abs(y - y_min) < tolerance or abs(y - y_max) < tolerance)
                    
                    # Classify column based on position
                    if is_corner:
                        columns_by_location['corner'].append(frame)
                    elif is_edge:
                        columns_by_location['edge'].append(frame)
                    else:
                        columns_by_location['interior'].append(frame)
            
            # Log summary
            column_counts = {loc: len(cols) for loc, cols in columns_by_location.items()}
            logger.info(f"Column location distribution: {column_counts}")
            
            return columns_by_location
            
        except Exception as e:
            logger.error(f"Error in get_columns_info: {str(e)}")
            return {'corner': [], 'edge': [], 'interior': []}


    def add_section_candidates_to_frames(self, frames):
        """Add section candidates to each frame based on configuration settings.
        
        Args:
            frames: Dictionary of frames with their properties
            
        Returns:
            Updated frames dictionary with section candidates added
        """
        # Get section types and filter criteria from config
        section_types = self.config.section_candidates.section_types

        # Load the template list of section names and weights
        section_candidates_template = self.load_section_names()

        # Check if any sections were loaded
        if not section_candidates_template:
            logger.error(f"Could not load section names for types: {section_types}")
            return frames

        # Get sections for the first type (currently we only support one type)
        base_sections = section_candidates_template.get(section_types[0], [])
        if not base_sections:
            logger.error(f"No sections found for type: {section_types[0]}")
            return frames

        logger.info(f"Assigning {len(base_sections)} section candidates to {len(frames)} frames")
        for frame_name, frame_info in frames.items():
            # Create an independent copy of the list and its dictionaries for each frame
            # This prevents modifications to one frame's section data affecting others
            frame_info['sections'] = [dict(s) for s in base_sections]
        return frames

    def get_all_frames(self) -> Dict[str, Dict]:
        """
        Gets all frames in the model and classifies them as beams or columns.

        Returns:
            Dictionary mapping frame names to frame info dictionaries
            e.g. {'B1': {'type': 'beam', 'length': 24.0}, 'C1': {'type': 'column', 'length': 12.0}}
        """
        try:
            number_frames, frame_names, ret = self._model.FrameObj.GetNameList()
            if ret != 0 or not frame_names:
                logger.error("Failed to get frame names from model")
                return {}
            frames_info = {}
            
            # First, get all points coordinates for floor determination
            point_coordinates = {}
            number_points, point_names, ret = self._model.PointObj.GetNameList()
            if ret == 0 and point_names:
                for point in point_names:
                    x, y, z, ret = self._model.PointObj.GetCoordCartesian(point)
                    if ret == 0:
                        point_coordinates[point] = (x, y, z)
            
            # Collect unique Z coordinates to identify floors
            unique_z_coords = sorted(set(z for _, _, z in point_coordinates.values()))
            floor_levels = {z: idx+1 for idx, z in enumerate(unique_z_coords)}
            
            # Build a mapping of points to connected frames for adjacency detection
            points_to_frames = {}
            for frame in frame_names:
                point_i, point_j, ret = self._model.FrameObj.GetPoints(frame)
                if ret == 0:
                    if point_i not in points_to_frames:
                        points_to_frames[point_i] = []
                    if point_j not in points_to_frames:
                        points_to_frames[point_j] = []
                    points_to_frames[point_i].append(frame)
                    points_to_frames[point_j].append(frame)
            
            # Process each frame
            for frame in frame_names:
                # Get frame endpoints
                point_i, point_j, ret = self._model.FrameObj.GetPoints(frame)
                if ret != 0:
                    continue
                    
                # Get coordinates
                if point_i not in point_coordinates or point_j not in point_coordinates:
                    continue
                
                x_i, y_i, z_i = point_coordinates[point_i]
                x_j, y_j, z_j = point_coordinates[point_j]
                
                # Determine if frame is beam (horizontal) or column (vertical)
                is_beam = abs(z_i - z_j) <= 0.1
                
                # Calculate length
                dx = x_j - x_i
                dy = y_j - y_i
                dz = z_j - z_i
                frame_length = (dx**2 + dy**2 + dz**2)**0.5
                
                # Determine floor based on Z coordinate (use the lower endpoint for columns)
                frame_z = min(z_i, z_j) if not is_beam else z_i  # For beams use any point
                floor = floor_levels.get(frame_z, 1)  # Default to floor 1 if not found
                
                # Find adjacent frames (frames that share an endpoint with this frame)
                adjacent_frames = []
                for point in [point_i, point_j]:
                    for adj_frame in points_to_frames.get(point, []):
                        if adj_frame != frame and adj_frame not in adjacent_frames:
                            adjacent_frames.append(adj_frame)
                
                # Add to the dictionary with appropriate type, length, floor and adjacent frames
                frames_info[frame] = {
                    'type': 'beam' if is_beam else 'column',
                    'length': frame_length,
                    'floor': floor,
                    'floor_z': frame_z,  # Add the actual Z coordinate of the floor
                    'adjacent_frames': adjacent_frames,
                    'point_i': point_i,
                    'point_j': point_j,
                    'coords_i': (x_i, y_i, z_i),
                    'coords_j': (x_j, y_j, z_j)
                }
            
            # Log summary
            beam_count = sum(1 for info in frames_info.values() if info['type'] == 'beam')
            column_count = sum(1 for info in frames_info.values() if info['type'] == 'column')
            logger.info(f"Frame classification summary: {beam_count} beams, {column_count} columns")
            logger.info(f"Identified {len(floor_levels)} floor levels")
            
            return frames_info
            
        except Exception as e:
            logger.error(f"Error in get_all_frames: {str(e)}")
            return {}

    def import_section_properties_to_sap(self, section_property_names: List[str]):
        logger.info(f"Importing {len(section_property_names)} unique section properties")
        for section_name in section_property_names:
            ret = self._model.PropFrame.ImportProp(
                section_name,
                "A992Fy50",
                "AISC16.xml",
                section_name
            )
            if ret != 0:
                logger.warning(f"Failed to import section {section_name}. It could be already imported.")

