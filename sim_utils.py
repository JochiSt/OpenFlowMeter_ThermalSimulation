"""
   simulation utils, some functions, which are useful for FEM simulations
"""

import os

def create_simdir(sim_dir = "./simdata"):
    if not os.path.exists(sim_dir):
        os.mkdir(sim_dir)