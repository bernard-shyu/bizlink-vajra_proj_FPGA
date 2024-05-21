#--------------------------------------------------------------------------------------------------------------------------------------------------------------
# Script execution examples: 
#	BASH_shell:   export MY_HW_ID=0   MY_PATH=XilinxCEDStore-Learning      MY_PROJ=bxu_vpk120_ChipScoPy_Example_Design;  TCL_Vivado.sh -source ~/fpgaspace/TCL_scripts/bxu_vivado_proj.tcl  -tclargs $HOME/VIVADO_projects/$MY_PATH $MY_PROJ $MY_HW_ID  -B
#	VIVADO%  set MY_HW_ID 0; set MY_PATH XilinxCEDStore-Learning; set MY_PROJ bxu_vpk120_ChipScoPy_Example_Design;
#	         set argc 4; set argv [list $env(HOME)/VIVADO_projects/$MY_PATH $MY_PROJ $MY_HW_ID -I];  source $env(HOME)/fpgaspace/TCL_scripts/bxu_vivado_proj.tcl
#--------------------------------------------------------------------------------------------------------------------------------------------------------------
#	BASH_shell:   export MY_HW_ID=111A MY_RATE=56G HWSERVER="-s 10.20.2.145:3121" MY_CONN=SLoop_x8; export MY_PATH=BZProj_iBERT_Testing  MY_PROJ=VPK120_iBERT_2xQDD_${MY_RATE}  MY_LMAP="-S bxu_ibert_set_LinkChannels.tcl"; \
#	                     TCL_Vivado.sh -source ~/fpgaspace/TCL_scripts/bxu_vivado_proj.tcl -tclargs $HOME/VIVADO_projects/$MY_PATH $MY_PROJ $MY_HW_ID -I $MY_LMAP $HWSERVER
#	VIVADO%  set MY_HW_ID 111A; set MY_RATE 56G; set MY_LMAP SLoop_x8;  # set MY_HW_ID 0; set MY_HW_ID 112A;   set MY_RATE 56G;  set MY_RATE 112G;  set MY_RATE ETH25G;   set MY_LMAP SLoop_x4;  set MY_LMAP SLoop_x8;  set MY_LMAP XConn_x4;  set MY_LMAP XConn_x8;
#	         set MY_PATH BZProj_iBERT_Testing; set MY_PROJ VPK120_iBERT_2xQDD_${MY_RATE}; set argc 5; set argv [list $env(HOME)/VIVADO_projects/$MY_PATH $MY_PROJ $MY_HW_ID -S vpk120_ibert_ChMap_$MY_LMAP.tcl];    source $env(HOME)/fpgaspace/TCL_scripts/bxu_vivado_proj.tcl
#                set MY_PATH BZProj_iBERT_Testing; set MY_PROJ VPK120_iBERT_2xQDD_${MY_RATE}; set argc 6; set argv [list $env(HOME)/VIVADO_projects/$MY_PATH $MY_PROJ $MY_HW_ID -S vpk120_ibert_ChMap_$MY_LMAP.tcl -I]; source $env(HOME)/fpgaspace/TCL_scripts/bxu_vivado_proj.tcl
#--------------------------------------------------------------------------------------------------------------------------------------------------------------
if { $argc < 3 } {
	puts "Syntax:  $argv0  <PROJ_PATH>  <PROJ_NAME>  <HW_ID>  \[ -B \] \[ -I \] \[ -S <TCL_script> \] \[ -s <hw_server> \]"
	puts "HW_ID: VPK120 S/N (0 or 111A or 112A)   hw_server: 'TPLab-Ubuntu-1:3121' or 'HPElite-i7-TP261:3121'"
	puts "Options: -B (open board file), -I (program Image), -S (extra TCL script)\n\n"
	puts [exec echo "You've run as ($argc):  $argv0 $argv\n"]
	puts [exec head -11 "$argv0"]
	puts "\n"
	exit
} else {
	set BXU_PROJ_PATH [lindex $argv 0]
	set BXU_PROJ_NAME [lindex $argv 1]
	set BXU_HW_ID     [lindex $argv 2]

	set BXU_OPTIONS ""
	set BXU_OPEN_BOARD     0
	set BXU_PROG_IMAGE     0
	set BXU_EXTRA_TCL      0
	set BXU_EXTRA_TCL_FILE ""
	set BXU_HW_SERVER      ""
	for {set i 3} {$i < $argc} {incr i} {
		set OPTION [lindex $argv $i]
		append BXU_OPTIONS $OPTION " "
		switch -regexp  -- $OPTION {
		  "-B"  { set BXU_OPEN_BOARD    1; }
		  "-I"  { set BXU_PROG_IMAGE    1; }
		  "-S"  { set BXU_EXTRA_TCL     1;
		          incr i
		          set BXU_EXTRA_TCL_FILE  [lindex $argv $i]
		        }
		  "-s"  { incr i
		          set BXU_HW_SERVER [lindex $argv $i]
		        }
		}
	}
}

set TCL_SCRIPT_PATH [ exec dirname $argv0 ]
set BXU_PROJ_FILE  ${BXU_PROJ_PATH}/${BXU_PROJ_NAME}/${BXU_PROJ_NAME}.xpr
set BXU_IMAGE_FILE [ exec find ${BXU_PROJ_PATH}/${BXU_PROJ_NAME}/${BXU_PROJ_NAME}.runs -name \*.pdi ]
set BXU_BOARD_FILE [ exec find ${BXU_PROJ_PATH}/${BXU_PROJ_NAME}/${BXU_PROJ_NAME}.srcs -name \*.bd ]

puts "Run as: $argv0 $BXU_PROJ_PATH $BXU_PROJ_NAME $BXU_HW_ID $BXU_OPTIONS"
puts "open_Board:     $BXU_OPEN_BOARD,   program_Image: $BXU_PROG_IMAGE,   EXTRA_TCL: $BXU_EXTRA_TCL"
puts "Vivado Project: $BXU_PROJ_FILE"
puts "Vivado Image:   $BXU_IMAGE_FILE"
puts "Vivado Board:   $BXU_BOARD_FILE"
puts "Extra TCL File: $BXU_EXTRA_TCL_FILE"

#-------------------------------------------------------------------------------------------------------
# Open Vivado Project file
#-------------------------------------------------------------------------------------------------------
set CurrProj [get_projects];         # Check if Project is opened already or not
puts "CurrProj: $CurrProj"
if { $CurrProj != "" && $CurrProj != $BXU_PROJ_NAME } {
	close_project
	set CurrProj ""
}

if { $CurrProj == "" } {
	start_gui
	open_project $BXU_PROJ_FILE 
	update_compile_order -fileset sources_1
}

#-------------------------------------------------------------------------------------------------------
# Open Vivado Board Design file
#-------------------------------------------------------------------------------------------------------
if { $BXU_OPEN_BOARD } {
	open_bd_design $BXU_BOARD_FILE
}

# TCL for FPGA Hardware check:
#	current_hw_server  ==> TPLab-Ubuntu-1:3121
#	current_hw_target  ==> TPLab-Ubuntu-1:3121/xilinx_tcf/Xilinx/872311160111A
#	current_hw_target  ==> HPElite-i7-TP261:3121/xilinx_tcf/Xilinx/872311160112A
#	current_hw_device  ==> xcvp1202_1

#-------------------------------------------------------------------------------------------------------
# Open Hardware Server -- daily disconnect / re-connect to FPGA hw_server
#-------------------------------------------------------------------------------------------------------
open_hw_manager

set CurrHWServer [current_hw_server];         # daily disconnect / re-connect to FPGA hw_server
puts "current_hw_server: $CurrHWServer"
if { $CurrHWServer != "" }  { disconnect_hw_server   "$CurrHWServer" }

switch $BXU_HW_ID {
  "111A" { if { $BXU_HW_SERVER == "" }  { set CurrHWServer "TPLab-Ubuntu-1:3121"
           } else                       { set CurrHWServer $BXU_HW_SERVER } }
  "112A" { if { $BXU_HW_SERVER == "" }  { set CurrHWServer "HPElite-i7-TP261:3121"
           } else                       { set CurrHWServer $BXU_HW_SERVER } }
  "0"    { set CurrHWServer "" }
}
set Target_HWID "*/xilinx_tcf/Xilinx/*$BXU_HW_ID"

if { $CurrHWServer != "" }  {
	connect_hw_server -url "$CurrHWServer" -allow_non_jtag

	#-----------------------------------------------------------------------------------------------
	# Open Hardware Target / Program Device
	#-----------------------------------------------------------------------------------------------
	current_hw_target [get_hw_targets $Target_HWID]
	set_property PARAM.FREQUENCY 15000000 [get_hw_targets $Target_HWID]
	open_hw_target

	if { $BXU_PROG_IMAGE } {
		set_property PROBES.FILE {} [get_hw_devices xcvp1202_1]
		set_property FULL_PROBES.FILE {} [get_hw_devices xcvp1202_1]
		set_property PROGRAM.FILE $BXU_IMAGE_FILE [get_hw_devices xcvp1202_1]
		program_hw_devices [get_hw_devices xcvp1202_1]
	}

	refresh_hw_device [lindex [get_hw_devices xcvp1202_1] 0]
}

#-------------------------------------------------------------------------------------------------------
# To run extra TCL script. For example, to create iBERT Links for VPK120 QSP-DD channels
#-------------------------------------------------------------------------------------------------------
if { $BXU_EXTRA_TCL } {
	source ${TCL_SCRIPT_PATH}/${BXU_EXTRA_TCL_FILE}
}

