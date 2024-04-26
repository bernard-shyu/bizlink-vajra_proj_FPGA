#!/usr/bin/env python3
#------------------------------------------------------------------------------------------
# ### License
#------------------------------------------------------------------------------------------
# Copyright (C) 2022, Xilinx, Inc.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");<br>
# you may not use this file except in compliance with the License.<br><br>
# You may obtain a copy of the License at <a href="http://www.apache.org/licenses/LICENSE-2.0"?>http://www.apache.org/licenses/LICENSE-2.0</a><br><br>
# Unless required by applicable law or agreed to in writing, software<br>
# distributed under the License is distributed on an "AS IS" BASIS,<br>
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.<br>
# See the License for the specific language governing permissions and<br>
# limitations under the License.<br>
#
#------------------------------------------------------------------------------------------
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
# - [External loopback](https://www.samtec.com/kits/optics-fpga/hspce-fmcp/)
# - This example assumes that the device has already been programmed with the example design (ie the debug cores have already been initialized)

#------------------------------------------
"""
export ip="10.20.2.146";     export CS_SERVER_URL="TCP:$ip:3042" HW_SERVER_URL="TCP:$ip:3121"
export HW_PLATFORM="vpk120"; export CREATE_LGROUP=False
export PLOT_1_RESOL_X=900;   export PLOT_1_RESOL_Y=800;  export PLOT_F_RESOL_X=3840;  export PLOT_F_RESOL_Y=2160
export PROG_DEVICE=True;     export PDI_FILE="./VPK120_iBERT_2xQDD_56G.pdi"
export SHOW_FIG_TITLE=True;  export MAX_SLICES=100;
export QUAD_NAME="Quad_202"; export QUAD_CHAN=2;
export APP_DBG_LEVEL=5;
"""

#------------------------------------------------------------------------------------------
# ## 1 - Initialization: Imports
#
# After this step,
# * Required functions and classes are imported
# * Paths to server(s) and files are set correctly
#------------------------------------------------------------------------------------------
import os
from more_itertools import one

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
import sys
import random
import math
import re
import numpy as np

import matplotlib
matplotlib.use("Qt5Agg")      # 表示使用 Qt5
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar

#------------------------------------------------------------------------------------------
# Print levels (default: info)
#--------------------------------
DBG_LEVEL_WIP    = -1   # working in progress, LEVEL to be defined later
DBG_LEVEL_ERR    = 0
DBG_LEVEL_WARN   = 1
DBG_LEVEL_NOTICE = 2
DBG_LEVEL_INFO   = 3
DBG_LEVEL_DEBUG  = 4
DBG_LEVEL_TRACE  = 5
APP_DBG_LEVEL    = int(os.getenv("APP_DBG_LEVEL", "3"))
#--------------------------------
def BPrint(*args, level=DBG_LEVEL_INFO):
    if level <= APP_DBG_LEVEL:
        print(*args)

#------------------------------------------------------------------------------------------
# ## 2 - Create a session and connect to the hw_server and cs_server
#
# The session is a container that keeps track of devices and debug cores.
# After this step,
# - Session is initialized and connected to server(s)
# - Versions are detected and reported to stdout

# %%
# Specify locations of the running hw_server and cs_server below.
#------------------------------------------------------------------------------------------

PLOT_1_RESOL_X = int(os.getenv("PLOT_1_RESOL_X", "900"))
PLOT_1_RESOL_Y = int(os.getenv("PLOT_1_RESOL_Y", "800"))
PLOT_F_RESOL_X = int(os.getenv("PLOT_F_RESOL_X", "3200"))
PLOT_F_RESOL_Y = int(os.getenv("PLOT_F_RESOL_Y", "1900"))

QUAD_NAME    =     os.getenv("QUAD_NAME", "Quad_202")
QUAD_CHAN    = int(os.getenv("QUAD_CHAN", "0"))

CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")

# specify hw and if programming is desired
HW_PLATFORM = os.getenv("HW_PLATFORM", "vpk120")
PROG_DEVICE = os.getenv("PROG_DEVICE", 'True').lower() in ('true', '1', 't')
CREATE_LGROUP = os.getenv("CREATE_LGROUP", 'True').lower() in ('true', '1', 't')

MAX_SLICES   = int(os.getenv("MAX_SLICES", "200"))
SHOW_FIG_TITLE = os.getenv("SHOW_FIG_TITLE", 'False').lower() in ('true', '1', 't')

# The get_design_files() function tries to find the PDI and LTX files. In non-standard
# configurations, you can put the path for PROGRAMMING_FILE and PROBES_FILE below.
design_files = get_design_files(f"{HW_PLATFORM}/production/chipscopy_ced")
PDI_FILE = design_files.programming_file
PDI_FILE = os.getenv("PDI_FILE", "./VPK120_iBERT_2xQDD_56G.pdi")

BPrint(f"PROGRAMMING_FILE: {PDI_FILE}", level=DBG_LEVEL_NOTICE)
BPrint(f"Servers URL: {CS_URL} {HW_URL} HW: {HW_PLATFORM}  Do_Programming: {PROG_DEVICE}\n", level=DBG_LEVEL_NOTICE)

session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
if DBG_LEVEL_INFO <= APP_DBG_LEVEL:
    report_versions(session)

# %% [markdown]
# ## 3 - Program the device with the example design
# After this step,
# * Device is programmed with the example programming file

# %%
# Typical case - one device on the board - get it.
device = session.devices.filter_by(family="versal").get()
if PROG_DEVICE:
    device.program(PDI_FILE)
else:
    BPrint("skipping programming", level=DBG_LEVEL_NOTICE)

# %% [markdown]
# ## 4 - Discover and setup the IBERT core
#
# Debug core discovery initializes the chipscope server debug cores.
#
# After this step,
#
# - The cs_server is initialized and ready for use
# - The first ibert found is used

# %%
# # Set any params as needed
# params_to_set = {"IBERT.internal_mode": True}
# session.set_param(params_to_set)
#device = session.devices.filter_by(family="versal").get()

# Use the first available device and set up its debug cores

BPrint(f"Discovering debug cores...", level=DBG_LEVEL_NOTICE)
device.discover_and_setup_cores(ibert_scan=True)

if len(device.ibert_cores) == 0:
    BPrint("No IBERT core found! Exiting...", level=DBG_LEVEL_ERR)
    exit()

# %% [markdown]
# ## 5 - Print the hierarchy of the IBERT core
# We also ensure that all the quads instantiated by the ChipScoPy CED design are found by the APIs

# %%
# Use the first available IBERT core from the device
BPrint(f"--> Found {[f'{ibert.name} ({ibert.handle})' for ibert in device.ibert_cores]}\n", level=DBG_LEVEL_NOTICE)

ibert_gtm = one(device.ibert_cores.filter_by(name="IBERT Versal GTM"))

if len(ibert_gtm.gt_groups) == 0:
    BPrint("No GT Groups available for use! Exiting...", level=DBG_LEVEL_WARN)
    exit()

# We also ensure that all the quads instantiated by the ChipScoPy CED design are found by the APIs
if DBG_LEVEL_DEBUG <= APP_DBG_LEVEL:
    report_hierarchy(ibert_gtm)
BPrint(f"--> GT Groups available - {ibert_gtm.gt_groups}", level=DBG_LEVEL_NOTICE)
BPrint(f"==> GT Groups available - {[gt_group_obj.name for gt_group_obj in ibert_gtm.gt_groups]}", level=DBG_LEVEL_DEBUG)


#------------------------------------------------------------------------------------------
# The class correlates to chipscopy.api.ibert.link.Link
class FakeYKScanLink():
    def __init__(self, qname, ch):
        self.nID         = 0
        self.status      = "53.109 Gbps"
        self.line_rate   = "53.121 Gbps"
        self.bit_count   = 0
        self.error_count = 0
        self.ber         = random.random() / 1000000
        self.GT_Group    = ibert_gtm.gt_groups.filter_by(name=qname)[0]
        self.channel     = ch
        BPrint(f"--> GT Group channels - {self.GT_Group.gts}", level=DBG_LEVEL_INFO)


class MyYKScanLink():
    def __init__(self, link):
        self.YKName = f"YK-{link.GT_Group.name}[{link.channel}]"
        self.fig = plt.figure(FigureClass=MyYKFigure, layout='constrained', num=self.YKName, figsize=[8,6])   # figsize=[12,10]  dpi=100
        self.fig.init_YK_axes(self.YKName)

        self.link = link
        self.YK   = create_yk_scans(target_objs=link.rx)[0]                # returns: chipscopy.api.ibert.yk_scan.YKScan object
        self.YK.updates_callback = lambda obj: self.yk_scan_updates(obj)
        self.YK_samples_count = 0

        #------------------------------------------------------------------------------
        BPrint(f"{self.YKName}:: TX='{link.tx}'  TX-pll='{link.tx.pll}'  LINK='{link}' ", level=DBG_LEVEL_INFO)
        BPrint(f"{self.YKName}:: RX='{link.rx}'  RX-pll='{link.rx.pll}'  RX-yk_scan='{link.rx.yk_scan}' ", level=DBG_LEVEL_INFO)
        self.update_link()
        self.bprint_link(DBG_LEVEL_INFO)

    def bprint_link(self, level):
        BPrint(f"{self.YKName}:: SELF={self}  LINK='{self.link}' values=({self.ber}, {self.status}, {self.line_rate}, {self.bit_count}, {self.error_count}) ", level)

    def update_link(self):
        self.status      = self.link.status
        self.line_rate   = self.link.line_rate
        self.bit_count   = self.link.bit_count
        self.error_count = self.link.error_count
        self.ber         = self.link.ber                                                                                      # main BER read method: works
        #self.ber1       = self.link.rx.property_for_alias(RX_BER)                                                            # another BER method 1: not working
        #self.ber2       = list(self.link.rx.property.refresh(self.link.rx.property_for_alias[RX_BER]).values())[0]           # another BER method 2: works, almost the same value as <self.link.ber>

    # ## 6 - Define YK Scan Update Method
    def yk_scan_updates(self, obj):
        #------------------------------------------------------------------------------
        # BER by random number simulation: it works
        #------------------------------------------------------------------------------
        ber = random.random() / 1000000
        #self.fig.update_yk_ber(ber)

        #------------------------------------------------------------------------------
        # BER from chipscopy.api.ibert.rx.link for its BER / STAUS ...: NOT work
        #------------------------------------------------------------------------------
        """
        # self.count += 1; if self.count % 64 == 0: self.update_link()
        self.update_link()
        self.fig.update_yk_ber(self.ber)
        """

        #------------------------------------
        self.YK_samples_count +=1      #  ==> len(obj.scan_data) - 1
        self.fig.update_yk_scan(obj, self)

    def yk_link_updates(self):
        self.update_link()
        self.bprint_link(DBG_LEVEL_TRACE)
        self.fig.update_yk_ber(self)

#------------------------------------------
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
        self.axis_X_OFFSET = 0
        self.YKSCAN_SLICER_SIZE = 2000
        X_max = MAX_SLICES * self.YKSCAN_SLICER_SIZE 

        # Initialize circular buffer
        self.YKScan_slicer_buf = np.zeros((0, self.YKSCAN_SLICER_SIZE))  # Assuming 2D data (x, y)
        self.scatter_X_data  = np.linspace( 0, X_max - 1, X_max )

        # Each figure corresponds to a QUAD channel
        self.fig_name = fig_name
        self.suptitle(fig_name)

        # axis of EYE diagram
        self.ax_EYE = plt.subplot2grid((3,2), (0,0), rowspan=2)
        self.ax_EYE.set_xlabel("ES Sample")
        self.ax_EYE.set_ylabel("Amplitude (%)")
        self.ax_EYE.set_xlim(0, MAX_SLICES * self.YKSCAN_SLICER_SIZE)
        self.ax_EYE.set_ylim(0,100)
        self.ax_EYE.set_yticks(range(0, 100, 20))
        if SHOW_FIG_TITLE: self.ax_EYE.set_title("Slicer eye")
        else:              self.ax_EYE.set_xlabel("EYE")

        # Set custom x-axis labels (divide by 2000)
        scatter_X_ticks  = self.scatter_X_data[0::int(X_max/5)]
        scatter_X_labels = [f"{x/self.YKSCAN_SLICER_SIZE:.0f}" for x in scatter_X_ticks]
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
    def update_yk_scan(self, obj, myYK):

        assert self.YKSCAN_SLICER_SIZE == len(obj.scan_data[-1].slicer)

        # Update the circular buffer with new data.
        self.YKScan_slicer_buf = np.append(self.YKScan_slicer_buf, [list(obj.scan_data[-1].slicer)], axis=0)          # append new data
        if self.YKScan_slicer_buf.shape[0] > MAX_SLICES:
            self.YKScan_slicer_buf = np.delete(self.YKScan_slicer_buf, 0, axis=0)                                     # remove oldest slice data
            obj.scan_data.pop(0)
        else:
            self.axis_X_OFFSET += self.YKSCAN_SLICER_SIZE

        # Update the scatter plot with data from the buffer.
        self.scatter_plot_EYE.set_offsets(np.column_stack((self.scatter_X_data[0:self.axis_X_OFFSET], self.YKScan_slicer_buf.flatten())))  # Set new data points

        BPrint("{}: samples#{:5d}  SHAPE: {} / {}   \t\tDATA: ({:.1f}, {:.1f}, {:.1f}, {:.1f})".format( self.fig_name,
           myYK.YK_samples_count, self.scatter_X_data[0:self.axis_X_OFFSET].shape, self.YKScan_slicer_buf.shape,
           obj.scan_data[-1].slicer[-1], obj.scan_data[-1].slicer[-2], obj.scan_data[-1].slicer[-3], obj.scan_data[-1].slicer[-4]), level=DBG_LEVEL_TRACE)
        #self.ax_EYE.set_xlabel("ES Sample ({}): ({:.1f}, {:.1f}, {:.1f})".format(myYK.YK_samples_count, obj.scan_data[-1].slicer[-1], obj.scan_data[-1].slicer[-2], obj.scan_data[-1].slicer[-3]))

        if self.ax_HIST.lines:
            for line2 in self.ax_HIST.lines:
                self.ax_HIST.set_xlim(0, self.ax_HIST.get_xlim()[1] + self.YKSCAN_SLICER_SIZE)
                line2.set_xdata(list(line2.get_xdata()) + list(range(len(line2.get_xdata()), len(line2.get_xdata()) + self.YKSCAN_SLICER_SIZE)))
                line2.set_ydata(list(line2.get_ydata()) + list(obj.scan_data[-1].slicer))
        else:
            #self.ax_HIST.cla()
            #color: blue / green / teal / brown / charcoal / black / gray / silver / cyan / violet
            self.ax_HIST.hist(list(obj.scan_data[-1].slicer), 50, orientation = 'horizontal', color='cyan', stacked=True, range=(0,100))

        myYK.snr =  obj.scan_data[-1].snr
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
                if myYK.YK_samples_count  > self.ax_BER.get_xlim()[1]:
                    self.ax_BER.set_xlim(0, myYK.YK_samples_count+10)
                line4.set_xdata(list(line4.get_xdata()) + [myYK.YK_samples_count])
                line4.set_ydata(list(line4.get_ydata()) + [math.log10(myYK.ber)])
                #self.ax_BER.set_xlabel(f"BER Sample: {myYK.ber:.3E}")
        else:
            self.ax_BER.plot(myYK.YK_samples_count, math.log10(myYK.ber), color='violet')


#------------------------------------------
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, ykobj=None, nID=0):
        super().__init__(ykobj.fig)
        self.setParent(parent)
        self.ykobj = ykobj
        self.nID   = nID
        self.updateTable = parent.updateTable

        # Setup a timer to trigger the redraw by calling update_plot.
        self.timer = QtCore.QTimer()
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def update_plot(self):
        self.flush_events()
        self.ykobj.yk_link_updates()
        self.draw_idle()
        self.updateTable( self.nID, 0, str(self.ykobj.YK_samples_count) )
        self.updateTable( self.nID, 3, str(self.ykobj.status) )
        self.updateTable( self.nID, 4, "{}".format(self.ykobj.bit_count) )        # type: string
        self.updateTable( self.nID, 5, "{:d}".format(self.ykobj.error_count) )    # type: int
        self.updateTable( self.nID, 6, "{:.3e}".format(self.ykobj.ber) )          # type: float
        self.updateTable( self.nID, 7, "{:.3f}".format(self.ykobj.snr) )          # type: float
        #self.updateTable( self.nID, ?, str(self.ykobj.line_rate) )
        #BPrint("QTable_TYP: bits={}, err={}, ber={}, snr={}".format(type(self.ykobj.bit_count), type(self.ykobj.error_count), type(self.ykobj.ber), type(self.ykobj.snr)), level=DBG_LEVEL_WIP)
        BPrint("QTable_VAL: bits={}, err={}, ber={}, snr={}".format(     self.ykobj.bit_count,       self.ykobj.error_count,       self.ykobj.ber,       self.ykobj.snr),  level=DBG_LEVEL_WIP)


#------------------------------------------
class MyWidget(QtWidgets.QMainWindow):
    def __init__(self, n_links):
        super().__init__()
        self.setWindowTitle('BizLink HPC Cable Test')

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
            c.ykobj.YK.stop() # Stops the YK scan from running.
        BPrint("Closed YK-Scan", level=DBG_LEVEL_NOTICE)
        event.accept()  # Close the widget
        BPrint("Closed Widget", level=DBG_LEVEL_NOTICE)

    def show_figures(self): 
        for c in self.canvases:
            #c.draw()
            c.ykobj.yk_link_updates()
            c.ykobj.YK.start()
        self.show()

    def createTable(self): 
        self.tableWidget = QtWidgets.QTableWidget(self.n_links, 10) 

        # Table will fit the screen horizontally 
        self.tableWidget.setHorizontalHeaderLabels( ("Samples", "TX", "RX", "Status", "Bits", "Errors", "BER", "SNR", "NA", "NA") )
        self.tableWidget.horizontalHeader().setStretchLastSection(True) 
        self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

    def updateTable(self, row, col, val): 
        BPrint(f"QTable: ({row},{col}) <= {val}", level=DBG_LEVEL_TRACE)
        self.tableWidget.setItem(row, col, QtWidgets.QTableWidgetItem(val)) 

    def create_YKScan_figure(self, link):
        ykobj  = MyYKScanLink(link)
        canvas = MplCanvas(self, ykobj, link.nID)
        self.layout_grid.addWidget(canvas, self.grid_row, self.grid_col)
        self.canvases.append(canvas)
        canvas.draw()

        self.updateTable( link.nID, 1, re.findall(".*(Quad_.*\.[RT]X).*", str(link.tx))[0] )
        self.updateTable( link.nID, 2, re.findall(".*(Quad_.*\.[RT]X).*", str(link.rx))[0] )
        self.updateTable( link.nID, 3, str(link.status) )

        #self.ui2(self.ykobj.fig)
        #ykobj.YK.start()

        self.grid_col += 1
        if  self.grid_col >= self.layout_grid_cols:
            self.grid_col = 0
            self.grid_row += 1

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


#------------------------------------------------------------------------------------------
def create_links_common(RXs, TXs):
    global myLinks

    BPrint(f"Links_TXs: {TXs}", level=DBG_LEVEL_INFO)
    BPrint(f"Links_RXs: {RXs}", level=DBG_LEVEL_INFO)
    myLinks = create_links(txs=TXs, rxs=RXs)

    nID = 0
    dbg_print = True
    for link in myLinks:
        link.nID = nID; nID += 1
        link.gt_name = re.findall(".*(Quad_[0-9]*).*", str(link.rx))[0]
        link.channel = int(re.findall(".*CH_([0-9]*).*", str(link.rx))[0])
        link.GT_Group  = ibert_gtm.gt_groups.filter_by(name=link.gt_name)[0]
        BPrint(f"\n----- {link.name} :: RX={link.rx} TX={link.tx}  GT={link.gt_name} CH={link.channel} -------", level=DBG_LEVEL_INFO)
        _, tx_pattern_report = link.tx.property.report(link.tx.property_for_alias[PATTERN]).popitem()
        _, rx_pattern_report = link.rx.property.report(link.rx.property_for_alias[PATTERN]).popitem()
        _, rx_loopback_report = link.tx.property.report(
            link.rx.property_for_alias[RX_LOOPBACK]
        ).popitem()

        if dbg_print:
            BPrint(f"--> Valid values for TX pattern - {tx_pattern_report['Valid values']}", level=DBG_LEVEL_DEBUG)
            BPrint(f"--> Valid values for RX pattern - {rx_pattern_report['Valid values']}", level=DBG_LEVEL_DEBUG)
            BPrint(f"--> Valid values for RX loopback - {rx_loopback_report['Valid values']}\n", level=DBG_LEVEL_DEBUG)
            BPrint(f"==> link.RX: {link.rx} / {link.rx.parent} RX_NAME={link.rx.name} GT_NAME={link.rx.parent.name} GT_alias={link.rx.parent.aliases} ", level=DBG_LEVEL_DEBUG)
            BPrint(f"==> link.TX: {link.tx} / {link.tx.parent} TX_NAME={link.tx.name} GT_NAME={link.tx.parent.name} GT_alias={link.tx.parent.aliases} ", level=DBG_LEVEL_DEBUG)
            if DBG_LEVEL_TRACE <= APP_DBG_LEVEL:
                link.generate_report()
            dbg_print = False

        props = {link.tx.property_for_alias[PATTERN]: "PRBS 31"}
        link.tx.property.set(**props)
        link.tx.property.commit(list(props.keys()))

        props = {
            link.rx.property_for_alias[PATTERN]: "PRBS 31",
            link.rx.property_for_alias[RX_LOOPBACK]: "Near-End PMA",
        }
        link.rx.property.set(**props)
        link.rx.property.commit(list(props.keys()))
        BPrint(f"\n--> Set both patterns to 'PRBS 31' & loopback to 'Near-End PMA' for {link}", level=DBG_LEVEL_DEBUG)

        assert link.rx.pll.locked and link.tx.pll.locked
        BPrint(f"--> RX and TX PLLs are locked for {link}. Checking for link lock...", level=DBG_LEVEL_DEBUG)
        #assert link.status != "No link"
        BPrint(f"--> {link} Link Status: '{link.status}'", level=DBG_LEVEL_DEBUG)

        #BPrint(f"--> {link} properties:  BER={link.ber}  Count={link.bit_count}", level=DBG_LEVEL_DEBUG)

#------------------------------------------
"""
    Self-looped onnection scheme (TCL_scripts/vpk120_ibert_ChMap_56G.tcl / 112G):
            VPK120 QDD-1 cage <--------+
                                       | QSFP-DD cable
            VPK120 QDD-2 cage <--------+
"""
def create_links_selfLooped():
    global q205, q204, q203, q202
    pass


#------------------------------------------
"""
    Cross-connected connection scheme (TCL_scripts/vpk120_ibert_ChMap2_56G.tcl / 112G):
    
            VPK120 (S/N 111)                             VPK120 (S/N 112)
            QDD-1 cage <-------------------------------> cage QDD-1
                            2x QSFP-DD 400G cables
            QDD-2 cage <-------------------------------> cage QDD-2
"""
def create_links_crossConnected():
    global q202, q203, q204, q205

    RXs = list(); TXs = list();
    for q in (q202, q203):
        for ch in range(4):
            RXs.append(q.gts[ch].rx)
            TXs.append(q.gts[ch].tx)

    for q, ch in ( (q204,0), (q204,2), (q205,0), (q205,2), (q204,1), (q204,3), (q205,1), (q205,3) ):
        RXs.append(q.gts[ch].rx)
        TXs.append(q.gts[ch].tx)

    create_links_common(RXs, TXs)


#------------------------------------------
if CREATE_LGROUP:
    q205 = one(ibert_gtm.gt_groups.filter_by(name="Quad_205"))
    q204 = one(ibert_gtm.gt_groups.filter_by(name="Quad_204"))
    q203 = one(ibert_gtm.gt_groups.filter_by(name="Quad_203"))
    q202 = one(ibert_gtm.gt_groups.filter_by(name="Quad_202"))
    create_links_crossConnected()
else:
    myLinks = [ FakeYKScanLink(QUAD_NAME, QUAD_CHAN) ]

all_lnkgrps = get_all_link_groups()
all_links   = get_all_links()
BPrint(f"\n--> All Link Groups available - {all_lnkgrps}", level=DBG_LEVEL_DEBUG)
BPrint(f"\n--> All Links available - {all_links}", level=DBG_LEVEL_DEBUG)


#------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    MainForm = MyWidget(len(all_links))

    # ## 7 - Create YK Scan
    # This step initializes the YK scan, setting its update method to the method we defined in the last step. 
    for link in myLinks:
        MainForm.create_YKScan_figure(link)

    MainForm.show_figures()

    sys.exit(app.exec_())

#------------------------------------------------------------------------------------------
