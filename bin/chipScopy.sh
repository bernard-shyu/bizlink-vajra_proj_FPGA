#!/bin/bash
#----------------------------------------------------------------------------
JUPYTER_PORT=${JUPYTER_PORT:=8080}	# externally defined export JUPYTER_PORT
JUPYTER_PORT=${1:-$JUPYTER_PORT}	# input parameter %1 for JUPYTER_PORT
JTAG_PORT=${JTAG_PORT:=3121}		# Xilinx default 3121, thus adopt 3199 to avoid conflict

# kill all previous instances
sudo killall -9 hw_server cs_server jupyter-notebook
rm -f /tmp/FPGA-$JTAG_PORT.*   # remove old LOGFILE

TOOLPATH=/opt/Xilinx/tools/Vivado_Lab/2023.2/bin
[ ! -d "$TOOLPATH" ] && TOOLPATH=/opt/Xilinx/tools/Vivado/2023.2/bin
[ ! -d "$TOOLPATH" ] && TOOLPATH=/fpga_share/Xilinx_tools/Vivado_Lab/2023.2/bin
[ ! -d "$TOOLPATH" ] && TOOLPATH=/fpga_share/Xilinx_tools/Vivado/2023.2/bin
cd $TOOLPATH

./cs_server & disown
./hw_server  -d -L/tmp/FPGA-$JTAG_PORT.`date +%F_%H%M`.log -stcp::$JTAG_PORT
#./hw_server -d -L/tmp/FPGA-$JTAG_PORT.`date +%F_%H%M`.log -stcp::$JTAG_PORT -e "set xvc-servers $XVC_SERVER:localhost:3000"

EXAMPLEPATH=$HOME/fpgaspace/chipscopy-examples
[ ! -d "$EXAMPLEPATH" ] &&
EXAMPLEPATH=$HOME/chipscopy-examples
cd $EXAMPLEPATH
source ~/venv/bin/activate;

MYIP=$(grep `uname -n` /etc/hosts | awk '{print $1}')
echo -e "\n\n\nIn local machine BASH terminal, run below: \n\t" \
	"ssh -NfL localhost:$JUPYTER_PORT:localhost:$JUPYTER_PORT `id -un`@$MYIP \n" \
	"\n============================================================================\n"

jupyter notebook --no-browser --port=$JUPYTER_PORT & disown

exit
#----------------------------------------------------------------------------
[How do I detach a process from Terminal, entirely?](https://superuser.com/questions/178587/how-do-i-detach-a-process-from-terminal-entirely)
[How to run a jupyter notebook through a remote server on local machine?](https://stackoverflow.com/questions/69244218/how-to-run-a-jupyter-notebook-through-a-remote-server-on-local-machine)

nohup ./cs_server &> /tmp/nohup.cs_server.out &
nohup ./cs_server > /tmp/nohup.cs_server.out 2>&1 &

In Browser, type: http://server.example.com:8080/tree?token=dd9024f1fb68434645d3902d161f41720650644dc5832f16

