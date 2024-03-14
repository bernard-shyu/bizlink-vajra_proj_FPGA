#!/bin/bash
#----------------------------------------------------------------------------
JUPYTER_PORT=${JUPYTER_PORT:=8080}	# externally defined export JUPYTER_PORT
JUPYTER_PORT=${1:-$JUPYTER_PORT}	# input parameter %1 for JUPYTER_PORT
JTAG_PORT=${JTAG_PORT:=3121}		# Xilinx default 3121, thus adopt 3199 to avoid conflict

rm -f /tmp/FPGA-$JTAG_PORT.*   # remove old LOGFILE

if [[ `uname -r` = *"microsoft-standard-WSL2"* ]]; then
	#export CS_SERVER_URL="TCP:10.20.2.146:3042"
	#export HW_SERVER_URL="TCP:10.20.2.146:3121"

	# /mnt/c/Windows/System32/cmd.exe /c 'tasklist ' | grep hw_server

	if [ "$LOCAL_FPGA_HW" = "True" ]; then
		echo -e "\nRestart cs_server"
		/mnt/c/Windows/System32/cmd.exe /c 'taskkill /IM cs_server.exe /F'
		/mnt/c/Windows/System32/cmd.exe /c 'C:\Xilinx\Vivado\2023.2\bin\cs_server.bat' & disown

		if ! /mnt/c/Windows/System32/cmd.exe /c 'tasklist ' | grep hw_server; then
			echo -e "\nRestart hw_server"
			/mnt/c/Windows/System32/cmd.exe /c 'C:\Xilinx\Vivado\2023.2\bin\hw_server.bat' & disown
		fi
	fi
else
	TOOLPATH=/opt/Xilinx/tools/Vivado_Lab/2023.2/bin
	[ ! -d "$TOOLPATH" ] && TOOLPATH=/opt/Xilinx/tools/Vivado/2023.2/bin
	[ ! -d "$TOOLPATH" ] && TOOLPATH=/fpga_share/Xilinx_tools/Vivado_Lab/2023.2/bin
	[ ! -d "$TOOLPATH" ] && TOOLPATH=/fpga_share/Xilinx_tools/Vivado/2023.2/bin

	if [ "$LOCAL_FPGA_HW" = "True" ] && [ -d "$TOOLPATH" ]; then
		cd $TOOLPATH

		sudo killall -9 cs_server     # kill all previous instances
		if ! ps -ef | egrep '[c]s_server' > /dev/null; then
			echo -e "\nRestart cs_server"
			./cs_server & disown
		fi

		# sudo killall -9 hw_server     # kill all previous instances   ## NO KILL
		if ! ps -ef | egrep '[h]w_server' > /dev/null; then
			echo -e "\nRestart hw_server"
			./hw_server  -d -L/tmp/FPGA-$JTAG_PORT.`date +%F_%H%M`.log -stcp::$JTAG_PORT
			#./hw_server -d -L/tmp/FPGA-$JTAG_PORT.`date +%F_%H%M`.log -stcp::$JTAG_PORT -e "set xvc-servers $XVC_SERVER:localhost:3000"
		fi
	fi
fi

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

