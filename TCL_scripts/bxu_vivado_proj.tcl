#-------------------------------------------------------------------------------------------------------
# Script execution: 
#	TCL shell:    TCL_Vivado.sh -source ~/fpgaspace/TCL_scripts/bxu_vpk120_ibert.tcl  -tclargs $HOME/VIVADO_projects/iBERT_study bxu_vpk120_ibert_2xQDD_56G 111 PI
#	TCL_Console%  set BXU_HW_ID 111
#	TCL_Console%  set argc 3; set argv [list $env(HOME)/VIVADO_projects/iBERT_study bxu_vpk120_ibert_2xQDD_56G $BXU_HW_ID];   source $env(HOME)/fpgaspace/TCL_scripts/bxu_vpk120_ibert.tcl 
#	TCL_Console%  set argc 4; set argv [list $env(HOME)/VIVADO_projects/iBERT_study bxu_vpk120_ibert_2xQDD_56G $BXU_HW_ID I]; source $env(HOME)/fpgaspace/TCL_scripts/bxu_vpk120_ibert.tcl 
#-------------------------------------------------------------------------------------------------------
if { $argc < 3 } {
	puts "Syntax:  $argv0  <PROJ_PATH>  <PROJ_NAME>  <HW_ID: 111 / 112>  [ <options>: P (open project) / I (program Image) ]"
	puts "Example: $argv0  /home/bernard/VIVADO_projects/iBERT_study bxu_vpk120_ibert_2xQDD_56G 111"
	exit
} else {
	set BXU_PROJ_PATH [lindex $argv 0]
	set BXU_PROJ_NAME [lindex $argv 1]
	set BXU_HW_ID     [lindex $argv 2]

	set BXU_OPTIONS ""
	set BXU_OPEN_PROJ   0
	set BXU_PROG_IMAGE  0
	if { $argc > 3 } {
		set BXU_OPTIONS [lindex $argv 3]
		switch -regexp -- $BXU_OPTIONS {
		  PI|IP { set BXU_OPEN_PROJ 1; set BXU_PROG_IMAGE 1; }
		  P     { set BXU_OPEN_PROJ 1 }
		  I     { set BXU_PROG_IMAGE 1; }
		}
	}
}

set TCL_SCRIPT_PATH [ exec dirname $argv0 ]
set BXU_PROJ_FILE  ${BXU_PROJ_PATH}/${BXU_PROJ_NAME}/${BXU_PROJ_NAME}.xpr
set BXU_IMAGE_FILE [ exec find ${BXU_PROJ_PATH}/${BXU_PROJ_NAME}/${BXU_PROJ_NAME}.runs -name \*.pdi ]
set BXU_BOARD_FILE [ exec find ${BXU_PROJ_PATH}/${BXU_PROJ_NAME}/${BXU_PROJ_NAME}.srcs -name \*.bd ]

puts "Run as: $argv0 $BXU_PROJ_PATH $BXU_PROJ_NAME $BXU_HW_ID $BXU_OPTIONS"
puts "Vivado Project: $BXU_PROJ_FILE"
puts "Vivado Image:   $BXU_IMAGE_FILE"
puts "Vivado Board:   $BXU_BOARD_FILE"
puts "open_Project: $BXU_OPEN_PROJ,  program_Image: $BXU_PROG_IMAGE"

#-------------------------------------------------------------------------------------------------------
# Open Vivado Project file
#-------------------------------------------------------------------------------------------------------
if { $BXU_OPEN_PROJ } {
	start_gui
	open_project $BXU_PROJ_FILE 
	update_compile_order -fileset sources_1
}

#-------------------------------------------------------------------------------------------------------
# Open Vivado Board Design file
#-------------------------------------------------------------------------------------------------------
# open_bd_design $BXU_BOARD_FILE

# TCL for FPGA Hardware check:
#	current_hw_server  ==> TPLab-Ubuntu-1:3121
#	current_hw_target  ==> TPLab-Ubuntu-1:3121/xilinx_tcf/Xilinx/872311160111A
#	current_hw_device  ==> xcvp1202_1

#-------------------------------------------------------------------------------------------------------
# Open Hardware Server -- daily disconnect / re-connect to FPGA hw_server
#-------------------------------------------------------------------------------------------------------
open_hw_manager

set CurrHW [current_hw_server];         # daily disconnect / re-connect to FPGA hw_server
puts "current_hw_server: $CurrHW"
if { $CurrHW != "" }  { disconnect_hw_server   "$CurrHW" }

switch $BXU_HW_ID {
  111 { set CurrHW "TPLab-Ubuntu-1:3121" }
  112 { set CurrHW "HPElite-i7-TP261:3121" }
}

connect_hw_server -url "$CurrHW" -allow_non_jtag

#-------------------------------------------------------------------------------------------------------
# Open Hardware Target / Program Device
#-------------------------------------------------------------------------------------------------------
current_hw_target [get_hw_targets */xilinx_tcf/Xilinx/*]
set_property PARAM.FREQUENCY 15000000 [get_hw_targets */xilinx_tcf/Xilinx/*]
open_hw_target

if { $BXU_PROG_IMAGE } {
	set_property PROBES.FILE {} [get_hw_devices xcvp1202_1]
	set_property FULL_PROBES.FILE {} [get_hw_devices xcvp1202_1]
	set_property PROGRAM.FILE $BXU_IMAGE_FILE [get_hw_devices xcvp1202_1]
	program_hw_devices [get_hw_devices xcvp1202_1]
}

refresh_hw_device [lindex [get_hw_devices xcvp1202_1] 0]

#-------------------------------------------------------------------------------------------------------
# Create iBERT Links for VPK120 QSP-DD channels
#-------------------------------------------------------------------------------------------------------
source ${TCL_SCRIPT_PATH}/vpk120_ibert_Channel-mapping.tcl
