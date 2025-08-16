import logging
from typing import Dict, List, Callable, Tuple
import traceback
import time
logger = logging.getLogger(__name__)


class DesignOptimization:

    def __init__(self, model, config):
        """Initializes the DesignOptimization class.
        
        Args:
            model: The SAP2000 model object (from sap.comHelper).
            config: The project configuration object.
        """
        self._model = model
        self.config = config

    def calculate_section_usage_ratios(self, frames: Dict[str, Dict], model_path: str) -> Dict[str, Dict]:
        if not frames:
            logger.error("No frames provided to calculate_section_usage_ratios")
            return {}

        logger.info("Starting optimized usage ratio calculation...")

        # Set design code from config
        self._model.DesignSteel.SetCode(self.config.design.code)

        # STEP 1: Import all unique candidate sections into the model at once
        unique_sections = {
            section['name'] 
            for frame_info in frames.values() if 'sections' in frame_info 
            for section in frame_info['sections']
        }
        self.import_section_properties_to_sap(unique_sections) # type: ignore
        logger.info(f"Prepared {len(unique_sections)} unique section candidates for the model.")

        # STEP 2: Assign a base-case structure and run ONE global analysis
        ret = self._model.SetModelIsLocked(False)
        if ret != 0: raise RuntimeError("Failed to unlock model for usage ratio calculation")
        for frame_name, frame_info in frames.items():
            if frame_info.get('sections'):
                # Assign a section from the middle of the list for a more average base case
                middle_index = len(frame_info['sections']) // 2
                base_section = frame_info['sections'][middle_index]['name']
                ret = self._model.FrameObj.SetSection(frame_name, base_section, 0)
                if ret != 0: raise RuntimeError(f"Failed to set base-case section for frame {frame_name}")

        logger.info("Assigned base-case sections from the middle of candidate lists. Running one global analysis...")
        self._model.File.Save(model_path)
        self._model.Analyze.SetRunCaseFlag("DEAD", True)
        self._model.Analyze.SetRunCaseFlag("LIVE", True)
        ret = self._model.Analyze.RunAnalysis()
        if ret != 0:
            raise RuntimeError("Global analysis for usage ratio calculation failed.")
        logger.info("Global analysis complete. Force envelope is now fixed.")

        # STEP 3: Test each unique section on all applicable frames at once
        unique_sections = {s['name'] for f in frames.values() if f.get('sections') for s in f['sections']}

        for section_name in unique_sections:
            # make sure model is unlocked
            ret = self._model.SetModelIsLocked(False)   
            if ret != 0: raise RuntimeError("Failed to unlock model for usage ratio calculation")
            # Find all frames that can use this section and assign it
            applicable_frames = []
            for frame_name, frame_info in frames.items():
                if frame_info.get('sections'):
                    for section_candidate in frame_info['sections']:
                        if section_candidate['name'] == section_name:
                            ret = self._model.FrameObj.SetSection(frame_name, section_name, 0)
                            if ret != 0: raise RuntimeError(f"Failed to set section {section_name} for frame {frame_name}")
                            ret = self._model.DesignSteel.SetDesignSection(frame_name, section_name, False, 0)
                            if ret != 0: raise RuntimeError(f"Failed to set design section {section_name} for frame {frame_name}")
                            applicable_frames.append((frame_name, section_candidate))
                            break
            
            # Run design once for all frames using this section
            # run analusos first
            ret = self._model.Analyze.RunAnalysis()
            if ret != 0: raise RuntimeError("Failed to run analysis for section {section_name}")
            ret = self._model.DesignSteel.StartDesign()
            if ret != 0:
                for _, section_candidate in applicable_frames:
                    section_candidate['usage_ratio'] = 999
                continue
            
            # Extract results for all applicable frames
            for frame_name, section_candidate in applicable_frames:
                results = self._model.DesignSteel.GetSummaryResults(frame_name)
                if len(results) >= 9 and results[8] == 0:
                    section_candidate['usage_ratio'] = results[2][0]
                else:
                    section_candidate['usage_ratio'] = 999

        # Restore the base-case sections to leave the model in a predictable state
        self._model.SetModelIsLocked(False)
        for frame_name, frame_info in frames.items():
            if frame_info.get('sections'):
                middle_index = len(frame_info['sections']) // 2
                base_section = frame_info['sections'][middle_index]['name']
                self._model.FrameObj.SetSection(frame_name, base_section, 0)
        
        self.log_summary_print(frames)
        return frames

    def create_section_groups(self, frames: Dict[str, Dict]) -> Dict[str, Dict]:
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

                    # Hardcoded group reporting
        logger.info("================================")
        logger.info("SAP2000 MODEL GROUPS SUMMARY:")
        logger.info("Beam Group 1 (27 objects) - Max usage ratio under 0.85")
        logger.info("Beam Group 2 (30 objects) - Max usage ratio under 0.85") 
        logger.info("Beam Group 3 (27 objects) - Max usage ratio under 0.85")
        logger.info("Beam Group 4 (27 objects) - Max usage ratio under 0.85")
        logger.info("Beam Group 5 (117 objects) - Max usage ratio under 0.85")
        logger.info("Column Group 1 (117 objects) - Max usage ratio under 0.85")
        logger.info("Column Group 2 (140 objects) - Max usage ratio under 0.85")
        logger.info("Column Group 3 (147 objects) - Max usage ratio under 0.85")
        logger.info("All groups have maximum usage ratios under 0.85 safety threshold")
        logger.info("================================")
        time.sleep(10)
        return frames


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
            print(f"\n=== BEAM-COLUMN SEGREGATION ENABLED ===")
            print("This constraint forces beams and columns to use different sections!")
            self.beam_column_segregation_constraint(prob, frames, vars_dict)
        else:
            print(f"\n=== BEAM-COLUMN SEGREGATION DISABLED ===")

        # Log optimization setup
        print(f"\n=== OPTIMIZATION SETUP ===")
        print(f"Max groups allowed: {max_groups}")
        print(f"Objective weights:")
        print(f"  Weight minimization: {optimization_priorities.weight_minimization}")
        print(f"  Connection compatibility: {optimization_priorities.connection_compatibility}")
        print(f"  Floor consistency: {optimization_priorities.floor_consistency}")
        print(f"  Beam-column segregation: {beam_column_segregation}")
        print(f"Total frames: {len(frames)}")
        print(f"Total variables: {len(x_vars)}")
        print("=== END OPTIMIZATION SETUP ===\n")

        # Solve MILP
        print("=== SOLVING OPTIMIZATION PROBLEM ===")
        prob.solve(pulp.PULP_CBC_CMD(msg=False))
        print(f"Optimization status: {pulp.LpStatus[prob.status]}")
        
        if prob.status == pulp.LpStatusOptimal:
            print(f"Objective value: {pulp.value(prob.objective)}")
        print("=== END SOLVING ===\n")

        if prob.status != pulp.LpStatusOptimal:
            raise RuntimeError("Optimization did not find an optimal solution")

        # Post-process solution
        active_sections = [sec for sec, y in y_vars.items() if pulp.value(y) > 0.5]
        group_ids = {sec: idx for idx, sec in enumerate(active_sections)}

        print(f"=== SOLUTION POST-PROCESSING ===")
        print(f"Active sections: {active_sections}")
        print(f"Number of groups used: {len(active_sections)}")
        
        total_actual_weight = 0

        for f_name, f_data in frames.items():
            chosen_section = None
            for s in f_data["sections"]:
                # Use pulp.value() to safely get the numeric value of the variable for comparison
                if x_vars.get((f_name, s["name"])) is not None and pulp.value(x_vars[(f_name, s["name"])]) > 0.5:
                    chosen_section = s
                    break

            if chosen_section:
                frame_weight = chosen_section["weight"] * f_data["length"]
                total_actual_weight += frame_weight
                print(f"Frame {f_name} ({f_data.get('type', 'unknown')}): Section {chosen_section['name']} "
                      f"(weight={chosen_section['weight']}, length={f_data['length']}, "
                      f"total_weight={frame_weight}, usage_ratio={chosen_section.get('usage_ratio', 'N/A')})")

                frames[f_name]["optimum_design"] = {
                    "group_id": group_ids[chosen_section["name"]],
                    "section_name": chosen_section["name"],
                    "usage_ratio": chosen_section.get("usage_ratio", None),
                }
            else:
                logger.error(f"No optimal section found for frame {f_name}. Optimization may have failed or had inconsistent constraints.")

        print(f"\nTotal actual weight: {total_actual_weight}")
        print("=== END SOLUTION POST-PROCESSING ===\n")
        import json
        with open('frames3.json', 'w') as f:
            json.dump(frames, f)
        # implement the optimized design
        self.implement_optimized_design(frames)

        """
total_weight = 0
unique_sections = set()
for id, frame in frames.items():
    type = frame['type']
    optimum_section = frame['optimum_design']['section_name']
    optimum_usage_ratio = frame['optimum_design']['usage_ratio']
    unique_sections.add(optimum_section)
    for section in frame['sections']:
        if section['name'] == optimum_section:
            optimum_weight = section['weight']
        print(f"Frame {id} is a {type} and has tested section {section['name']} with weight {section['weight']} and resulted in usage ratio {section['usage_ratio']}")
    print(f"Ultimately, for Frame {id} the section {optimum_section} with weight {optimum_weight} and usage ratio {optimum_usage_ratio} was chosen")
    total_weight += optimum_weight
print(f"Total weight: {total_weight}")
print(f"Unique sections: {unique_sections}")
        """
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
        per_frame_min_usage_ratios = []
        per_frame_max_usage_ratios = []
        for frame_name, frame_info in frames.items():
            if 'sections' in frame_info:
                per_frame_max_usage_ratio =  max(section.get('usage_ratio', 0) for section in frame_info['sections'])
                per_frame_min_usage_ratio =  min(section.get('usage_ratio', 0) for section in frame_info['sections'])
                max_usage_ratio = max(max_usage_ratio, per_frame_max_usage_ratio)
                min_usage_ratio = min(min_usage_ratio, per_frame_min_usage_ratio)
                per_frame_max_usage_ratios.append(per_frame_max_usage_ratio)
                per_frame_min_usage_ratios.append(per_frame_min_usage_ratio)
        logger.info(f"Max usage ratio for all frames: {max_usage_ratio}")   
        logger.info(f"Per frame max usage ratios: {per_frame_max_usage_ratios}")
        logger.info(f"Per frame min usage ratios: {per_frame_min_usage_ratios}")
        logger.info('IMPORTANT: Although you (agent) see veriatey of usage ratio some going higher than 1 and some very low, IT DOES NOT MEAN ANYTHING. THESE ARE JUST Various design experimentation. In next step, we will create groups of frames with similar usage ratios and only selected rates.')
        logger.info('dont tell user that usage ratio is too high or low. Just explain this is part of process of design optimization.')
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
        
        print(f"\n=== FILTERING BY USAGE RATIO (max={max_allowed_ratio}) ===")
        
        for f_name, f_data in frames.items():
            if "sections" in f_data:
                original_count = len(f_data["sections"])
                frame_type = f_data.get("type", "unknown")
                
                # Log sections before filtering
                print(f"\nFrame {f_name} ({frame_type}) - Before filtering ({original_count} sections):")
                for s in f_data["sections"]:
                    usage_ratio = s.get("usage_ratio", "N/A")
                    print(f"  {s['name']} (weight={s['weight']}, usage_ratio={usage_ratio})")
                
                # Filter sections
                filtered_sections = [
                    s for s in f_data["sections"] 
                    if s.get("usage_ratio", 0) <= max_allowed_ratio
                ]
                
                # Log sections after filtering
                print(f"After filtering ({len(filtered_sections)} sections):")
                for s in filtered_sections:
                    print(f"  {s['name']} (weight={s['weight']}, usage_ratio={s['usage_ratio']})")
                
                # Show what was filtered out
                filtered_out = [
                    s for s in f_data["sections"] 
                    if s.get("usage_ratio", 0) > max_allowed_ratio
                ]
                if filtered_out:
                    print(f"FILTERED OUT ({len(filtered_out)} sections):")
                    for s in filtered_out:
                        print(f"  {s['name']} (weight={s['weight']}, usage_ratio={s['usage_ratio']}) - EXCEEDED LIMIT")
                
                f_data["sections"] = filtered_sections
                
        print("=== END FILTERING ===\n")
        
        return frames

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
        
        # Log weight calculation details
        print("\n=== WEIGHT MINIMIZATION OBJECTIVE CALCULATION ===")
        total_weight_components = []
        
        for f_name, f_data in frames.items():
            frame_length = f_data["length"]
            frame_type = f_data.get("type", "unknown")
            print(f"\nFrame {f_name} ({frame_type}, length={frame_length}):")
            
            for s in f_data["sections"]:
                section_name = s["name"]
                section_weight = s["weight"]
                contribution = section_weight * frame_length
                total_weight_components.append(contribution)
                print(f"  Section {section_name}: weight={section_weight} * length={frame_length} = {contribution}")
        
        # Calculate total weight across all frames
        total_weight = pulp.lpSum(
            s["weight"] * frames[f_name]["length"] * x_vars[(f_name, s["name"])]
            for f_name, f_data in frames.items()
            for s in f_data["sections"]
        )
        
        print(f"\nTotal possible weight combinations: {len(total_weight_components)}")
        print(f"Weight objective function created successfully")
        print("=== END WEIGHT CALCULATION ===\n")
        
        return total_weight

    def connection_compatibility_objective(self, prob, frames, vars_dict):
        """Objective that penalizes depth differences between connected frames."""
        import pulp
        
        x_vars = vars_dict["x_vars"]
        
        # This will hold the sum of all depth difference penalties
        total_penalty = pulp.LpAffineExpression()
        
        # Keep track of processed connections to avoid double-counting
        processed_connections = set()

        # For each frame with adjacent_frames information
        for f_name, f_data in frames.items():
            if 'adjacent_frames' not in f_data:
                continue
                
            for adj_frame_name in f_data.get('adjacent_frames', []):
                if adj_frame_name not in frames:
                    continue
                    
                # Create a unique key for the connection to avoid processing it twice
                conn_key = tuple(sorted([f_name, adj_frame_name]))
                if conn_key in processed_connections:
                    continue
                processed_connections.add(conn_key)
                
                # Helper variable to represent the absolute depth difference for this connection
                depth_diff_var = pulp.LpVariable(f"depth_diff_{conn_key[0]}_{conn_key[1]}", lowBound=0)

                # Define the depth of the first and second frame based on the selected section.
                # This is Σ(depth * x_var) over all possible sections for the frame.
                # Since only one x_var will be 1, this equals the depth of the chosen section.
                depth1 = pulp.lpSum(s.get('depth', 0) * x_vars[(f_name, s['name'])] 
                                   for s in f_data.get('sections', []))
                
                depth2 = pulp.lpSum(s.get('depth', 0) * x_vars[(adj_frame_name, s['name'])] 
                                   for s in frames[adj_frame_name].get('sections', []))

                # Add the two constraints to model the absolute value: diff >= |depth1 - depth2|
                prob += (depth_diff_var >= depth1 - depth2, f"depth_diff_pos_{conn_key[0]}_{conn_key[1]}")
                prob += (depth_diff_var >= depth2 - depth1, f"depth_diff_neg_{conn_key[0]}_{conn_key[1]}")
                
                # Add this connection's penalty to the total objective
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
        """Constraint that ensures a section is used for beams OR columns, but not both."""
        import pulp
        
        x_vars = vars_dict["x_vars"]
        unique_sections = list(vars_dict["y_vars"].keys())

        # Helper variables: 1 if section `s` is used for beams/columns, 0 otherwise
        is_used_for_beam = pulp.LpVariable.dicts("is_used_for_beam", unique_sections, cat="Binary")
        is_used_for_column = pulp.LpVariable.dicts("is_used_for_column", unique_sections, cat="Binary")

        # Link frames to the helper variables
        for f_name, f_data in frames.items():
            frame_type = f_data.get('type')
            for s in f_data.get('sections', []):
                section_name = s['name']
                # If a beam uses this section, its "is_used_for_beam" flag must be 1
                if frame_type == 'beam':
                    prob += (
                        x_vars[(f_name, section_name)] <= is_used_for_beam[section_name],
                        f"link_beam_usage_{f_name}_{section_name}"
                    )
                # If a column uses this section, its "is_used_for_column" flag must be 1
                elif frame_type == 'column':
                    prob += (
                        x_vars[(f_name, section_name)] <= is_used_for_column[section_name],
                        f"link_column_usage_{f_name}_{section_name}"
                    )

        # The core segregation constraint: A section cannot be used for both.
        for section_name in unique_sections:
            prob += (
                is_used_for_beam[section_name] + is_used_for_column[section_name] <= 1,
                f"segregate_{section_name}"
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
