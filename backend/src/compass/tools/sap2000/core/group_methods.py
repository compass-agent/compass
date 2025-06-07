import logging
from typing import List, Tuple, Dict

logger = logging.getLogger(__name__)

class GroupMethods:
    def create_assign_section_group(
        self, 
        group_name: str, 
        frames: List[str]
    ) -> Tuple[List[str], int]:
        """
        Creates a group and assigns the specified frames to it.
        
        Args:
            group_name: Name of the group to create
            frames: List of frame names to include in the group
            
        Returns:
            tuple: (list of frame names in the group, status code)
            where status code is 0 for success, 1 for failure
        """
        try:
            # Create the group if it doesn't exist
            ret = self._model.GroupDef.SetGroup(group_name)
            if ret != 0:
                logger.warning(f"Failed to create group {group_name}")
                return ([], 1)
                
            # Track successfully added frames
            added_frames = []
            
            # Add frames to the group
            for frame in frames:
                ret = self._model.FrameObj.SetGroupAssign(frame, group_name)
                if ret != 0:
                    logger.warning(f"Failed to assign frame {frame} to group {group_name}")
                else:
                    added_frames.append(frame)
            
            logger.info(f"Successfully created group {group_name} with {len(added_frames)} frames")
            return (added_frames, 0)
            
        except Exception as e:
            logger.error(f"Error in create_assign_section_group: {str(e)}")
            return ([], 1)

    def analyze_group_utilization(self, group_name: str, frame_type: str = "Beam") -> List[Tuple[str, float]]:
        """
        Analyzes the utilization ratios for frames in a group and logs useful statistics.
        Identifies underutilized frames that could potentially be regrouped.
        
        Args:
            group_name: Name of the frame group to analyze
            frame_type: Type of frame ("Beam" or "Column") for logging purposes
            
        Returns:
            List of underutilized frames with their utilization ratios
        """
        try:
            # Get utilization ratios for the group
            # The GetSummaryResults API returns a tuple with the following structure:
            # (number_items, frame_names, ratios, ratio_types, locations, combo_names, error_summary, warning_summary, status)
            ret = self._model.DesignSteel.GetSummaryResults(
                group_name,
                0,  # number_items (will be populated in results)
                [],  # frame_names (will be populated in results)
                [],  # ratios (will be populated in results)
                [],  # ratio_types (will be populated in results)
                [],  # locations (will be populated in results)
                [],  # combo_names (will be populated in results)
                [],  # error_summary (will be populated in results)
                [],  # warning_summary (will be populated in results)
                1   # ItemType = Group
            )
            
            # Parse the return value - last element (index 8) is the status code
            status_code = ret[8]
            if status_code != 0:  # Status code (0 = success)
                logger.warning(f"No utilization results found for group: {group_name}, error code: {status_code}")
                return []
                
            # Extract data from the returned tuple
            number_items = ret[0]  # First element is the number of items
            frame_names = ret[1]
            ratios = ret[2]
            ratio_types = ret[3]
            locations = ret[4]
            combo_names = ret[5]
            error_summary = ret[6]
            warning_summary = ret[7]
            
            # Check if we have valid data
            if not frame_names or not ratios:
                logger.warning(f"No utilization results found for group: {group_name}")
                return []
                
            # Log any errors or warnings
            for i, error in enumerate(error_summary):
                if error and error.strip():
                    logger.error(f"Design error for {frame_names[i]}: {error}")
            
            for i, warning in enumerate(warning_summary):
                if warning and warning.strip():
                    logger.warning(f"Design warning for {frame_names[i]}: {warning}")
            
            # Calculate statistics
            avg_ratio = sum(ratios) / len(ratios) if ratios else 0
            max_ratio = max(ratios) if ratios else 0
            min_ratio = min(ratios) if ratios else 0
            
            # Get index of max utilized frame
            max_index = ratios.index(max_ratio) if ratios else -1
            
            # Log group summary
            logger.info(f"{group_name} Utilization Summary:")
            logger.info(f"  Total Members: {number_items}")
            logger.info(f"  Average Utilization: {avg_ratio:.3f}")
            logger.info(f"  Maximum Utilization: {max_ratio:.3f}")
            logger.info(f"  Minimum Utilization: {min_ratio:.3f}")
            
            # Log most utilized frame details
            if max_index >= 0:
                max_frame = frame_names[max_index]
                max_ratio_type = ratio_types[max_index]
                max_combo = combo_names[max_index]
                max_location = locations[max_index]
                
                # Get ratio type description
                ratio_type_desc = "Unknown"
                if max_ratio_type == 1:
                    ratio_type_desc = "PMM"
                elif max_ratio_type == 2:
                    ratio_type_desc = "Major shear"
                elif max_ratio_type == 3:
                    ratio_type_desc = "Minor shear"
                elif max_ratio_type == 4:
                    ratio_type_desc = "Major beam-column capacity"
                elif max_ratio_type == 5:
                    ratio_type_desc = "Minor beam-column capacity"
                elif max_ratio_type == 6:
                    ratio_type_desc = "Other"
                
                # Get section information
                section_name, auto_list, _ = self._model.FrameObj.GetSection(max_frame)
                
                logger.info(f"  Most Utilized {frame_type}:")
                logger.info(f"    Frame: {max_frame}")
                logger.info(f"    Section: {section_name}")
                logger.info(f"    Utilization: {max_ratio:.3f}")
                logger.info(f"    Controlling Type: {ratio_type_desc}")
                logger.info(f"    Location: {max_location} ft from start")
                logger.info(f"    Combo: {max_combo}")
            
            # Find and log underutilized frames (under 50% utilization)
            underutilized = [(frame_names[i], ratios[i]) for i in range(len(ratios)) if ratios[i] < 0.5]
            
            if underutilized:
                logger.info(f"  Underutilized {frame_type}s (below 50%):")
                for frame, ratio in sorted(underutilized, key=lambda x: x[1]):
                    section, _, _ = self._model.FrameObj.GetSection(frame)
                    logger.info(f"    {frame}: {ratio:.3f} (Section: {section})")
                    
                # Recommendation for potential regrouping
                if len(underutilized) > 2:
                    logger.info(f"  Recommendation: Consider regrouping {len(underutilized)} {frame_type.lower()}s with low utilization")
            
            return underutilized
        
        except Exception as e:
            logger.error(f"Error in analyze_group_utilization: {str(e)}")
            return []

    def add_base_restraints(self, frames: Dict[str, Dict]) -> Tuple[List[str], int]:
        """
        Add restraints to ground-level column bases by checking frame connectivity.
        Only restrains points that are at the bottom of columns with no frames connecting below them.
        
        Args:
            frames: Dictionary of frames with their properties
            
        Returns:
            tuple: (list of restrained point names, status code) where status code is 0 for success, 1 for failure
        """
        try:
            # Get restraints from config
            restraints = self.config.restraints.base_restraints

            # Get all frame names
            number_frames, frame_names, ret = self._model.FrameObj.GetNameList()
            if ret != 0 or not frame_names:
                logger.error("Failed to get frame names from model")
                return ([], 1)

            # Get all point names for later use
            number_points, point_names, ret = self._model.PointObj.GetNameList()
            if ret != 0 or not point_names:
                logger.error("Failed to get point names from model")
                return ([], 1)

            # Create a dictionary to store points and their connected frames
            point_connections = {}
            for point_name in point_names:
                point_connections[point_name] = []

            # Map frames to their points and build connectivity
            for frame_name in frame_names:
                point_i, point_j, ret = self._model.FrameObj.GetPoints(frame_name)
                if ret == 0:
                    point_connections[point_i].append(frame_name)
                    point_connections[point_j].append(frame_name)

            # Find and restrain ground-level column bases
            restrained_points = []
            for frame_name in frame_names:
                point_i, point_j, ret = self._model.FrameObj.GetPoints(frame_name)
                if ret != 0:
                    continue

                # Get coordinates of both points
                x_i, y_i, z_i, ret_i = self._model.PointObj.GetCoordCartesian(point_i)
                x_j, y_j, z_j, ret_j = self._model.PointObj.GetCoordCartesian(point_j)
                
                if ret_i != 0 or ret_j != 0:
                    continue

                # Determine which point is the bottom point
                bottom_point = point_i if z_i < z_j else point_j
                top_point = point_j if z_i < z_j else point_i

                # Check if this is a ground-level column by verifying no frames connect to the bottom point
                if len(point_connections[bottom_point]) == 1:  # Only connected to current frame
                    _, ret = self._model.PointObj.SetRestraint(bottom_point, restraints)
                    
                    if ret == 0:
                        restrained_points.append(bottom_point)
                        logger.info(f"Applied restraints to ground-level column base {bottom_point} "
                                  f"at coordinates ({x_i if bottom_point == point_i else x_j}, "
                                  f"{y_i if bottom_point == point_i else y_j}, "
                                  f"{z_i if bottom_point == point_i else z_j})")
                    else:
                        logger.warning(f"Failed to apply restraints to point {bottom_point}")

            logger.info(f"Successfully restrained {len(restrained_points)} ground-level column bases")
            return (restrained_points, 0)

        except Exception as e:
            logger.error(f"Error in add_base_restraints: {str(e)}")
            return ([], 1)
