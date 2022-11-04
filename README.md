# Thermal Simulations for the [Open Flow Meter](https://github.com/JochiSt/OpenFlowMeter)

## Pre-Setup
In order to run the simulations contained inside this repository, [ELMERFEM]
(http://www.elmerfem.org/) must be installed.

### Install ELMER FEM
The easiest way of installing ELMER FEM is compiling it from the source code.
```bash
cd ~/Downloads
mkdir elmer
cd elmer
git clone https://www.github.com/ElmerCSC/elmerfem.git
cd elmerfem
mkdir build
cd build
cmake -DWITH_ELMERGUI:BOOL=FALSE -DWITH_MPI:BOOL=FALSE -DCMAKE_INSTALL_PREFIX=../../install ../
make -j install
```

For a convinient usage add the installation directory to `PATH` in your `.bashrc`
```bash
# ELMER FEM
export ELMER_HOME=$HOME/Downloads/elmer/install/
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$ELMER_HOME/lib
export PATH=$PATH:$ELMER_HOME/bin
```

Now ELMER FEM should be ready for usage. In case you want to look at the 
simulation output, `Paraview` is one software, you can use. It can be installed 
via `sudo apt install paraview`.

## Setup
Setup a virtual python environment and install the required packages via
```
pip install -r requirements.txt
```

