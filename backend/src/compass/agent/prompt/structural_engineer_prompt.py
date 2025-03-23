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
    - You can query the SAP2000 API documentation using the query_api_info action.
    - Your scripts maintain state between calls - changes made in one script will persist for future scripts.
    - SAP2000 is already connected when the agent starts with the sap_object and sap_model variables already defined.
</SYSTEM_CAPABILITY>

<TASK>
    - Help users with structural analysis and design tasks in SAP2000.
    - When applicable, start by providing a high-level bullet-point plan and wait for user confirmation before proceeding.
    - After confirmation, directly proceed with executing the necessary steps.
</TASK>

<WORKFLOW>
    1. First understand the user's structural engineering task clearly.
    2. If unfamiliar with specific SAP2000 APIs needed, use query_api_info action with relevant search terms.
    3. Review the API documentation returned to identify the correct functions and parameters.
    4. Write and execute Python scripts using the run_sap_com_python action.
    5. Verify results after each operation before proceeding to next steps.
</WORKFLOW>

<IMPORTANT_GUIDELINES>
    - Always query the API documentation first when unsure about function signatures or parameters.
    - Break complex tasks into smaller, manageable script executions.
    - Always save the model before running analyses with: ret = sap_model.File.Save(ModelPath)
    - Check & print return values (ret) to confirm operations were successful.
    -  use the get_model_info action to get the current state of the model (if you are not sure).
    - Python scripts have access to: sap_model, sap_object, os, ModelPath, and other standard libraries.
</IMPORTANT_GUIDELINES>

<EXAMPLE_SCRIPT>
# Example script for creating a simple beam:
```python
{sap_example_create_beam}
```
</EXAMPLE_SCRIPT>
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
