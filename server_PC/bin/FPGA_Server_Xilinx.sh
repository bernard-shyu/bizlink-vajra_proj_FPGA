#!/bin/bash
#----------------------------------------------------------------------------
# export HWSERV_RESTART=True           # env-var to indicate whether to kill previous hw_server or not
# export LOCAL_FPGA_HW=True            # env-var for remote ChipScoPy/Jupyter execution
#----------------------------------------------------------------------------
JTAG_PORT=${JTAG_PORT:=3121}           # externally defined export JTAG_PORT, default 3121
JTAG_PORT=${1:-$JTAG_PORT}             # input parameter %1 for JTAG_PORT

rm -f /tmp/FPGA-*.log                  # remove old LOGFILE

if [[ `uname -r` = *"microsoft-standard-WSL2"* ]]; then
	#export CS_SERVER_URL="TCP:10.20.2.146:3042"
	#export HW_SERVER_URL="TCP:10.20.2.146:3121"

	# /mnt/c/Windows/System32/cmd.exe /c 'tasklist ' | grep hw_server

	if [ "$LOCAL_FPGA_HW" = "True" ]; then
		#----------------------------------------------------------------------------
		if ! /mnt/c/Windows/System32/cmd.exe /c 'tasklist ' | grep hw_server; then
			echo -e "\nRestart hw_server"
			/mnt/c/Windows/System32/cmd.exe /c 'C:\Xilinx\Vivado\2023.2\bin\hw_server.bat' & disown
		fi

		#----------------------------------------------------------------------------
		echo -e "\nRestart cs_server"
		/mnt/c/Windows/System32/cmd.exe /c 'taskkill /IM cs_server.exe /F'
		/mnt/c/Windows/System32/cmd.exe /c 'C:\Xilinx\Vivado\2023.2\bin\cs_server.bat' & disown
	fi
else
	TOOLPATH=""
	[ ! -d "$TOOLPATH" ] && TOOLPATH=/opt/Xilinx/tools/Vivado/2023.2/bin
	[ ! -d "$TOOLPATH" ] && TOOLPATH=/opt/Xilinx/tools/Vivado_Lab/2023.2/bin
	[ ! -d "$TOOLPATH" ] && TOOLPATH=/fpga_share/Xilinx_tools/Vivado/2023.2/bin
	[ ! -d "$TOOLPATH" ] && TOOLPATH=/fpga_share/Xilinx_tools/Vivado_Lab/2023.2/bin

	if [ "$LOCAL_FPGA_HW" = "True" ] && [ -d "$TOOLPATH" ]; then
		cd $TOOLPATH

		#----------------------------------------------------------------------------
		[ "$HWSERV_RESTART" = "True" ]  && sudo killall -9 hw_server     # kill previous instances
		if ! ps -ef | egrep '[h]w_server' > /dev/null; then
			echo -e "\nRestart hw_server"
			./hw_server  -d -L/tmp/FPGA-hw_$JTAG_PORT.`date +%F_%H%M`.log -stcp::$JTAG_PORT -levents,eventcore,protocol,discovery,tcflog,jtag2,jtag,xvc,pcie
			#./hw_server -d -L/tmp/FPGA-$JTAG_PORT.`date +%F_%H%M`.log -stcp::$JTAG_PORT
			#./hw_server -d -L/tmp/FPGA-$JTAG_PORT.`date +%F_%H%M`.log -stcp::$JTAG_PORT -e "set xvc-servers $XVC_SERVER:localhost:3000"
		fi

		#----------------------------------------------------------------------------
		# Usage: cs_server [OPTIONS]
		# 
		# Options:
		#   -L, --log-file <file>           enable logging, use -L- to send log to
		#                                   stdout
		#   -l, --log-domains <domains>     enable logging based on domain. Format -
		#                                   "<domains separated by comma>:<level>". The
		#                                   level should be one of the following: TRACE/
		#                                   DEBUG/INFO/SUCCESS/WARNING/ERROR/CRITICAL
		#   -s <url>                        set agent listening port and protocol
		#                                   [default: TCP::3042]
		#   -d, --daemon-mode               run in daemon mode
		#   -I, --idle-timeout <idle-seconds>
		#                                   exit if there are no connections for the
		#                                   specified time
		#   -i, --interactive               run in interactive mode
		#----------------------------------------------------------------------------
		sudo killall -9 cs_server     # kill previous instances
		if ! ps -ef | egrep '[c]s_server' > /dev/null; then
			echo -e "\nRestart cs_server"
			./cs_server -L /tmp/FPGA-cs_server.`date +%F_%H%M`.log -d  & disown
			# ./cs_server & disown
		fi
	fi
fi

