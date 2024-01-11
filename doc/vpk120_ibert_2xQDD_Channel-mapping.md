------------------------------------------------------------------------------
2x QSFP-DD links creation  (53 Gbps) -- External QSFP-DD Cable
------------------------------------------------------------------------------

set xil_newLinks [list]

set xil_newLink [create_hw_sio_link -description {Link 0}  [lindex [get_hw_sio_txs IBERT_0.Quad_202.CH_0.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_204.CH_0.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 1}  [lindex [get_hw_sio_txs IBERT_0.Quad_202.CH_1.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_204.CH_2.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 2}  [lindex [get_hw_sio_txs IBERT_0.Quad_202.CH_2.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_205.CH_0.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 3}  [lindex [get_hw_sio_txs IBERT_0.Quad_202.CH_3.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_205.CH_2.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 4}  [lindex [get_hw_sio_txs IBERT_0.Quad_203.CH_0.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_204.CH_1.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 5}  [lindex [get_hw_sio_txs IBERT_0.Quad_203.CH_1.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_204.CH_3.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 6}  [lindex [get_hw_sio_txs IBERT_0.Quad_203.CH_2.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_205.CH_1.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 7}  [lindex [get_hw_sio_txs IBERT_0.Quad_203.CH_3.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_205.CH_3.RX] 0] ]; lappend xil_newLinks $xil_newLink

set xil_newLink [create_hw_sio_link -description {Link 8}  [lindex [get_hw_sio_txs IBERT_0.Quad_204.CH_0.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_202.CH_0.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 9}  [lindex [get_hw_sio_txs IBERT_0.Quad_204.CH_2.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_202.CH_1.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 10} [lindex [get_hw_sio_txs IBERT_0.Quad_205.CH_0.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_202.CH_2.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 11} [lindex [get_hw_sio_txs IBERT_0.Quad_205.CH_2.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_202.CH_3.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 12} [lindex [get_hw_sio_txs IBERT_0.Quad_204.CH_1.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_203.CH_0.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 13} [lindex [get_hw_sio_txs IBERT_0.Quad_204.CH_3.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_203.CH_1.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 14} [lindex [get_hw_sio_txs IBERT_0.Quad_205.CH_1.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_203.CH_2.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 15} [lindex [get_hw_sio_txs IBERT_0.Quad_205.CH_3.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_203.CH_3.RX] 0] ]; lappend xil_newLinks $xil_newLink

set xil_newLinkGroup [create_hw_sio_linkgroup -description {Link Group 0} [get_hw_sio_links $xil_newLinks]]
unset xil_newLinks



------------------------------------------------------------------------------
2x QSFP-DD links creation  (106 Gbps) -- External QSFP-DD Cable
------------------------------------------------------------------------------

set xil_newLinks [list]

set xil_newLink [create_hw_sio_link -description {Link 0}  [lindex [get_hw_sio_txs IBERT_0.Quad_202.CH_0.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_204.CH_0.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 1}  [lindex [get_hw_sio_txs IBERT_0.Quad_202.CH_2.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_205.CH_0.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 2}  [lindex [get_hw_sio_txs IBERT_0.Quad_203.CH_0.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_204.CH_1.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 3}  [lindex [get_hw_sio_txs IBERT_0.Quad_203.CH_2.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_205.CH_1.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 4}  [lindex [get_hw_sio_txs IBERT_0.Quad_204.CH_0.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_202.CH_0.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 5}  [lindex [get_hw_sio_txs IBERT_0.Quad_204.CH_2.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_202.CH_1.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 6}  [lindex [get_hw_sio_txs IBERT_0.Quad_205.CH_0.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_202.CH_2.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 7}  [lindex [get_hw_sio_txs IBERT_0.Quad_205.CH_2.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_202.CH_3.RX] 0] ]; lappend xil_newLinks $xil_newLink


set xil_newLinkGroup [create_hw_sio_linkgroup -description {Link Group 0} [get_hw_sio_links $xil_newLinks]]
unset xil_newLinks

------------------------------------------------------------------------------



------------------------------------------------------------------------------
2x QSFP-DD links creation  (106 Gbps) -- Loopback dongle
------------------------------------------------------------------------------

set xil_newLinks [list]

set xil_newLink [create_hw_sio_link -description {Link 0}  [lindex [get_hw_sio_txs IBERT_0.Quad_202.CH_0.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_202.CH_0.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 1}  [lindex [get_hw_sio_txs IBERT_0.Quad_202.CH_2.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_202.CH_2.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 2}  [lindex [get_hw_sio_txs IBERT_0.Quad_203.CH_0.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_203.CH_0.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 3}  [lindex [get_hw_sio_txs IBERT_0.Quad_203.CH_2.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_203.CH_2.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 4}  [lindex [get_hw_sio_txs IBERT_0.Quad_204.CH_0.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_204.CH_0.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 5}  [lindex [get_hw_sio_txs IBERT_0.Quad_204.CH_2.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_204.CH_2.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 6}  [lindex [get_hw_sio_txs IBERT_0.Quad_205.CH_0.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_205.CH_0.RX] 0] ]; lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 7}  [lindex [get_hw_sio_txs IBERT_0.Quad_205.CH_2.TX] 0] [lindex  [get_hw_sio_rxs IBERT_0.Quad_205.CH_2.RX] 0] ]; lappend xil_newLinks $xil_newLink


set xil_newLinkGroup [create_hw_sio_linkgroup -description {Link Group 0} [get_hw_sio_links $xil_newLinks]]
unset xil_newLinks

------------------------------------------------------------------------------
