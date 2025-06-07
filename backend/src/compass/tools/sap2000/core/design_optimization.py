import logging
from typing import Dict, List, Callable, Tuple
import traceback

logger = logging.getLogger(__name__)


class DesignOptimization:

    def calculate_section_usage_ratios(self, frames: Dict[str, Dict], model_path: str) -> Dict[str, Dict]:
        if not frames:
            logger.error("No frames provided to calculate_section_usage_ratios")
            return {}

        # Find the maximum number of sections per frame
        max_sections = max([len(frame.get('sections', [])) for frame in frames.values()], default=0)
        max_sections = min(max_sections, 100)  # Limit to first x candidates to save time
        
        # Set design code from config
        self._model.DesignSteel.SetCode(self.config.design.code)

        # STEP 0: Import all unique sections at once
        unique_sections = {section['name'] for frame_info in frames.values() 
                          if 'sections' in frame_info 
                          for section in frame_info['sections']}
        self.import_section_properties_to_sap(unique_sections)

        # STEP 2: Run the analysis ONCE with initial sections
        logger.info("Running analysis with initial sections")
        self._model.Analyze.SetRunCaseFlag("DEAD", True)
        self._model.Analyze.SetRunCaseFlag("LIVE", True)
        self._model.File.Save(model_path)
        ret = self._model.Analyze.RunAnalysis()
        ret = self._model.DesignSteel.StartDesign()

        # STEP 3: For each section candidate, run only the design check
        for section_index in range(max_sections):
            logger.info(f"Running design checks for section candidate {section_index+1}/{max_sections}")
            
            # Unlock the model before setting sections
            ret = self._model.SetModelIsLocked(False)
            if ret != 0:
                logger.error("Failed to unlock the model")
                return frames
            
            # Assign the section at this index to each frame
            for frame_name, frame_info in frames.items():
                if 'sections' in frame_info and section_index < len(frame_info['sections']):
                    section_candidate = frame_info['sections'][section_index]
                    section_name = section_candidate['name']
                    
                    # Set the section for this frame - section is already imported
                    ret = self._model.FrameObj.SetSection(frame_name, section_name, 0)
                    
                    # IMPORTANT: Also set the design section to keep it in sync with analysis section
                    ret = self._model.DesignSteel.SetDesignSection(frame_name, section_name, False, 0)
                    
                    # Verify section was actually changed
                    actual_section, auto_list, ret = self._model.FrameObj.GetSection(frame_name)
                    if actual_section != section_name:
                        raise Exception(f"Section mismatch for frame {frame_name}: Expected {section_name}, got {actual_section}")
            
            # Run only the steel design check (not full analysis)
            logger.info(f"Running design for section set {section_index+1}")
            # Run analysis with new sections
            self._model.Analyze.SetRunCaseFlag("DEAD", True)
            self._model.Analyze.SetRunCaseFlag("LIVE", True)
            ret = self._model.Analyze.RunAnalysis()
            ret = self._model.DesignSteel.StartDesign()
            
            # Extract usage ratios for each frame
            for frame_name, frame_info in frames.items():
                if 'sections' in frame_info and section_index < len(frame_info['sections']):
                    # Get design results for this frame
                    # Based on API: NumberItems, FrameName, Ratio, RatioType, Location, ComboName, ErrorSummary, WarningSummary, ret
                    results = self._model.DesignSteel.GetSummaryResults(frame_name)
                    # Parse the results based on the documented API structure
                    if len(results) >= 9 and results[8] == 0:  # Success
                        frame_info['sections'][section_index]['usage_ratio'] = results[2][0]
                        frame_info['sections'][section_index]['ratio_type'] = results[3][0]
                        frame_info['sections'][section_index]['location'] = results[4][0]
                    else:
                        raise Exception(f"Failed to get design results for frame {frame_name}. Error code: {results[8]}")
        
        self.log_summary_print(frames)
        return frames

    def create_section_groups(self, frames: Dict[str, Dict]) -> Dict[str, List[str]]:
        """Assign exactly one section to every frame while allowing at most
        the number of distinct sections specified in the config. The problem is 
        formulated and solved as a Mixed-Integer Linear Program using PuLP.
        After solving, each frame dict is updated with an ``optimum_design`` key::

            frames[i]['optimum_design'] = {
                'group_id'    : int,   # identifier of the group / section
                'section_name': str,   # chosen section for the frame
                'usage_ratio' : float  # usage ratio of that section
            }

        Args:
            frames: Dictionary of frames with their properties

        The function returns the modified *frames* mapping.
        """
        # Import here to keep the dependency local and optional for callers
        import pulp

        if not frames:
            logger.error("No frames provided to create_section_groups")
            return {}

        # Get values from config
        max_groups = self.config.design.max_groups
        optimization_priorities = self.config.design.objective_weights
        beam_column_segregation = self.config.design.beam_column_segregation

        # Filter frames in-place and extract unique sections
        self.filter_frames_by_usage_ratio(frames)
        unique_sections = self.extract_unique_sections(frames)

        # Create MILP
        prob = pulp.LpProblem("Section_Optimization", pulp.LpMinimize)

        # Binary vars x_{ip}: frame i uses section p
        x_vars = {}
        for f_name, f_data in frames.items():
            for s in f_data["sections"]:
                x_vars[(f_name, s["name"])] = pulp.LpVariable(f"x_{f_name}_{s['name']}", cat="Binary")

        # Binary vars y_p: section p is active anywhere
        y_vars = {sec: pulp.LpVariable(f"y_{sec}", cat="Binary") for sec in unique_sections}
        
        # Create a variables dictionary to pass to objective/constraint functions
        vars_dict = {"x_vars": x_vars, "y_vars": y_vars, "prob": prob}

        # Build the full objective function with all components using optimization priorities
        prob += optimization_priorities.weight_minimization * self.weight_minimization_objective(prob, frames, vars_dict)
        prob += optimization_priorities.connection_compatibility * self.connection_compatibility_objective(prob, frames, vars_dict)
        prob += optimization_priorities.floor_consistency * self.floor_consistency_objective(prob, frames, vars_dict)

        # Add constraints
        self.one_section_per_frame_constraint(prob, frames, vars_dict)
        self.section_activation_constraint(prob, frames, vars_dict)
        self.max_groups_constraint(prob, frames, vars_dict, max_groups)
        
        # Only add beam-column segregation constraint if enabled in config
        if beam_column_segregation:
            self.beam_column_segregation_constraint(prob, frames, vars_dict)

        # Solve MILP
        prob.solve(pulp.PULP_CBC_CMD(msg=False))

        if prob.status != pulp.LpStatusOptimal:
            raise RuntimeError("Optimization did not find an optimal solution")

        # Post-process solution
        active_sections = [sec for sec, y in y_vars.items() if pulp.value(y) > 0.5]
        group_ids = {sec: idx for idx, sec in enumerate(active_sections)}

        for f_name, f_data in frames.items():
            chosen_section = None
            for s in f_data["sections"]:
                if pulp.value(x_vars[(f_name, s["name"])]):
                    chosen_section = s
                    break

            frames[f_name]["optimum_design"] = {
                "group_id": group_ids[chosen_section["name"]],
                "section_name": chosen_section["name"],
                "usage_ratio": chosen_section.get("usage_ratio", None),
            }
        import json
        with open('frames3.json', 'w') as f:
            json.dump(frames, f)
        # implement the optimized design
        self.implement_optimized_design(frames)

        return frames

    def log_summary_print(self, frames: Dict[str, Dict]):
        # Log summary
        frames_processed = sum(1 for frame in frames.values() 
                            if 'sections' in frame 
                            and any('usage_ratio' in section for section in frame['sections']))
        logger.info(f"Calculated usage ratios for {frames_processed} frames")
        # calculate the max usage ration for all frames:
        max_usage_ratio = 0
        min_usage_ratio = 100
        per_frame_max_usage_ratios = []
        for frame_name, frame_info in frames.items():
            if 'sections' in frame_info:
                per_frame_max_usage_ratio =  max(section.get('usage_ratio', 0) for section in frame_info['sections'])
                max_usage_ratio = max(max_usage_ratio, per_frame_max_usage_ratio)
                min_usage_ratio = min(min_usage_ratio, per_frame_max_usage_ratio)
                per_frame_max_usage_ratios.append(per_frame_max_usage_ratio)
        logger.info(f"Max usage ratio for all frames: {max_usage_ratio}")   
        logger.info(f"Per frame max usage ratios: {per_frame_max_usage_ratios}")

    def implement_optimized_design(self, frames: Dict[str, Dict]) -> bool:
        """Implements the optimized design by creating groups and assigning sections.
        
        This method:
        1. Groups frames based on their optimized section assignments
        2. Creates SAP2000 groups for each distinct section group
        3. Assigns frames to their respective groups
        4. Sets the optimized section for each frame
        5. Runs analysis and design to validate the implemented design
        
        Args:
            frames: Dictionary of frames with their optimized design
            
        Returns:
            bool: True if implementation was successful, False otherwise
        """
        try:
            # First unlock the model
            ret = self._model.SetModelIsLocked(False)
            # Group frames by their group_id
            frames_by_group = {}
            for frame_name, frame_info in frames.items():
                group_id = frame_info['optimum_design']['group_id']
                section_name = frame_info['optimum_design']['section_name']
                
                if group_id not in frames_by_group:
                    frames_by_group[group_id] = {
                        'section': section_name,
                        'frames': []
                    }
                    
                frames_by_group[group_id]['frames'].append(frame_name)
                
            # Create groups and assign sections
            for group_id, group_info in frames_by_group.items():
                section_name = group_info['section']
                frame_list = group_info['frames']
                
                # Skip empty groups
                if not frame_list:
                    continue
                    
                # Create meaningful group name
                group_name = f"Group_{group_id}_{section_name}"
                
                # Create the group in SAP2000
                ret = self._model.GroupDef.SetGroup(group_name)
                if ret != 0:
                    logger.warning(f"Failed to create group {group_name}")
                    continue
                
                logger.info(f"Created group {group_name} for {len(frame_list)} frames with section {section_name}")
                
                # Assign frames to the group
                assigned_frames = 0
                for frame in frame_list:
                    # Assign frame to group
                    ret = self._model.FrameObj.SetGroupAssign(frame, group_name)
                    if ret != 0:
                        logger.warning(f"Failed to assign frame {frame} to group {group_name}")
                        continue
                    assigned_frames += 1
                
                logger.info(f"Successfully assigned {assigned_frames}/{len(frame_list)} frames to group {group_name}")
                
                # Now set the section for the entire group at once
                ret = self._model.FrameObj.SetSection(group_name, section_name, 1)  # 1 = Group
                if ret != 0:
                    logger.warning(f"Failed to set section {section_name} for group {group_name}")
                    continue
                
                # Also set the design section for the entire group
                ret = self._model.DesignSteel.SetDesignSection(group_name, section_name, False, 1)  # 1 = Group
                if ret != 0:
                    logger.warning(f"Failed to set design section {section_name} for group {group_name}")
                    continue
                
                logger.info(f"Successfully set section {section_name} for group {group_name}")
            
            # Run analysis and design to validate the optimized design
            logger.info("Running analysis with optimized sections")
            self._model.Analyze.SetRunCaseFlag("DEAD", True)
            self._model.Analyze.SetRunCaseFlag("LIVE", True)
            ret = self._model.Analyze.RunAnalysis()
            if ret != 0:
                logger.error("Failed to run analysis with optimized design")
                return False
                
            ret = self._model.DesignSteel.StartDesign()
            if ret != 0:
                logger.error("Failed to run design with optimized sections")
                return False
                
            logger.info("Successfully implemented and validated optimized design")
            return True
            
        except Exception as e:
            logger.error(f"Error in implement_optimized_design: {str(e)}")
            traceback.print_exc()
            return False

    def filter_frames_by_usage_ratio(self, frames: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Filter frames based on their usage ratio, removing frames that exceed the maximum allowed ratio.
        Uses the maximum allowed usage ratio from the configuration.

        Args:
            frames: Dictionary of frame data including usage ratios

        Returns:
            Dictionary containing only frames that meet the usage ratio criteria
        """
        max_allowed_ratio = self.config.design.maximum_allowed_usage_ratio
        
        for f_name, f_data in frames.items():
            if "sections" in f_data:
                f_data["sections"] = [
                    s for s in f_data["sections"] 
                    if s.get("usage_ratio", 0) <= max_allowed_ratio
                ]

    def extract_unique_sections(self, frames):
        """Extract set of unique section names from frames.
        
        Args:
            frames: Dictionary of frames with their properties
            
        Returns:
            Set of unique section names
        """
        unique_sections = set()
        for frame in frames.values():
            for s in frame.get("sections", []):
                unique_sections.add(s["name"])
        return unique_sections

    def weight_minimization_objective(self, prob, frames, vars_dict):
        """Objective that minimizes the total weight of all frames.
        
        Args:
            prob: PuLP problem instance
            frames: Dictionary of frames with their properties
            vars_dict: Dictionary containing optimization variables
            
        Returns:
            An objective term for total weight
        """
        import pulp
        
        x_vars = vars_dict["x_vars"]
        
        # Calculate total weight across all frames
        total_weight = pulp.lpSum(
            s["weight"] * frames[f_name]["length"] * x_vars[(f_name, s["name"])]
            for f_name, f_data in frames.items()
            for s in f_data["sections"]
        )
        
        return total_weight

    def connection_compatibility_objective(self, prob, frames, vars_dict):
        """Objective that penalizes depth differences between connected frames.
        
        Args:
            prob: PuLP problem instance
            frames: Dictionary of frames with their properties
            vars_dict: Dictionary containing optimization variables
            
        Returns:
            An objective term that can be added to the main objective
        """
        import pulp
        
        x_vars = vars_dict["x_vars"]
        
        # Create variables for depth differences (abs value approximation)
        depth_diff_vars = {}
        
        # Collect all connected frames
        total_penalty = 0
        
        # For each frame with adjacent_frames information
        for f_name, f_data in frames.items():
            if 'adjacent_frames' not in f_data:
                continue
                
            for adj_frame in f_data.get('adjacent_frames', []):
                if adj_frame not in frames:
                    continue
                    
                # Create a unique key for this connection (to avoid duplicates)
                conn_key = tuple(sorted([f_name, adj_frame]))
                
                # Skip if already processed this connection
                if conn_key in depth_diff_vars:
                    continue
                    
                # Create depth diff var for this connection
                depth_diff_var = pulp.LpVariable(f"depth_diff_{conn_key[0]}_{conn_key[1]}", 
                                                lowBound=0, cat="Continuous")
                depth_diff_vars[conn_key] = depth_diff_var
                
                # Add constraints to define the depth difference
                for s1 in f_data.get('sections', []):
                    for s2 in frames[adj_frame].get('sections', []):
                        if (f_name, s1['name']) in x_vars and (adj_frame, s2['name']) in x_vars:
                            # If both sections are selected, then depth_diff >= their depth difference
                            # This requires linearization since we can't directly use abs()
                            depth_diff = abs(s1.get('depth', 0) - s2.get('depth', 0))
                            
                            # This is a simplified version - a complete implementation would
                            # use binary variables and big-M constraints to model this properly
                            prob += (
                                depth_diff_var >= depth_diff * (x_vars[(f_name, s1['name'])] + x_vars[(adj_frame, s2['name'])] - 1),
                                f"depth_diff_{conn_key[0]}_{conn_key[1]}_{s1['name']}_{s2['name']}"
                            )
                
                # Add this connection's penalty to the total
                total_penalty += depth_diff_var
        
        return total_penalty

    def floor_consistency_objective(self, prob, frames, vars_dict):
        """Objective that penalizes using different sections for columns on the same floor.
        
        Args:
            prob: PuLP problem instance
            frames: Dictionary of frames with their properties
            vars_dict: Dictionary containing optimization variables
            
        Returns:
            An objective term that can be added to the main objective
        """
        import pulp
        import itertools
        
        x_vars = vars_dict["x_vars"]
        
        # Group frames by floor
        frames_by_floor = {}
        for f_name, f_data in frames.items():
            if 'floor' in f_data:
                floor = f_data['floor']
                if floor not in frames_by_floor:
                    frames_by_floor[floor] = []
                frames_by_floor[floor].append(f_name)
        
        # Create variables for section differences
        diff_vars = {}
        total_penalty = 0
        
        # For each floor, penalize different sections
        for floor, floor_frames in frames_by_floor.items():
            # Only consider columns for floor consistency
            floor_columns = [f for f in floor_frames if frames[f].get('type') == 'column']
            
            # For each pair of columns on this floor
            for f1, f2 in itertools.combinations(floor_columns, 2):
                # Create difference variable for this pair
                pair_key = tuple(sorted([f1, f2]))
                diff_var = pulp.LpVariable(f"floor_diff_{pair_key[0]}_{pair_key[1]}", 
                                        cat="Binary")
                diff_vars[pair_key] = diff_var
                
                # For each possible section pair
                for s1 in frames[f1].get('sections', []):
                    for s2 in frames[f2].get('sections', []):
                        if s1['name'] != s2['name'] and (f1, s1['name']) in x_vars and (f2, s2['name']) in x_vars:
                            # If both frames select different sections, diff must be 1
                            prob += (
                                diff_var >= x_vars[(f1, s1['name'])] + x_vars[(f2, s2['name'])] - 1,
                                f"floor_diff_{f1}_{f2}_{s1['name']}_{s2['name']}"
                            )
                
                # Add this pair's penalty to the total
                total_penalty += diff_var
        
        return total_penalty

    def beam_column_segregation_constraint(self, prob, frames, vars_dict):
        """Constraint that forces beams and columns to use different section groups.
        
        Args:
            prob: PuLP problem instance
            frames: Dictionary of frames with their properties
            vars_dict: Dictionary containing optimization variables
        """
        import pulp
        
        x_vars = vars_dict["x_vars"]
        y_vars = vars_dict["y_vars"]
        
        # Create binary variables for section type (beam or column)
        section_type_vars = {
            section_name: pulp.LpVariable(f"is_beam_section_{section_name}", cat="Binary")
            for section_name in y_vars.keys()
        }
        
        # For each active section, it must be either a beam section or a column section
        for section_name, is_beam_var in section_type_vars.items():
            # If section is used (y=1), then it must be classified (is_beam=0 or is_beam=1)
            prob += (is_beam_var <= y_vars[section_name], f"section_type_link_{section_name}")
        
        # A beam frame can only use a beam section
        for f_name, f_data in frames.items():
            if f_data.get('type') == 'beam':
                for s in f_data.get('sections', []):
                    if (f_name, s['name']) in x_vars:
                        prob += (
                            x_vars[(f_name, s['name'])] <= section_type_vars[s['name']],
                            f"beam_section_link_{f_name}_{s['name']}"
                        )
            elif f_data.get('type') == 'column':
                for s in f_data.get('sections', []):
                    if (f_name, s['name']) in x_vars:
                        prob += (
                            x_vars[(f_name, s['name'])] <= (1 - section_type_vars[s['name']]),
                            f"column_section_link_{f_name}_{s['name']}"
                        )

    def one_section_per_frame_constraint(self, prob, frames, vars_dict):
        """Constraint that enforces each frame to have exactly one section.
        
        Args:
            prob: PuLP problem instance
            frames: Dictionary of frames with their properties
            vars_dict: Dictionary containing optimization variables
        """
        import pulp
        
        x_vars = vars_dict["x_vars"]
        
        for f_name, f_data in frames.items():
            prob += (
                pulp.lpSum(x_vars[(f_name, s["name"])] for s in f_data["sections"]) == 1,
                f"one_section_{f_name}"
            )

    def section_activation_constraint(self, prob, frames, vars_dict):
        """Constraint that ensures sections are activated only if used by at least one frame.
        
        Args:
            prob: PuLP problem instance
            frames: Dictionary of frames with their properties
            vars_dict: Dictionary containing optimization variables
        """
        import pulp
        
        x_vars = vars_dict["x_vars"]
        y_vars = vars_dict["y_vars"]
        
        for (f_name, sec_name), x in x_vars.items():
            prob += (x <= y_vars[sec_name], f"link_{f_name}_{sec_name}")

    def max_groups_constraint(self, prob, frames, vars_dict, max_groups):
        """Constraint that limits the total number of active section groups.
        
        Args:
            prob: PuLP problem instance
            frames: Dictionary of frames with their properties
            vars_dict: Dictionary containing optimization variables
            max_groups: Maximum number of distinct section groups allowed
        """
        import pulp
        
        y_vars = vars_dict["y_vars"]
        
        prob += (
            pulp.lpSum(y_vars.values()) <= max_groups,
            "max_groups_limit"
        )

# Note: Removed all standalone functions as they are now class methods
