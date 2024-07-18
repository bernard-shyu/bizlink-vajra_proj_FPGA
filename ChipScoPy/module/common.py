#======================================================================================================================================
from PyQt5 import QtWidgets, QtCore, QtGui
import numpy as np
import pandas as pd
import argparse, configparser, math, re
import os, sys, time, datetime, threading

#======================================================================================================================================

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
TODAY = f"{app_start_time.date()}"

last_check = app_start_time
def bprint_loading_time(msg, level=DBG_LEVEL_NOTICE):
    global last_check
    now = datetime.datetime.now()
    elapsed1 = (now - app_start_time).seconds
    elapsed2 = (now - last_check).seconds
    last_check = now
    BPrint("\n----------------------------------------------------------------------------------------------------------------------------------------------------------------\n" + \
       f"Application loading time  APP: {app_start_time}   NOW: {now}   ELAPSED:{elapsed1:>4} / {elapsed2:<4}\t THREAD: {threading.current_thread().name}" +  \
       "\n----------------------------------------------------------------------------------------------------------------------------------------------------------------\n\n", level=level)

def sleep_QAppVitalize(n):
    for _ in range(int(n)):
        QtWidgets.QApplication.processEvents()
        time.sleep(1)
    n -= int(n)
    if n > 0:
        QtWidgets.QApplication.processEvents()
        time.sleep(n)
"""
def sleep_QAppVitalize(n):
    for _ in range(int(n * 5 + 0.01)):
        QtWidgets.QApplication.processEvents()
        time.sleep(0.2)     # sleeping precision unit is 0.2 sec
"""

#--------------------------------------------------------------------------------------------------------------------------------------
# https://docs.python.org/3/library/argparse.html,  https://docs.python.org/3/howto/argparse.html
# https://stackoverflow.com/questions/20063/whats-the-best-way-to-parse-command-line-arguments
#--------------------------------------------------------------------------------------------------------------------------------------
ENV_COMMON_HELP="""
export SHOW_FIG_TITLE=True;
export QWIN_TITLE_STYLE='color: red; font-size: 24px; font-weight: bold; background-color: rgba(255, 255, 128, 120);';
export QWIN_GUI_FONTNAME='Times';  export QWIN_GUI_FONTSIZE=12;
"""

SHOW_FIG_TITLE    = os.getenv("SHOW_FIG_TITLE", 'False').lower() in ('true', '1', 't')
QWIN_TITLE_STYLE  = os.getenv("QWIN_TITLE_STYLE", 'color: blue; font-size: 22px; font-weight: bold; background-color: rgba(255, 255, 128, 120);')
QWIN_GUI_FONTNAME = os.getenv("QWIN_GUI_FONTNAME", 'Arial')     # Arial | Helvetica | Times
QWIN_GUI_FONTSIZE = int(os.getenv("QWIN_GUI_FONTSIZE", '16'))

#--------------------------------------------------------------------------------------------------------------------------------------
def get_parameter(argName, defValue, meta, helpTxt, argType = 'string'):
    if argType  == 'string':
        argVal = os.getenv(f'{argName}', f"{defValue}")
        argVal = config.get('GENERAL_SECTION', argName, fallback=argVal)
        parser.add_argument(f'--{argName}', default=argVal, metavar=meta, help=helpTxt)
    elif argType  == 'int':
        argVal = int(os.getenv(f'{argName}', f"{defValue}"))
        argVal = config.get('GENERAL_SECTION', argName, fallback=argVal)
        parser.add_argument(f'--{argName}', default=argVal, metavar=meta, help=helpTxt, type=int)

def init_argParser(title, help_txt, config_file):
    global parser, config
    parser = argparse.ArgumentParser(description=f"{title} by Bernard Shyu", epilog=(ENV_COMMON_HELP + help_txt) )
    config = configparser.ConfigParser()
    config.read(config_file, encoding="utf-8")
    return parser

def finish_argParser(dbg_SrcName, DEFAULT_A):
    global sysconfig

    get_parameter( "DBG_LEVEL",    "3",         "level",  'debug level (ERR=0 WARN=1 NOTICE=2 INFO=3 DEBUG=4 TRACE=5, default=3)', argType='int' )
    get_parameter( "DBG_SRCNAME",  "",          "name",   f"DataSource name for trace ({dbg_SrcName}), default: ''" )
    get_parameter( "DBG_LVADJ",    "2",         "level",  'For the traced DataSource, the adjustment of debug level escalation, default: 2', argType='int' )
    get_parameter( "DBG_ASYCOUNT", "0",         "count",  'For all DataSources, the initial count of TRACE level async-messages to be shown, default: 0', argType='int' )
    get_parameter( "DBG_SYNCOUNT", "0",         "count",  'For all DataSources, the initial count of TRACE level sync-messages  to be shown, default: 0', argType='int' )
    get_parameter( "RESOLUTION",   "3200x1800", "resol",  'App Window Resolution: 3840x2160 / 3200x1800 / 2600x1400 / 1600x990 / 900x800' )
    get_parameter( "QWIN_OVHEAD",  "80",        "pixel",  'Overhead for Main-Windows, including Windows Title, borders, Tool-bar area.  default: 80', argType='int' )
    get_parameter( "FSM_MAGIC",    DEFAULT_A,   "magic",  f"Special MAGIC formula for performance tuning. Default:  '{DEFAULT_A}'" )
    parser.add_argument('--SIMULATE', action='store_true', help='Whether to SIMULATE by random data or by real data source. default: False')

    sysconfig = parser.parse_args()

    sysconfig.FSM_MAGIC_A = []
    for m in sysconfig.FSM_MAGIC.split():
        sysconfig.FSM_MAGIC_A.append(int(m))

    sysconfig.APP_RESOL_X = int(re.findall("([0-9]+)x[0-9]+", sysconfig.RESOLUTION)[0])
    sysconfig.APP_RESOL_Y = int(re.findall("[0-9]+x([0-9]+)", sysconfig.RESOLUTION)[0])
    return sysconfig

def calculate_plotFigure_size(grid_rows, grid_cols, N_links):
    # height of each table cell, depends on system FONT size
    if   QWIN_GUI_FONTSIZE <= 10: TB_CELL_HEIGHT = 30;  QWIN_OVHEAD = sysconfig.QWIN_OVHEAD
    elif QWIN_GUI_FONTSIZE <= 20: TB_CELL_HEIGHT = 31;  QWIN_OVHEAD = sysconfig.QWIN_OVHEAD + 8
    elif QWIN_GUI_FONTSIZE <= 30: TB_CELL_HEIGHT = 32;  QWIN_OVHEAD = sysconfig.QWIN_OVHEAD + 16
    else:                         TB_CELL_HEIGHT = 33;  QWIN_OVHEAD = sysconfig.QWIN_OVHEAD + 24
    #-------------------------------------------------------------------------------------------
    MATPLOTLIB_DPI  = 100   # density (or dots) per inch, default: 100.0
    sysconfig.FIG_PIXEL_WIDTH  = int((sysconfig.APP_RESOL_X - 10) / grid_cols)
    sysconfig.FIG_PIXEL_HEIGHT = int((sysconfig.APP_RESOL_Y - QWIN_OVHEAD - TB_CELL_HEIGHT * (N_links + 1)) / grid_rows)
    sysconfig.FIG_SIZE_X = sysconfig.FIG_PIXEL_WIDTH  / MATPLOTLIB_DPI
    sysconfig.FIG_SIZE_Y = sysconfig.FIG_PIXEL_HEIGHT / MATPLOTLIB_DPI
    assert sysconfig.FIG_SIZE_Y > 0

def get_configuration(secName, argName, defValue = ""):
    global config
    return config.get(secName, argName, fallback=defValue)

#======================================================================================================================================
def is_float_number(s):
    # print(is_float_number("3.14"))  # Output: True
    # print(is_float_number("abc"))   # Output: False
    return re.match(r'^[-+]?\d*\.\d+$', s) is not None


def is_scientific_number(s):
    # print(is_scientific_number("1.23e5"))  # Output: True
    # print(is_scientific_number("abc"))    # Output: False
    return re.match(r'^[-+]?\d*\.\d+[eE][-+]?\d+$', s) is not None

#======================================================================================================================================
class Base_DataSource(QtCore.QObject):
    WATCHDOG_INTERVAL = 10 * 1000

    def __init__(self, dView):
        super().__init__()
        if not dView is None:
            self.dsrcName = dView.myName
            self.dataView = dView

        #------------------------------------------------------------------------------
        self.ASYN_samples_count = 0    # YK-Scan samples
        self.SYNC_samples_count = 0    # Channel-Link samples

        #------------------------------------------------------------------------------
        self.fsm_state   = 0
        self.fsm_running = True

        # Setup a timer to trigger the redraw by calling update_plot.
        self.watchdog_timer = QtCore.QTimer()
        self.watchdog_timer.setInterval(self.WATCHDOG_INTERVAL)
        self.watchdog_timer.timeout.connect(self.fsmFunc_watchdog)
        self.watchdog_timer.start()


    def BPrt_HEAD_COMMON(self, HEAD0 = True, HEAD1 = True, HEAD2 = True, ):
        h0 = f"#{self.ASYN_samples_count:<3d}/{self.SYNC_samples_count:<3d} S:{self.fsm_state:<2} "  if HEAD0 else ""
        h1 = "t:{:<4d} ".format((datetime.datetime.now() - app_start_time).seconds)                  if HEAD1 else ""
        h2 = f"T:{threading.current_thread().name:<10} "                                             if HEAD2 else ""
        return "{:<18} {}{}{}  ".format(f"{self.dsrcName}:", h0, h1, h2)

    # helper method to trace data for initial counts of traffic
    def BPrt_traceData(self, msgTxt, trType="ASYNC"):
        if trType == "ASYNC":
            lvl = self.dataView.mydbg_INFO  if self.ASYN_samples_count < sysconfig.DBG_ASYCOUNT  else self.dataView.mydbg_TRACE
        elif trType == "SYNC":
            lvl = self.dataView.mydbg_INFO  if self.SYNC_samples_count < sysconfig.DBG_SYNCOUNT  else self.dataView.mydbg_TRACE
        BPrint(msgTxt, level=lvl)

    def __refresh_common_data__(self):
        self.SYNC_samples_count +=1
        self.now         = datetime.datetime.now()
        self.elapsed     = (self.now - app_start_time).seconds

    @QtCore.pyqtSlot()
    def fsmFunc_worker_thread(self):
        INTERVAL = sysconfig.FSM_MAGIC_A[0]/10.0     # DEFAULT: 10
        while self.fsm_running:
            match self.fsm_state:
                case self.fsm_state if self.fsm_state < 10:  # reset && initial fetch
                    lvl = self.dataView.mydbg_INFO
                    if not self.fsmFunc_reset(): 
                        self.fsm_state += 1
                    else:
                        self.fsm_state = 10

                case 10: # main state, main-loop for polling, sporadically fetching or stopping
                    lvl = self.dataView.mydbg_TRACE
                    self.fsmFunc_refresh_plots()

                #case 2: # inital stop
                #case 3: # sporadically fetching
                #case 4: # sporadically stop 
                case _: raise ValueError(f"Not valid BaseDataSource.fsm_state : {self.fsm_state}\n")

            BPrint(self.BPrt_HEAD_COMMON() + f"FSM-WorkerThread.{QtCore.QThread.currentThread()} ", level=lvl)
            sleep_QAppVitalize(INTERVAL)     # QtCore.QTimer.singleShot(2000, lambda:self.fsmFunc_worker_thread())  (REF: https://stackoverflow.com/questions/41545300/equivalent-to-time-sleep-for-a-pyqt-application)

    #----------------------------------------------------------------------------------
    #def start_data(self):             pass    # Abstract method: to start data-source engine, like YK.start()
    #def stop_data(self):              pass    # Abstract method: to stop data-source engine, like YK.stop()
    #def async_update_data(self):      pass    # Abstract method: to update data from ource engine, asynchronously by call-back
    def fsmFunc_watchdog(self):        pass    # Abstract method: long  timer polling function
    def fsmFunc_refresh_plots(self):   pass    # Abstract method: FSM function, polling periodically
    def fsmFunc_reset(self):           pass    # Abstract method: FSM function, resetting initially
    #----------------------------------------------------------------------------------

    def finish_object(self):
        self.fsm_running = False
        self.watchdog_timer.stop()


#======================================================================================================================================
# Data View classes: to present the source data to Matplotlib figures / canvas, and rendering to QT-Windows
#======================================================================================================================================

#----------------------------------------------------------------------------------------------------------------------------
class Base_DataView(QtCore.QObject):
    def __init__(self, name, parent):
        super().__init__()
        self.myArena = parent
        self.myName  = name
        self.updateTable = parent.updateTable

        #------------------------------------------------------------------------------
        if self.myName == sysconfig.DBG_SRCNAME:
            self.mydbg_INFO  = DBG_LEVEL_INFO  - sysconfig.DBG_LVADJ
            self.mydbg_DEBUG = DBG_LEVEL_DEBUG - sysconfig.DBG_LVADJ
            self.mydbg_TRACE = DBG_LEVEL_TRACE - sysconfig.DBG_LVADJ
        else:
            self.mydbg_INFO  = DBG_LEVEL_INFO
            self.mydbg_DEBUG = DBG_LEVEL_DEBUG
            self.mydbg_TRACE = DBG_LEVEL_TRACE

    def setup_worker_thread(self):
        self.worker_thread = QtCore.QThread()
        self.myDataSrc.moveToThread(self.worker_thread)                           # move worker to the worker thread
        self.s_start_FSM_Worker.connect(self.myDataSrc.fsmFunc_worker_thread)
        self.worker_thread.start()                                                # start the thread

