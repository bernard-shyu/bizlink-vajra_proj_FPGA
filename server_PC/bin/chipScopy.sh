#!/bin/bash
#----------------------------------------------------------------------------
source FPGA_Server_Xilinx.sh

JUPYTER_PORT=${JUPYTER_PORT:=8080}	# externally defined export JUPYTER_PORT
JUPYTER_PORT=${1:-$JUPYTER_PORT}	# input parameter %1 for JUPYTER_PORT

if [ -d "$MYCHIPSCOPY_PATH" ]; then
	cd $MYCHIPSCOPY_PATH
else
	EXAMPLEPATH=$HOME/fpgaspace/chipscopy-examples
	[ ! -d "$EXAMPLEPATH" ] &&
	EXAMPLEPATH=$HOME/chipscopy-examples
	cd $EXAMPLEPATH
fi
source ~/venv/bin/activate;

SSH_PORT=""
netstat -lnt | grep '0.0.0.0:2222' > /dev/null && SSH_PORT="-p 2222"

MYIP=$(grep `uname -n` /etc/hosts | awk '{print $1}')
echo -e "\n\n\nIn local machine BASH terminal, run below: \n\t" \
	"ssh $SSH_PORT -NL localhost:$JUPYTER_PORT:localhost:$JUPYTER_PORT `id -un`@$MYIP \n" \
	"\n============================================================================\n"

sudo killall -9 jupyter-notebook    # kill all previous instances
jupyter notebook --no-browser --port=$JUPYTER_PORT & disown

exit
#----------------------------------------------------------------------------
[How do I detach a process from Terminal, entirely?](https://superuser.com/questions/178587/how-do-i-detach-a-process-from-terminal-entirely)
[How to run a jupyter notebook through a remote server on local machine?](https://stackoverflow.com/questions/69244218/how-to-run-a-jupyter-notebook-through-a-remote-server-on-local-machine)

nohup ./cs_server &> /tmp/nohup.cs_server.out &
nohup ./cs_server > /tmp/nohup.cs_server.out 2>&1 &

In Browser, type: http://server.example.com:8080/tree?token=dd9024f1fb68434645d3902d161f41720650644dc5832f16

