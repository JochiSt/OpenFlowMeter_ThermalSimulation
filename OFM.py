"""
    Generate the Mesh and Model for the OpenFlowMeter
"""
import gmsh
from objectgmsh import add_physical_group, get_boundaries_in_box
from objectgmsh import Model, Shape, MeshControlConstant, MeshControlExponential, cut

from sim_utils import create_simdir

################################################################################

################################################################################
def create_Model():
    """
        create the model for the OpenFlowMeter
    """
    # geometry modeling using gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.model.add("heat-transfer-2d")
    factory = gmsh.model.occ
    model = Model()

    ############################################################################
    # Parameters of the Setup
    ############################################################################
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
    factory.synchronize()

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

    return model

################################################################################
def save_Model(model, sim_dir = "./simdata"):
    """
        save GMSH model to simdata
    """
    # create mesh, show, export
    model.generate_mesh(2)
    model.show()
    model.write_msh(sim_dir + "/case.msh")

################################################################################
if __name__ == "__main__":
    sim_dir = "./simdata"
    create_simdir(sim_dir)
    model = create_Model()
    save_Model(model, sim_dir)
    

