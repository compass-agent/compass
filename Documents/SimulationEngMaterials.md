

https://www.youtube.com/watch?v=dDhGgyXKYH4
Opensource end to end simulation process
This video outline the process for running OpenFOAM simulations and can be summarized in three main steps:
	1.	Geometry and Meshing:
	•	This involves defining the geometry and creating a mesh for the simulation.
	•	It can be done directly in OpenFOAM using tools like blockMesh (suitable for simpler geometries) or through third-party modeling and meshing software like Salome (popular for complex geometries).
	•	The result is a file that describes the geometry and mesh, which gets placed inside the OpenFOAM case study.
	2.	OpenFOAM Solving:
	•	In this step, users set up their simulation by defining initial and boundary conditions, material properties, transport properties, and time information.
	•	Users must select a solver based on whether the simulation is steady-state or dynamic.
	•	The output includes files containing simulation results at specified time steps.
	3.	Post-Processing:
	•	This step involves visualizing the simulation results.
	•	Tools like ParaView are recommended, which allow importing the output folders from the previous step to visually analyze the results. 



https://www.youtube.com/watch?v=IJLROB28nXE&t=2441s
[OpenFoam Tutorial 5] Turbulent Flow in a Pipe with Salome as Mesher

A good but long tutorial starting from meshing in Salome and then running the simulation in OpenFOAM and then post-processing in ParaView. 

My take a ways: 
Meshing is not something that can be automated. It needs many manual tricks. But AI can help in explianing the process or help to know how to do x y z. For instance, user question of what is the way to set a smaller mess size in a specific area. 
Salome then genetates a  .unv file that is then can be used in OpenFOAM. 

Important: To start the OpenFOAM, his suggestion is start with an existing tutorial and then modify it. So then the question is how to pick the right tutorial and how to modify it? . 

I think AI also can help here. This should be back and forth AI discussion with user to undetstand the usecase. For instance, is it incompressible or compressible flow?  Does it have turbulence?  ... Then it will decide which is the one to start with. In tutorails, the folders are partitioned by solver, type of flow, etc.  For each solver such as simpleFoam, pimpleFoam, AI can access to its documentation and even ints source code. In openFoam, manually users can run simpleFoam -doc to see the documentation. Which basically take them to the webpage. 

When you pick a tutorial at the ned 
cp -r $FOAM_TUTORIALS/incompressible/simpleFoam/pitzDaily .

it has typically following files:
/constant
    momentumTransport # file
    turbulenceProperties # file
/system
/0


Then, Copy or move the .unv file into the case folder where you want to run your solver (e.g., case_name/constant/triSurface or just case_name).Then running 

Then we should run ideasUnvToFoam meshFile.unv
This command will create an OpenFOAM mesh in the polyMesh folder under case_name/constant/.
Within that you have bunch of files for example bounday. 
You may need to change the type of them. For instance for surface you may defined as wall  or inlet or outletl you need to chage its type from patch to wall. 


You can also then run checkMesh to ensure there are no problems
It will provide you some information such as Number of severly non-orthoganal faces (>70 degrees). Then it will say if the mesh is Ok or not. 
For instance, in tri mesh if your non-orthogonal angles are higher than 80, then there is a chance of you simulation not converging. 
One of main reason for not converging is that the mesh is not fine enough. 


THen after that, we should make sure to check the turbulenceProperties  and momentumTransport files.  Agent when read must provide descition or suggestion for changes to the user. And make necessary changes as needed. 


Then the 0 folder is where the initial boundary conditions are defined. 
Agent needs to look into those files and provide suggestions. For instance the nuTide and omega files are not needed for the case so should be removed.









OpenFoam + ParaView Installation guide on MacOs
https://openfoam.org/download/8-macos/



https://www.youtube.com/watch?v=3joVOlzCm_Y&t=450s
Building ParaView from source codes [On Demand 15]

This video showing how we can clone the ParView Source code and then compile it (using cmake). Why people do that?
because for instance you can create your own plugins for ParaViews and basically have your own version of it running. 



If you have a plugin, it does not mean you have to again add it at source code level and then compile yourself. Instead paraview has a sort of pluging manager that within UI you can add your pluging by providing the path to the plugin. It makes it easier to manage. 


Plugins? Examples

Q: Can we put our AI to control actions through Plugin and Code?

Q: Can we somehow print out each page info so AI can read it? 



Lincensing? What can we do and what can't we do?






Leveraging ParaView’s Python API for Automation

ParaView offers a Python interface that allows users to control nearly every aspect of the software programmatically. This includes operations like:
	•	Loading datasets
	•	Applying filters and transformations
	•	Adjusting visualization properties
	•	Automating camera movements
	•	And more…

The ParaView GUI itself uses these Python APIs internally, making this approach highly reliable for scripting workflows and automating repetitive tasks. This is especially valuable for embedding ParaView functionality into custom Python applications or AI-driven systems.
ParaView’s Trace Feature: Automating GUI Actions

What is Trace?

ParaView’s Trace feature converts manual user actions in the GUI into Python commands. This enables you to record workflows, save them as scripts, and replay them later programmatically.

How to Use Trace
	1.	Start Recording: In the ParaView menu, go to Tools → Start Trace.
	2.	Perform Actions: Interact with the GUI as you normally would (e.g., load data, apply filters, adjust settings).
	3.	Stop Trace: Choose Tools → Stop Trace, then save the resulting Python script.
	4.	Result: The saved script contains all the Python commands needed to replicate your actions.

from paraview.simple import *
#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

# get active view
renderView1 = GetActiveViewOrCreate('RenderView')

# reset view to fit data bounds
renderView1.ResetCamera(-0.0206, 0.29, -0.0254, 0.0254, -0.0005, 0.0005)

# set camera position and view up
renderView1.CameraPosition = [0.275, 0.068, 0.587]
renderView1.CameraViewUp = [0.057, 0.989, -0.129]

Benefits of Trace
	•	Learning Tool: Easily discover the corresponding Python commands for GUI actions.
	•	Reusability: Scripts can be edited, reused, and incorporated into larger automation workflows.
	•	Debugging: Understand and refine complex operations step-by-step.

Reading Logs in ParaView

ParaView provides logging features to monitor performance and track actions:
	1.	Timer Log: Measures performance (e.g., filter execution times, rendering times).
	2.	Standard or Error Logs: Captures warnings, errors, or informational messages.

How to Access Logs Programmatically

Timer Logs

Use the following functions from paraview.servermanager:
from paraview.servermanager import ToggleTimerLog, GetTimerLog

# Start the Timer Log
ToggleTimerLog(True)

# [Perform actions or execute scripts here]

# Stop the Timer Log
ToggleTimerLog(False)

# Retrieve the Timer Log as a string
logs = GetTimerLog()
print(logs)
Reading Logs as a List of Lines

To retrieve Timer Log data in a structured format (e.g., one line per list element):
def get_paraview_logs():
    from paraview.servermanager import GetTimerLog
    raw_log = GetTimerLog()
    return raw_log.split("\n")

Embedding ParaView in Your Own Python Interpreter

What is it?

Instead of using ParaView’s built-in Python shell or standalone pvpython executable, you can install ParaView’s Python libraries in your Python environment and directly use them in your own scripts or applications.

This approach avoids the need to save or execute intermediate script files and allows for tighter integration with your custom workflows.

Setting Up ParaView in Your Python Environment
	1.	Install ParaView Python Libraries
	•	On macOS or Linux, use pip or conda (if available):


If unavailable, you can use the pvpython interpreter bundled with ParaView or manually configure your Python environment to include ParaView modules.

	2.	Import and Use the API
	•	Once installed, you can import ParaView’s modules:

	2.	Import and Use the API
	•	Once installed, you can import ParaView’s modules:

from paraview.simple import *
from paraview.servermanager import ToggleTimerLog, GetTimerLog

Running ParaView Commands Dynamically (Without Saving Scripts)

To execute a series of Python commands dynamically, use the following approach:

from paraview.simple import *
from paraview.servermanager import ToggleTimerLog

def run_paraview_commands(command_list, use_timer=True):
    """
    Execute a list of Python commands (strings) dynamically in ParaView.

    :param command_list: List of Python command strings.
    :param use_timer: Enable or disable Timer Logs during execution.
    """
    if use_timer:
        ToggleTimerLog(True)

    # Combine all commands into one block and execute
    code_str = "\n".join(command_list)
    exec(code_str, globals(), globals())

    if use_timer:
        ToggleTimerLog(False)
    
    commands = [
    "sphere = Sphere()",  # Create a sphere source
    "Show(sphere)",       # Show the sphere in the current view
    "Render()"            # Render the current view
]

# Run the commands
run_paraview_commands(commands, use_timer=True)

# Retrieve logs
logs = get_paraview_logs()
for line in logs:
    print(line)