#!/bin/sh
#
#Argument $1 the number of trials for QDistRnd
#(more trials = more accuracy)

path/to/gap -q << EOI
LoadPackage("QDistRnd");;
lsX:=ReadMTXE("path/to/code/hx.mtx");;
lsZ:=ReadMTXE("path/to/code/hz.mtx");;
DistRandCSS(lsX[3],lsZ[3],$1,0,8);
DistRandCSS(lsZ[3],lsX[3],$1,0,8);
quit;
EOI
