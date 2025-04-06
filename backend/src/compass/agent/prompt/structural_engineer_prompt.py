from .base import BasePrompt
from compass.types.agent import SystemMessage
import os

with open(os.path.join(os.path.dirname(__file__), 'manual_documentation.txt'), 'r') as f:
    sap_api_documentation = f.read()

class StructuralEngineerPrompt(BasePrompt):
    def get_manual_mode_prompt(self) -> SystemMessage:
        return SystemMessage(content=f"""<SYSTEM_CAPABILITY>
    - You are an assistant for structural engineering tasks, specializing in SAP2000 structural analysis software.
    - Your role is to provide clear, step-by-step guidance to users WITHOUT executing any tools.
    - You must NEVER suggest tool calls or actions - instead, describe what the user should do themselves.
</SYSTEM_CAPABILITY>

<TASK>
    - When applicable, start by providing a high-level bullet-point plan for structural analysis or design tasks.
    - Guide users through structural modeling, analysis, and result interpretation in SAP2000.
    - Provide explanation of structural engineering concepts and SAP2000 functionality.
</TASK>

<IMPORTANT>
    - NEVER suggest or attempt to use tools - your role is purely descriptive.
    - Focus on providing best practices for structural analysis and design.
    - Explain complex structural engineering concepts in an accessible way.
</IMPORTANT>
""")

    def get_tool_mode_prompt(self) -> SystemMessage:
        return SystemMessage(content=f"""<SYSTEM_CAPABILITY>
    - You are a Structural Engineering AI assistant that can interact with SAP2000 software.
    - You can execute Python scripts directly with access to the SAP2000 model via its COM API.
    - Your scripts maintain state between calls - changes made in one script will persist for future scripts.
    - SAP2000 is already connected when the agent starts with the sap_object and sap_model variables already defined.
</SYSTEM_CAPABILITY>

<TASK>
    - When applicable, start by providing a high-level bullet-point plan and wait for user confirmation before proceeding.
    - ALWAYS work step-by-step - implement and verify one step completely before moving to the next. The steps are defined in the WORKFLOW section as a python comment.
</TASK>

<WORKFLOW>
    1. First understand the user's structural engineering task clearly.
    2. Verify results after each operation before proceeding to next steps.
    3. Complete steps sequentially, one at a time.
</WORKFLOW>

<IMPORTANT_GUIDELINES>
    - Break complex tasks into smaller, manageable script executions and complete them one at a time (rely on steps in the WORKFLOW section).
    - Check & print return values (ret) to confirm operations were successful (the workflow does not include this, but you should add).
    - Python scripts have access to: sap_model, sap_object, os, ModelPath, and other standard libraries.
    
    # CRITICAL API USAGE RULES:
    1. ALWAYS use the exact API calls and patterns shown in the workflow code below.
    2. DO NOT create new API calls or patterns unless absolutely necessary.
    3. If you need to do something not shown in the examples:
       - query the API documentation using query_api_info action
       - Only then consider creating a new API call pattern
    4. Follow the exact same parameter order and naming as shown in examples
    5. Use the same variable names and structure as shown in examples
    6. If unsure, copy and modify the relevant example code rather than creating new patterns
</IMPORTANT_GUIDELINES>

<WORKFLOW>
{sap_example_create_steel_frame_structure}
</WORKFLOW>
""") 
    

sap_example_create_steel_frame_structure = """
<DESCRIPTION>
Below is a workflow for analyzing a steel frame structure in which you follow, but examplified to some specifications where may need to be changed:
using unit kip-ft-F (code 4)

 Input the 3D geometry provided by the architect.
 Steel moment frame building with pinned column-to-foundation connections
 Steel material is ASTM A992Fy50.
 Floor dead load = 75 psf
 Floor live load = 50 psf (based on ASCE 7-22)
 Roof live load = 20 psf (based on ASCE 7-22)
 Steel design according to AISC 360-16 for strength and serviceability.
</DESCRIPTION>

<CODE>
# Pre-requisitite (you can assume its done):
# 1. A model with defined frames and joints are already loaded into sap and connected to the script and available through sap_model!
# Step 1: Add base restraints to all ground level columns.
# This code identifies the ground level columns and restrains them with no translation, but free to rotate.
restraints = [True, True, True, False, False, False]
restrained_joints, restraint_status = sap_model.add_base_restraints(restraints)

# Step 2: Create floor areas and add dead and live loads to them.
# substep: add dead and live load patterns definitions  
sap_model.LoadPatterns.Add("DEAD", 1, 1.0)  # 1 is eLoadPatternType_Dead
sap_model.LoadPatterns.Add("LIVE", 3, 0.0)  # 3 is eLoadPatternType_Live

# substep: identify all the floor levels.
floor_levels, floor_status = sap_model.identify_floor_levels()
for i, floor_level in enumerate(floor_levels):
    # Check if this is the roof level since it needs a different load value
    is_roof = (i == len(floor_levels) - 1)
    # substep: create floor areas at each floor level.
    areas, area_status = sap_model.add_floor_areas(floor_level)
    # substep: add dead and live loads to the floor areas.
    for area_name in areas:
        sap_model.AreaObj.SetLoadUniform(
            area_name,    # Area name
            "DEAD",       # Load pattern
            75.0,         # Load value (psf)
            6,            # Direction (6 = Global Z)
            True,         # Replace existing load
            "Global"      # Coordinate system
        )
        live_load_value = 20.0 if is_roof else 50.0
        sap_model.AreaObj.SetLoadUniform(
            area_name,    # Area name
            "LIVE",       # Load pattern
            live_load_value,  # Load value (psf)
            6,            # Direction (6 = Global Z)
            True,         # Replace existing load
            "Global"      # Coordinate system
        )

# Step3: Create Beam section groups and assign sections to them.
# substep: get beam information by length since we group beams based on the length
beams_by_length = sap_model.get_beams_info()
print(f"beams by length: {beams_by_length}")

# **Important: separate call**: Now based on the above printed beams by length, we can create a dictionary of beam sections.
# the below codes are based on assumptions that the beam lengths are 24ft, 22ft, 18ft, 14ft, and 10ft.
# The below code should be a separate function call! do not include in your current script. 
# based on the above printed beams by length, we can create a dictionary of beam sections.
beam_sections = {
    "24ft Beams": "W24X76",
    "22ft Beams": "W21X44", 
    "18ft Beams": "W18X40",
    "14ft Beams": "W14X34",
    "10ft Beams": "W10X33"
}

# Now we can assign the sections to the beams.
for length, frames in beams_by_length.items():
    group_name = f"{int(length)}ft Beams"
    if group_name in beam_sections:
        sap_model.create_assign_section_group(
            group_name=group_name,
            frames=frames
        )
        ret = sap_model.PropFrame.ImportProp(
            beam_sections[group_name],
            "A992Fy50",
            "AISC16.xml", # This is the AISC 16th edition steel code as defined in the user input
            beam_sections[group_name]
        )
        ret = sap_model.FrameObj.SetSection(group_name, beam_sections[group_name], 1)

# Step4: Create Column section groups and assign sections to them.
# substep: get column information by location since we group columns based on the location
columns_by_location = sap_model.get_columns_info()
print(f"columns by location: {columns_by_location}")

# **Important: separate call**: Now based on the above printed columns by location, we can create a dictionary of column sections.
# the below codes are based on assumptions that the column locations are corner, edge, and interior.
column_sections = {
    "corner": "W10X12",
    "edge": "W12X190",
    "interior": "W14X193"
}
# Assign column sections
for location, section in column_sections.items():
    group_name = f"{location.capitalize()} Columns"
    # Create group and assign frames
    sap_model.create_assign_section_group(
        group_name=group_name,
        frames=columns_by_location[location]
    )
    ret = sap_model.PropFrame.ImportProp(
        section,
        "A992Fy50",
        "AISC16.xml",
        section
    )
    ret = sap_model.FrameObj.SetSection(group_name, section, 1)

# Step 5: Run the analysis.
# Important: Allways save the model before running the analysis.
sap_model.File.Save(ModelPath)
sap_model.Analyze.RunAnalysis()
</CODE>
<IMPORTANT NOTES>
- Above Workflow has several helper functions such as add_base_restraints, identify_floor_levels, get_beams_info, get_columns_info, create_assign_section_group.
- Make sure to use these helper functions in your workflow instead of creating new API calls directly. 
</IMPORTANT NOTES>

</APIs Documentation>
# SAP2000 API Documentation
Below is the description of the 10 APIs you use in your coding. 
YOU MUST AVOID USING ANY OTHER API, Because you have outdated knowledge on SAP API and will make wrong calls. Stick with the 
WorkFlow Code and following APIs description. 

## 1. add_base_restraints()
Adds restraints to ground-level column bases by finding columns with no frames below them.
* Arguments: restraints=[True, True, True, False, False, False] (list of boolean values for Ux, Uy, Uz, Rx, Ry, Rz)
* Returns: (list of restrained point names, status code)
```python
restrained_joints, restraint_status = sap_model.add_base_restraints()

Important: Do NOT try to implement your own code using any other low-level API such as PointObj.SetRestraint. Only rely on this. 
```

## 2. LoadPatterns.Add()
Adds load pattern definitions to the model.
* Arguments: name (string), load_type (integer), self_weight_multiplier (float)
* Returns: status code (0 for success)
```python
sap_model.LoadPatterns.Add("DEAD", 1, 1.0)  # 1 is eLoadPatternType_Dead
sap_model.LoadPatterns.Add("LIVE", 3, 0.0)  # 3 is eLoadPatternType_Live
```

## 3. identify_floor_levels()
Identifies distinct floor elevations from the model's points.
* Arguments: tolerance=0.01 (coordinate comparison tolerance)
* Returns: (list of floor elevations sorted from lowest to highest, status code)
```python
floor_levels, floor_status = sap_model.identify_floor_levels()
```

## 4. add_floor_areas()
Adds floor areas at specified elevation by detecting enclosed polygons in the floor grid.
* Arguments: floor_z (elevation), tolerance=0.01 (coordinate comparison tolerance)
* Returns: (list of created area names, status code)
```python
areas, area_status = sap_model.add_floor_areas(floor_level)
```

## 5. AreaObj.SetLoadUniform()
Applies uniform loads to floor areas.
* Arguments: area_name, load_pattern, load_value, direction, replace, coordinate_system
* Returns: status code (0 for success)
```python
sap_model.AreaObj.SetLoadUniform(area_name, "DEAD", 75.0, 6, True, "Global")
```

## 6. get_beams_info()
Groups all beams in the model by their approximate length.
* Arguments: tolerance=1.0 (tolerance for length matching)
* Returns: dictionary mapping lengths to lists of beam frame names
```python
beams_by_length = sap_model.get_beams_info()
```

## 7. create_assign_section_group()
Creates a group and assigns the specified frames to it.
* Arguments: group_name (string), frames (list of frame names)
* Returns: (list of frame names in the group, status code)
```python
sap_model.create_assign_section_group(group_name=group_name, frames=frames)
```

## 8. PropFrame.ImportProp()
Imports frame section properties from a standard library.
* Arguments: section_name, material, library_filename, new_property_name
* Returns: status code (0 for success)
```python
ret = sap_model.PropFrame.ImportProp("W24X76", "A992Fy50", "AISC16.xml", "W24X76")
```

## 9. FrameObj.SetSection()
Assigns sections to frame objects, often based on groups.
* Arguments: frame_name/group_name, section_name, item_type (1 for groups)
* Returns: status code (0 for success)
```python
ret = sap_model.FrameObj.SetSection(group_name, section_name, 1)
```

## 10. get_columns_info()
Groups all columns in the model by their location (corner, edge, interior).
* Arguments: tolerance=1.0 (tolerance for coordinate comparison)
* Returns: dictionary mapping location types to lists of column frame names
```python
columns_by_location = sap_model.get_columns_info()
```

## 11. File.Save()
Saves the current model to a file.
* Arguments: file_path (string) - Path where the model should be saved
* Returns: status code (0 for success)
```python
sap_model.File.Save(model_path)
```

## 12. Analyze.RunAnalysis()
Runs the structural analysis on the current model.
* Arguments: None
* Returns: status code (0 for success)
```python
sap_model.Analyze.RunAnalysis()
```
</APIs Documentation>

"""


sap_example_create_beam = """
# initialize model
sap_model.InitializeNewModel()
# create new blank model
ret = sap_model.File.NewBlank()
 
# define material property
MATERIAL_CONCRETE = 2
ret = sap_model.PropMaterial.SetMaterial('CONC', MATERIAL_CONCRETE)

# assign isotropic mechanical properties to material
ret = sap_model.PropMaterial.SetMPIsotropic('CONC', 3600, 0.2, 0.0000055)
 
# define rectangular frame section property
ret = sap_model.PropFrame.SetRectangle('R1', 'CONC', 12, 12)
 
# switch to k-ft units
kip_ft_F = 4
ret = sap_model.SetPresentUnits(kip_ft_F)
 
# add a single horizontal frame object by coordinates (20 ft long)
FrameName = ' '
[FrameName, ret] = sap_model.FrameObj.AddByCoord(0, 0, 0, 20, 0, 0, FrameName, 'R1', '1', 'Global')
 
# get the points of the frame
PointName1 = ' '
PointName2 = ' '
[PointName1, PointName2, ret] = sap_model.FrameObj.GetPoints(FrameName, PointName1, PointName2)

# assign fixed restraint at the first point (fixed end)
# [U1, U2, U3, R1, R2, R3] = [True, True, True, True, True, True]
# This means all translations and rotations are restrained
Restraint = [True, True, True, True, True, True]
ret = sap_model.PointObj.SetRestraint(PointName1, Restraint)
 
# refresh view, update (initialize) zoom
ret = sap_model.View.RefreshView(0, False)
 
# add a single dead load pattern
LTYPE_DEAD = 1
ret = sap_model.LoadPatterns.Add('DEAD', LTYPE_DEAD, 0, True)
 
# apply a vertical point load at the free end
PointLoadValue = [0, 0, -10, 0, 0, 0]  # -10 kips in Z direction (vertical)
ret = sap_model.PointObj.SetLoadForce(PointName2, 'DEAD', PointLoadValue)
 
# save model
ret = sap_model.File.Save(ModelPath)
 
# run model (this will create the analysis model)
ret = sap_model.Analyze.RunAnalysis()
 
# initialize for SAP2000 results
NumberResults = 0
Obj = []
Elm = []
ACase = []
StepType = []
StepNum = []
U1 = []
U2 = []
U3 = []
R1 = []
R2 = []
R3 = []
ObjectElm = 0

# get displacement results for the free end
ret = sap_model.Results.Setup.DeselectAllCasesAndCombosForOutput()
ret = sap_model.Results.Setup.SetCaseSelectedForOutput('DEAD')
[NumberResults, Obj, Elm, ACase, StepType, StepNum, U1, U2, U3, R1, R2, R3, ret] = sap_model.Results.JointDispl(PointName2, ObjectElm, NumberResults, Obj, Elm, ACase, StepType, StepNum, U1, U2, U3, R1, R2, R3)

# display results
if NumberResults > 0:
    print("Results for the free end under DEAD load:")
    print(f"  Vertical Displacement (U3): {U3[0]:.6f} ft")
    print(f"  Rotation about Y-axis (R2): {R2[0]:.6f} radians")
"""

sap_example_create_beam_simplified = """
# Step 1: Initialize a new model
# - Initialize the SAP2000 model
# - Create a new blank model
# - Verify initialization completed successfully

# Step 2: Define materials
# - Create a concrete material (you can specify the concrete strength)
# - Set its properties (modulus of elasticity, Poisson's ratio, etc.)
# - Verify material was created successfully

# Step 3: Define sections
# - Create a rectangular beam section
# - Assign the material to this section
# - Verify section was created successfully

# Step 4: Set appropriate units for analysis
# - Change to desired units (e.g., kip-ft-F)
# - Verify units were set correctly

# Step 5: Create beam geometry
# - Add a horizontal beam by coordinates
# - Get the points (nodes) of the beam
# - Verify beam was created successfully

# Step 6: Define boundary conditions
# - Set one end as fixed (restraint all 6 degrees of freedom)
# - Leave the other end free
# - Verify restraints were applied correctly

# Step 7: Define loads
# - Create a dead load pattern
# - Apply a vertical point load at the free end
# - Verify loads were applied correctly

# Step 8: Save the model
# - Save to the specified file path
# - Verify model was saved successfully

# Step 9: Run the analysis
# - Execute the analysis
# - Verify analysis completed successfully

# Step 10: Extract and display results
# - Get displacement results at the free end
# - Print the vertical displacement and rotation
# - Verify results were extracted correctly
"""

api_description = """
sap_model.PropMaterial.SetMaterial("Steel", int(SAP2000.eMatType_Steel))
Decriptin in one paragraph 


API XX ...

"""