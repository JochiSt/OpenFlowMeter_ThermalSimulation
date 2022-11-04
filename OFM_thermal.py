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

# remove the pt100 volume from the gas volume. Note, the PT100 volume is empty
# and will not get meshed at this stage
factory.cut([(2, gas_volume)], [(2, pt100_volume)])

factory.synchronize()

ph_pipe_walls = add_physical_group(2, [upper_pipe_wall, lower_pipe_wall], "steel_v2a")
ph_gas        = add_physical_group(2, [gas_volume], "gas")

gmsh.model.mesh.setSize( gmsh.model.getEntities(0), 0.1e-3)
gmsh.model.mesh.generate(2)

# show mesh & export
gmsh.fltk.run()  # comment this line out if your system doesn't support the gmsh GUI
gmsh.write(sim_dir + "/case.msh")

################################################################################
# ELMER
################################################################################
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



