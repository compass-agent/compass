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
    - ALWAYS work step-by-step - implement and verify one step completely before moving to the next.
</TASK>

<WORKFLOW>
    1. First understand the user's structural engineering task clearly.
    2. Verify results after each operation before proceeding to next steps.
    3. Complete steps sequentially, one at a time.
</WORKFLOW>

<IMPORTANT_GUIDELINES>
    - Break complex tasks into smaller, manageable script executions and complete them one at a time.
    - Check & print return values (ret) to confirm operations were successful.
    - Python scripts have access to: sap_model, sap_object, os, ModelPath, and other standard libraries.
    
    # CRITICAL API USAGE RULES:
    1. ALWAYS use the exact API calls and patterns shown in the example code below.
    2. DO NOT create new API calls or patterns unless absolutely necessary.
    3. If you need to do something not shown in the examples:
       - query the API documentation using query_api_info action
       - Only then consider creating a new API call pattern
    4. Follow the exact same parameter order and naming as shown in examples
    5. Use the same variable names and structure as shown in examples
    6. If unsure, copy and modify the relevant example code rather than creating new patterns
</IMPORTANT_GUIDELINES>

<EXAMPLE_WORKFLOW>
# Simplified steps for creating a basic beam model:

```python
{sap_example_create_steel_frame_structure}
```
</EXAMPLE_WORKFLOW>
""") 
    

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
self.sap_model.PropMaterial.SetMaterial("Steel", int(SAP2000.eMatType_Steel))
Decriptin in one paragraph 


API XX ...

"""



sap_example_create_steel_frame_structure = """
Below is an example of how to create a steel frame structure in SAP2000 for following specifications:
using unit kip-ft-F
material properties: E = 4176000 ksi, v = 0.3, d = 0.00000650
4 levels with heights of 0', 18', 30', and 42'
9 grid lines in the X-direction at 0', 24', 48', 72', 84', 96', 120', 144', and 168'
5 grid lines in the Y-direction at 0', 22', 40', 54', and 64'
Steel columns (24"×24") at each grid intersection
Steel beams (18"×12") connecting all columns at each level
Floor dead load of 75 psf
Floor live load of 50 psf
Roof live load of 20 psf
Fixed supports at all column bases


#  Step 1: start a new model # MAKE SURE to use 4 for kip-ft-F units
self.sap_model.InitializeNewModel(4)
self.sap_model.File.NewBlank()

# Step 2: Create a new material as steel. 
# Important: make sure to use int(SAP2000.eMatType_Steel) instead of 1.
self.sap_model.PropMaterial.SetMaterial("Steel", int(SAP2000.eMatType_Steel))
self.sap_model.PropMaterial.SetMPIsotropic("Steel", float(4176000.0), float(0.3), float(0.00000650))

# Step 3: Delete the default load patterns and add new ones.
self.sap_model.LoadPatterns.Delete("MODAL")
self.sap_model.LoadPatterns.Add("DEAD", int(SAP2000.eLoadPatternType_Dead), 1.0)  # 1 = Dead, 
self.sap_model.LoadPatterns.Add("LIVE", int(SAP2000.eLoadPatternType_Live), 0.0)  # 3 = Live, self-weight multiplier = 0.0

# Step 4: Define the column and beam properties.
self.sap_model.PropFrame.SetRectangle("COLUMN", "A992Fy50", 2, 2)  # 24" x 24" column
self.sap_model.PropFrame.SetRectangle("BEAM", "A992Fy50", 1.5, 1)  # 18" x 12" beam

# Step 5:  Define columns and beams
x_coords = [0, 24, 48, 72, 84, 96, 120, 144, 168]
y_coords = [0, 22, 40, 54, 64]
z_coords = [0, 18, 30, 42]
columns_created = 0
for x in x_coords:
    for y in y_coords:
        ret = self.sap_model.FrameObj.AddByCoord(
            x, y, z_coords[0],   # Bottom point
            x, y, z_coords[-1],  # Top point
            ""  # Auto-name
        )
        col_name = ret[0]
        self.sap_model.FrameObj.SetSection(col_name, "COLUMN")
        columns_created += 1

frame_names = self.sap_model.FrameObj.GetNameList()[1]
restraints_applied = 0
for frame_name in frame_names:
    # Get points of the frame
    point_names = self.sap_model.FrameObj.GetPoints(frame_name, "", "")[0:2]
    # Get coordinates of each point
    for point_name in point_names:
        xyz = self.sap_model.PointObj.GetCoordCartesian(point_name)[0:3]
        
        # If point is at z=0, it's a column base - apply restraint
        if abs(xyz[2]) < 0.001:  # Check if z-coordinate is approximately 0
            # Set fixed restraint for the column bases
            restraint = [True, True, True, False, False, False]
            self.sap_model.PointObj.SetRestraint(point_name, restraint)
            restraints_applied += 1
            break  # Only need to restrain one end of the column

beams_created = 0
# Create X-direction beams
for z in z_coords[1:]:  # Skip the base level
    for y in y_coords:
        for i in range(len(x_coords)-1):
            ret = self.sap_model.FrameObj.AddByCoord(
                x_coords[i], y, z,     # Start point
                x_coords[i+1], y, z,   # End point
                ""  # Auto-name
            )
            beam_name = ret[0]
            self.sap_model.FrameObj.SetSection(beam_name, "BEAM")
            beams_created += 1
    # Create Y-direction beams
    for x in x_coords:
        for i in range(len(y_coords)-1):
            ret = self.sap_model.FrameObj.AddByCoord(
                x, y_coords[i], z,     # Start point
                x, y_coords[i+1], z,   # End point
                ""  # Auto-name
            )
            beam_name = ret[0]
            self.sap_model.FrameObj.SetSection(beam_name, "BEAM")
            beams_created += 1

# Step 5: Create floor areas with appropriate loads
x_coords = [0, 24, 48, 72, 84, 96, 120, 144, 168]
y_coords = [0, 22, 40, 54, 64]
z_coords = [0, 18, 30, 42]  # Floor levels
# Create shell areas at each floor level (skip the base level at z=0)
for z_index, z in enumerate(z_coords[1:], 1):
    # Determine if this is the roof level (the highest level)
    is_roof = (z_index == len(z_coords) - 1)
    # Loop through each bay defined by grid lines
    for i in range(len(x_coords) - 1):
        for j in range(len(y_coords) - 1):
            # Define the coordinates arrays for the 4 corners
            x_array = [x_coords[i], x_coords[i+1], x_coords[i+1], x_coords[i]]
            y_array = [y_coords[j], y_coords[j], y_coords[j+1], y_coords[j+1]]
            z_array = [z, z, z, z]  # All points at the same elevation
            
            # Create the area - using the proper API syntax
            ret = self.sap_model.AreaObj.AddByCoord(
                4,          # Number of points
                x_array,    # X coordinates array
                y_array,    # Y coordinates array
                z_array,    # Z coordinates array
                ""          # Auto-name
            )
            
            # Extract the area name from the return value (4th element, index 3)
            area_name = ret[3]
            
            # Apply dead load (75 psf) - Direction 6 is Global Z
            self.sap_model.AreaObj.SetLoadUniform(
                area_name,    # Area name
                "DEAD",       # Load pattern
                75.0,         # Load value (psf)
                6,            # Direction (6 = Global Z)
                True,         # Replace existing load
                "Global"      # Coordinate system
            )
            
            # Apply live load
            if is_roof:
                # Roof live load (20 psf)
                self.sap_model.AreaObj.SetLoadUniform(
                    area_name,    # Area name
                    "LIVE",       # Load pattern  
                    20.0,         # Load value (psf)
                    6,            # Direction (6 = Global Z)
                    True,         # Replace existing load
                    "Global"      # Coordinate system
                )
            else:
                # Floor live load (50 psf)
                self.sap_model.AreaObj.SetLoadUniform(
                    area_name,    # Area name
                    "LIVE",       # Load pattern
                    50.0,         # Load value (psf)
                    6,            # Direction (6 = Global Z)
                    True,         # Replace existing load
                    "Global"      # Coordinate system
                )
"""