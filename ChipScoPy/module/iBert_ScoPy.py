#======================================================================================================================================
from chipscopy import create_session, report_versions, report_hierarchy, get_design_files
from chipscopy.api.ibert import create_yk_scans
from chipscopy.api.ibert import delete_link_groups, get_all_links, get_all_link_groups, create_links, create_link_groups
from chipscopy.api.ibert.aliases import ( PATTERN,
    EYE_SCAN_HORZ_RANGE, EYE_SCAN_VERT_RANGE, EYE_SCAN_VERT_STEP, EYE_SCAN_HORZ_STEP, EYE_SCAN_TARGET_BER,
    TX_PRE_CURSOR, TX_POST_CURSOR, TX_DIFFERENTIAL_SWING,
    RX_LOOPBACK, RX_BER, RX_STATUS, RX_LINE_RATE, RX_RECEIVED_BIT_COUNT, RX_NORMALIZED_RECEIVED_BIT_COUNT, RX_PATTERN_CHECKER_ERROR_COUNT, RX_TERMINATION_VOLTAGE, RX_COMMON_MODE
)
from more_itertools import one

from module.common      import *
#======================================================================================================================================
# ## 2 - Create a session and connect to the hw_server and cs_server
#
# The session is a container that keeps track of devices and debug cores.
# - Session is initialized and connected to server(s)
# - Versions are detected and reported to stdout
#======================================================================================================================================
def create_iBERT_session_device():
    global ibert_gtm

    # Specify locations of the running hw_server and cs_server below.
    session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
    if DBG_LEVEL_INFO <= sysconfig.DBG_LEVEL:
        report_versions(session)

    # Versal devices: [ 'xcvp1202:255211775190703847597631284360770503682:jsn-VPK120 FT4232H-872311160112A-14d00093-0',
    #                   'xcvp1202:255211775190703847597631284360770495362:jsn-VPK120 FT4232H-872311160111A-14d00093-0' ]
    BPrint(f"Versal devices: {session.devices}", level=DBG_LEVEL_NOTICE)

    # ## 3 - Program the device with PDI_FILE programming image file.
    if sysconfig.FPGA_HWID == "0": 
        device = session.devices.filter_by(family="versal").get()
    else:
        device = None
        for d in session.devices:
            context = d['cable_context']
            if len( re.findall(f"jsn.*{sysconfig.FPGA_HWID}", context) ) > 0:
                BPrint(f"Found Versal devices for {sysconfig.FPGA_HWID}: {context}", level=DBG_LEVEL_NOTICE)
                device = d
                break
            else:
                BPrint(f"Versal devices: {context}", level=DBG_LEVEL_NOTICE)

    if os.path.exists(sysconfig.PDI_FILE):
        device.program(sysconfig.PDI_FILE)
    else:
        BPrint("skipping programming", level=DBG_LEVEL_NOTICE)

    # ## 4 - Discover and setup the IBERT core. Debug core discovery initializes the chipscope server debug cores.
    # - The cs_server is initialized and ready for use
    # - The first ibert found is used

    # # Set any params as needed
    # params_to_set = {"IBERT.internal_mode": True}
    # session.set_param(params_to_set)

    BPrint(f"Discovering debug cores...", level=DBG_LEVEL_NOTICE)
    device.discover_and_setup_cores(ibert_scan=True)
    if len(device.ibert_cores) == 0:
        BPrint("No IBERT core found! Exiting...", level=DBG_LEVEL_ERR)
        exit()
    
    # ## 5 - Print the hierarchy of the IBERT core
    # We also ensure that all the quads instantiated by the ChipScoPy CED design are found by the APIs
    
    # Use the first available IBERT core from the device
    BPrint(f"--> Found {[f'{ibert.name} ({ibert.handle})' for ibert in device.ibert_cores]}\n", level=DBG_LEVEL_NOTICE)
    ibert_gtm = one(device.ibert_cores.filter_by(name="IBERT Versal GTM"))
    if len(ibert_gtm.gt_groups) == 0:
        BPrint("No GT Groups available for use! Exiting...", level=DBG_LEVEL_WARN)
        exit()

    # We also ensure that all the quads instantiated by the ChipScoPy CED design are found by the APIs
    if DBG_LEVEL_DEBUG <= sysconfig.DBG_LEVEL:
        report_hierarchy(ibert_gtm)
    BPrint(f"--> GT Groups available - {ibert_gtm.gt_groups}", level=DBG_LEVEL_NOTICE)
    BPrint(f"==> GT Groups available - {[gt_group_obj.name for gt_group_obj in ibert_gtm.gt_groups]}", level=DBG_LEVEL_DEBUG)


#--------------------------------------------------------------------------------------------------------------------------------------
def get_property_value(obj, propName, lv=DBG_LEVEL_DEBUG):
    #-------------------------------------------------------------------
    # other likely methods to get property values:
    #-------------------------------------------------------------------
    #val = obj.property.refresh(propName)[propName]
    #val = obj.property.get(propName)
    #val = obj.property.refresh(obj.property_for_alias[propName]).values()
    #val = list(obj.property.refresh(obj.property_for_alias[propName]).values())[0]
    #_, val = obj.property.get(obj.property_for_alias[propName]).popitem()
    #val   = obj.property.refresh(obj.property_for_alias[propName]).values()
    #-------------------------------------------------------------------
    alias  = obj.property_for_alias.get(propName)
    _, val = obj.property.get(alias).popitem()
    BPrint(f"iBERT object {obj} property: {propName} = {val} ", level=lv)
    return val

def set_property_value(obj, propName, val, lv=DBG_LEVEL_DEBUG):
    alias  = obj.property_for_alias.get(propName)
    props = { alias: val }
    obj.property.set(**props)
    obj.property.commit(list(props.keys()))

    if lv < DBG_LEVEL_DEBUG:
        get_property_value(obj, propName, lv)


def check_link_status(link):
    if link.status == "No link" or link.ber > 1e-5:
        lr = get_property_value( link.rx, 'Line Rate'                  )
        ls = get_property_value( link.rx, 'Pattern Checker Lock Status')
        ec = get_property_value( link.rx, 'Pattern Checker Error Count')
        cc = get_property_value( link.rx, 'Pattern Checker Cycle Count')
        return f"LinkStatus='{link.status}'   LineRate={lr}   Patten Checker: LockStatus='{ls}'  ErrorCount='{ec}'  CycleCount='{cc}'"
    else:
        return ""

#======================================================================================================================================
def create_links_common(RXs, TXs):
    global myLinks

    BPrint(f"Links_TXs: {TXs}", level=DBG_LEVEL_INFO)
    BPrint(f"Links_RXs: {RXs}", level=DBG_LEVEL_INFO)
    myLinks = create_links(txs=TXs, rxs=RXs)

    nID = 0
    if   DBG_LEVEL_TRACE <= sysconfig.DBG_LEVEL:  dbg_print = True;  dbg_print_all = True; 
    elif DBG_LEVEL_DEBUG <= sysconfig.DBG_LEVEL:  dbg_print = True;  dbg_print_all = False;
    else:                                         dbg_print = False; dbg_print_all = False; 

    #----------------------------------------------------------------------------------------------------------
    # We split TX & RX reset in 2 loops: 1st TX, 2nd RX
    # Note: the TX -> RX pair may not come in the order of the below FOR-LOOP.
    #----------------------------------------------------------------------------------------------------------
    for link in myLinks:
        link.nID = nID; nID += 1
        link.gt_name  = re.findall(".*(Quad_[0-9]*).*", str(link.rx))[0]
        link.channel  = int(re.findall(".*CH_([0-9]*).*", str(link.rx))[0])
        link.GT_Group = ibert_gtm.gt_groups.filter_by(name=link.gt_name)[0]
        link.GT_Chan  = link.GT_Group.gts[link.channel]
        BPrint(f"\n--- {link.name} :: RX={link.rx} TX={link.tx}  GT={link.gt_name} CH={link.channel} ST={link.status}  -----", level=DBG_LEVEL_INFO)

        set_property_value( link.rx, 'Pattern',  sysconfig.DPATTERN, DBG_LEVEL_INFO) 
        set_property_value( link.tx, 'Pattern',  sysconfig.DPATTERN, DBG_LEVEL_DEBUG) 
        set_property_value( link.rx, 'Loopback', "None"   , DBG_LEVEL_DEBUG)
        set_property_value( link.tx, 'Loopback', "None"   , DBG_LEVEL_DEBUG)

        link.GT_Chan.reset()
        link.tx.reset()
        #set_property_value( link.tx, 'Reset', 1, DBG_LEVEL_DEBUG)

        if link.status == "No link":     # assert link.status != "No link"
            BPrint(f"link.status:'No link'   ==> {check_link_status(link)}", level=DBG_LEVEL_WARN)

        assert link.rx.pll.locked and link.tx.pll.locked
        BPrint(f"--> RX and TX PLLs are locked for {link}. Checking for link lock...", level=DBG_LEVEL_DEBUG)

        if dbg_print:
            _, tx_pattern_report      = link.tx.property.report(link.tx.property_for_alias[PATTERN]).popitem()
            _, tx_preCursor_report    = link.tx.property.report(link.tx.property_for_alias[TX_PRE_CURSOR]).popitem()
            _, tx_postCursor_report   = link.tx.property.report(link.tx.property_for_alias[TX_POST_CURSOR]).popitem()
            #_, tx_diffSwing_report    = link.tx.property.report(link.tx.property_for_alias[TX_DIFFERENTIAL_SWING]).popitem()
            #_, rx_termVolt_report     = link.tx.property.report(link.rx.property_for_alias[RX_TERMINATION_VOLTAGE]).popitem()
            _, rx_pattern_report      = link.rx.property.report(link.rx.property_for_alias[PATTERN]).popitem()
            _, rx_loopback_report     = link.tx.property.report(link.rx.property_for_alias[RX_LOOPBACK]).popitem()

            BPrint(f"\n\n--> {link} properties:  BER={link.ber}  Count={link.bit_count}", level=DBG_LEVEL_INFO)
            BPrint(f"--> Valid values for TX pattern     - {tx_pattern_report['Valid values']}", level=DBG_LEVEL_INFO)
            BPrint(f"--> Valid values for TX pre-Cursor  - {tx_preCursor_report['Valid values']}", level=DBG_LEVEL_INFO)
            BPrint(f"--> Valid values for TX post-Cursor - {tx_postCursor_report['Valid values']}", level=DBG_LEVEL_INFO)
            #BPrint(f"--> Valid values for TX diff Swing  - {tx_diffSwing_report['Valid values']}", level=DBG_LEVEL_INFO)
            #BPrint(f"--> Valid values for RX term Volt   - {rx_termVolt_report['Valid values']}", level=DBG_LEVEL_INFO)
            BPrint(f"--> Valid values for RX pattern     - {rx_pattern_report['Valid values']}", level=DBG_LEVEL_INFO)
            BPrint(f"--> Valid values for RX loopback    - {rx_loopback_report['Valid values']}\n", level=DBG_LEVEL_INFO)

            BPrint(f"==> link.RX: {link.rx} / {link.rx.parent} RX_NAME={link.rx.name} GT_NAME={link.rx.parent.name} GT_alias={link.rx.parent.aliases}", level=DBG_LEVEL_INFO)
            BPrint(f"==> link.TX: {link.tx} / {link.tx.parent} TX_NAME={link.tx.name} GT_NAME={link.tx.parent.name} GT_alias={link.tx.parent.aliases}\n ", level=DBG_LEVEL_INFO)
            BPrint(f"GTG_alias={link.GT_Group.property_for_alias}", level=DBG_LEVEL_INFO)
            BPrint(f"GT_alias={link.GT_Chan.property_for_alias}", level=DBG_LEVEL_INFO)
            BPrint(f"TX_alias={link.tx.property_for_alias}\n", level=DBG_LEVEL_INFO)
            BPrint(f"RX_alias={link.rx.property_for_alias}\n", level=DBG_LEVEL_INFO)

            get_property_value( link.rx, 'Pattern' )
            get_property_value( link.rx, 'Loopback' )
            get_property_value( link.rx, 'Line Rate' )
            get_property_value( link.rx, 'Pattern Checker Lock Status' )
            get_property_value( link.rx, 'Pattern Checker Error Count' )
            get_property_value( link.rx, 'Pattern Checker Cycle Count' )
            get_property_value( link.tx, 'Pattern' )
            get_property_value( link.tx, 'Loopback' )

            link.generate_report()
            dbg_print = dbg_print_all

    #----------------------------------------------------------------------------------------------------------
    # This is 2nd loop for RX reset
    #----------------------------------------------------------------------------------------------------------
    for link in myLinks:
        link.rx.reset()
        #set_property_value( link.rx, 'Reset', 1, DBG_LEVEL_DEBUG)
        #set_property_value( link.rx, 'RX BER Reset', 1, DBG_LEVEL_DEBUG)


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
def create_links_SelfLooped_X8():
    global q205, q204, q203, q202

    RXs = list(); TXs = list();
    for q_TX, ch_TX, q_RX, ch_RX in ( (q202,0, q204,0), (q202,1, q204,2), (q202,2, q205,0), (q202,3, q205,2), (q203,0, q204,1), (q203,1, q204,3), (q203,2, q205,1), (q203,3, q205,3)
                                    , (q204,0, q202,0), (q204,2, q202,1), (q205,0, q202,2), (q205,2, q202,3), (q204,1, q203,0), (q204,3, q203,1), (q205,1, q203,2), (q205,3, q203,3) ):
        RXs.append(q_RX.gts[ch_RX].rx)
        TXs.append(q_TX.gts[ch_TX].tx)

    create_links_common(RXs, TXs)

#------------------------------------------
def create_links_SelfLooped_X4():
    global q205, q204, q203, q202

    RXs = list(); TXs = list();
    for q_TX, ch_TX, q_RX, ch_RX in ( (q202,0, q204,0), (q202,1, q204,2), (q202,2, q205,0), (q202,3, q205,2)
                                    , (q204,0, q202,0), (q205,0, q202,2), (q204,1, q203,0), (q205,1, q203,2) ):
        RXs.append(q_RX.gts[ch_RX].rx)
        TXs.append(q_TX.gts[ch_TX].tx)

    create_links_common(RXs, TXs)

#------------------------------------------
def create_links_XConnected_X8():
    global q202, q203, q204, q205

    RXs = list(); TXs = list();
    for q, ch in ( (q202,0), (q202,1), (q202,2), (q202,3), (q203,0), (q203,1), (q203,2), (q203,3), (q204,0), (q204,2), (q205,0), (q205,2), (q204,1), (q204,3), (q205,1), (q205,3) ):
        RXs.append(q.gts[ch].rx)
        TXs.append(q.gts[ch].tx)

    create_links_common(RXs, TXs)

#------------------------------------------
def create_links_XConnected_X4():
    global q202, q203, q204, q205

    RXs = list(); TXs = list();
    for q, ch in ( (q202,0), (q202,2), (q203,0), (q203,2), (q204,0), (q204,2), (q205,0), (q205,2) ):
        RXs.append(q.gts[ch].rx)
        TXs.append(q.gts[ch].tx)

    create_links_common(RXs, TXs)

#------------------------------------------
class FakeLink:
    def __init__(self, nID):
        self.nID = nID;
        self.name = f"FakeLink-{nID}"

def create_fake_links():
    global myLinks, all_lnkgrps, all_links

    myLinks = []
    for nID in range(global_N_links):
        link = FakeLink(nID)
        link.gt_name  = f"Quad_90{int(nID/4)}"
        link.channel  = nID % 4
        #link.GT_Group = ibert_gtm.gt_groups.filter_by(name=link.gt_name)[0]
        #link.GT_Chan  = link.GT_Group.gts[link.channel]
        link.tx = f"IBERT_0.{link.gt_name}.CH_{link.channel}.TX(TX)"
        link.rx = f"IBERT_0.{link.gt_name}.CH_{link.channel}.RX(RX)"
        link.status = f"{sysconfig.DATA_RATE} Gbps"
        myLinks.append(link)
        BPrint(f"\n--- {link.name:<12}:: RX={link.rx} TX={link.tx}  GT={link.gt_name} CH={link.channel} ST={link.status}  -----", level=DBG_LEVEL_INFO)

#------------------------------------------
def create_LinkGroups():
    global q205, q204, q203, q202
    global myLinks, all_lnkgrps, all_links

    q205 = one(ibert_gtm.gt_groups.filter_by(name="Quad_205"))
    q204 = one(ibert_gtm.gt_groups.filter_by(name="Quad_204"))
    q203 = one(ibert_gtm.gt_groups.filter_by(name="Quad_203"))
    q202 = one(ibert_gtm.gt_groups.filter_by(name="Quad_202"))

    match sysconfig.CONN_TYPE:
        case "S4" | "SLoop_x4": create_links_SelfLooped_X4()
        case "S8" | "SLoop_x8": create_links_SelfLooped_X8()
        case "X4" | "XConn_x4": create_links_XConnected_X4()
        case "X8" | "XConn_x8": create_links_XConnected_X8()
        case _:                 raise ValueError(f"Not valid Connection Type: {sysconfig.CONN_TYPE}\n")

    # These below RESET aren't necessarily required
    """
    q202.reset()
    q203.reset()
    q204.reset()
    q205.reset()
    """

    all_lnkgrps = get_all_link_groups()
    all_links   = get_all_links()
    BPrint(f"\n--> All Link Groups available - {all_lnkgrps}", level=DBG_LEVEL_DEBUG)
    BPrint(f"\n--> All Links available - {all_links}", level=DBG_LEVEL_DEBUG)


#======================================================================================================================================
def init_iBERT_engine(syscfg, N_links):
    global sysconfig, global_N_links, myLinks

    sysconfig = syscfg
    global_N_links = N_links

    if sysconfig.SIMULATE:
        create_fake_links()
    else:
        create_iBERT_session_device()
        bprint_loading_time("Xilinx iBERT-core created")

        create_LinkGroups()
        bprint_loading_time("Xilinx Link-Groups created")

    return myLinks

