#!/usr/bin/env python3
#--------------------------------------------------------------------------------------------------------------------------------------
# # IBERT yk scan example
# ## Description
# This example shows how to interact with the IBERT (Integrated Bit Error Ratio Tester) debug core service via ChipScoPy APIs.
# - Program the ChipScoPy CED design onto the XCVP1202 device on a VPK120 board
# - Verify that the expected IBERT quads are instantiated by the design
# - Run and plot YK scans
#
# ## Requirements
# - Local or remote Xilinx Versal board, VPK120 or VHK158 (only)
# - Xilinx hw_server 2023.2 installed and running
# - Xilinx cs_server 2023.2 installed and running
# - Python 3.8 or greater installed
# - ChipScoPy 2023.2 installed
# - Jupyter notebook support installed - Please do so, using the command `pip install chipscopy[jupyter]`
# - Plotting support installed - Please do so, using the command `pip install chipscopy[core-addons]`

#--------------------------------------------------------------------------------------------------------------------------------------
# ## 1 - Initialization: Imports & environments
#--------------------------------------------------------------------------------------------------------------------------------------
from chipscopy import create_session, report_versions, report_hierarchy, get_design_files
from chipscopy.api.ibert import create_yk_scans
from chipscopy.api.ibert import delete_link_groups, get_all_links, get_all_link_groups, create_links, create_link_groups
from chipscopy.api.ibert.aliases import ( PATTERN,
    EYE_SCAN_HORZ_RANGE, EYE_SCAN_VERT_RANGE, EYE_SCAN_VERT_STEP, EYE_SCAN_HORZ_STEP, EYE_SCAN_TARGET_BER,
    TX_PRE_CURSOR, TX_POST_CURSOR, TX_DIFFERENTIAL_SWING,
    RX_LOOPBACK, RX_BER, RX_STATUS, RX_LINE_RATE, RX_RECEIVED_BIT_COUNT, RX_NORMALIZED_RECEIVED_BIT_COUNT, RX_PATTERN_CHECKER_ERROR_COUNT, RX_TERMINATION_VOLTAGE, RX_COMMON_MODE
)
from more_itertools import one

#------------------------------------------
from PyQt5 import QtWidgets, QtCore, QtGui
import numpy as np
import pandas as pd
import argparse, math, re
import os, sys, time, datetime, threading

import matplotlib
matplotlib.use("Qt5Agg")      # 表示使用 Qt5
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar

#--------------------------------------------------------------------------------------------------------------------------------------
# Print levels (default: info)
#--------------------------------
DBG_LEVEL_WIP    = -1   # working in progress, LEVEL to be defined later
DBG_LEVEL_ERR    = 0
DBG_LEVEL_WARN   = 1
DBG_LEVEL_NOTICE = 2
DBG_LEVEL_INFO   = 3
DBG_LEVEL_DEBUG  = 4
DBG_LEVEL_TRACE  = 5
#--------------------------------
def BPrint(*args, level=DBG_LEVEL_INFO):
    if level <= sysconfig.DBG_LEVEL:
        print(*args)

app_start_time = datetime.datetime.now()
APP_TITLE = "ChipScoPy APP fro BizLink iBERT HPC-cables testing"

last_check = app_start_time
def bprint_loading_time(msg, level=DBG_LEVEL_NOTICE):
    global last_check
    now = datetime.datetime.now()
    elapsed1 = (now - app_start_time).seconds
    elapsed2 = (now - last_check).seconds
    last_check = now
    BPrint("\n----------------------------------------------------------------------------------------------------------------------------------------------------------------\n" + \
       f"ChipScoPy loading time  APP: {app_start_time}   NOW: {now}   ELAPSED:{elapsed1:>4} / {elapsed2:<4}\t" + \
       "\n----------------------------------------------------------------------------------------------------------------------------------------------------------------\n\n", level=level)

#--------------------------------------------------------------------------------------------------------------------------------------
# Configuration variables: 1) external EXPORT Environment variables, 2) command-line arguments (higher priority)
#--------------------------------------------------------------------------------------------------------------------------------------
ENV_HELP="""
EXPORT Environment variables:
----->
export ip="10.20.2.146";     export CS_SERVER_URL="TCP:$ip:3042" HW_SERVER_URL="TCP:$ip:3121";
export HW_PLATFORM="vpk120"; export VERSAL_HWID="112A"
export WIN_RESOLUTION="3840x2160";
export PDI_FILE="./PDI_Files/VPK120_iBERT_2xQDD_56G.pdi";      export CSV_PATH="./YK_CSV_Files";
export SHOW_FIG_TITLE=True;  export WIN_TITLE_FONT=8;
export MAX_SLICES=20;        export YKSCAN_SLICER_SIZE=200;    export HIST_BINS=40;      
export CONN_TYPE=XConn_x8;   export DATA_PATTERN="PRBS 9";
export QUAD_NAME="Quad_202"; export QUAD_CHAN=2;
export APP_DBG_LEVEL=5;
"""

CSV_PATH     =     os.getenv("CSV_PATH", "./YK_CSV_Files")
QUAD_NAME    =     os.getenv("QUAD_NAME", "Quad_202")
QUAD_CHAN    = int(os.getenv("QUAD_CHAN", "0"))

CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")

# specify hw and if programming is desired
HW_PLATFORM = os.getenv("HW_PLATFORM", "vpk120")
SHOW_FIG_TITLE = os.getenv("SHOW_FIG_TITLE", 'False').lower() in ('true', '1', 't')
WIN_TITLE_FONT = os.getenv("WIN_TITLE_FONT", '8')

MAX_SLICES    = int(os.getenv("MAX_SLICES", "12"))
HIST_BINS     = int(os.getenv("HIST_BINS",  "100"))
VIVADO_SLICES = 4    # Vivado always shows 8000 samples
YKSCAN_SLICER_SIZE = int(os.getenv("YKSCAN_SLICER_SIZE",  "2000"))   # for simulation purpose, we may choose smaller value

#--------------------------------------------------------------------------------------------------------------------------------------
# https://docs.python.org/3/library/argparse.html,  https://docs.python.org/3/howto/argparse.html
# https://stackoverflow.com/questions/20063/whats-the-best-way-to-parse-command-line-arguments
#--------------------------------------------------------------------------------------------------------------------------------------
parser = argparse.ArgumentParser(description=f"{APP_TITLE} by Bernard Shyu", epilog=ENV_HELP)

# The get_design_files() function tries to find the PDI and LTX files. In non-standard
# configurations, you can put the path for PROGRAMMING_FILE and PROBES_FILE below.
# design_files = get_design_files(f"{HW_PLATFORM}/production/chipscopy_ced")
# PDI_FILE = design_files.programming_file
PDI_FILE = os.getenv("PDI_FILE", "")
parser.add_argument('--PDI_FILE', default=PDI_FILE, metavar='filename', help='FPGA image file (*.pdi) Ex. PDI_Files/VPK120_iBERT_2xQDD_56G.pdi')

VERSAL_HWID = os.getenv("VERSAL_HWID", "0")     # default: NOT specified, auto-detection
parser.add_argument('--HWID', default=VERSAL_HWID, metavar='hwID', help='VPK120 HWID: S/N (0 or 111A or 112A)')

CONN_TYPE = os.getenv("CONN_TYPE", "SLoop_x8")
parser.add_argument('--CONN_TYPE', default=CONN_TYPE, metavar='type', help='Connection Type: SLoop_x4 | SLoop_x8 | XConn_x4 | XConn_x8.  Or shorter: S4 | S8 | X4 | X8.  Default: SLoop_x8')

DATA_PATTERN = os.getenv("DATA_PATTERN", "PRBS 31")
parser.add_argument('--PATTERN', default=DATA_PATTERN, metavar='pattern', help='Bits data pattern: PRBS 7 / PRBS 9 / ...')

APP_DBG_LEVEL = int(os.getenv("APP_DBG_LEVEL", "3"))
parser.add_argument('--DBG_LEVEL', default=APP_DBG_LEVEL, metavar='level', help='debug level (ERR=0 WARN=1 NOTICE=2 INFO=3 DEBUG=4 TRACE=5, default=3)', type=int)

WIN_RESOLUTION = os.getenv("WIN_RESOLUTION", "3200x1800")    # 3200x1800 /  3840x2160 / 900x800
parser.add_argument('--RESOLUTION', default=WIN_RESOLUTION, metavar='resol', help='App Window Resolution: 3200x1800 /  3840x2160 / 900x800')

parser.add_argument('--SIMULATE', action='store_true', help='Whether to SIMULATE by random data or by real iBERT data source. default: False')

sysconfig = parser.parse_args()

#--------------------------------------------------------------------------------------------------------------------------------------
def calculate_plotFigure_size(res_X, res_Y):
    MWIN_OVERHEAD  = 60    # overhead for Main-Windows, including Windows Title, borders, Tool-bar area
    TB_CELL_HEIGHT = 30    # height of each table cell
    MATPLOTLIB_DPI = 100   # density (or dots) per inch, default: 100.0
    fig_size_x     = (res_X - 10) / global_grid_cols / MATPLOTLIB_DPI
    fig_size_y     = (res_Y - MWIN_OVERHEAD - TB_CELL_HEIGHT * (global_N_links + 1)) / global_grid_rows / MATPLOTLIB_DPI
    return (fig_size_x, fig_size_y)

TEST_DATA_RATE = int(re.findall(".*VPK120_iBERT_.*_([0-9]+)G.pdi", sysconfig.PDI_FILE)[0])

match sysconfig.CONN_TYPE:
    case "S4" | "SLoop_x4" | "X4" | "XConn_x4": global_N_links = 8;   global_grid_rows = 2;  global_grid_cols = 4;
    case "S8" | "SLoop_x8" | "X8" | "XConn_x8": global_N_links = 16;  global_grid_rows = 2;  global_grid_cols = 8;
    case _:   raise ValueError(f"Not valid Connection Type: {sysconfig.CONN_TYPE}\n")

PLOT_RESOL_X   = int(re.findall("([0-9]+)x[0-9]+", sysconfig.RESOLUTION)[0])
PLOT_RESOL_Y   = int(re.findall("[0-9]+x([0-9]+)", sysconfig.RESOLUTION)[0])
FIG_SIZE_X, FIG_SIZE_Y = calculate_plotFigure_size( PLOT_RESOL_X, PLOT_RESOL_Y )

BPrint(f"\n{APP_TITLE } --- {app_start_time}\n", level=DBG_LEVEL_NOTICE)
BPrint(f"Servers URL: {CS_URL} {HW_URL}\t\tFPGA_HW: {HW_PLATFORM}  HWID: {sysconfig.HWID}\tPDI: '{sysconfig.PDI_FILE}' \n", level=DBG_LEVEL_NOTICE)
BPrint(f"SYSCONFIG: dbg={sysconfig.DBG_LEVEL} cTyp={sysconfig.CONN_TYPE} pattern={sysconfig.PATTERN} RATE={TEST_DATA_RATE}G " +
       f"SIM={sysconfig.SIMULATE} resolution={sysconfig.RESOLUTION} FIG={FIG_SIZE_X},{FIG_SIZE_Y} \n", level=DBG_LEVEL_NOTICE)

assert FIG_SIZE_Y > 0

#--------------------------------------------------------------------------------------------------------------------------------------
# ## 2 - Create a session and connect to the hw_server and cs_server
#
# The session is a container that keeps track of devices and debug cores.
# - Session is initialized and connected to server(s)
# - Versions are detected and reported to stdout
#--------------------------------------------------------------------------------------------------------------------------------------
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
    if sysconfig.HWID == "0": 
        device = session.devices.filter_by(family="versal").get()
    else:
        device = None
        for d in session.devices:
            context = d['cable_context']
            if len( re.findall(f"jsn.*{sysconfig.HWID}", context) ) > 0:
                BPrint(f"Found Versal devices for {sysconfig.HWID}: {context}", level=DBG_LEVEL_NOTICE)
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


#--------------------------------------------------------------------------------------------------------------------------------------
# Data source classes: iBERT-Link data, YK-Scan data, radom number simulattion
#-------------------------------------------------------------------------
class BaseDataSource(QtCore.QObject):
    WATCHDOG_INTERVAL = 10 * 1000

    def __init__(self, canvas, name):
        super().__init__()
        self.dsrcName = name
        self.canvas = canvas

        self.snr  = 0
        self.ber  = 0
        self.eye  = 0
        self.hist = ""

        #------------------------------------------------------------------------------
        # Initialize circular buffer
        self.YKScan_slicer_buf = np.zeros((0, YKSCAN_SLICER_SIZE))  # Assuming 2D data (X, Y), X-dim will grow to MAX_SLICES
        self.YK_is_started = False

        self.ASYN_samples_count = 0    # YK-Scan samples
        self.SYNC_samples_count = 0    # Channel-Link samples

        self.DBG_TRACE_ASYN_COUNT = 0        # set non-ZERO for tracing data traffic for initial counts
        self.DBG_TRACE_SYNC_COUNT = 0        # set non-ZERO for tracing data traffic for initial counts

        #------------------------------------------------------------------------------
        self.fig = plt.figure(FigureClass=MyYKFigure, num=self.dsrcName, layout='constrained', edgecolor='black', linewidth=3, figsize=[FIG_SIZE_X, FIG_SIZE_Y])   # facecolor='yellow', dpi=100
        self.fig.init_YK_axes(self.dsrcName)

        #------------------------------------------------------------------------------
        self.fsm_state   = 0
        self.fsm_running = True

        # Setup a timer to trigger the redraw by calling update_plot.
        self.watchdog_timer = QtCore.QTimer()
        self.watchdog_timer.setInterval(self.WATCHDOG_INTERVAL)
        self.watchdog_timer.timeout.connect(self.fsmFunc_watchdog)
        self.watchdog_timer.start()


    def BPrt_HEAD_COMMON(self):
        # return "{}: #{:<4d}/{:<4d}\t ".format(self.dsrcName, self.ASYN_samples_count, self.SYNC_samples_count)
        return "{}: #{:<4d}/{:<4d} T:{:<4d}\t".format(self.dsrcName, self.ASYN_samples_count, self.SYNC_samples_count, (datetime.datetime.now() - app_start_time).seconds)

    def BPrt_HEAD_WATER(self):
        return self.BPrt_HEAD_COMMON() + f"WATER:{self.YKScan_slicer_buf.shape[0]:>2}/{str(self.YK_is_started):<5} FSM:{self.fsm_state}\t"

    def __refresh_common_data__(self):
        self.SYNC_samples_count +=1
        self.now         = datetime.datetime.now()
        self.elapsed     = (self.now - app_start_time).seconds

    @QtCore.pyqtSlot()
    def fsmFunc_worker_thread(self):
        while self.fsm_running:
            match self.fsm_state:
                case self.fsm_state if self.fsm_state < 10:  # reset && initial fetch
                    lvl = DBG_LEVEL_INFO
                    if not self.fsmFunc_reset(): 
                        self.fsm_state += 1
                    else:
                        self.fsm_state = 10

                case 10: # main state, main-loop for polling, sporadically fetching or stopping
                    lvl = DBG_LEVEL_TRACE
                    self.fsmFunc_refresh_plots()

                #case 2: # inital stop
                #case 3: # sporadically fetching
                #case 4: # sporadically stop 
                case _: raise ValueError(f"Not valid BaseDataSource.fsm_state : {self.fsm_state}\n")

            BPrint(self.BPrt_HEAD_WATER() + f"FSM-WorkerThread.{QtCore.QThread.currentThread()} / {threading.current_thread().name}", level=lvl)
            time.sleep(2)

    #----------------------------------------------------------------------------------
    #def start_data(self):             pass    # Abstract method: to start data-source engine, like YK.start()
    #def stop_data(self):              pass    # Abstract method: to stop data-source engine, like YK.stop()
    #def async_update_data(self):      pass    # Abstract method: to update data from ource engine, asynchronously by call-back
    def fsmFunc_watchdog(self):        pass    # Abstract method: long  timer polling function
    def fsmFunc_refresh_plots(self):   pass    # Abstract method: FSM function, polling periodically
    def fsmFunc_reset(self):           pass    # Abstract method: FSM function, resetting initially
    #----------------------------------------------------------------------------------

    def finish_object(self):
        self.watchdog_timer.stop()


class Base_YKScanLink(BaseDataSource):
    s_update_YKScan = QtCore.pyqtSignal(int)

    def __init__(self, canvas, link):
        super().__init__(canvas, f"YK-{link.gt_name}_CH{link.channel}")
        self.link = link
        link.myLink = self

        #------------------------------------------------------------------------------
        self.s_update_YKScan.connect(self.asynFunc_update_YKScan, QtCore.Qt.QueuedConnection)
        self.YKScan_slicer_viewPointer = 0
        self.YKScan_slicer_viewBuffer  = np.zeros(MAX_SLICES * YKSCAN_SLICER_SIZE)

    def bprint_link(self):
        return self.BPrt_HEAD_COMMON() + f"SELF={self} LINK={str(self.link):<8}  STATUS={self.status:<12} BER={self.ber:<15} RATE={self.line_rate:<12} BITS={self.bit_count:<18} ERR={self.error_count}"

    def sync_update_LinkData(self):  pass    # Abstract method: to update data from ource engine, asynchronously by call-back

    ## FSM-RESET state, fetching YKScan for 4 slices (VIVADO_SLICES), and filling up to 12 (MAX_SLICES)
    def fill_up_slicer_buf(self):
        while self.ASYN_samples_count < VIVADO_SLICES: # MAX_SLICES:
            self.sync_refresh_plotBER()
            time.sleep(2)

        for i in range(VIVADO_SLICES, MAX_SLICES):
            self.YKScan_slicer_buf = np.append(self.YKScan_slicer_buf, [self.YKScan_slicer_buf[i % VIVADO_SLICES]], axis=0)

    def sync_refresh_plotBER(self):
        self.sync_update_LinkData()
        self.fig.update_yk_ber(self)
        self.canvas.update_table()
        lvl = DBG_LEVEL_INFO  if self.SYNC_samples_count < self.DBG_TRACE_SYNC_COUNT  else DBG_LEVEL_TRACE
        BPrint(self.bprint_link(), level=lvl)

    def sync_refresh_plotYK(self):
        # rotate VIVADO_SLICES(=4) slicers of view-buffer from self.YKScan_slicer_buf[MAX_SLICES(=12)]
        v = self.YKScan_slicer_viewPointer
        self.YKScan_slicer_viewBuffer = self.YKScan_slicer_buf[v]
        for i in range(1,VIVADO_SLICES):
            self.YKScan_slicer_viewBuffer = np.concatenate(( self.YKScan_slicer_viewBuffer, self.YKScan_slicer_buf[v + i] ))
        self.YKScan_slicer_viewPointer += VIVADO_SLICES
        if  self.YKScan_slicer_viewPointer >= MAX_SLICES:
            self.YKScan_slicer_viewPointer = 0;

        # refresh the matplotlib figures
        self.fig.update_yk_scan(self)

        lvl = DBG_LEVEL_INFO  if self.ASYN_samples_count < self.DBG_TRACE_ASYN_COUNT  else DBG_LEVEL_TRACE
        BPrint(self.BPrt_HEAD_WATER() + f"refresh_plotYK.{v}.{self.YKScan_slicer_viewPointer}: BER: {self.ber:.2e}  SNR: {self.snr:6.2f}  WATER:{self.YKScan_slicer_buf.shape[0]} Elapsed:{self.elapsed}", level=lvl)

    def fsmFunc_refresh_plots(self):
        self.sync_refresh_plotBER()
        self.sync_refresh_plotYK()
        self.canvas.draw()    # self.canvas.draw_idle()

    #  ----------- 00 -------------------------------------------------------------------- 100 ---------
    #  peaks:                   Peak0                                Peak1
    #  valeys:                                   Valey0
    #---------------------------------------------------------------------------------------------------
    def find_NRZ_peaks_and_valleys(self, hist, bins):
        half_BINS = int(HIST_BINS / 2)

        #-----------------------------------------------------------------------------------------------
        # find the highest peak in [0:50], Peak0
        Peak0 = hist[0:half_BINS].max()
        i_P0  = hist[0:half_BINS].argmax()

        #-----------------------------------------------------------------------------------------------
        # find the highest peak in [50:100], Peak1
        Peak1 = hist[half_BINS:HIST_BINS].max()
        i_P1  = hist[half_BINS:HIST_BINS].argmax() + half_BINS

        #---------------------------------------------------------------------------------------------------
        # find the valeys
        Valey0 = hist[i_P0:i_P1].min();
        i_V0   = hist[i_P0:i_P1].argmin() + i_P0

        #---------------------------------------------------------------------------------------------------
        # self.hist: Histogram statistics
        # self.eye : EYE opening. i.e average of Peaks distance
        #---------------------------------------------------------------------------------------------------
        self.hist = f"Peaks: ({i_P0}={Peak0:n}, {i_P1}={Peak1:n})   Valeys: {Valey0:n}"
        self.eye  = i_P1 - i_P0


    #  ----------- 00 -------------------------------- 50 -------------------------------- 100 ---------
    #  peaks:              Peak0           Peak1                  Peak2           Peak3
    #  valeys:                    Valey0             Valey1               Valey2
    #---------------------------------------------------------------------------------------------------
    def find_PAM4_peaks_and_valleys(self, hist, bins):
        HILL_MIN_WIDTH = 3   # The hill peak should have sufficient width
        half_BINS = int(HIST_BINS / 2)

        #-----------------------------------------------------------------------------------------------
        # find the highest peak in [0:50], it can be Peak0 or Peak1
        p  = hist[0:half_BINS].max()
        i  = hist[0:half_BINS].argmax()
        # find the 2nd peak in [0:50] to the LEFT or RIGHT side
        L = hist[0:i-HILL_MIN_WIDTH].max()
        R = hist[i+HILL_MIN_WIDTH:half_BINS].max()
        if L < R:
            # 2nd peak is RIGHT side
            Peak0 = p;  i_P0 = i
            Peak1 = R;  i_P1 = hist[i+HILL_MIN_WIDTH:half_BINS].argmax() + i + HILL_MIN_WIDTH
        else:
            # 2nd peak is LEFT  side
            Peak1 = p;  i_P1 = i
            Peak0 = L;  i_P0 = hist[0:i-HILL_MIN_WIDTH].argmax()

        #-----------------------------------------------------------------------------------------------
        # find the highest peak in [50:100], it can be Peak2 or Peak3
        P  = hist[half_BINS:HIST_BINS].max()
        i  = hist[half_BINS:HIST_BINS].argmax() + half_BINS
        # find the 2nd peak in [50:100] to the LEFT or RIGHT side
        L = hist[half_BINS:i-HILL_MIN_WIDTH].max()
        R = hist[i+HILL_MIN_WIDTH:HIST_BINS].max()
        if L < R:
            # 2nd peak is RIGHT side
            Peak2 = p;  i_P2 = i
            Peak3 = R;  i_P3 = hist[i+HILL_MIN_WIDTH:HIST_BINS].argmax() + i + HILL_MIN_WIDTH
        else:
            # 2nd peak is LEFT  side
            Peak3 = p;  i_P3 = i
            Peak2 = L;  i_P2 = hist[half_BINS:i-HILL_MIN_WIDTH].argmax() + half_BINS

        #-----------------------------------------------------------------------------------------------
        # find the valeys
        Valey0 = hist[i_P0:i_P1].min();   i_V0 = hist[i_P0:i_P1].argmin() + i_P0
        Valey1 = hist[i_P1:i_P2].min();   i_V1 = hist[i_P1:i_P2].argmin() + i_P1
        Valey2 = hist[i_P2:i_P3].min();   i_V2 = hist[i_P2:i_P3].argmin() + i_P2

        """
        # find the standard-deviation
        stdvar0 = np.std(hist[0:i_V0])
        stdvar1 = np.std(hist[i_V0:i_V1])
        stdvar2 = np.std(hist[i_V1:i_V2])
        stdvar3 = np.std(hist[i_V2:HIST_BINS])
        BPrint(self.BPrt_HEAD_WATER() + f"std:   {stdvar0:9.3f}    {stdvar1:9.3f}    {stdvar2:9.3f}    {stdvar3:9.3f} ", level = DBG_LEVEL_TRACE)
        """

        #-----------------------------------------------------------------------------------------------
        # self.hist: Histogram statistics
        # self.eye : EYE opening. i.e average of Peaks distance
        #-----------------------------------------------------------------------------------------------
        #self.hist = f"Peaks: ({i_P0}={Peak0}, {i_P1}={Peak1}, {i_P2}={Peak2}, {i_P3}={Peak3})   Valeys: ({i_V0}={Valey0}, {i_V1}={Valey1}, {i_V2}={Valey2})"
        self.hist = f"Peaks: ({i_P0}={Peak0:n}, {i_P1}={Peak1:n}, {i_P2}={Peak2:n}, {i_P3}={Peak3:n})   Valeys: ({Valey0:n}, {Valey1:n}, {Valey2:n})"
        self.eye  = ((i_P3 - i_P2) + (i_P2 - i_P1) + (i_P1 - i_P0)) / 3

    def find_peaks_and_valleys(self, hist, bins):
        if len(hist) != HIST_BINS:
            BPrint(self.BPrt_HEAD_WATER() + f"find Histogram-Peaks: {len(hist)} / {len(bins)} ", level = DBG_LEVEL_INFO)
            return
        if TEST_DATA_RATE > 50:
            self.find_PAM4_peaks_and_valleys(hist, bins)
        else:
            self.find_NRZ_peaks_and_valleys(hist, bins)
        BPrint(self.BPrt_HEAD_WATER() + f"Histogram-EYE: {self.eye:.3f}  statistic: {self.hist}", level = DBG_LEVEL_TRACE)


class Fake_YKScanLink(Base_YKScanLink):
    #s_update_YKScan = QtCore.pyqtSignal(int)
    WATCHDOG_INTERVAL = 5 * 1000

    def __init__(self, canvas, link):
        super().__init__(canvas, link)
        np.random.seed(42)
        self.peaks_rand_mode   = True
        self.std_dev = 1.5
        self.wdog_i = 0

    #----------------------------------------------------------------------------------
    def fsmFunc_reset(self):
        BPrint(self.BPrt_HEAD_WATER() + f"fsmFunc_reset", level=DBG_LEVEL_INFO)
        match self.fsm_state:
            case 0:
                self.bits_increment = 2 * TEST_DATA_RATE * 1.0E9    # incremented by every 2 seconds
                self.bit_count   = "0"
                self.bit_count_N = 0
                self.error_count = 0
                self.status      = self.link.status
                self.line_rate   = self.link.status
                self.comments    = ""
                return False
            case 1:
                self.sync_refresh_plotBER()
                return False
            case 2:
                self.fill_up_slicer_buf()
                return True

    def fsmFunc_watchdog(self):
        if self.fsm_state < 10:
            # RESET state, replenish the data as soon as possible
            self.sync_update_YKScanData()
            self.sync_update_YKScanData()
        else:
            # Normal state, replenish the data at much slower WATCHDOG_INTERVAL
            if self.wdog_i % 8 == 0: self.sync_update_YKScanData()
            self.wdog_i += 1

    def asynFunc_update_YKScan(self, waterlevel):
        pass

    #----------------------------------------------------------------------------------
    def sync_update_YKScanData(self):
        self.ASYN_samples_count +=1      #  ==> len(obj.scan_data) - 1
        if self.peaks_rand_mode:
            # Each peak will have separate randomness
            peak_positions = [20, 40, 60, 80]
            for i in range(4): peak_positions[i] +=  4*(np.random.rand() - 0.5)          #  Adding randomness to PEAK position by +2/-2
        else:
            # All 4 peaks will have the same randomness
            peak_positions = np.array([20, 40, 60, 80]) + 4*(np.random.rand() - 0.5)     #  Adding randomness to PEAK position by +2/-2

        slice_buf = []
        #for _ in range(0, YKSCAN_SLICER_SIZE, 10):
        for _ in range(YKSCAN_SLICER_SIZE):
            peak_pos = peak_positions[np.random.randint(4)]  # Randomly select a peak position
            #slice_data = np.random.normal(loc=peak_pos, scale=self.std_dev, size=10)
            slice_data = np.random.normal(loc=peak_pos, scale=self.std_dev)
            slice_buf.append(slice_data)

        self.YKScan_slicer_buf = np.append(self.YKScan_slicer_buf, [slice_buf], axis=0)          # append new data
        waterlevel = self.YKScan_slicer_buf.shape[0]
        if waterlevel > MAX_SLICES:
            self.YKScan_slicer_buf = np.delete(self.YKScan_slicer_buf, 0, axis=0)                                     # remove oldest slice data
            BPrint(self.BPrt_HEAD_WATER() + f"buffer FULL", level=DBG_LEVEL_INFO)
        self.s_update_YKScan.emit(waterlevel)    # ==> invoke asynFunc_update_YKScan() for PyQT's thread context

        """
        now = datetime.datetime.now() 
        print(f"\n\n{now} {len(self.YKScan_slicer_buf)}\n")
        print(self.YKScan_slicer_buf[0:YKSCAN_SLICER_SIZE:20])
        """

    #----------------------------------------------------------------------------------
    def sync_update_LinkData(self):
        self.__refresh_common_data__()
        self.bit_count_N += self.bits_increment
        self.bit_count    = f"{self.bit_count_N:.3e}"
        self.error_count += np.random.randint(100)                 # random int between 0 and 100
        self.ber          = self.error_count / self.bit_count_N;   #  np.random.random() / 1000000   # BER by random number simulation
        self.snr          = 18 + np.random.rand() * 4              # random float between 0 and 4


# The class correlates to chipscopy.api.ibert.link.Link
class IBert_YKScanLink(Base_YKScanLink):
    WATCHDOG_INTERVAL = 120 * 1000

    def __init__(self, canvas, link):
        super().__init__(canvas, link)

        #------------------------------------------------------------------------------
        self.YK   = create_yk_scans(target_objs=link.rx)[0]                # returns: chipscopy.api.ibert.yk_scan.YKScan object
        self.YK.updates_callback = lambda obj: self.asynCB_update_YKScanData(obj)
        BPrint(f"{self.dsrcName}:: TX={link.tx}  RX={link.rx}  LINK={str(link):<8}  YK={self.YK.name:<10}  RX.yk_scan={link.rx.yk_scan}", level=DBG_LEVEL_INFO)

        #------------------------------------------------------------------------------
        # Pandas table to keep data for CSV file
        self.pd_data = pd.DataFrame(columns=["Samples", "Elapsed Time", "Status", "Line Rate", "Bits Count", "Errors Count", "BER", "SNR", "EYE-Opening", "Histogram", "comments"])

    #----------------------------------------------------------------------------------
    def fsmFunc_reset(self):
        BPrint(self.BPrt_HEAD_WATER() + f"fsmFunc_reset", level=DBG_LEVEL_INFO)
        match self.fsm_state:
            case 0:
                self.link.tx.reset(); 
                self.link.rx.reset();
                set_property_value( self.link.rx, 'RX BER Reset', 1, DBG_LEVEL_INFO);
                return False
            case 1:
                self.sync_refresh_plotBER()
                time.sleep(self.link.nID * 1)      # interleaving to prevent overwhelming of data traffic from simultaneous YKScan on all Quad/CH
                self.__YKEngine_manage__(True, 0)  # launch YK.start(), to start the YKScan engine
                return False
            case 2:
                self.fill_up_slicer_buf()
                return True

    def fsmFunc_watchdog(self):
        self.__YKEngine_manage__(True, 1)  # relaunch YK.start(), likely it is stopped by throttling of flow control

    #----------------------------------------------------------------------------------
    def __YKEngine_manage__(self, to_start_YK, _where_):
        try:
            BPrint(self.BPrt_HEAD_WATER() + f"__YKEngine_manage__({_where_}, {to_start_YK})", level=DBG_LEVEL_TRACE)
            if to_start_YK:
                if not self.YK_is_started:
                    BPrint(self.BPrt_HEAD_WATER() + f"__YKEngine_manage__({_where_}) do YK.start()", level=DBG_LEVEL_INFO)
                    self.YK.start()
                self.YK_is_started = True
            else:
                if self.YK_is_started:
                    BPrint(self.BPrt_HEAD_WATER() + f"__YKEngine_manage__({_where_}) do YK.stop()", level=DBG_LEVEL_INFO)
                    self.YK.stop()
                self.YK_is_started = False
        except Exception as e:
            print(f"YKScan-{self.dsrcName} Exception: {str(e)}")

    def asynFunc_update_YKScan(self, waterlevel):
        # throttle the YKScan engine in advance to prevent overflow of the slicer buffer
        if waterlevel > VIVADO_SLICES:
            self.__YKEngine_manage__(False, 10)  # launch YK.stop(), to stop the YKScan engine from running.

    # ## 6 - Define YK Scan Update Method
    #----------------------------------------------------------------------------------
    def asynCB_update_YKScanData(self, obj):
        self.ASYN_samples_count +=1      #  ==> len(obj.scan_data) - 1
        self.snr = obj.scan_data[-1].snr

        #------------------------------------------------------------------------------
        # assert YKSCAN_SLICER_SIZE == len(obj.scan_data[-1].slicer)
        if YKSCAN_SLICER_SIZE != len(obj.scan_data[-1].slicer):
            BPrint(self.BPrt_HEAD_COMMON() + f"ERROR slicer: {len(obj.scan_data[-1].slicer)}", level=DBG_LEVEL_ERR)
            if len(obj.scan_data[-1].slicer) != 0:
                obj.scan_data.pop(0)
            return

        #------------------------------------------------------------------------------
        # Update the circular buffer with new data.
        self.YKScan_slicer_buf = np.append(self.YKScan_slicer_buf, [list(obj.scan_data[-1].slicer)], axis=0)          # append new data
        waterlevel = self.YKScan_slicer_buf.shape[0]
        if waterlevel > MAX_SLICES:
            self.YKScan_slicer_buf = np.delete(self.YKScan_slicer_buf, 0, axis=0)                                     # remove oldest slice data
            BPrint(self.BPrt_HEAD_WATER() + f"buffer FULL", level=DBG_LEVEL_INFO)
        self.s_update_YKScan.emit(waterlevel)    # ==> invoke asynFunc_update_YKScan() for PyQT's thread context

        if len(obj.scan_data) > 2:   # only keep a few samples
            obj.scan_data.pop(0)

        #------------------------------------------------------------------------------
        lvl = DBG_LEVEL_INFO  if self.ASYN_samples_count < self.DBG_TRACE_ASYN_COUNT  else DBG_LEVEL_TRACE
        BPrint(self.BPrt_HEAD_COMMON() + f"BUF_SHAPE:{self.YKScan_slicer_buf.shape}   SNR:{self.snr:.2f}   DATA:" +
           f"({self.YKScan_slicer_buf[0][-1]:.1f}, {self.YKScan_slicer_buf[0][-2]:.1f}, {self.YKScan_slicer_buf[0][-3]:.1f}, {self.YKScan_slicer_buf[0][-4]:.1f})", level=lvl)

    #----------------------------------------------------------------------------------
    def sync_update_LinkData(self):
        self.__refresh_common_data__()
        self.status      = self.link.status
        self.line_rate   = self.link.line_rate
        self.bit_count   = self.link.bit_count
        self.error_count = self.link.error_count
        self.ber         = self.link.ber                                                                                      # main BER read method: works
        #self.ber1       = self.link.rx.property_for_alias(RX_BER)                                                            # another BER method 1: not working
        #self.ber2       = list(self.link.rx.property.refresh(self.link.rx.property_for_alias[RX_BER]).values())[0]           # another BER method 2: works, almost the same value as <self.link.ber>

        # Append data into Pandas table
        self.comments = check_link_status(self.link)
        if self.comments == "":
            # the Link works normally, then get its statistical data
            ber_series = self.pd_data['BER']
            snr_series = self.pd_data['SNR']
            self.comments = "BER: ({:.2e}, {:.2e}) mean={:.2e} std={:.2e}    SNR: ({:.2e}, {:.2e}) mean={:.2e} std={:.2e}".format( 
               ber_series.min(), ber_series.max(), ber_series.mean(), ber_series.std(),  snr_series.min(), snr_series.max(), snr_series.mean(), snr_series.std() )
        self.pd_data.loc[len(self.pd_data)] = [ self.SYNC_samples_count, self.elapsed, self.status, self.line_rate, self.bit_count, self.error_count, self.ber, self.snr, self.eye, self.hist, self.comments ]

    #----------------------------------------------------------------------------------
    def finish_object(self):
        super().finish_object()
        self.fsm_running = False
        path = f"{CSV_PATH}/YK_{app_start_time.year}-{app_start_time.month:02}{app_start_time.day:02}"
        os.makedirs(path, exist_ok=True)
        self.pd_data.to_csv(f"{path}/{self.dsrcName}-{app_start_time.hour:02}{app_start_time.minute:02}.csv")
        self.__YKEngine_manage__(False, 11)  # launch YK.stop(), to stop the YKScan engine from running.


#--------------------------------------------------------------------------------------------------------------------------------------
class MyYKFigure(matplotlib.figure.Figure):
    # ## 8 - Run YK Scan
    #
    # Initialize the plots and start the YK Scan to begin updating the plots. 
    # YK Scan plot should contain three subplots, these plots should look something like:
    # ![yk_scan_example.png](./yk_scan_example.png)
    # Note: Depending on the hardware setup and external loopback connection, the plot might look different.
    def __init__(self, *args, **kwargs):
        # Custom initialization logic (if needed)
        super().__init__(*args, **kwargs)

    def init_YK_axes(self, fig_name):
        # Each figure corresponds to a QUAD channel
        self.fig_name = fig_name
        self.suptitle(fig_name)

        SLICER_CHUNK_SIZE  = VIVADO_SLICES * YKSCAN_SLICER_SIZE 

        # axis of EYE diagram
        self.ax_EYE = plt.subplot2grid((3,2), (0,0), rowspan=2)
        self.ax_EYE.set_xlabel("ES Sample")
        self.ax_EYE.set_ylabel("Amplitude (%)")
        self.ax_EYE.set_xlim(0, SLICER_CHUNK_SIZE)
        self.ax_EYE.set_ylim(0,100)
        self.ax_EYE.set_yticks(range(0, 100, 20))
        if SHOW_FIG_TITLE: self.ax_EYE.set_title("Slicer eye")
        else:              self.ax_EYE.set_xlabel("EYE")

        # Set custom x-axis labels (divide by YKSCAN_SLICER_SIZE:2000)
        self.scatter_X_data = np.linspace( 0, SLICER_CHUNK_SIZE - 1, SLICER_CHUNK_SIZE )
        scatter_X_ticks     = self.scatter_X_data[0::int(SLICER_CHUNK_SIZE/5)]
        scatter_X_labels    = [f"{x/YKSCAN_SLICER_SIZE:.0f}" for x in scatter_X_ticks]
        self.ax_EYE.set_xticks(scatter_X_ticks, scatter_X_labels)
        self.scatter_plot_EYE = self.ax_EYE.scatter([], [], s=1, color='blue')

        # axis of Histogram diagram
        self.ax_HIST = plt.subplot2grid((3,2), (0,1), rowspan=2)
        self.ax_HIST.set_xlabel("Count")
        self.ax_HIST.set_ylabel("Amplitude (%)")
        self.ax_HIST.set_ylim(0,100)
        self.ax_HIST.set_yticks(range(0, 100, 20))
        if SHOW_FIG_TITLE: self.ax_HIST.set_title("Histogram")
        else:              self.ax_HIST.set_xlabel("Histogram")

        # axis of SNR diagram
        self.ax_SNR_data = []
        self.ax_SNR = plt.subplot(3,2,5)
        self.ax_SNR.set_xlabel("SNR Sample")
        self.ax_SNR.set_ylabel("SNR (dB)")
        self.ax_SNR.set_ylim(-10,50)
        if SHOW_FIG_TITLE: self.ax_SNR.set_title("Signal-to-Noise Ratio")
        else:              self.ax_SNR.set_xlabel("SNR")

        # axis of BER diagram
        self.ax_BER_data = []
        self.ax_BER = plt.subplot(3,2,6)
        self.ax_BER.set_xlabel("BER Sample")
        self.ax_BER.set_ylabel("log10")
        self.ax_BER.set_ylim(-1,-20)
        if SHOW_FIG_TITLE: self.ax_BER.set_title("Bit-Error-Rate")
        else:              self.ax_BER.set_xlabel("BER")

    # ## 6 - Define YK Scan Update Method
    # This method will be called each time the yk scan updates, allowing it to update its graphs in real time. 
    def update_yk_scan(self, myYK):
        # Update the scatter plot with data from the buffer.
        self.scatter_plot_EYE.set_offsets( np.column_stack((self.scatter_X_data, myYK.YKScan_slicer_viewBuffer)) )  # Set new data points

        # Update the histogram plot     ## color: blue / green / teal / brown / charcoal / black / gray / silver / cyan / violet
        self.ax_HIST.cla()              ## NOTE: Histogram must be cleared regularly, otherwise, it will be unresponsive, with messagebox of <<"python3" is not responding>> 
        hist, edges, _ = self.ax_HIST.hist(list(myYK.YKScan_slicer_buf.flatten()), bins=HIST_BINS, orientation='horizontal', color='cyan', range=(0,100))
        myYK.find_peaks_and_valleys(hist, edges) 

        self.ax_SNR_data.append(myYK.snr)
        self.ax_SNR.plot(self.ax_SNR_data, color='teal')
        """
        if self.ax_HIST.lines:
            for line2 in self.ax_HIST.lines:
                self.ax_HIST.set_xlim(0, self.ax_HIST.get_xlim()[1] + YKSCAN_SLICER_SIZE)
                line2.set_xdata(list(line2.get_xdata()) + list(range(len(line2.get_xdata()), len(line2.get_xdata()) + YKSCAN_SLICER_SIZE)))
                line2.set_ydata(list(line2.get_ydata()) + list(myYK.YKScan_slicer_buf[0]))
        else:
            #self.ax_HIST.cla()
            #color: blue / green / teal / brown / charcoal / black / gray / silver / cyan / violet
            self.ax_HIST.hist(list(myYK.YKScan_slicer_buf[0]), 50, orientation = 'horizontal', color='cyan', stacked=True, range=(0,100))

        if self.ax_SNR.lines:
            for line3 in self.ax_SNR.lines:
                if myYK.ASYN_samples_count > self.ax_SNR.get_xlim()[1]:
                    self.ax_SNR.set_xlim(0, myYK.ASYN_samples_count+10)
                line3.set_xdata(list(line3.get_xdata()) + [myYK.ASYN_samples_count])
                line3.set_ydata(list(line3.get_ydata()) + [myYK.snr])
        else:
            self.ax_SNR.plot(myYK.ASYN_samples_count, myYK.snr)
        """

    def update_yk_ber(self, myYK):
        self.ax_BER_data.append(math.log10(myYK.ber))
        self.ax_BER.plot(self.ax_BER_data, color='violet')
        """
        if self.ax_BER.lines:
            for line4 in self.ax_BER.lines:
                if myYK.SYNC_samples_count  > self.ax_BER.get_xlim()[1]:
                    self.ax_BER.set_xlim(0, myYK.SYNC_samples_count+10)
                line4.set_xdata(list(line4.get_xdata()) + [myYK.SYNC_samples_count])
                line4.set_ydata(list(line4.get_ydata()) + [math.log10(myYK.ber)])
        else:
            self.ax_BER.plot(myYK.SYNC_samples_count, math.log10(myYK.ber), color='violet')
        """


#--------------------------------------------------------------------------------------------------------------------------------------
class MplCanvas(FigureCanvas):
    s_start_FSM_Worker = QtCore.pyqtSignal()

    # def __init__(self, parent=None, ykobj=None, nID=0):
    def __init__(self, link, parent=None):
        self.myParent = parent
        self.nID      = link.nID
        if sysconfig.SIMULATE:   self.ykobj = Fake_YKScanLink(self, link)
        else:                    self.ykobj = IBert_YKScanLink(self, link)
        self.updateTable = parent.updateTable
        super().__init__(self.ykobj.fig)

        self.worker_thread = QtCore.QThread()
        self.ykobj.moveToThread(self.worker_thread)                           # move worker to the worker thread
        self.s_start_FSM_Worker.connect(self.ykobj.fsmFunc_worker_thread)
        self.worker_thread.start()                                            # start the thread

    def close_canvas(self):
        self.ykobj.finish_object()

    def start_canvas(self):
        self.s_start_FSM_Worker.emit()

    def update_table(self):
        self.updateTable( self.nID, 0, f"{self.ykobj.ASYN_samples_count:^10}" )
        self.updateTable( self.nID, 1, f"{self.ykobj.SYNC_samples_count:^10}" )
        self.updateTable( self.nID, 4, f"{self.ykobj.status:^20}", QtGui.QColor(255,128,128) if self.ykobj.status == "No link" else QtGui.QColor(128,255,128) )
        self.updateTable( self.nID, 5, f"{self.ykobj.bit_count:^24}" )                     # type: string
        self.updateTable( self.nID, 6, "{:^24}".format(f"{self.ykobj.error_count:.3e}") )  # type: int
        self.updateTable( self.nID, 7, "{:^20}".format(f"{self.ykobj.ber:.3e}") )          # type: float
        self.updateTable( self.nID, 8, "{:^20}".format(f"{self.ykobj.snr:.3f}") )          # type: float
        self.updateTable( self.nID, 9, "{:^20}".format(f"{self.ykobj.eye:.3f}") )          # type: float
        self.updateTable( self.nID,10, self.ykobj.hist )
        self.updateTable( self.nID,11, self.ykobj.comments )
        #BPrint("QTable_TYP: bits={}, err={}, ber={}, snr={}".format(type(self.ykobj.bit_count), type(self.ykobj.error_count), type(self.ykobj.ber), type(self.ykobj.snr)), level=DBG_LEVEL_WIP)
        #BPrint("QTable_VAL: bits={}, err={}, ber={}, snr={}".format(     self.ykobj.bit_count,       self.ykobj.error_count,       self.ykobj.ber,       self.ykobj.snr),  level=DBG_LEVEL_WIP)


#--------------------------------------------------------------------------------------------------------------------------------------
class HPC_Test_MainWidget(QtWidgets.QMainWindow):
    def __init__(self, n_links):
        super().__init__()
        titleText = HW_URL if sysconfig.HWID == "0" else f"{HW_URL} / {sysconfig.HWID}"
        if sysconfig.SIMULATE: titleText = "SIMULATION"
        self.setWindowTitle(f"<b><font color='black' size='{WIN_TITLE_FONT}'>BizLink HPC Cable Test: </font><font color='blue' size='{WIN_TITLE_FONT}'>{titleText}</font></b>")

        self.canvases = []
        self.resizing_windows = False
        self.grid_row = 0
        self.grid_col = 0
        self.n_links  = n_links
        self.setGeometry(0, 0, PLOT_RESOL_X, PLOT_RESOL_Y)

        # Create a central widget
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)

        # Create a vertical layout for the central widget
        self.layout_main = QtWidgets.QVBoxLayout(central_widget)

        # Create a horizontal layout for the toobar
        self.layout_TBar = QtWidgets.QHBoxLayout()
        self.layout_main.addLayout(self.layout_TBar)

        # Create a grid layout for the canvases
        self.layout_grid = QtWidgets.QGridLayout()
        self.layout_main.addLayout(self.layout_grid)

        # Create iBERT multiple channels table 
        self.createTable() 
        self.layout_main.addWidget(self.tableWidget)

    def closeEvent(self, event):
        BPrint("OnClose: to do YK.stop()", level=DBG_LEVEL_NOTICE)
        for c in self.canvases:
            c.close_canvas()
        BPrint("Closed YK-Scan", level=DBG_LEVEL_NOTICE)
        event.accept()  # Close the widget
        BPrint("Closed Widget", level=DBG_LEVEL_NOTICE)

    def resizeEvent(self, event):
        BPrint(f"resizeEvent: {event.oldSize()} => {event.size()}\t\tmain={self.size()}  tbl={self.tableWidget.size()}  fig={self.canvases[0].get_width_height()} ", level=DBG_LEVEL_TRACE)
        self.resizing_windows = True

    def leaveEvent(self, event):
        if  self.resizing_windows:
            self.resizing_windows = False
            BPrint(f"resizeEvent: main={self.size()}  tbl={self.tableWidget.size()}  fig={self.canvases[0].get_width_height()} ", level=DBG_LEVEL_INFO)
            """
            ## To adjust dynamically the Canvas size, but it didn't work ###
            figX, figY = self.canvases[0].get_width_height()
            resX, resY = self.size().width(), self.size().height()
            tblX, tblY = self.tableWidget.size().width(), self.tableWidget.size().height()
            FIG_SIZE_X, FIG_SIZE_Y = calculate_plotFigure_size( resX, resY )
            for c in self.canvases:
                c.ykobj.fig.set_size_inches( FIG_SIZE_X, FIG_SIZE_Y )
            plt.draw() # Redraw the updated plot
            BPrint(f"leaveEvent: main=({PLOT_RESOL_X},{PLOT_RESOL_Y}) => ({resX:>4},{resY:<4}) tbl=({tblX:<3},{tblX:<3}) fig=({figX:<3},{figX:<3}) ", level=DBG_LEVEL_INFO)
            """

    def show_figures(self): 
        canvas_time = datetime.datetime.now()
        for c in self.canvases:
            c.start_canvas()
        self.show()
        gui_time = datetime.datetime.now()
        bprint_loading_time(f"HPC_Test_MainWidget::show_figures() finished, CANVAS={canvas_time - app_start_time}  GUI={gui_time - app_start_time}")

    def createTable(self): 
        self.tableWidget = QtWidgets.QTableWidget(self.n_links, 12) 

        # Table will fit the screen horizontally 
        self.tableWidget.setHorizontalHeaderLabels( ("YKcount", "LinkCount", "TX", "RX", "Status", "Bits", "Errors", "BER", "SNR", "EYE", "Histogram", "comments") )
        header = self.tableWidget.horizontalHeader()
        header.setStretchLastSection(True) 
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)    # header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

    def updateTable(self, row, col, val, color=None): 
        BPrint(f"QTable: ({row},{col}) <= {val}", level=DBG_LEVEL_TRACE)
        self.tableWidget.setItem(row, col, QtWidgets.QTableWidgetItem(val)) 
        if color is not None:
            self.tableWidget.item(row, col).setBackground(color)

    def create_YKScan_figure(self, link):
        #canvas = MplCanvas(self, MyYKScanLink(link), link.nID)
        canvas = MplCanvas(link, self)
        self.layout_grid.addWidget(canvas, self.grid_row, self.grid_col)
        self.canvases.append(canvas)
        canvas.draw()

        self.updateTable( link.nID, 2, "{:^20}".format(re.findall(".*(Quad_.*\.[RT]X).*", str(link.tx))[0]) )
        self.updateTable( link.nID, 3, "{:^20}".format(re.findall(".*(Quad_.*\.[RT]X).*", str(link.rx))[0]) )
        self.updateTable( link.nID, 4, "{:^20}".format(str(link.status)) )

        self.grid_col += 1
        if  self.grid_col >= global_grid_cols:
            self.grid_col = 0
            self.grid_row += 1

    """
    def ui(self, fig):
        self.canvas = FigureCanvas(fig)

        self.graphicview = QtWidgets.QGraphicsView(self)
        self.graphicview.setGeometry(0, 0, PLOT_1_RESOL_X, PLOT_1_RESOL_Y)

        self.graphicscene = QtWidgets.QGraphicsScene()
        self.graphicscene.setSceneRect(0, 0, PLOT_1_RESOL_X - 20, PLOT_1_RESOL_Y - 20)
        self.graphicscene.addWidget(self.canvas)

        self.graphicview.setScene(self.graphicscene)

    def ui2(self, fig):
        self.canvas = FigureCanvas(fig)

        # Create toolbar, passing canvas as first parament, parent (self, the MainWindow) as second.
        toolbar = NavigationToolbar(self.canvas, self)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)

        # Create a placeholder widget to hold our toolbar and canvas.
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
    """


#--------------------------------------------------------------------------------------------------------------------------------------
def create_links_common(RXs, TXs):
    global myLinks

    BPrint(f"Links_TXs: {TXs}", level=DBG_LEVEL_INFO)
    BPrint(f"Links_RXs: {RXs}", level=DBG_LEVEL_INFO)
    myLinks = create_links(txs=TXs, rxs=RXs)

    nID = 0
    if   DBG_LEVEL_TRACE <= sysconfig.DBG_LEVEL:  dbg_print = True;  dbg_print_all = True; 
    elif DBG_LEVEL_DEBUG <= sysconfig.DBG_LEVEL:  dbg_print = True;  dbg_print_all = False;
    else:                                         dbg_print = False; dbg_print_all = False; 

    for link in myLinks:
        link.nID = nID; nID += 1
        link.gt_name  = re.findall(".*(Quad_[0-9]*).*", str(link.rx))[0]
        link.channel  = int(re.findall(".*CH_([0-9]*).*", str(link.rx))[0])
        link.GT_Group = ibert_gtm.gt_groups.filter_by(name=link.gt_name)[0]
        link.GT_Chan  = link.GT_Group.gts[link.channel]
        BPrint(f"\n--- {link.name} :: RX={link.rx} TX={link.tx}  GT={link.gt_name} CH={link.channel} ST={link.status}  -----", level=DBG_LEVEL_INFO)

        set_property_value( link.rx, 'Pattern',  sysconfig.PATTERN, DBG_LEVEL_INFO) 
        set_property_value( link.tx, 'Pattern',  sysconfig.PATTERN, DBG_LEVEL_DEBUG) 
        set_property_value( link.rx, 'Loopback', "None"   , DBG_LEVEL_DEBUG)
        set_property_value( link.tx, 'Loopback', "None"   , DBG_LEVEL_DEBUG)

        """
        link.GT_Chan.reset()
        link.tx.reset()
        link.rx.reset()
        """

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
        link.status = f"{TEST_DATA_RATE} Gbps"
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
    q202.reset()
    q203.reset()
    q204.reset()
    q205.reset()

    all_lnkgrps = get_all_link_groups()
    all_links   = get_all_links()
    BPrint(f"\n--> All Link Groups available - {all_lnkgrps}", level=DBG_LEVEL_DEBUG)
    BPrint(f"\n--> All Links available - {all_links}", level=DBG_LEVEL_DEBUG)


#--------------------------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    if sysconfig.SIMULATE:
        create_fake_links()
    else:
        create_iBERT_session_device()
        bprint_loading_time("Xilinx iBERT-core created")

        create_LinkGroups()
        bprint_loading_time("Xilinx Link-Groups created")

    MainForm = HPC_Test_MainWidget(len(myLinks))

    # ## 7 - Create YK Scan
    # This step initializes the YK scan, setting its update method to the method we defined in the last step. 
    for link in myLinks:
        MainForm.create_YKScan_figure(link)
        #link.myLink.reset_iBERT_engine()
    bprint_loading_time("BizLink iBERT Matplotlib/Figures created")

    MainForm.show_figures()

    sys.exit(app.exec_())

#--------------------------------------------------------------------------------------------------------------------------------------
