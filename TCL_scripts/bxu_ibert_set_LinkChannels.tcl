#--------------------------------------------------------------------------------------------------------------------------------------
# Environment variables definition in TCL/Vivado or BASH:
#--------------------------------------------------------------------------------------------------------------------------------------
#   set BXU_CREATE_ONLY   <bool_val>     # values: 1 (Create link only)  0 (default, will do RESET as well)
#   set BXU_RESET_DELAY   <delay>        # value:  delay in msec for iBERT TX/RX reset   (default delay: 200)
#   set BXU_CONN_TYPE     <type>         # values: SLoop_x4  SLoop_x8  XConn_x4  XConn_x8  ||  S4  S8  X4  X8  (default type: SLoop_x8)
#   (BASH) export MY_CONN=<type>         # 
#----------------------------------------------------------------------------------------------------------------------------------
#   set BXU_POST_CURSOR   <dB_val>       # Values: [ User Design, 0 dB, -0.20 dB, -0.41 dB, -0.63 dB, -0.85 dB, -1.07 dB, -1.31 dB, -1.54 dB, -1.79 dB, -2.04 dB, -2.30 dB, -2.57 dB, -2.84 dB,
#   set BXU_PRE_CURSOR1   <dB_val>       #           -3.13 dB, -3.42 dB, -3.73 dB, -4.04 dB, -4.37 dB, -4.71 dB, -5.07 dB, -5.43 dB, -5.82 dB,
#                                        #           -6.22 dB, -6.65 dB, -7.09 dB, -7.56 dB, -8.06 dB, -8.59 dB, -9.15 dB, -9.75 dB, -10.39 dB, -11.09 dB, -11.84 dB, -12.67 dB, -13.58 dB, -14.61 dB, -15.77 dB ]
#----------------------------------------------------------------------------------------------------------------------------------
#   set BXU_PRE_CURSOR2   <dB_val>       # Values: [ User Design, 0 dB, -0.20 dB, -0.41 dB, -0.63 dB, -0.85 dB, -1.07 dB, -1.31 dB, -1.54 dB, -1.79 dB, -2.04 dB, -2.30 dB, -2.57 dB, -2.84 dB,
#   set BXU_PRE_CURSOR3   <dB_val>       #           -3.13 dB, -3.42 dB, -3.73 dB, -4.04 dB, -4.37 dB, -4.71 dB, -5.07 dB, -5.43 dB, -5.82 dB ] 
#----------------------------------------------------------------------------------------------------------------------------------
#   set BXU_MAIN_CURSOR   <volt_val>     # Values: [ User Design, 0.502 Vdd, 0.514 Vdd, 0.527 Vdd, 0.539 Vdd, 0.552 Vdd, 0.560 Vdd, 0.568 Vdd, 0.577 Vdd, 0.585 Vdd, 0.593 Vdd, 0.602 Vdd, 0.614 Vdd, 0.626 Vdd, 0.638 Vdd,
#                                        #           0.650 Vdd, 0.661 Vdd, 0.673 Vdd, 0.684 Vdd, 0.696 Vdd, 0.710 Vdd, 0.724 Vdd, 0.738 Vdd, 0.752 Vdd, 0.764 Vdd, 0.777 Vdd, 0.789 Vdd, 0.802 Vdd, 0.814 Vdd, 0.826 Vdd,
#                                        #           0.838 Vdd, 0.850 Vdd, 0.860 Vdd, 0.870 Vdd, 0.881 Vdd, 0.891 Vdd, 0.902 Vdd, 0.914 Vdd, 0.927 Vdd, 0.939 Vdd, 0.952 Vdd, 0.961 Vdd, 0.970 Vdd, 0.979 Vdd, 0.988 Vdd, 0.998 Vdd ]
#----------------------------------------------------------------------------------------------------------------------------------
#   set BXU_LOOPBACK      <mode>         # Values: [ User Design, None, Near-End PCS, Far-End PCS, Near-End PMA, Far-End PMA ]
#   set BXU_DATA_PATTERN  <pattern>      # Values: [ User Design, PRBS Disabled,   PRBS 7,  PRBS 9,  PRBS 13,  PRBS 15,  PRBS 23,  PRBS 31,   QPRBS 9, QPRBS 13, QPRBS 15, QPRBS 23, QPRBS 31,
#                                        #           PRBSQ 7, PRBSQ 9, PRBSQ 13, PRBSQ 15, PRBSQ 23, PRBSQ 31,   Configurable data pattern,   Square wave (2 * UI),   Square wave (Int data width * UI)]
#--------------------------------------------------------------------------------------------------------------------------------------
if { ![info exists BXU_CONN_TYPE] }  {
	if { [info exists env(MY_CONN)] }  { set BXU_CONN_TYPE $env(MY_CONN)
	} else                             { set BXU_CONN_TYPE "SLoop_x8" }
}

switch -regexp  -- $BXU_CONN_TYPE {
  "S4" - "SLoop_x4" { set connType "SelfLooped_X4" }
  "S8" - "SLoop_x8" { set connType "SelfLooped_X8" }
  "X4" - "XConn_x4" { set connType "XConnected_X4" }
  "X8" - "XConn_x8" { set connType "XConnected_X8" }
  default  { puts "unknown Connection type: $BXU_CONN_TYPE"
             return
           }
}

if { ![info exists BXU_CREATE_ONLY]  }  { set BXU_CREATE_ONLY    1              };    ###    0: the default,       1: for experiment now    ###
if { ![info exists BXU_PRE_CURSOR1]  }  { set BXU_PRE_CURSOR1    "User Design"  }
if { ![info exists BXU_PRE_CURSOR2]  }  { set BXU_PRE_CURSOR2    "User Design"  }
if { ![info exists BXU_PRE_CURSOR3]  }  { set BXU_PRE_CURSOR3    "User Design"  }
if { ![info exists BXU_POST_CURSOR]  }  { set BXU_POST_CURSOR    "User Design"  }
if { ![info exists BXU_MAIN_CURSOR]  }  { set BXU_MAIN_CURSOR    "User Design"  }
if { ![info exists BXU_LOOPBACK   ]  }  { set BXU_LOOPBACK       "None"         }
if { ![info exists BXU_DATA_PATTERN] }  { set BXU_DATA_PATTERN   "PRBS 31"      }
if { ![info exists BXU_RESET_DELAY]  }  { set BXU_RESET_DELAY    200            }

#--------------------------------------------------------------------------------------------------------------------------------------
# Connection Map for QSFP-DD ports: QDD-1 & QDD-2 on 2x VPK120 (SN: 111/112)
#--------------------------------------------------------------------------------------------------------------------------------------
#     "XConnected":                                                                   "SelfLooped": 
#     VPK120 (S/N 111)                        VPK120 (S/N 112)                        VPK120 (S/N 111)  and/or  VPK120 (S/N 112) 
#     ----------------                        ----------------                        ------------------------------------------
#     QDD-1 cage <-------------------------------> cage QDD-1                         QDD-1 cage <--------+                    
#                      2x QSFP-DD cables                                                                  |  1x QSFP-DD cable
#     QDD-2 cage <-------------------------------> cage QDD-2                         QDD-2 cage <--------+                   
#--------------------------------------------------------------------------------------------------------------------------------------
proc setup_links_common {cType f_link_method quad_list} {
	global links 
	set links {}
	foreach q $quad_list {
		if { $cType == "XConnected" } { set qq [split "$q $q"] }  else  { set qq [split $q] }
		lappend links $qq
	}

	$f_link_method $links
}

proc setup_links_SelfLooped_X8 {f_link_method} {
	setup_links_common "SelfLooped" $f_link_method {
	            {Quad_202 0 Quad_204 0} {Quad_202 1 Quad_204 2}  {Quad_202 2 Quad_205 0} {Quad_202 3 Quad_205 2}
	            {Quad_203 0 Quad_204 1} {Quad_203 1 Quad_204 3}  {Quad_203 2 Quad_205 1} {Quad_203 3 Quad_205 3}
	            {Quad_204 0 Quad_202 0} {Quad_204 2 Quad_202 1}  {Quad_205 0 Quad_202 2} {Quad_205 2 Quad_202 3}
	            {Quad_204 1 Quad_203 0} {Quad_204 3 Quad_203 1}  {Quad_205 1 Quad_203 2} {Quad_205 3 Quad_203 3} }
}

proc setup_links_SelfLooped_X4 {f_link_method} {
	setup_links_common "SelfLooped" $f_link_method {
	            {Quad_202 0 Quad_204 0} {Quad_202 1 Quad_204 2}  {Quad_202 2 Quad_205 0} {Quad_202 3 Quad_205 2}
	            {Quad_204 0 Quad_202 0} {Quad_205 0 Quad_202 2}  {Quad_204 1 Quad_203 0} {Quad_205 1 Quad_203 2} }
}

proc setup_links_XConnected_X8 {f_link_method} {
	setup_links_common "XConnected" $f_link_method {
	            {Quad_202 0} {Quad_202 1}  {Quad_202 2} {Quad_202 3}
	            {Quad_203 0} {Quad_203 1}  {Quad_203 2} {Quad_203 3}
	            {Quad_204 0} {Quad_204 2}  {Quad_205 0} {Quad_205 2}
	            {Quad_204 1} {Quad_204 3}  {Quad_205 1} {Quad_205 3} }
}

proc setup_links_XConnected_X4 {f_link_method} {
	setup_links_common "XConnected" $f_link_method {
	            {Quad_202 0} {Quad_202 2}  {Quad_203 0} {Quad_203 2}
	            {Quad_204 0} {Quad_204 2}  {Quad_205 0} {Quad_205 2} }
}

proc create_links_common {links} {
	set cmd "set xil_newLinks \[list\]"
	eval $cmd

	set i 0
	foreach qq $links {
		set qTX [lindex $qq 0];  set chTX [lindex $qq 1]
		set qRX [lindex $qq 2];  set chRX [lindex $qq 3]

		set lnk(TX) "IBERT_0.$qTX.CH_$chTX.TX"
		set lnk(RX) "IBERT_0.$qRX.CH_$chRX.RX"
		# DEBUG:: puts "LINK-$i: $qq   q0: [lindex $qq 0]  q1: [lindex $qq 1]  TX: ${lnk(TX)}  RX: ${lnk(RX)}"
		set cmd "set xil_newLink \[create_hw_sio_link -description \{Link $i\}  \[lindex \[get_hw_sio_txs ${lnk(TX)}\] 0\] \[lindex \[get_hw_sio_rxs ${lnk(RX)}\] 0\] \]; lappend xil_newLinks \$xil_newLink"
		eval $cmd
		incr i
	}
	set cmd "set xil_newLinkGroup \[create_hw_sio_linkgroup -description \{Link Group 0\} \[get_hw_sio_links \$xil_newLinks\]\];  unset xil_newLinks"
	eval $cmd
}

proc set_link_property {links prop side val {delay 0} } {
	foreach qq $links {
		set qTX [lindex $qq 0];  set chTX [lindex $qq 1]
		set qRX [lindex $qq 2];  set chRX [lindex $qq 3]
		if {$side == "TX"}  { set chPROP $chTX }           else { set chPROP $chRX }
		if {$delay > 0}     { set dlCmd "after $delay; " } else { set dlCmd "" }

		set cmd "${dlCmd}set_property CH${chPROP}_${prop} \{$val\} \[get_hw_sio_links \{IBERT_0.$qTX.CH_$chTX.TX->IBERT_0.$qRX.CH_$chRX.RX\}\]; commit_hw_sio -non_blocking \[get_hw_sio_links \{IBERT_0.$qTX.CH_$chTX.TX->IBERT_0.$qRX.CH_$chRX.RX\}\]"
		eval $cmd
	}
}


#--------------------------------------------------------------------------------------------------------------------------------------
proc set_link_TX_Pattern {links}     {  global BXU_DATA_PATTERN; set_link_property $links "TX_PATTERN" "TX" $BXU_DATA_PATTERN }
proc set_link_RX_Pattern {links}     {  global BXU_DATA_PATTERN; set_link_property $links "RX_PATTERN" "RX" $BXU_DATA_PATTERN }
proc set_link_Loopback {links}       {  global BXU_LOOPBACK;     set_link_property $links "LOOPBACK"   "RX" $BXU_LOOPBACK }
                                    
proc set_link_TX_Reset {links}       {  global BXU_RESET_DELAY;  set_link_property $links "TX_RESET"   "TX" "1" $BXU_RESET_DELAY }
proc set_link_RX_Reset {links}       {  global BXU_RESET_DELAY;  set_link_property $links "RX_RESET"   "RX" "1" $BXU_RESET_DELAY }
proc set_link_BER_Reset {links}      {  global BXU_RESET_DELAY;  set_link_property $links "RX_PRBS_RESET.BER" "RX" "1" $BXU_RESET_DELAY ;  set_link_property $links "RX_PRBS_RESET.BER" "RX" "0" $BXU_RESET_DELAY; }

proc set_link_TX_PreCursor {links}   {  global BXU_PRE_CURSOR1;  set_link_property $links "TX_PRE_CURSOR"   "TX" $BXU_PRE_CURSOR1 }
proc set_link_TX_PreCursor2 {links}  {  global BXU_PRE_CURSOR2;  set_link_property $links "TX_PRE_CURSOR2"  "TX" $BXU_PRE_CURSOR2 }
proc set_link_TX_PreCursor3 {links}  {  global BXU_PRE_CURSOR3;  set_link_property $links "TX_PRE_CURSOR3"  "TX" $BXU_PRE_CURSOR3 }
proc set_link_TX_PostCursor {links}  {  global BXU_POST_CURSOR;  set_link_property $links "TX_POST_CURSOR"  "TX" $BXU_POST_CURSOR }
proc set_link_TX_MainCursor {links}  {  global BXU_MAIN_CURSOR;  set_link_property $links "TX_MAIN_CURSOR"  "TX" $BXU_MAIN_CURSOR }


#--------------------------------------------------------------------------------------------------------------------------------------
proc create_ibert_links {cType} {
	set CurrLinks [get_hw_sio_links];         # Check if iBERT links were created or not
	if { $CurrLinks != "" } {
		remove_hw_sio_link [get_hw_sio_links]
	}

	setup_links_$cType create_links_common
	setup_links_$cType set_link_TX_Pattern
	setup_links_$cType set_link_RX_Pattern
	setup_links_$cType set_link_Loopback
}

proc reset_ibert_links {cType} {
	setup_links_$cType set_link_TX_Reset
	setup_links_$cType set_link_RX_Reset
	setup_links_$cType set_link_BER_Reset
}

proc tuning_ibert_links {cType} {
	setup_links_$cType set_link_TX_PreCursor
	setup_links_$cType set_link_TX_PreCursor2
	setup_links_$cType set_link_TX_PreCursor3
	setup_links_$cType set_link_TX_PostCursor
	setup_links_$cType set_link_TX_MainCursor
}


create_ibert_links $connType 
if { !$BXU_CREATE_ONLY } {
	reset_ibert_links  $connType 
	tuning_ibert_links $connType 
}

#--------------------------------------------------------------------------------------------------------------------------------------
# My learning
#--------------------------------------------------------------------------------------------------------------------------------------
proc __learn_create_iBERT_links__1__ {} {
	global q205 q204 q203 q202

	for {set i 0} {$i < 4} {incr i} { puts "I inside first loop: $i" }

	set links {}
	set links2 {}
	foreach q { {Quad_202 0} {Quad_202 1} {Quad_202 2} {Quad_202 3}
	            {Quad_203 0} {Quad_203 1} {Quad_203 2} {Quad_203 3}
	            {Quad_204 0} {Quad_204 2} {Quad_205 0} {Quad_205 2}
	            {Quad_204 1} {Quad_204 3} {Quad_205 1} {Quad_205 3}
	          } {
		set qq [split $q]
		set lnk(TX) "IBERT.[lindex $qq 0].CH_[lindex $qq 1].TX"
		set lnk(RX) "IBERT.[lindex $qq 0].CH_[lindex $qq 1].RX"
		puts "LINK  ==>  TX ${lnk(TX)} => RX ${lnk(RX)}  \t\t QUAD: Q:[lindex $qq 0]  CH:[lindex $qq 1]  <== $q"
		lappend links [list ${lnk(TX)} ${lnk(RX)}]
		lappend links2 {$lnk}
	}

	puts "\nLINK by pure array/list method:"
	foreach qq $links {
		puts "LINK  TX:[lindex $qq 0]   RX:[lindex $qq 1]"
	}
	#parray $links

	puts "\nLINK by associative array method:"
	foreach lnk $links2 { puts "LINK  $lnk" };  #  ===>  can't set "lnk": variable is array
}

proc __learn_create_iBERT_links__2__ {} {
	global q205 q204 q203 q202

	set links {}
	foreach {q ch} [list Quad_202 0   Quad_202 1   Quad_202 2   Quad_202 3 \
	                     Quad_203 0   Quad_203 1   Quad_203 2   Quad_203 3 \
	                     Quad_204 0   Quad_204 2   Quad_205 0   Quad_205 2 \
	                     Quad_204 1   Quad_204 3   Quad_205 1   Quad_205 3 \
	          ] {
		set lnk(TX) "IBERT.$q.CH_$ch.TX"
		set lnk(RX) "IBERT.$q.CH_$ch.RX"
		puts "LINK  ==>  TX ${lnk(TX)} => RX ${lnk(RX)}  \t\t QUAD: Q:$q  CH:$ch"
		lappend links [list ${lnk(TX)} ${lnk(RX)}]
	}

	puts "\nLINK by NEW array/list method:"
	foreach qq $links {
		puts "LINK  TX:[lindex $qq 0]   RX:[lindex $qq 1]"
	}
	#parray $links
}

#--------------------------------------------------------------------------------------------------------------------------------------
