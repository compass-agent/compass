"""
SAP2000 Model Information Extractor

This module provides a class to extract comprehensive information from a SAP2000 model.
It can be used to get a summary of the model's current state including frames, loads, joints, 
and other structural components.
"""

import logging
from typing import Dict, Any
import traceback  # Add import for traceback module

logger = logging.getLogger(__name__)

class SAPModelInfo:
    """
    Extract and analyze information from a SAP2000 model.
    
    This class provides methods to extract detailed information about various
    components of a SAP2000 model, including joints, frames, materials, and
    analysis results.
    """
    
    def __init__(self, sap_model, sap_object=None, model_path=None):
        """
        Initialize the SAP Model Info extractor.
        
        Args:
            sap_model: The SAP2000 model object obtained from the SAP2000 API
            sap_object: Optional SAP2000 object
            model_path: Optional path to the model file
        """
        self.sap_model = sap_model
        self.sap_object = sap_object
        self.model_path = model_path
        logger.info("Initialized SAP Model Info extractor")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Extract comprehensive information about the current SAP2000 model.
        
        Returns:
            A dictionary containing comprehensive information about the model including:
            - Model information (name, units, etc.)
            - Joint data (coordinates, restraints)
            - Frame data (connectivity, section assignments)
            - Load patterns and cases
            - Materials and section properties
            - Analysis results summary if available
        """
        model_info = {}
        
        try:
            # Get basic model information
            model_info["basic_info"] = self.get_basic_model_info()
            
            # Get joint information
            model_info["joints"] = self.get_joint_info()
            
            # Get frame information
            model_info["frames"] = self.get_frame_info()
            
            # Get load information
            model_info["loads"] = self.get_load_info()
            
            # Get material properties
            model_info["materials"] = self.get_material_info()
            
            """
            # Get section properties
            model_info["sections"] = self.get_section_info()
            
            # Get restraint information
            model_info["restraints"] = self.get_restraint_info()
            
            # Get analysis results if available
            model_info["analysis"] = self.get_analysis_info()
            
            # Get other model properties
            model_info["model_status"] = self.get_model_status()
            """
            
            return model_info
        
        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"Error extracting model information: {str(e)}\nTraceback:\n{error_traceback}")
            print(f"Exception: {str(e)}\nTraceback:\n{error_traceback}")  # Print to console for immediate visibility
            return {"error": str(e), "traceback": error_traceback}

    def get_basic_model_info(self) -> Dict[str, Any]:
        """Get basic information about the model."""
        info = {}
        
        # Get program info
        ret, program_name, program_version, _ = self.sap_model.GetProgramInfo()
        info["program"] = {
            "name": program_name,
            "version": program_version
        }
        
        # Get model file name - function returns single string, not tuple
        file_name = self.sap_model.GetModelFilename()
        info["file_name"] = file_name
        
        # Get units - returns a single value representing combined units
        units_code = self.sap_model.GetPresentUnits()
        
        # Map the units code to a human-readable string
        units_map = {
            1: "lb_in_F", 2: "lb_ft_F", 3: "kip_in_F", 4: "kip_ft_F",
            5: "kN_mm_C", 6: "kN_m_C", 7: "kgf_mm_C", 8: "kgf_m_C",
            9: "N_mm_C", 10: "N_m_C", 11: "Ton_mm_C", 12: "Ton_m_C",
            13: "kN_cm_C", 14: "kgf_cm_C", 15: "N_cm_C", 16: "Ton_cm_C"
        }
        
        # Split into components based on naming convention
        unit_parts = units_map.get(units_code, f"Unknown({units_code})").split('_')
        
        if len(unit_parts) >= 3:
            force_unit = unit_parts[0]
            length_unit = unit_parts[1]
            temp_unit = unit_parts[2]  # F or C for Fahrenheit or Celsius
        else:
            force_unit = "Unknown"
            length_unit = "Unknown"
            temp_unit = "Unknown"
            
        info["units"] = {
            "length": length_unit,
            "force": force_unit,
            "temperature": temp_unit,
            "combined": units_map.get(units_code, f"Unknown({units_code})")
        }
        
        return info

    def get_joint_info(self) -> Dict[str, Any]:
        """Get information about all joints in the model."""
        joint_info = {}
        
        # Get number of joints
        count = self.sap_model.PointObj.Count()
        joint_info["count"] = count
        
        # Get joint names
        number_names, joint_names, ret = self.sap_model.PointObj.GetNameList()
        
        # Sample of joint details (for first 10 joints or fewer)
        sample_size = min(10, count)
        joint_samples = []
        
        for i in range(sample_size):
            if i < len(joint_names):
                name = joint_names[i]
                # Get coordinates
                _, x, y, z = self.sap_model.PointObj.GetCoordCartesian(name)
                
                # Get restraints
                restraints = [False] * 6
                ret = self.sap_model.PointObj.GetRestraint(name, restraints)
                
                joint_data = {
                    "name": name,
                    "coordinates": {"x": x, "y": y, "z": z},
                    "restraints": {
                        "U1": restraints[0], "U2": restraints[1], "U3": restraints[2],
                        "R1": restraints[3], "R2": restraints[4], "R3": restraints[5]
                    }
                }
                joint_samples.append(joint_data)
        
        joint_info["samples"] = joint_samples
        return joint_info

    def get_frame_info(self) -> Dict[str, Any]:
        """Get information about frame elements in the model."""
        frame_info = {}
        
        # Get number of frames
        count = self.sap_model.FrameObj.Count()
        frame_info["count"] = count
        
        # Get frame names
        number_names, frame_names, ret = self.sap_model.FrameObj.GetNameList()
        
        # Sample of frame details (for first 10 frames or fewer)
        sample_size = min(10, count)
        frame_samples = []
        
        for i in range(sample_size):
            if i < len(frame_names):
                name = frame_names[i]
                # Get connectivity
                _, point_i, point_j = self.sap_model.FrameObj.GetPoints(name)
                
                # Get section property
                ret, section_name, s_auto = self.sap_model.FrameObj.GetSection(name)
                
                # Get material
                material_name = ""  # Initialize material_name before using it
                ret, material_name = self.sap_model.FrameObj.GetMaterialOverwrite(name, material_name)
                
                # Get material properties if material override exists
                material_type = None
                if material_name and material_name != "None":
                    ret, material_type, color, notes, guid = self.sap_model.PropMaterial.GetMaterial(material_name)
                else:
                    # If no material override, get material from section property
                    material_name = self.sap_model.PropFrame.GetMaterial(section_name)[1]
                
                frame_data = {
                    "name": name,
                    "connectivity": {"point_i": point_i, "point_j": point_j},
                    "section": section_name,
                    "material": material_name
                }
                frame_samples.append(frame_data)
        
        frame_info["samples"] = frame_samples
        return frame_info

    def get_load_info(self) -> Dict[str, Any]:
        """Get information about loads in the model."""
        load_info = {}
        
        # Get load patterns
        num_patterns = self.sap_model.LoadPatterns.Count()
        number_patterns, pattern_names, ret = self.sap_model.LoadPatterns.GetNameList()
        
        patterns = []
        for i in range(num_patterns):
            if i < len(pattern_names):
                name = pattern_names[i]
                # GetLoadType returns only two values: return code and pattern type
                ret, pattern_type = self.sap_model.LoadPatterns.GetLoadType(name)
                pattern = {
                    "name": name,
                    "type": pattern_type,
                    # Note: self_weight_multiplier is not directly available from GetLoadType
                    # would need a separate call to get it if needed
                }
                patterns.append(pattern)
        
        load_info["patterns"] = patterns
        
        # Get load cases
        num_cases = self.sap_model.LoadCases.Count()
        number_cases, case_names, ret = self.sap_model.LoadCases.GetNameList()
        
        cases = []
        for i in range(num_cases):
            if i < len(case_names):
                name = case_names[i]
                # According to documentation, use GetTypeOAPI_1 to get more details
                ret, case_type, sub_type, design_type, design_type_option, auto = self.sap_model.LoadCases.GetTypeOAPI_1(name)
                case = {
                    "name": name,
                    "type": case_type,
                    "sub_type": sub_type,
                    "design_type": design_type
                }
                cases.append(case)
        
        load_info["cases"] = cases
        
        # Get load combinations
        num_combos = self.sap_model.RespCombo.Count()
        number_combos, combo_names, ret = self.sap_model.RespCombo.GetNameList()
        
        combos = []
        for i in range(num_combos):
            if i < len(combo_names):
                name = combo_names[i]
                combo = {"name": name}
                combos.append(combo)
        
        load_info["combinations"] = combos
        
        return load_info

    def get_material_info(self) -> Dict[str, Any]:
        """Get information about materials in the model."""
        material_info = {}
        
        # Get material names
        number_materials, material_names, ret = self.sap_model.PropMaterial.GetNameList()
        material_info["count"] = len(material_names)
        
        materials = []
        for name in material_names:
            if name in material_names:
                ret, material_type, color, notes, guid = self.sap_model.PropMaterial.GetMaterial(name)
            
            # Use GetWeightAndMass instead of GetWeightPerVol (which doesn't exist)
            ret, weight, mass = self.sap_model.PropMaterial.GetWeightAndMass(name)
            
            # GetMPUniaxial returns E modulus and thermal coefficient
            ret, e_modulus, thermal_coef = self.sap_model.PropMaterial.GetMPUniaxial(name)
            
            # Try to get isotropic properties (may not apply to all materials)
            try:
                ret, e_iso, poisson, alpha, g = self.sap_model.PropMaterial.GetMPIsotropic(name)
                isotropic_props = {
                    "e_modulus": e_iso,
                    "poisson_ratio": poisson,
                    "thermal_coef": alpha,
                    "shear_modulus": g
                }
            except:
                isotropic_props = None
            
            material = {
                "name": name,
                "type": material_type,
                "weight": weight,
                "mass": mass,
                "e_modulus": e_modulus,
                "thermal_coef": thermal_coef,
                "isotropic_properties": isotropic_props
            }
            materials.append(material)
        
        material_info["materials"] = materials
        return material_info

    def get_section_info(self) -> Dict[str, Any]:
        """Get information about section properties in the model."""
        section_info = {}
        
        # Get section names
        number_sections, section_names, ret = self.sap_model.PropFrame.GetNameList()
        section_info["count"] = len(section_names)
        
        sections = []
        for name in section_names:
            _, section_type, _, _, _, _ = self.sap_model.PropFrame.GetSectProps(name)
            _, material_name = self.sap_model.PropFrame.GetMaterial(name)
            
            section = {
                "name": name,
                "type": section_type,
                "material": material_name
            }
            sections.append(section)
        
        section_info["sections"] = sections
        return section_info

    def get_restraint_info(self) -> Dict[str, Any]:
        """Get information about restraints in the model."""
        restraint_info = {}
        
        # Count restrained points
        restrained_points = 0
        number_points, point_names, ret = self.sap_model.PointObj.GetNameList()
        
        for name in point_names:
            _, restraint_x, restraint_y, restraint_z, restraint_rx, restraint_ry, restraint_rz = self.sap_model.PointObj.GetRestraint(name)
            if any([restraint_x, restraint_y, restraint_z, restraint_rx, restraint_ry, restraint_rz]):
                restrained_points += 1
        
        restraint_info["restrained_points_count"] = restrained_points
        
        return restraint_info

    def get_analysis_info(self) -> Dict[str, Any]:
        """Get information about analysis results if available."""
        analysis_info = {}
        
        # Check if results are available
        _, has_results = self.sap_model.Results.Exists()
        analysis_info["results_available"] = bool(has_results)
        
        if has_results:
            # Get number of modes if modal analysis
            try:
                num_modes = self.sap_model.Results.ModeShape.Count()
                if num_modes > 0:
                    modes = []
                    for mode in range(1, min(num_modes + 1, 6)):  # Get info for first 5 modes
                        _, period, freq, _, _ = self.sap_model.Results.ModeShape.GetModalPeriod(mode)
                        modes.append({
                            "mode": mode,
                            "period": period,
                            "frequency": freq
                        })
                    analysis_info["modal_results"] = {
                        "num_modes": num_modes,
                        "sample_modes": modes
                    }
            except Exception as e:
                logger.warning(f"Error getting modal analysis results: {str(e)}")
        
        return analysis_info

    def get_model_status(self) -> Dict[str, Any]:
        """Get status information about the model."""
        status_info = {}
        
        # Check if model has been run
        _, is_running = self.sap_model.GetModelIsLocked()
        status_info["is_locked"] = bool(is_running)
        
        # Get database lock state
        _, is_locked = self.sap_model.GetModelIsLocked()
        status_info["is_running"] = bool(is_locked)
        
        # Check if model has been modified since last save
        _, is_modified = self.sap_model.GetModelIsModified()
        status_info["is_modified"] = bool(is_modified)
        
        return status_info
    
    def save_model(self) -> bool:
        """
        Save the current model.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.model_path:
            logger.warning("Cannot save model: No model path specified")
            return False
            
        try:
            ret = self.sap_model.File.Save(self.model_path)
            logger.info(f"Save model result: {ret}")
            return ret == 0  # Return True if save was successful
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            return False

    def format_model_info(self) -> str:
        """
        Format the model information into a readable string.
        
        Returns:
            A formatted string with model information
        """
        model_info = self.get_model_info()
        
        # Simply convert the dictionary to a string representation
        import pprint
        pp = pprint.PrettyPrinter(indent=2)
        return pp.pformat(model_info)


# Function for backward compatibility with previous implementation
def extract_sap2000_model_info(sap_model, model_path=None):
    """
    Convenience function to extract all model information.
    This provides backward compatibility with the original function-based implementation.
    
    Args:
        sap_model: The SAP2000 model object
        model_path: Optional path to the model file
        
    Returns:
        A formatted string with model information
    """
    model_info = SAPModelInfo(sap_model, model_path=model_path)
    return model_info.format_model_info()


if __name__ == "__main__":
    import os
    import comtypes.client
    import comtypes.gen.SAP2000v1
    helper = comtypes.client.CreateObject('SAP2000v1.Helper')
    helper = helper.QueryInterface(comtypes.gen.SAP2000v1.cHelper)
    sap_object = helper.GetObject("CSI.SAP2000.API.SapObject")
    sap_model = sap_object.SapModel
    APIPath = R'C:\Users\sadoughi\Projects\compass\experiment\model'
    model_path = APIPath + os.sep + 'compass_model.sdb' 
    model_info = SAPModelInfo(sap_model, sap_object, model_path)
    model_info_text = model_info.format_model_info()
    print(model_info_text)