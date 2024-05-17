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

#------------------------------------------
from PyQt5 import QtWidgets, QtCore, QtGui
import random
import math
import re
import numpy as np
import pandas as pd
import os
import sys
import argparse
import datetime
import time
from more_itertools import one

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

#--------------------------------------------------------------------------------------------------------------------------------------
# Configuration variables: 1) external EXPORT Environment variables, 2) command-line arguments (higher priority)
#--------------------------------------------------------------------------------------------------------------------------------------
"""
export ip="10.20.2.146";     export CS_SERVER_URL="TCP:$ip:3042" HW_SERVER_URL="TCP:$ip:3121"
export HW_PLATFORM="vpk120"; export CREATE_LGROUP=False
export PLOT_1_RESOL_X=900;   export PLOT_1_RESOL_Y=800;  export PLOT_F_RESOL_X=3840;  export PLOT_F_RESOL_Y=2160
export PDI_FILE="./PDI_Files/VPK120_iBERT_2xQDD_56G.pdi"
export SHOW_FIG_TITLE=True;  export MAX_SLICES=100;
export CSV_PATH="./YK_CSV_Files";
export CONN_TYPE=XConn_x8;
export QUAD_NAME="Quad_202"; export QUAD_CHAN=2;
export APP_DBG_LEVEL=5;
"""

PLOT_1_RESOL_X = int(os.getenv("PLOT_1_RESOL_X", "900"))
PLOT_1_RESOL_Y = int(os.getenv("PLOT_1_RESOL_Y", "800"))
PLOT_F_RESOL_X = int(os.getenv("PLOT_F_RESOL_X", "3200"))
PLOT_F_RESOL_Y = int(os.getenv("PLOT_F_RESOL_Y", "1900"))

CSV_PATH     =     os.getenv("CSV_PATH", "./YK_CSV_Files")
QUAD_NAME    =     os.getenv("QUAD_NAME", "Quad_202")
QUAD_CHAN    = int(os.getenv("QUAD_CHAN", "0"))

CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")

# specify hw and if programming is desired
HW_PLATFORM = os.getenv("HW_PLATFORM", "vpk120")
CREATE_LGROUP = os.getenv("CREATE_LGROUP", 'True').lower() in ('true', '1', 't')
SHOW_FIG_TITLE = os.getenv("SHOW_FIG_TITLE", 'False').lower() in ('true', '1', 't')

MAX_SLICES   = int(os.getenv("MAX_SLICES", "5"))
YKSCAN_SLICER_SIZE = 2000
SLICER_CHUNK_SIZE  = MAX_SLICES * YKSCAN_SLICER_SIZE 

#--------------------------------------------------------------------------------------------------------------------------------------
# https://docs.python.org/3/library/argparse.html,  https://docs.python.org/3/howto/argparse.html
# https://stackoverflow.com/questions/20063/whats-the-best-way-to-parse-command-line-arguments
#--------------------------------------------------------------------------------------------------------------------------------------
parser = argparse.ArgumentParser(description=f"{APP_TITLE} by Bernard Shyu")

# The get_design_files() function tries to find the PDI and LTX files. In non-standard
# configurations, you can put the path for PROGRAMMING_FILE and PROBES_FILE below.
# design_files = get_design_files(f"{HW_PLATFORM}/production/chipscopy_ced")
# PDI_FILE = design_files.programming_file
PDI_FILE = os.getenv("PDI_FILE", "")
parser.add_argument('--PDI_FILE', default=PDI_FILE, metavar='filename', help='FPGA image file (*.pdi) Ex. PDI_Files/VPK120_iBERT_2xQDD_56G.pdi')

CONN_TYPE = os.getenv("CONN_TYPE", "SLoop_x8")
parser.add_argument('--CONN_TYPE', default=CONN_TYPE, metavar='type', help='Connection Type: SLoop_x4 | SLoop_x8 | XConn_x4 | XConn_x8.  Or shorter: S4 | S8 | X4 | X8.  Default: SLoop_x8')

APP_DBG_LEVEL = int(os.getenv("APP_DBG_LEVEL", "3"))
parser.add_argument('--DBG_LEVEL', default=APP_DBG_LEVEL, metavar='level', help='debug level (ERR=0 WARN=1 NOTICE=2 INFO=3 DEBUG=4 TRACE=5, default=3)', type=int)

parser.add_argument('--NFIGURE', default=-1, metavar='number', help='number of Matplotlib Figures, default: -1 (auto)')

sysconfig = parser.parse_args()

#--------------------------------------------------------------------------------------------------------------------------------------
BPrint(f"\n{APP_TITLE } --- {app_start_time}\n", level=DBG_LEVEL_NOTICE)
BPrint(f"Servers URL: {CS_URL} {HW_URL}\t\tHW: {HW_PLATFORM}\tPDI: '{sysconfig.PDI_FILE}'\n", level=DBG_LEVEL_NOTICE)
BPrint(f"SYSCONFIG: fig={sysconfig.NFIGURE} dbg={sysconfig.DBG_LEVEL} cTyp={sysconfig.CONN_TYPE} \n", level=DBG_LEVEL_NOTICE)

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

    # ## 3 - Program the device with PDI_FILE programming image file.
    device = session.devices.filter_by(family="versal").get()
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
    if link.status == "No link" or link.ber > 1e-6:
        lr = get_property_value( link.rx, 'Line Rate'                  )
        ls = get_property_value( link.rx, 'Pattern Checker Lock Status')
        ec = get_property_value( link.rx, 'Pattern Checker Error Count')
        cc = get_property_value( link.rx, 'Pattern Checker Cycle Count')
        return f"LinkStatus='{link.status}'   LineRate={lr}   Patten Checker: LockStatus='{ls}'  ErrorCount='{ec}'  CycleCount='{cc}'"
    else:
        return ""


#--------------------------------------------------------------------------------------------------------------------------------------
# The class correlates to chipscopy.api.ibert.link.Link
class FakeYKScanLink():
    def __init__(self, qname, ch):
        self.nID         = 0
        self.status      = "53.109 Gbps"
        self.line_rate   = "53.121 Gbps"
        self.bit_count   = 0
        self.error_count = 0
        self.ber         = random.random() / 1000000   # BER by random number simulation
        self.GT_Group    = ibert_gtm.gt_groups.filter_by(name=qname)[0]
        self.channel     = ch
        self.rx          = self.GT_Group.gts[ch].rx
        self.tx          = self.GT_Group.gts[ch].tx
        BPrint(f"--> GT Group channels - {self.GT_Group.gts}", level=DBG_LEVEL_INFO)


class MyYKScanLink():
    def __init__(self, link):
        self.YKName = f"YK-{link.GT_Group.name}_CH{link.channel}"
        self.fig = plt.figure(FigureClass=MyYKFigure, num=self.YKName, layout='constrained', edgecolor='black', linewidth=3, figsize=[8,6])   # facecolor='yellow', figsize=[12,10], dpi=100
        self.fig.init_YK_axes(self.YKName)

        #------------------------------------------------------------------------------
        self.snr  = 0
        self.link = link
        self.YK   = create_yk_scans(target_objs=link.rx)[0]                # returns: chipscopy.api.ibert.yk_scan.YKScan object
        self.YK.updates_callback = lambda obj: self.update_YKScan_data(obj)
        self.YK_samples_count = 0
        self.LINK_samples_count = 0
        self.YK_need_restart = 0
        link.myLink = self

        #------------------------------------------------------------------------------
        # Initialize circular buffer
        self.YKScan_slicer_buf = np.zeros((0, YKSCAN_SLICER_SIZE))  # Assuming 2D data (X, Y), X-dim will grow to MAX_SLICES
        self.YK_slice_samples_count = 0

        #------------------------------------------------------------------------------
        # Pandas table to keep data for CSV file
        self.pd_data = pd.DataFrame(columns=["Samples", "Elapsed Time", "Status", "Line Rate", "Bits Count", "Errors Count", "BER", "SNR", "comments"])

        #------------------------------------------------------------------------------
        #self.__refresh_link_data__()
        BPrint(f"\n{self.YKName}:: TX='{link.tx}'  TX-pll='{link.tx.pll}'  LINK='{link}'  YK='{self.YK.name}' ", level=DBG_LEVEL_INFO)
        BPrint(f"{self.YKName}:: RX='{link.rx}'  RX-pll='{link.rx.pll}'  RX-yk_scan='{link.rx.yk_scan}' ", level=DBG_LEVEL_INFO)
        #self.bprint_link(DBG_LEVEL_INFO)

    def bprint_link(self, l):
        BPrint("{}:: SELF={} LINK={:<19}  STATUS={:<15} BER={:<18} RATE={} BITS={} ERR={}".format(self.YKName, self, str(self.link), self.status, self.ber, self.line_rate, self.bit_count, self.error_count), level=l)

    def reset_iBERT_engine(self):
        self.link.tx.reset()
        self.link.rx.reset()
        set_property_value( self.link.rx, 'RX BER Reset', 1, DBG_LEVEL_INFO) 
        self.__refresh_link_data__()
        self.bprint_link(DBG_LEVEL_INFO)

    def __refresh_link_data__(self):
        self.LINK_samples_count +=1
        self.now         = datetime.datetime.now()
        self.elapsed     = (self.now - app_start_time).seconds
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
        self.pd_data.loc[len(self.pd_data)] = [ self.LINK_samples_count, self.elapsed, self.status, self.line_rate, self.bit_count, self.error_count, self.ber, self.snr, self.comments ]

    # ## 6 - Define YK Scan Update Method
    def update_YKScan_data(self, obj):
        self.YK_samples_count +=1      #  ==> len(obj.scan_data) - 1
        self.snr = obj.scan_data[-1].snr

        #------------------------------------------------------------------------------
        # assert YKSCAN_SLICER_SIZE == len(obj.scan_data[-1].slicer)
        if YKSCAN_SLICER_SIZE != len(obj.scan_data[-1].slicer):
            self.YK_need_restart +=1
            BPrint(f"{self.YKName}: samples#{self.YK_samples_count:5d}  ERROR slicer: {len(obj.scan_data[-1].slicer)}", level=DBG_LEVEL_ERR)
            return

        #------------------------------------------------------------------------------
        # Update the circular buffer with new data.
        self.YKScan_slicer_buf = np.append(self.YKScan_slicer_buf, [list(obj.scan_data[-1].slicer)], axis=0)          # append new data
        if self.YKScan_slicer_buf.shape[0] > MAX_SLICES:
            self.YKScan_slicer_buf = np.delete(self.YKScan_slicer_buf, 0, axis=0)                                     # remove oldest slice data
        else:
            self.YK_slice_samples_count += YKSCAN_SLICER_SIZE

        lvl = DBG_LEVEL_TRACE
        #if self.YK_samples_count < 5:  lvl = DBG_LEVEL_WIP
        BPrint("{}: samples#{:5d}  SHAPE: {}   \tSNR:{:.2f}\t  DATA: ({:.1f}, {:.1f}, {:.1f}, {:.1f})".format( 
           self.YKName, self.YK_samples_count, self.YKScan_slicer_buf.shape, self.snr,
           self.YKScan_slicer_buf[0][-1], self.YKScan_slicer_buf[0][-2], self.YKScan_slicer_buf[0][-3], self.YKScan_slicer_buf[0][-4]), level=lvl )    # level=DBG_LEVEL_TRACE

        #------------------------------------------------------------------------------
        if len(obj.scan_data) > 3:   # only keep a few samples
            obj.scan_data.pop(0)

    def update_link_data(self):
        self.__refresh_link_data__()
        self.bprint_link(DBG_LEVEL_TRACE)

    def update_YKScan_figures(self):
        BPrint(f"{self.YKName}: samples#{self.YK_samples_count:4d}, {self.LINK_samples_count:<4d}   BER: {self.ber:.2e}  SNR: {self.snr:6.2f}  Elapsed: {self.elapsed}", level=DBG_LEVEL_TRACE)
        self.fig.update_yk_ber(self)
        self.fig.update_yk_scan(self)
        try:
            if self.YK_need_restart == 1:
                self.YK_need_restart +=1
                self.YK.start()
        except Exception as e:
            print(f"YKScan-{self.YKName} Exception (restart): {str(e)}")

    def finish_object(self):
        path = f"{CSV_PATH}/YK_{app_start_time.year}-{app_start_time.month:02}{app_start_time.day:02}"
        os.makedirs(path, exist_ok=True)
        self.pd_data.to_csv(f"{path}/{self.YKName}-{app_start_time.hour:02}{app_start_time.minute:02}.csv")
        try:
            self.YK.stop()     # Stops the YK scan from running.
        except Exception as e:
            print(f"YKScan-{self.YKName} Exception (finish): {str(e)}")


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
        self.ax_HIST.set_xlim(0,500)
        self.ax_HIST.set_ylim(0,100)
        self.ax_HIST.set_yticks(range(0, 100, 20))
        if SHOW_FIG_TITLE: self.ax_HIST.set_title("Histogram")
        else:              self.ax_HIST.set_xlabel("Histogram")

        # axis of SNR diagram
        self.ax_SNR = plt.subplot(3,2,5)
        self.ax_SNR.set_xlabel("SNR Sample")
        self.ax_SNR.set_ylabel("SNR (dB)")
        self.ax_SNR.set_xlim(0,10)
        self.ax_SNR.set_ylim(-10,50)
        if SHOW_FIG_TITLE: self.ax_SNR.set_title("Signal-to-Noise Ratio")
        else:              self.ax_SNR.set_xlabel("SNR")

        # axis of BER diagram
        self.ax_BER = plt.subplot(3,2,6)
        self.ax_BER.set_xlabel("BER Sample")
        self.ax_BER.set_ylabel("log10")
        self.ax_BER.set_xlim(0,10)
        self.ax_BER.set_ylim(-1,-20)
        if SHOW_FIG_TITLE: self.ax_BER.set_title("Bit-Error-Rate")
        else:              self.ax_BER.set_xlabel("BER")

    # ## 6 - Define YK Scan Update Method
    # This method will be called each time the yk scan updates, allowing it to update its graphs in real time. 
    def update_yk_scan(self, myYK):
        # Update the scatter plot with data from the buffer.
        self.scatter_plot_EYE.set_offsets(np.column_stack((self.scatter_X_data[0:myYK.YK_slice_samples_count], myYK.YKScan_slicer_buf.flatten())))  # Set new data points

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
                if myYK.YK_samples_count > self.ax_SNR.get_xlim()[1]:
                    self.ax_SNR.set_xlim(0, myYK.YK_samples_count+10)
                line3.set_xdata(list(line3.get_xdata()) + [myYK.YK_samples_count])
                line3.set_ydata(list(line3.get_ydata()) + [myYK.snr])
                #self.ax_SNR.set_xlabel(f"SNR Sample: {myYK.snr:.3f}")
        else:
            self.ax_SNR.plot(myYK.YK_samples_count, myYK.snr)

    def update_yk_ber(self, myYK):
        if self.ax_BER.lines:
            for line4 in self.ax_BER.lines:
                if myYK.LINK_samples_count  > self.ax_BER.get_xlim()[1]:
                    self.ax_BER.set_xlim(0, myYK.LINK_samples_count+10)
                line4.set_xdata(list(line4.get_xdata()) + [myYK.LINK_samples_count])
                line4.set_ydata(list(line4.get_ydata()) + [math.log10(myYK.ber)])
                #self.ax_BER.set_xlabel(f"BER Sample: {myYK.ber:.3E}")
        else:
            self.ax_BER.plot(myYK.LINK_samples_count, math.log10(myYK.ber), color='violet')


#--------------------------------------------------------------------------------------------------------------------------------------
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, ykobj=None, nID=0):
        super().__init__(ykobj.fig)
        self.setParent(parent)
        self.ykobj = ykobj
        self.nID   = nID
        self.updateTable = parent.updateTable

    def close_canvas(self):
        self.timer_plot.stop()
        self.timer_table.stop()
        self.ykobj.finish_object()

    def start_canvas(self):
        BPrint(f"Start YK-Scan: {self.ykobj.YKName}", level=DBG_LEVEL_INFO)
        time.sleep(1)
        #self.draw()
        self.ykobj.YK.start()
        self.ykobj.update_link_data()

        # Setup a timer to trigger the redraw by calling update_plot.
        self.timer_plot = QtCore.QTimer()
        self.timer_plot.setInterval(10000)
        self.timer_plot.timeout.connect(self.update_plot)
        self.timer_plot.start()

        # Setup a timer to update the data values for table
        self.timer_table = QtCore.QTimer()
        self.timer_table.setInterval(2000)
        self.timer_table.timeout.connect(self.update_table)
        self.timer_table.start()

    def update_plot(self):
        self.ykobj.update_YKScan_figures()
        self.draw_idle()

    def update_table(self):
        self.ykobj.update_link_data()
        self.updateTable( self.nID, 0, f"{self.ykobj.YK_samples_count:^16}" )
        self.updateTable( self.nID, 1, f"{self.ykobj.LINK_samples_count:^16}" )
        self.updateTable( self.nID, 4, f"{self.ykobj.status:^30}", QtGui.QColor(255,128,128) if self.ykobj.status == "No link" else QtGui.QColor(128,255,128) )
        self.updateTable( self.nID, 5, f"{self.ykobj.bit_count:^30}" )                     # type: string
        self.updateTable( self.nID, 6, "{:^30}".format(f"{self.ykobj.error_count:.3e}") )  # type: int
        self.updateTable( self.nID, 7, "{:^30}".format(f"{self.ykobj.ber:.3e}") )          # type: float
        self.updateTable( self.nID, 8, "{:^30}".format(f"{self.ykobj.snr:.3f}") )          # type: float
        self.updateTable( self.nID, 9, self.ykobj.comments )
        #BPrint("QTable_TYP: bits={}, err={}, ber={}, snr={}".format(type(self.ykobj.bit_count), type(self.ykobj.error_count), type(self.ykobj.ber), type(self.ykobj.snr)), level=DBG_LEVEL_WIP)
        #BPrint("QTable_VAL: bits={}, err={}, ber={}, snr={}".format(     self.ykobj.bit_count,       self.ykobj.error_count,       self.ykobj.ber,       self.ykobj.snr),  level=DBG_LEVEL_WIP)

    """
    # Sample code from consulting AI-Copilot
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super().__init__(fig)
        self.setParent(parent)
        self.plot_data(ax)

    def plot_data(self, ax):
        # Example data (replace with your actual data)
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        ax.plot(x, y)
        ax.set_title("Scatter Plot")
    """


#--------------------------------------------------------------------------------------------------------------------------------------
class MyWidget(QtWidgets.QMainWindow):
    def __init__(self, n_links):
        super().__init__()
        self.setWindowTitle(f"<b><font color='black' size='8'>BizLink HPC Cable Test: </font><font color='blue' size='8'>{HW_URL}</font></b>")

        self.canvases = []
        self.grid_row = 0
        self.grid_col = 0
        self.n_links  = n_links
        if   n_links > 8:  self.layout_grid_rows = 2; self.layout_grid_cols = 8;  self.setGeometry(0, 0, PLOT_F_RESOL_X, PLOT_F_RESOL_Y)
        elif n_links > 1:  self.layout_grid_rows = 2; self.layout_grid_cols = 4;  self.setGeometry(0, 0, PLOT_F_RESOL_X, PLOT_F_RESOL_Y)
        else:              self.layout_grid_rows = 1; self.layout_grid_cols = 1;  self.resize(PLOT_1_RESOL_X, PLOT_1_RESOL_Y)

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

    def show_figures(self): 
        canvas_time = datetime.datetime.now()
        for c in self.canvases:
            c.start_canvas()
        self.show()
        gui_time = datetime.datetime.now()
        BPrint(f"\nChipScoPy loading time: APP={app_start_time}  CANVAS={canvas_time - app_start_time}  GUI={gui_time - app_start_time} \n", level=DBG_LEVEL_NOTICE)

    def createTable(self): 
        self.tableWidget = QtWidgets.QTableWidget(self.n_links, 10) 

        # Table will fit the screen horizontally 
        self.tableWidget.setHorizontalHeaderLabels( ("YK-Samples", "Link-Samples", "TX", "RX", "Status", "Bits", "Errors", "BER", "SNR", "comments") )
        header = self.tableWidget.horizontalHeader()
        header.setStretchLastSection(True) 
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)    # header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

    def updateTable(self, row, col, val, color=None): 
        BPrint(f"QTable: ({row},{col}) <= {val}", level=DBG_LEVEL_TRACE)
        self.tableWidget.setItem(row, col, QtWidgets.QTableWidgetItem(val)) 
        if color is not None:
            self.tableWidget.item(row, col).setBackground(color)

    def create_YKScan_figure(self, link):
        canvas = MplCanvas(self, MyYKScanLink(link), link.nID)
        self.layout_grid.addWidget(canvas, self.grid_row, self.grid_col)
        self.canvases.append(canvas)
        canvas.draw()

        self.updateTable( link.nID, 2, "{:^30}".format(re.findall(".*(Quad_.*\.[RT]X).*", str(link.tx))[0]) )
        self.updateTable( link.nID, 3, "{:^30}".format(re.findall(".*(Quad_.*\.[RT]X).*", str(link.rx))[0]) )
        self.updateTable( link.nID, 4, "{:^20}".format(str(link.status)) )

        self.grid_col += 1
        if  self.grid_col >= self.layout_grid_cols:
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
        link.gt_name = re.findall(".*(Quad_[0-9]*).*", str(link.rx))[0]
        link.channel = int(re.findall(".*CH_([0-9]*).*", str(link.rx))[0])
        link.GT_Group  = ibert_gtm.gt_groups.filter_by(name=link.gt_name)[0]
        link.GT_Chan   = link.GT_Group.gts[link.channel]
        BPrint(f"\n--- {link.name} :: RX={link.rx} TX={link.tx}  GT={link.gt_name} CH={link.channel} ST={link.status}  -----", level=DBG_LEVEL_INFO)

        set_property_value( link.rx, 'Pattern',  "PRBS 31", DBG_LEVEL_INFO) 
        set_property_value( link.rx, 'Loopback', "None"   , DBG_LEVEL_DEBUG)
        set_property_value( link.tx, 'Pattern',  "PRBS 31", DBG_LEVEL_INFO) 
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
def create_LinkGroups():
    global q205, q204, q203, q202
    global myLinks, all_lnkgrps, all_links

    if CREATE_LGROUP:
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
    else:
        myLinks = [ FakeYKScanLink(QUAD_NAME, QUAD_CHAN) ]

    all_lnkgrps = get_all_link_groups()
    all_links   = get_all_links()
    BPrint(f"\n--> All Link Groups available - {all_lnkgrps}", level=DBG_LEVEL_DEBUG)
    BPrint(f"\n--> All Links available - {all_links}", level=DBG_LEVEL_DEBUG)


#--------------------------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    create_iBERT_session_device()
    create_LinkGroups()

    MainForm = MyWidget(len(all_links))

    # ## 7 - Create YK Scan
    # This step initializes the YK scan, setting its update method to the method we defined in the last step. 
    for link in myLinks:
        MainForm.create_YKScan_figure(link)
        link.myLink.reset_iBERT_engine()

    MainForm.show_figures()

    sys.exit(app.exec_())

#--------------------------------------------------------------------------------------------------------------------------------------
