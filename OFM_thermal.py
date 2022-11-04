"""
 Thermal Simulation of the Open Flow Meter using pyelmer
 
 I used the pyelmer example 'heat_transfer_2d_manual.py' as a starting point.
"""

################################################################################
# first import the required packages
import os
import gmsh
from pyelmer import elmer
from pyelmer import execute
from pyelmer.post import scan_logfile

from objectgmsh import add_physical_group, get_boundaries_in_box
from objectgmsh import Model, Shape, MeshControlConstant, MeshControlExponential, cut

################################################################################
# set up working directory
sim_dir = "./simdata"
if not os.path.exists(sim_dir):
    os.mkdir(sim_dir)

################################################################################
# Parameters of the Setup
################################################################################
# Keep in mind: Unit = Meter

# Put everything into a 6mm OD Swagelock pipe with 4mm ID
# Outer planes of the pipe will be at constant room temperature
PIPE_OUTER_DIAMETER = 6E-3
PIPE_INNER_DIAMETER = 4E-3
PIPE_LENGTH         = 100E-3

# PT100
PT100_HEIGHT        = 2E-3
PT100_THICKNESS     = 1E-3

################################################################################
# GMESH
################################################################################
gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)
gmsh.model.add("OFM-Thermal")
model = Model()

factory = gmsh.model.occ

# addRectangle (x,y,z) of lower left point , width, height
upper_pipe_wall = factory.addRectangle( -PIPE_LENGTH/2, PIPE_INNER_DIAMETER/2, 0, 
                                        PIPE_LENGTH, (PIPE_OUTER_DIAMETER-PIPE_INNER_DIAMETER)/2)
lower_pipe_wall = factory.addRectangle( -PIPE_LENGTH/2, -PIPE_OUTER_DIAMETER/2, 0, 
                                        PIPE_LENGTH, (PIPE_OUTER_DIAMETER-PIPE_INNER_DIAMETER)/2)
                                        
gas_volume      = factory.addRectangle( -PIPE_LENGTH/2, -PIPE_INNER_DIAMETER/2, 0, 
                                        PIPE_LENGTH, PIPE_INNER_DIAMETER)
                                        
pt100_volume    = factory.addRectangle( -PT100_THICKNESS/2, -PT100_HEIGHT/2, 0,
                                        PT100_THICKNESS, PT100_HEIGHT)

# remove the pt100 volume from the gas volume. 
# if removeTool=True, the PT100 volume is empty and will not get meshed
factory.cut([(2, gas_volume)], [(2, pt100_volume)], removeTool=False)

factory.synchronize()

s_pipe  = Shape(model, 2, "pipe",  [upper_pipe_wall, lower_pipe_wall])
s_gas   = Shape(model, 2, "gas",   [gas_volume])
s_pt100 = Shape(model, 2, "pt100", [pt100_volume])

factory.synchronize()

# set interfaces between different shapes
s_gas.set_interface(s_pipe)
s_pt100.set_interface(s_gas)

# add physical groups
model.make_physical()

# detect and define boundaries
# gas inlet and gas outlet
bnd_gas_in  = Shape( model, 1, "bnd_gas_in",  [s_gas.left_boundary])
bnd_gas_out = Shape( model, 1, "bnd_gas_out", [s_gas.right_boundary])

# constant temperature outermost surfaces => lab temperature
bnd_lab_T = Shape( model, 1, "bnd_lab_T", [s_pipe.top_boundary, s_pipe.bottom_boundary])

# constant temperature
bnd_pt100_T = Shape( model, 1, "bnd_pt100_T", [s_pt100.top_boundary, 
                                                s_pt100.bottom_boundary, 
                                                s_pt100.left_boundary, 
                                                s_pt100.right_boundary])

# set mesh constraints
model.deactivate_characteristic_length()
MeshControlConstant(model, 50e-6*10, [s_gas, s_pipe])
MeshControlConstant(model, 25e-6*10, [s_pt100])

# create mesh, show, export
model.generate_mesh()
#model.show()
model.write_msh(sim_dir + "/case.msh")

################################################################################
# ELMER
################################################################################
data_dir = "./data"
if not os.path.exists(data_dir):
    os.mkdir(data_dir)
elmer.data_dir = data_dir

sim = elmer.Simulation()
sim.settings = {
    "Coordinate System" : "Cartesian 2D", 
    "Simulation Type"   : "Steady state"
    }

################################################################################
# Material properties
# Argon
# from https://www.chemie.de/lexikon/Argon.html
gas = elmer.Material(sim, "gas")
gas.data = {
    "Density"           : 1.784,    # kg/m^3
    "Heat Capacity"     : 520,      # J/(Kg*K)
    "Heat Conductivity" : 0.01772 , # W/m K
    }

# Stainless Steel V2A
# from https://www.hsm-stahl.de/fileadmin/user_upload/datenblatt/HSM_Datenblatt_1.4301.pdf
steel_v2a = elmer.Material(sim, "steel_v2a")
steel_v2a.data = {
    "Density"           : 7900.0,   # kg/m^3
    "Heat Capacity"     : 500.0,    # J/(Kg*K)
    "Heat Conductivity" : 15,       # W/m K      
    }
    
################################################################################
solver_heat = elmer.Solver(sim, "heat_solver")
solver_heat.data = {
    "Equation": "HeatSolver",
    "Procedure": '"HeatSolve" "HeatSolver"',
    "Variable": '"Temperature"',
    "Variable Dofs": 1,
}
solver_output = elmer.Solver(sim, "output_solver")
solver_output.data = {
    "Exec Solver": "After timestep",
    "Equation": "ResultOutputSolver",
    "Procedure": '"ResultOutputSolve" "ResultOutputSolver"',
}
eqn = elmer.Equation(sim, "main", [solver_heat])
T0 = elmer.InitialCondition(sim, "T0", {"Temperature": 273.15})

bdy_pipe = elmer.Body(sim, "pipe", [s_pipe.ph_id])
bdy_pipe.material = steel_v2a
bdy_pipe.initial_condition = T0
bdy_pipe.equation = eqn

bdy_gas = elmer.Body(sim, "gas", [s_gas.ph_id])
bdy_gas.material = gas
bdy_gas.initial_condition = T0
bdy_gas.equation = eqn

bndry_lab_T = elmer.Boundary(sim, "lab_T", [bnd_lab_T.ph_id])
bndry_lab_T.data.update({"Temperature": 293.15})

bndry_pt100 = elmer.Boundary(sim, "PT100", [bnd_pt100_T.ph_id])
bndry_pt100.data.update({"Temperature": 393.15})

################################################################################
# write simulation files
sim.write_startinfo(sim_dir)
sim.write_sif(sim_dir)

# execute ElmerGrid & ElmerSolver
execute.run_elmer_grid(sim_dir, "case.msh")
execute.run_elmer_solver(sim_dir)

################################################################################
# scan log for errors and warnings
err, warn, stats = scan_logfile(sim_dir)
print("Errors:     ", err)
print("Warnings:   ", warn)
print("Statistics: ", stats)
