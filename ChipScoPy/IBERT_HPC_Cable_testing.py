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

#======================================================================================================================================
# ## 1 - Initialization: Imports & environments
#======================================================================================================================================
from module.common      import *
from module.iBert_ScoPy import *

#------------------------------------------
from PyQt5 import QtWidgets, QtCore, QtGui
import numpy as np
import pandas as pd
import argparse, configparser, math, re
import os, sys, time, datetime, threading

import matplotlib
matplotlib.use("Qt5Agg")      # 表示使用 Qt5
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar

#--------------------------------------------------------------------------------------------------------------------------------------
# Configuration variables: 1) external EXPORT Environment variables, 2) command-line arguments (higher priority)
#--------------------------------------------------------------------------------------------------------------------------------------
ENV_HELP="""
EXPORT Environment variables:
----->
export SERVER_IP="10.20.2.8";         export FPGA_CS_PORT="3042";              export FPGA_HW_PORT="3121";
export FPGA_HWID="112A";              export CONN_TYPE=XConn_x8;               export DPATTERN="PRBS 9";
export MAX_SLICES=20;                 export YKSCAN_SLICER_SIZE=200;           export HIST_BINS=40;
export CSV_PATH="YK_CSV_Files";       export CONFIG_FILE="config.ini";         export PDI_FILE="PDI_Files/VPK120_iBERT_2xQDD_53G.pdi";
"""

# specify hw and if programming is desired
CSV_PATH           = os.getenv("CSV_PATH", "YK_CSV_Files")
CONFIG_FILE        = os.getenv("CONFIG_FILE", 'config.iBert_HPCTest.ini')

MAX_SLICES         = int(os.getenv("MAX_SLICES",         "12"))
HIST_BINS          = int(os.getenv("HIST_BINS",          "100"))
YKSCAN_SLICER_SIZE = int(os.getenv("YKSCAN_SLICER_SIZE", "2000"))           # for simulation purpose, we may choose smaller value
VIVADO_SLICES      = 4    # Vivado always shows 8000 samples

#--------------------------------------------------------------------------------------------------------------------------------------
APP_TITLE = "ChipScoPy APP for BizLink iBERT HPC-cables testing"
parser = init_argParser(APP_TITLE, ENV_HELP, CONFIG_FILE)

# The get_design_files() function tries to find the PDI and LTX files. In non-standard configurations, you can put the path for PROGRAMMING_FILE and PROBES_FILE below.
#    design_files = get_design_files(f"{HW_PLATFORM}/production/chipscopy_ced")
#    PDI_FILE = design_files.programming_file
SIM_PDIFILE="Bernard_Simulation/VPK120_iBERT_2xQDD_53G.pdi"
get_parameter( "PDI_FILE",     SIM_PDIFILE, "filename", 'FPGA image file (*.pdi) Ex. PDI_Files/VPK120_iBERT_2xQDD_53G.pdi' )
get_parameter( "SERVER_IP",    "localhost", "ip",       'FPGA-board IP address. Default: localhost' )
get_parameter( "FPGA_CS_PORT", "3042",      "port",     'FPGA-board cs_server port. Default: 3042' )
get_parameter( "FPGA_HW_PORT", "3121",      "port",     'FPGA-board hw_server port. Default: 3121' )
get_parameter( "FPGA_HWID",    "0",         "hwID",     'FPGA-board HWID: S/N (0 or 111A or 112A). Default: 0 (NOT specified, auto-detection)' )
get_parameter( "CONN_TYPE",    "SLoop_x8",  "type",     'Connection Type: SLoop_x4 | SLoop_x8 | XConn_x4 | XConn_x8.  Or shorter: S4 | S8 | X4 | X8.  Default: SLoop_x8' )
get_parameter( "TESTID",       "",          "TID",      'Specify the TID-name of testing configuration, Ex. "B5.sn111_B1.sn112", means cable B5 on VPK120-sn111 && cable B1 on sn112. Default: ""' )
get_parameter( "DPATTERN",     "PRBS 31",   "pattern",  'Bits data pattern: PRBS 7 / PRBS 9 / ...' )

sysconfig = finish_argParser("YK-Quad_204_CH0")

#--------------------------------------------------------------------------------------------------------------------------------------
sysconfig.DATA_RATE = int(re.findall(".*VPK120_iBERT_.*_([0-9]+)G.pdi", sysconfig.PDI_FILE)[0])

match sysconfig.CONN_TYPE:
    case "S4" | "SLoop_x4" | "X4" | "XConn_x4": global_N_links = 8;   global_grid_rows = 2;  global_grid_cols = 4;
    case "S8" | "SLoop_x8" | "X8" | "XConn_x8": global_N_links = 16;  global_grid_rows = 2;  global_grid_cols = 8;
    case _:   raise ValueError(f"Not valid Connection Type: {sysconfig.CONN_TYPE}\n")

calculate_plotFigure_size(global_grid_rows, global_grid_cols, global_N_links)

sysconfig.CS_URL = f"TCP:{sysconfig.SERVER_IP}:{sysconfig.FPGA_CS_PORT}"
sysconfig.HW_URL = f"TCP:{sysconfig.SERVER_IP}:{sysconfig.FPGA_HW_PORT}"

BPrint(f"\n{APP_TITLE } --- {app_start_time}\n", level=DBG_LEVEL_NOTICE)
BPrint(f"Servers: CS:{sysconfig.CS_URL} HW:{sysconfig.HW_URL}   FPGA_HW: {sysconfig.FPGA_HWID}   PDI: '{sysconfig.PDI_FILE}'", level=DBG_LEVEL_NOTICE)
BPrint(f"SYSCONFIG: cTyp={sysconfig.CONN_TYPE} pattern={sysconfig.DPATTERN} TID={sysconfig.TESTID} RATE={sysconfig.DATA_RATE}G " +
       f"resolution={sysconfig.RESOLUTION} FIG={sysconfig.FIG_SIZE_X},{sysconfig.FIG_SIZE_Y}", level=DBG_LEVEL_NOTICE)
BPrint(f"DEBUG: level={sysconfig.DBG_LEVEL} srcName={sysconfig.DBG_SRCNAME} lvAdj={sysconfig.DBG_LVADJ} AsynCnt={sysconfig.DBG_ASYCOUNT} SynCnt={sysconfig.DBG_SYNCOUNT} SIM={sysconfig.SIMULATE} \n", level=DBG_LEVEL_NOTICE)

#======================================================================================================================================
# Data source classes: iBERT-Link data, YK-Scan data, radom number simulattion
#======================================================================================================================================
#----------------------------------------------------------------------------------------------------------------------------
class Base_YKScanLink_DataSrc(Base_DataSource):
    s_update_YKScan = QtCore.pyqtSignal(int)

    def __init__(self, dView, link):
        super().__init__(dView)
        self.link = link
        link.myLink = self

        #------------------------------------------------------------------------------
        # Initialize circular buffer
        self.YKScan_slicer_buf = np.zeros((0, YKSCAN_SLICER_SIZE))  # Assuming 2D data (X, Y), X-dim will grow to MAX_SLICES
        self.YK_is_started = False

        self.s_update_YKScan.connect(self.asynFunc_update_YKScan, QtCore.Qt.QueuedConnection)
        self.YKScan_slicer_viewPointer = 0
        self.YKScan_slicer_viewBuffer  = np.zeros(VIVADO_SLICES * YKSCAN_SLICER_SIZE)
        self.YKScan_slicer_init_filled = False

        self.ax_SNR_data = []
        self.ax_BER_data = []

    def BPrt_HEAD_WATER(self):
        return self.BPrt_HEAD_COMMON() + f"WATER:{self.YKScan_slicer_buf.shape[0]:>2}/{str(self.YK_is_started):<5}\t"

    def bprint_link(self):
        return self.BPrt_HEAD_COMMON() + f"LINK STATUS={self.status:<12} BER={self.ber:<15} RATE={self.line_rate:<12} BITS={self.bit_count:<18} ERR={self.error_count}"
        #return self.BPrt_HEAD_COMMON() + f"SELF={self} LINK={str(self.link):<8}  STATUS={self.status:<12} BER={self.ber:<15} RATE={self.line_rate:<12} BITS={self.bit_count:<18} ERR={self.error_count}"

    def sync_update_LinkData(self):  pass    # Abstract method: to update data from ource engine, synchronously by polling
    def async_update_YKData(self):   pass    # Abstract method: to update data from ource engine, asynchronously by call-back

    ## FSM-RESET state, fetching YKScan for 4 slices (VIVADO_SLICES), and filling up to 12 (MAX_SLICES)
    def fill_up_slicer_buf(self):
        if self.YKScan_slicer_init_filled:         return
        if self.ASYN_samples_count >= MAX_SLICES:  return

        while self.ASYN_samples_count == 0:
            self.sync_refresh_plotBER()
            sleep_QAppVitalize(2)

        for i in range(self.ASYN_samples_count, MAX_SLICES):
            self.YKScan_slicer_buf = np.append(self.YKScan_slicer_buf, [self.YKScan_slicer_buf[i % self.ASYN_samples_count]], axis=0)
        self.YKScan_slicer_init_filled = True

    def fsmFunc_early_plots(self):
        self.sync_refresh_plotBER()
        if self.ASYN_samples_count > 0:
            self.fill_up_slicer_buf()
            self.sync_refresh_plotYK()
        self.dataView.myCanvas.draw()

    def sync_refresh_plotBER(self):
        self.sync_update_LinkData()
        self.dataView.myFigure.update_yk_ber(self)
        self.dataView.update_table()
        self.BPrt_traceData( self.bprint_link(), trType="SYNC" )

    def sync_refresh_plotYK(self):
        self.async_update_YKData()
        # rotate VIVADO_SLICES(=4) slicers of view-buffer from self.YKScan_slicer_buf[MAX_SLICES(=12)]
        v = self.YKScan_slicer_viewPointer
        self.YKScan_slicer_viewBuffer = self.YKScan_slicer_buf[v:(v + VIVADO_SLICES)]
        self.YKScan_slicer_viewPointer += VIVADO_SLICES
        if  self.YKScan_slicer_viewPointer >= MAX_SLICES:
            self.YKScan_slicer_viewPointer = 0;

        # refresh the matplotlib figures
        self.dataView.myFigure.update_yk_scan(self)
        self.BPrt_traceData( self.BPrt_HEAD_WATER() + f"refresh_plotYK.{v}.{self.YKScan_slicer_viewPointer}: BER: {self.ber:.2e}  SNR: {self.snr:6.2f}  Elapsed:{self.elapsed}" )

    def fsmFunc_refresh_plots(self):
        self.sync_refresh_plotBER()
        self.sync_refresh_plotYK()
        self.dataView.myCanvas.draw()       # myCanvas.draw_idle(): not good, easier with lagging, non-responsive

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
        if (i + HILL_MIN_WIDTH) >= half_BINS:
            # DEBUG >> (0:50): SHAPE=(100,) P=10373.0 I=48      Exception: zero-size array to reduction operation maximum which has no identity
            BPrint(self.BPrt_HEAD_WATER() + f"Peaks too NARROW on (0:50):   P={p} I={i}", level = self.dataView.mydbg_INFO)
            Peak0 = p;  i_P0 = i - 1
            Peak1 = p;  i_P1 = i
        else:
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
        if (i - HILL_MIN_WIDTH) <= half_BINS:
            BPrint(self.BPrt_HEAD_WATER() + f"Peaks too NARROW on (50:100): P={p} I={i}", level = self.dataView.mydbg_INFO)
            Peak2 = p;  i_P2 = i
            Peak3 = p;  i_P3 = i + 1
        else:
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
        BPrint(self.BPrt_HEAD_WATER() + f"std:   {stdvar0:9.3f}    {stdvar1:9.3f}    {stdvar2:9.3f}    {stdvar3:9.3f} ", level = self.dataView.mydbg_TRACE)
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
            BPrint(self.BPrt_HEAD_WATER() + f"find Histogram-Peaks: {len(hist)} / {len(bins)} ", level = self.dataView.mydbg_INFO)
            return
        if sysconfig.DATA_RATE > 50:
            self.find_PAM4_peaks_and_valleys(hist, bins)
        else:
            self.find_NRZ_peaks_and_valleys(hist, bins)
        BPrint(self.BPrt_HEAD_WATER() + f"Histogram-EYE: {self.eye:.3f}  statistic: {self.hist}", level = self.dataView.mydbg_TRACE)


#----------------------------------------------------------------------------------------------------------------------------
class Fake_YKScanLink_DataSrc(Base_YKScanLink_DataSrc):
    #s_update_YKScan = QtCore.pyqtSignal(int)
    WATCHDOG_INTERVAL = 5 * 1000

    def __init__(self, dView, link):
        super().__init__(dView, link)
        np.random.seed(42)
        self.peaks_rand_mode   = True
        self.std_dev = 1.5
        self.wdog_i = 0

        #------------------------------------------------------------------------------
        self.bits_increment = 2 * sysconfig.DATA_RATE * 1.0E9    # incremented by every 2 seconds
        self.bit_count   = "0"
        self.bit_count_N = 0
        self.error_count = 0
        self.status      = self.link.status
        self.line_rate   = self.link.status
        self.comments    = ""

    #----------------------------------------------------------------------------------
    def fsmFunc_reset(self):
        BPrint(self.BPrt_HEAD_WATER() + f"fsmFunc_reset", level=self.dataView.mydbg_INFO)
        self.fsmFunc_early_plots()
        match self.fsm_state:
            case 4:
                self.fill_up_slicer_buf()
                return True
            case _:
                return False

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

        slice_data = []
        for peak_pos in peak_positions:
            slice_data.append( np.random.normal(loc=peak_pos, scale=self.std_dev, size=int(YKSCAN_SLICER_SIZE/4)) )
        slice_buf = np.column_stack(( slice_data[0], slice_data[1], slice_data[2], slice_data[3] ))

        self.YKScan_slicer_buf = np.append(self.YKScan_slicer_buf, [slice_buf.flatten('c')], axis=0)          # append new data
        waterlevel = self.YKScan_slicer_buf.shape[0]
        if waterlevel > MAX_SLICES:
            self.YKScan_slicer_buf = np.delete(self.YKScan_slicer_buf, 0, axis=0)                                     # remove oldest slice data
            BPrint(self.BPrt_HEAD_WATER() + f"buffer FULL", level=self.dataView.mydbg_DEBUG)
        self.s_update_YKScan.emit(waterlevel)    # ==> invoke asynFunc_update_YKScan() for PyQT's thread context

        self.ax_SNR_data.append(self.snr)

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
        self.error_count += np.random.randint(100) + 1             # random int between 0 and 100
        self.ber          = self.error_count / self.bit_count_N;   #  np.random.random() / 1000000   # BER by random number simulation
        self.snr          = 18 + np.random.rand() * 4              # random float between 0 and 4
        self.ax_BER_data.append(math.log10(self.ber))


# The class correlates to chipscopy.api.ibert.link.Link
#----------------------------------------------------------------------------------------------------------------------------
class IBert_YKScanLink_DataSrc(Base_YKScanLink_DataSrc):
    WATCHDOG_INTERVAL = 300 * 1000

    def __init__(self, dView, link):
        super().__init__(dView, link)

        #------------------------------------------------------------------------------
        self.monitor_YK_cnt = 0
        self.YK   = create_yk_scans(target_objs=link.rx)[0]                # returns: chipscopy.api.ibert.yk_scan.YKScan object
        self.YK.updates_callback = lambda obj: self.asynCB_update_YKScanData(obj)
        BPrint(f"{self.dsrcName}:: TX={link.tx}  RX={link.rx}  LINK={str(link):<8}  YK={self.YK.name:<10}  RX.yk_scan={link.rx.yk_scan}", level=self.dataView.mydbg_INFO)

        #------------------------------------------------------------------------------
        # Pandas table to keep data for CSV file
        self.pd_data = pd.DataFrame(columns=["Samples", "Elapsed Time", "Status", "Line Rate", "Bits Count", "Errors Count", "BER", "SNR", "EYE-Opening", "Histogram", "comments"])

    #----------------------------------------------------------------------------------
    def fsmFunc_reset(self):
        BPrint(self.BPrt_HEAD_WATER() + f"fsmFunc_reset", level=self.dataView.mydbg_INFO)
        self.fsmFunc_early_plots()
        match self.fsm_state:
            case 1:
                sleep_QAppVitalize(self.link.nID*4) # interleaving to prevent overwhelming of data traffic from simultaneous YKScan on all Quad/CH
                self.__YKEngine_manage__(True, 0)   # launch YK.start(), to start the YKScan engine
                return False
            case 4:
                self.__YKEngine_manage__(False, 12) # launch YK.stop(), to stop the YKScan engine
                return False
            case 9:
                self.fill_up_slicer_buf()
                return True                         # end of FSM-RESET state
            case _:
                return False

    def fsmFunc_watchdog(self):
        BPrint(self.BPrt_HEAD_WATER() + f"Watchdog", level=self.dataView.mydbg_DEBUG)
        if self.fsm_state >= 10:  # Normal FSM-state
            self.__YKEngine_manage__(True, 1)  # relaunch YK.start(), likely it is stopped by throttling of flow control

    def async_update_YKData(self):
        self.monitor_YK_cnt += 1
        if  self.monitor_YK_cnt >= 4:
            self.monitor_YK_cnt = 0
            self.__YKEngine_manage__(False, 13)     # launch YK.stop(), to stop the YKScan engine

    #----------------------------------------------------------------------------------
    def __YKEngine_manage__(self, to_start_YK, _where_):
        try:
            BPrint(self.BPrt_HEAD_WATER() + f"__YKEngine_manage__({_where_:2},  do_YK_Start={to_start_YK})", level=self.dataView.mydbg_DEBUG)
            if to_start_YK:
                if not self.YK_is_started:
                    self.YK.start()
                self.YK_is_started = True
            else:
                if self.YK_is_started:
                    self.YK.stop()
                self.YK_is_started = False
        except Exception as e:
            print(f"YKScan-{self.dsrcName} ({_where_:2} {to_start_YK} {self.YK_is_started})  Exception: {str(e)}")

    def asynFunc_update_YKScan(self, waterlevel):
        # throttle the YKScan engine in advance to prevent overflow of the slicer buffer
        if waterlevel > VIVADO_SLICES:
            self.__YKEngine_manage__(False, 10)  # launch YK.stop(), to stop the YKScan engine from running.

    # ## 6 - Define YK Scan Update Method
    #----------------------------------------------------------------------------------
    def asynCB_update_YKScanData(self, obj):
        # assert YKSCAN_SLICER_SIZE == len(obj.scan_data[-1].slicer)
        if YKSCAN_SLICER_SIZE != len(obj.scan_data[-1].slicer):
            BPrint(self.BPrt_HEAD_COMMON() + f"ERROR slicer: {len(obj.scan_data[-1].slicer)}", level=DBG_LEVEL_ERR)
            if len(obj.scan_data[-1].slicer) != 0:
                obj.scan_data.pop(0)
            self.s_update_YKScan.emit(VIVADO_SLICES + 1)    # ==> to launch YK.stop() to rejuvenate the YK-engine
            return

        #------------------------------------------------------------------------------
        self.ASYN_samples_count +=1      #  ==> len(obj.scan_data) - 1
        self.snr = obj.scan_data[-1].snr
        self.ax_SNR_data.append(self.snr)

        #------------------------------------------------------------------------------
        # Update the circular buffer with new data.
        self.YKScan_slicer_buf = np.append(self.YKScan_slicer_buf, [list(obj.scan_data[-1].slicer)], axis=0)          # append new data
        waterlevel = self.YKScan_slicer_buf.shape[0]
        if waterlevel > MAX_SLICES:
            self.YKScan_slicer_buf = np.delete(self.YKScan_slicer_buf, 0, axis=0)                                     # remove oldest slice data
            BPrint(self.BPrt_HEAD_WATER() + f"buffer FULL", level=self.dataView.mydbg_DEBUG)
        self.s_update_YKScan.emit(waterlevel)    # ==> invoke asynFunc_update_YKScan() for PyQT's thread context

        if len(obj.scan_data) > 2:   # only keep a few samples
            obj.scan_data.pop(0)

        #------------------------------------------------------------------------------
        self.BPrt_traceData( self.BPrt_HEAD_COMMON() + f"BUF_SHAPE:{self.YKScan_slicer_buf.shape}   SNR:{self.snr:.2f}   DATA:" +
           f"({self.YKScan_slicer_buf[0][-1]:.1f}, {self.YKScan_slicer_buf[0][-2]:.1f}, {self.YKScan_slicer_buf[0][-3]:.1f}, {self.YKScan_slicer_buf[0][-4]:.1f})" )

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
        self.ax_BER_data.append(math.log10(self.ber))

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
        #path = f"{CSV_PATH}/YK_{sysconfig.FPGA_HWID}.{app_start_time.year}-{app_start_time.month:02}{app_start_time.day:02}"
        path = f"{CSV_PATH}/TID_{sysconfig.TESTID}.{app_start_time.year}-{app_start_time.month:02}{app_start_time.day:02}"
        os.makedirs(path, exist_ok=True)
        self.pd_data.to_csv(f"{path}/Sn{sysconfig.FPGA_HWID}_{sysconfig.DATA_RATE}G.{self.dsrcName}-{app_start_time.hour:02}{app_start_time.minute:02}.csv")
        self.__YKEngine_manage__(False, 11)  # launch YK.stop(), to stop the YKScan engine from running.


#======================================================================================================================================
# Data View classes: to present the source data to Matplotlib figures / canvas, and rendering to QT-Windows
#======================================================================================================================================
class MyYK_Figure(matplotlib.figure.Figure):
    # ## 8 - Run YK Scan
    #
    # Initialize the plots and start the YK Scan to begin updating the plots. 
    # YK Scan plot should contain three subplots, these plots should look something like:
    # ![yk_scan_example.png](./yk_scan_example.png)
    # Note: Depending on the hardware setup and external loopback connection, the plot might look different.
    def __init__(self, *args, **kwargs):
        # Custom initialization logic (if needed)
        super().__init__(*args, **kwargs)

    def init_YK_axes(self, dView):
        # Each figure corresponds to a QUAD channel
        self.dataView = dView
        self.fig_name = dView.myName
        self.suptitle(dView.myName)

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
        self.ax_SNR = plt.subplot(3,2,5)
        self.ax_SNR.set_xlabel("SNR Sample")
        self.ax_SNR.set_ylabel("SNR (dB)")
        self.ax_SNR.set_ylim(-10,50)
        if SHOW_FIG_TITLE: self.ax_SNR.set_title("Signal-to-Noise Ratio")
        else:              self.ax_SNR.set_xlabel("SNR")

        # axis of BER diagram
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

        # self.scatter_plot_EYE.set_offsets( np.column_stack((self.scatter_X_data, myYK.YKScan_slicer_viewBuffer.flatten())) )
        # >>>
        #      ValueError: all the input array dimensions except for the concatenation axis must match exactly,
        #                  but along dimension 0, the array at index 0 has size 8000 and the array at index 1 has size 6000
        buf = myYK.YKScan_slicer_viewBuffer.flatten()
        self.scatter_plot_EYE.set_offsets( np.column_stack((self.scatter_X_data[0:len(buf)], buf)) )  # Set new data points

        # Check if it's rotating the YKScan_slicer_buf on OLD data, then we won't need to do HISTOGRAM
        if myYK.ASYN_samples_calc == myYK.ASYN_samples_count:
            return
        myYK.ASYN_samples_calc = myYK.ASYN_samples_count

        # Update the histogram plot     ## color: blue / green / teal / brown / charcoal / black / gray / silver / cyan / violet
        self.ax_HIST.cla()              ## NOTE: Histogram must be cleared regularly, otherwise, it will be unresponsive, with messagebox of <<"python3" is not responding>> 
        hist, edges, _ = self.ax_HIST.hist(list(myYK.YKScan_slicer_buf.flatten()), bins=HIST_BINS, orientation='horizontal', color='cyan', range=(0,100))
        myYK.find_peaks_and_valleys(hist, edges) 
        """
        If the data has already been binned and counted, use bar or stairs to plot the distribution:
        counts, bins = np.histogram(x)
        plt.stairs(counts, bins)
        """

        self.ax_SNR.plot(myYK.ax_SNR_data, color='teal')

    def update_yk_ber(self, myYK):
        self.ax_BER.plot(myYK.ax_BER_data, color='violet')


#----------------------------------------------------------------------------------------------------------------------------
class MyLink_TableEntry:
    def __init__(self, canvas, name):
        pass


#----------------------------------------------------------------------------------------------------------------------------
class YKScan_DataView(Base_DataView):
    s_start_FSM_Worker = QtCore.pyqtSignal()

    def __init__(self, link, parent):
        super().__init__(f"YK-{link.gt_name}_CH{link.channel}", parent)
        self.link    = link
        self.nID     = link.nID

        #------------------------------------------------------------------------------
        if sysconfig.SIMULATE:   self.myDataSrc = Fake_YKScanLink_DataSrc(self, link)
        else:                    self.myDataSrc = IBert_YKScanLink_DataSrc(self, link)
        self.worker_thread = QtCore.QThread()
        self.myDataSrc.moveToThread(self.worker_thread)                           # move worker to the worker thread
        self.s_start_FSM_Worker.connect(self.myDataSrc.fsmFunc_worker_thread)
        self.worker_thread.start()                                                # start the thread

        #------------------------------------------------------------------------------
        self.myFigure = plt.figure(FigureClass=MyYK_Figure, num=self.myName, layout='constrained', edgecolor='black', linewidth=3, figsize=[sysconfig.FIG_SIZE_X, sysconfig.FIG_SIZE_Y])   # facecolor='yellow', dpi=100
        self.myFigure.init_YK_axes(self)
        self.myCanvas = FigureCanvas(self.myFigure)
        #self.mytable  = MyLink_TableEntry()

    def update_table(self):
        self.updateTable( self.nID, 0, f"{self.myDataSrc.ASYN_samples_count:^10}" )
        self.updateTable( self.nID, 1, f"{self.myDataSrc.SYNC_samples_count:^10}" )
        self.updateTable( self.nID, 4, f"{self.myDataSrc.status:^20}", QtGui.QColor(255,128,128) if self.myDataSrc.status == "No link" else QtGui.QColor(128,255,128) )
        self.updateTable( self.nID, 5, f"{self.myDataSrc.bit_count:^24}" )                     # type: string
        self.updateTable( self.nID, 6, "{:^24}".format(f"{self.myDataSrc.error_count:.3e}") )  # type: int
        self.updateTable( self.nID, 7, "{:^20}".format(f"{self.myDataSrc.ber:.3e}") )          # type: float
        self.updateTable( self.nID, 8, "{:^20}".format(f"{self.myDataSrc.snr:.3f}") )          # type: float
        self.updateTable( self.nID, 9, "{:^20}".format(f"{self.myDataSrc.eye:.3f}") )          # type: float
        self.updateTable( self.nID,10, self.myDataSrc.hist )
        self.updateTable( self.nID,11, self.myDataSrc.comments )
        #BPrint("QTable_TYP: bits={}, err={}, ber={}, snr={}".format(type(self.myDataSrc.bit_count), type(self.myDataSrc.error_count), type(self.myDataSrc.ber), type(self.myDataSrc.snr)), level=DBG_LEVEL_WIP)
        #BPrint("QTable_VAL: bits={}, err={}, ber={}, snr={}".format(     self.myDataSrc.bit_count,       self.myDataSrc.error_count,       self.myDataSrc.ber,       self.myDataSrc.snr),  level=DBG_LEVEL_WIP)

    def start_object(self):
        self.s_start_FSM_Worker.emit()

    def finish_object(self):
        self.myDataSrc.finish_object()


#----------------------------------------------------------------------------------------------------------------------------
class HPCTest_ViewArena(QtCore.QObject):
    #def __init__(self, wgCanvas, wgTable, N_Links, N_CavasRows, N_CanvasCols):
    def __init__(self, qwin, qlayout, n_links):
        super().__init__()
        self.dataViews = []
        self.grid_row = 0
        self.grid_col = 0
        self.n_links  = n_links
        self.myLayout = qlayout
        self.myWidget = qwin

        # Create a grid layout for the dataViews
        self.layout_grid = QtWidgets.QGridLayout()
        self.myLayout.addLayout(self.layout_grid)

        # Create iBERT multiple channels table 
        self.createTable() 
        self.myLayout.addWidget(self.tableWidget)

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

    def create_dataView_objects(self, link):
        dview = YKScan_DataView(link, self)
        self.layout_grid.addWidget(dview.myCanvas, self.grid_row, self.grid_col)
        self.dataViews.append(dview)
        dview.myCanvas.draw()

        # issue: "SyntaxWarning: invalid escape sequence"  (https://stackoverflow.com/questions/52335970/how-to-fix-syntaxwarning-invalid-escape-sequence-in-python)
        # RootCause: "\ is the escape character in Python string literals."
        #             it will cause a DeprecationWarning (< 3.12) or a SyntaxWarning (3.12+) otherwise.
        # To check:  python -Wd -c '"\A"'
        #            <string>:1: DeprecationWarning: invalid escape sequence '\A'
        # Resolution: should always use \\ or raw strings r"xxx"
        #             r"""raw strings""" for docstrings
        self.updateTable( link.nID, 2, "{:^20}".format(re.findall(r".*(Quad_.*\.[RT]X).*", str(link.tx))[0]) )
        self.updateTable( link.nID, 3, "{:^20}".format(re.findall(r".*(Quad_.*\.[RT]X).*", str(link.rx))[0]) )
        self.updateTable( link.nID, 4, "{:^20}".format(str(link.status)) )

        self.grid_col += 1
        if  self.grid_col >= global_grid_cols:
            self.grid_col = 0
            self.grid_row += 1

    def show_dataView(self):
        canvas_time = datetime.datetime.now()
        for c in self.dataViews:
            QtWidgets.QApplication.processEvents()
            c.start_object()
        self.myWidget.show()
        gui_time = datetime.datetime.now()
        bprint_loading_time(f"HPC_Test_MainWidget::show_figures() finished, CANVAS={canvas_time - app_start_time}  GUI={gui_time - app_start_time}")

    def finish_object(self):
        for c in self.dataViews:
            QtWidgets.QApplication.processEvents()
            c.finish_object()


#======================================================================================================================================
class HPC_Test_MainWidget(QtWidgets.QMainWindow):
    def __init__(self, n_links):
        super().__init__()
        self.setWindowTitle(f"BizLink HPC Cable Test  /  FPGA HW:{sysconfig.SERVER_IP}:{sysconfig.FPGA_HW_PORT}  CS:{sysconfig.FPGA_CS_PORT}")

        self.resizing_windows = False
        self.setGeometry(0, 0, sysconfig.APP_RESOL_X, sysconfig.APP_RESOL_Y)

        # Create a central widget
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)

        # Create a vertical layout for the central widget
        self.layout_main = QtWidgets.QVBoxLayout(central_widget)
        self.create_ToolBar()
        self.my_viewArena = HPCTest_ViewArena(self, self.layout_main, n_links)

    def create_ToolBar(self):
        # Create a horizontal layout for the toobar
        self.layout_toolbar = QtWidgets.QHBoxLayout()

        titleText = "SIMULATION"  if sysconfig.FPGA_HWID == "0" else f"{sysconfig.FPGA_HWID}"
        if sysconfig.TESTID != "": titleText = f"{titleText} / {sysconfig.TESTID} / {sysconfig.DATA_RATE}G"

        label = QtWidgets.QLabel(titleText, self)
        label.setStyleSheet(WTITLE_STYLE)
        self.layout_toolbar.addWidget(label)

        btn = QtWidgets.QPushButton("Bernard Button", self)
        self.layout_toolbar.addWidget(btn)

        box = QtWidgets.QComboBox(self)
        box.addItems(['A','B','C','D'])
        box.setGeometry(10,10,200,50)
        self.layout_toolbar.addWidget(box)

        self.layout_main.addLayout(self.layout_toolbar)

    def closeEvent(self, event):
        BPrint("OnClose: to do YK.stop()", level=DBG_LEVEL_NOTICE)
        self.my_viewArena.finish_object()
        event.accept()  # Close the widget
        BPrint("Closed Widget", level=DBG_LEVEL_NOTICE)

    def resizeEvent(self, event):
        BPrint(f"resizeEvent: {event.oldSize()} => {event.size()}\t\tmain={self.size()}  tbl={self.my_viewArena.tableWidget.size()}  fig={self.my_viewArena.dataViews[0].myCanvas.get_width_height()} ", level=DBG_LEVEL_TRACE)
        self.resizing_windows = True

    def leaveEvent(self, event):
        if  self.resizing_windows:
            self.resizing_windows = False
            BPrint(f"resizeEvent: main={self.size()}  tbl={self.my_viewArena.tableWidget.size()}  fig={self.my_viewArena.dataViews[0].myCanvas.get_width_height()} ", level=DBG_LEVEL_INFO)
            """
            ## To adjust dynamically the Canvas size, but it didn't work ###
            figX, figY = self.my_viewArena.dataViews[0].myCanvas .get_width_height()
            resX, resY = self.size().width(), self.size().height()
            tblX, tblY = self.tableWidget.size().width(), self.tableWidget.size().height()
            sysconfig.FIG_SIZE_X, sysconfig.FIG_SIZE_Y = calculate_plotFigure_size( resX, resY )
            for c in self.my_viewArena.dataViews:
                c.myDataSrc.fig.set_size_inches( sysconfig.FIG_SIZE_X, sysconfig.FIG_SIZE_Y )
            plt.draw() # Redraw the updated plot
            BPrint(f"leaveEvent: main=({sysconfig.APP_RESOL_X},{sysconfig.APP_RESOL_Y}) => ({resX:>4},{resY:<4}) tbl=({tblX:<3},{tblX:<3}) fig=({figX:<3},{figX:<3}) ", level=DBG_LEVEL_INFO)
            """

    def show_figures(self): 
        self.my_viewArena.show_dataView()

    def create_YKScanLink_objects(self, link):
        self.my_viewArena.create_dataView_objects(link)


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

#======================================================================================================================================
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    myLinks = init_iBERT_engine(sysconfig, global_N_links)
    MainForm = HPC_Test_MainWidget(len(myLinks))

    # ## 7 - Create YK Scan
    # This step initializes the YK scan, setting its update method to the method we defined in the last step. 
    for link in myLinks:
        MainForm.create_YKScanLink_objects(link)
        #link.myLink.reset_iBERT_engine()
    bprint_loading_time("BizLink iBERT Matplotlib/Figures created")

    MainForm.show_figures()

    sys.exit(app.exec_())

#--------------------------------------------------------------------------------------------------------------------------------------
