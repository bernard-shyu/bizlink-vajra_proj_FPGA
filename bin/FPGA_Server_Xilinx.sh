#!/bin/bash
#----------------------------------------------------------------------------
JTAG_PORT=${JTAG_PORT:=3121}           # externally defined export JTAG_PORT, default 3121
JTAG_PORT=${1:-$JTAG_PORT}             # input parameter %1 for JTAG_PORT

# kill all previous instances
sudo killall -9 hw_server
rm -f /tmp/FPGA-$JTAG_PORT.*   # remove old LOGFILE

TOOLPATH=/opt/Xilinx/tools/Vivado_Lab/2023.2/bin
[ ! -d "$TOOLPATH" ] && TOOLPATH=/opt/Xilinx/tools/Vivado/2023.2/bin
[ ! -d "$TOOLPATH" ] && TOOLPATH=/fpga_share/Xilinx_tools/Vivado_Lab/2023.2/bin
[ ! -d "$TOOLPATH" ] && TOOLPATH=/fpga_share/Xilinx_tools/Vivado/2023.2/bin
cd $TOOLPATH

./hw_server -d -levents,eventcore,protocol,discovery,tcflog,jtag2,jtag,xvc,pcie -L/tmp/FPGA-$JTAG_PORT.`date +%F_%H%M`.log -stcp::$JTAG_PORT
