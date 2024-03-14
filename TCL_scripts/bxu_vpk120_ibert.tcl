if { $argc != 3 } {
	puts "Syntax:  $argv0  <PROJ_PATH>  <PROJ_NAME>  <HW_ID: 111 or 112 or -111 or -112 >"
	puts "Example: $argv0  /home/bernard/VIVADO_projects/iBERT_study bxu_vpk120_ibert_2xQDD_56G 111"
	exit
} else {
	set BXU_PROJ_PATH [lindex $argv 0]
	set BXU_PROJ_NAME [lindex $argv 1]
	set BXU_HW_ID [lindex $argv 2]
}

set BXU_PROJ_FILE  ${BXU_PROJ_PATH}/${BXU_PROJ_NAME}/${BXU_PROJ_NAME}.xpr
set BXU_IMAGE_FILE [ exec find ${BXU_PROJ_PATH}/${BXU_PROJ_NAME}/${BXU_PROJ_NAME}.runs -name \*.pdi ]
set BXU_BOARD_FILE [ exec find ${BXU_PROJ_PATH}/${BXU_PROJ_NAME}/${BXU_PROJ_NAME}.srcs -name \*.bd ]

puts "Run as: $argv0 $BXU_PROJ_PATH $BXU_PROJ_NAME $BXU_HW_ID"
puts "Vivado Project: $BXU_PROJ_FILE"
puts "Vivado Image:   $BXU_IMAGE_FILE"
puts "Vivado Board:   $BXU_BOARD_FILE"

if { $BXU_HW_ID > 0 } {
	start_gui
	open_project $BXU_PROJ_FILE 
	update_compile_order -fileset sources_1
} else {
	set BXU_HW_ID [ expr 0 - $BXU_HW_ID ]
}

# open_bd_design $BXU_BOARD_FILE

open_hw_manager
if { $BXU_HW_ID == 111 } {
	connect_hw_server -url TPLab-Ubuntu-1:3121 -allow_non_jtag
	current_hw_target [get_hw_targets */xilinx_tcf/Xilinx/872311160111A]
	set_property PARAM.FREQUENCY 15000000 [get_hw_targets */xilinx_tcf/Xilinx/872311160111A]
} else {
	connect_hw_server -url HPElite-i7-TP261:3121 -allow_non_jtag
	current_hw_target [get_hw_targets */xilinx_tcf/Xilinx/872311160112A]
	set_property PARAM.FREQUENCY 15000000 [get_hw_targets */xilinx_tcf/Xilinx/872311160112A]
}
open_hw_target

set_property PROBES.FILE {} [get_hw_devices xcvp1202_1]
set_property FULL_PROBES.FILE {} [get_hw_devices xcvp1202_1]
set_property PROGRAM.FILE $BXU_IMAGE_FILE [get_hw_devices xcvp1202_1]
program_hw_devices [get_hw_devices xcvp1202_1]
refresh_hw_device [lindex [get_hw_devices xcvp1202_1] 0]

set TCL_SCRIPT_PATH [ exec dirname $argv0 ]
source ${TCL_SCRIPT_PATH}/vpk120_ibert_Channel-mapping.tcl
