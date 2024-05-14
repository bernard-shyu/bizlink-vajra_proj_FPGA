#------------------------------------------------------------------------------------------------
proc setup_links_SelfLooped {f_link_method} {
	global links 
	set links {}
	foreach q { {Quad_202 0 Quad_204 0} {Quad_202 1 Quad_204 2}  {Quad_202 2 Quad_205 0} {Quad_202 3 Quad_205 2}
	            {Quad_203 0 Quad_204 1} {Quad_203 1 Quad_204 3}  {Quad_203 2 Quad_205 1} {Quad_203 3 Quad_205 3}
	            {Quad_204 0 Quad_202 0} {Quad_204 2 Quad_202 1}  {Quad_205 0 Quad_202 2} {Quad_205 2 Quad_202 3}
	            {Quad_204 1 Quad_203 0} {Quad_204 3 Quad_203 1}  {Quad_205 1 Quad_203 2} {Quad_205 3 Quad_203 3}
	          } {
		set qq [split $q]
		lappend links $qq
	}

	$f_link_method $links
}

proc setup_links_XConnected {f_link_method} {
	global links 
	set links {}
	foreach q { {Quad_202 0} {Quad_202 1} {Quad_202 2} {Quad_202 3}
	            {Quad_203 0} {Quad_203 1} {Quad_203 2} {Quad_203 3}
	            {Quad_204 0} {Quad_204 2} {Quad_205 0} {Quad_205 2}
	            {Quad_204 1} {Quad_204 3} {Quad_205 1} {Quad_205 3}
	          } {
		set qq [split "$q $q"]
		lappend links $qq
	}

	$f_link_method $links
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

proc set_link_property {links prop side val {dl 0} } {
	foreach qq $links {
		set qTX [lindex $qq 0];  set chTX [lindex $qq 1]
		set qRX [lindex $qq 2];  set chRX [lindex $qq 3]
		if {$side == "TX"}  { set chPROP $chTX }      else { set chPROP $chRX }
		if {$dl > 0 }       { set delay "after $dl; " } else { set delay "" }

		set cmd "${delay}set_property CH${chPROP}_${prop} \{$val\} \[get_hw_sio_links \{IBERT_0.$qTX.CH_$chTX.TX->IBERT_0.$qRX.CH_$chRX.RX\}\]; commit_hw_sio -non_blocking \[get_hw_sio_links \{IBERT_0.$qTX.CH_$chTX.TX->IBERT_0.$qRX.CH_$chRX.RX\}\]"
		eval $cmd
	}
}


#------------------------------------------------------------------------------------------------
# Valid property values
#------------------------------------------------------------------------------------------------
# TX/RX pattern  ['User Design', 'PRBS Disabled', 'PRBS 7', 'PRBS 9', 'PRBS 13', 'PRBS 15', 'PRBS 23', 'PRBS 31',
#                 'QPRBS 9', 'QPRBS 13', 'QPRBS 15', 'QPRBS 23', 'QPRBS 31', 'PRBSQ 7', 'PRBSQ 9', 'PRBSQ 13', 'PRBSQ 15', 'PRBSQ 23', 'PRBSQ 31', 'Configurable data pattern', 'Square wave (2 * UI)', 'Square wave (Int data width * UI)']
#
# loopback ['User Design', 'None', 'Near-End PCS', 'Far-End PCS', 'Near-End PMA', 'Far-End PMA']
#
# TX pre-Cursor ['User Design', '0 dB', '-0.20 dB', '-0.41 dB', '-0.63 dB', '-0.85 dB', '-1.07 dB', '-1.31 dB', '-1.54 dB', '-1.79 dB', '-2.04 dB', '-2.30 dB', '-2.57 dB', '-2.84 dB', '-3.13 dB', '-3.42 dB', '-3.73 dB',
#        '-4.04 dB', '-4.37 dB', '-4.71 dB', '-5.07 dB', '-5.43 dB', '-5.82 dB', '-6.22 dB', '-6.65 dB', '-7.09 dB', '-7.56 dB', '-8.06 dB', '-8.59 dB', '-9.15 dB', '-9.75 dB', '-10.39 dB', '-11.09 dB', '-11.84 dB', '-12.67 dB', '-13.58 dB', '-14.61 dB', '-15.77 dB']
#
# TX post-Cursor ['User Design', '0 dB', '-0.20 dB', '-0.41 dB', '-0.63 dB', '-0.85 dB', '-1.07 dB', '-1.31 dB', '-1.54 dB', '-1.79 dB', '-2.04 dB', '-2.30 dB', '-2.57 dB', '-2.84 dB', '-3.13 dB', '-3.42 dB', '-3.73 dB',
#        '-4.04 dB', '-4.37 dB', '-4.71 dB', '-5.07 dB', '-5.43 dB', '-5.82 dB', '-6.22 dB', '-6.65 dB', '-7.09 dB', '-7.56 dB', '-8.06 dB', '-8.59 dB', '-9.15 dB', '-9.75 dB', '-10.39 dB', '-11.09 dB', '-11.84 dB', '-12.67 dB', '-13.58 dB', '-14.61 dB', '-15.77 dB']
#------------------------------------------------------------------------------------------------
proc set_link_TX_Pattern {links}     {  set_link_property $links "TX_PATTERN" "TX" "PRBS 15" }
proc set_link_RX_Pattern {links}     {  set_link_property $links "RX_PATTERN" "RX" "PRBS 15" }

proc set_link_Loopback {links}       {  set_link_property $links "LOOPBACK"   "RX" "None" }
                                    
proc set_link_TX_Reset {links}       {  set_link_property $links "TX_RESET"   "TX" "1" 200 }
proc set_link_RX_Reset {links}       {  set_link_property $links "RX_RESET"   "RX" "1" 200 }
proc set_link_BER_Reset {links}      {  set_link_property $links "RX_PRBS_RESET.BER" "RX" "1" 200;  set_link_property $links "RX_PRBS_RESET.BER" "RX" "0" 200; }

proc set_link_TX_PreCursor {links}   {  set_link_property $links "TX_PRE_CURSOR"   "TX" "-0.20 dB" }
proc set_link_TX_PreCursor2 {links}  {  set_link_property $links "TX_PRE_CURSOR2"  "TX" "-0.20 dB" }
proc set_link_TX_PreCursor3 {links}  {  set_link_property $links "TX_PRE_CURSOR3"  "TX" "-0.20 dB" }
proc set_link_TX_PostCursor {links}  {  set_link_property $links "TX_POST_CURSOR"  "TX" "-0.20 dB" }
proc set_link_TX_MainCursor {links}  {  set_link_property $links "TX_MAIN_CURSOR"  "TX" "0.850 Vdd" }


#------------------------------------------------------------------------------------------------
proc create_ibert_links {cType} {
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

set connType "XConnected"
set connType "SelfLooped"

create_ibert_links $connType 
reset_ibert_links  $connType 


#------------------------------------------------------------------------------------------------
# My learning
#------------------------------------------------------------------------------------------------
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

#------------------------------------------------------------------------------------------------
