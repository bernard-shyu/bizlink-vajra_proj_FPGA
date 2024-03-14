#!/bin/bash
#----------------------------------------------------------------------------
cat <<-END
	`basename $0`   [tcl | gui | batch]  [-nojournal] [-nolog]
	#---------------------------------------------------------------------------------------------------------------------------------------------
	Frequent commands: source <XXX.tcl> / exec <BASH-Commands> / start_gui / stop_gui
	Project mode: create_project / add_files / import_files / add_directories
	Non-Project: read_verilog / read_vhdl / read_edif / read_ip / read_xdc
	#---------------------------------------------------------------------------------------------------------------------------------------------
END

VIVADO_MODE=${VIVADO_MODE:=tcl}		# externally defined export VIVADO_MODE
case "X_$1" in
  "X_tcl" | "X_gui" | "X_batch" )
	VIVADO_MODE=${1:-$VIVADO_MODE}
	shift;;
esac

/fpga_share/Xilinx_tools/Vivado/2023.2/bin/vivado -mode $VIVADO_MODE $*

exit
#----------------------------------------------------------------------------

