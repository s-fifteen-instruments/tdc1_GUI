# This program is a Graphical User Interface (GUI) for S-Fifteen Instruments'
# TimeStamp unit (TDC1).
# Copyright (C) 2021 Gan Jun Herng.

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#
# See bottom of file for a brief history of version updates.
#


from os import stat
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QMenu, \
    QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QDialog, QRadioButton, QSpinBox, \
    QDoubleSpinBox, QTabWidget, QComboBox, QMessageBox, QGroupBox, QCheckBox
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QSize, QTimer, bin_
import pyqtgraph as pg

import numpy as np
from datetime import datetime
import time

from S15lib.instruments import usb_counter_fpga as tdc1
from S15lib.instruments import serial_connection
import serial

"""[summary]
    This is the GUI for the usb counter TDC1. It processes data from TDC1's three different modes - singles, pairs and timestamp - and displays
    the data in a live-updating graph.

    Usage:
    Live Start button can be used to start the graphing without any logging.
    Select logfile and Start logging buttons are used to log data to a csv file in addition to plotting.
"""


PLT_SAMPLES = 501 # plot samples

class logWorker(QtCore.QObject):
    """[summary]
    Worker object for threading the logging process to ensure the GUI does not freeze up while data is being logged and plotted.

    Args:
        QtCore (QObject): [description]
    """
    # Worker Signals
    data_is_logged = QtCore.pyqtSignal(float, float, tuple, str, list)
    histogram_logged = QtCore.pyqtSignal(dict, int, int)
    coincidences_data_logged = QtCore.pyqtSignal('PyQt_PyObject') # Replace 'PyQt_PyObject' with object?
    thread_finished = QtCore.pyqtSignal('PyQt_PyObject')
    permission_error = QtCore.pyqtSignal('PyQt_PyObject')

    def __init__(self):
        super(logWorker, self).__init__()
        self.active_flag = False
        self.radio_flags = [0,0,0,0] # 0 represents unchecked radio button, 1 for checked
        self.int_time = 1
        self.ch_start = 1
        self.ch_stop = 3
        self.bin_width = 2
        self.bins = 501
        self.offset = 0
        self.runtime = 0
    
    # Connected to MainWindow.logging_requested
    @QtCore.pyqtSlot(float, str, str, bool, str, object, int, int, int, int)
    def log_which_data(self, int_time: float, file_name: str, device_path: str, log_flag: bool, \
        dev_mode: str, tdc1_dev: object, start: int, stop: int, offset: int, bin_width: int):
        self.int_time = int_time
        self.ch_start = start
        self.ch_stop = stop
        self.offset = offset
        self.bin_width = bin_width
        self.active_flag = True
        if dev_mode == 'singles':
            print('initiating singles log...')
            self.log_counts_data(file_name, \
        device_path, log_flag, dev_mode, tdc1_dev)
        elif dev_mode == 'g2':
            print('initiating g2 log...')
            self.log_g2(file_name, device_path, log_flag, dev_mode, \
                tdc1_dev)
        elif dev_mode == 'pairs':
            print('initiating pairs log')
            self.log_coincidences_data(file_name, \
        device_path, log_flag, dev_mode, tdc1_dev)

    def log_counts_data(self, file_name: str, device_path: str, log_flag: bool, \
        dev_mode: str, tdc1_dev: object):
        start = time.time()
        now = start
        # If log file is selected and GUI is running, log to file + display counts
        if log_flag == True and self.active_flag == True:
            try:
                open(file_name)
            except IOError:
                # --- Add functionality to handle empty files --- #
                f = open(file_name, 'w')
                f.write('#time_stamp,counts\n')
            while self.active_flag == True:
                counts = tdc1_dev.get_counts(self.int_time)
                now = time.time()
                self.data_is_logged.emit(start, now, counts, dev_mode, self.radio_flags)
                try:
                    with open(file_name, 'a+') as f:
                        time_data: str = datetime.now().isoformat()
                        data_pairs = '{},{},{},{},{}\n'.format(time_data, *counts)
                        f.write(data_pairs)
                    if self.active_flag == False:
                        break
                except PermissionError:
                    tdc1_dev._com.reset_input_buffer()
                    self.permission_error.emit(tdc1_dev)
                    return
        # Else, plot without logging to file
        elif log_flag == False:
            while self.active_flag == True:
                counts = tdc1_dev.get_counts(self.int_time)
                now = time.time()
                self.data_is_logged.emit(start, now, counts, dev_mode, self.radio_flags)
                if self.active_flag == False:
                    break
        print('terminating singles log.')
        self.thread_finished.emit(tdc1_dev)

    def log_coincidences_data(self, file_name: str, device_path: str, log_flag: bool, \
        dev_mode: str, tdc1_dev: object):
        """[summary]
        Logs the data from TDC1 Timestamp unit when in Coincidences mode. See log_counts_data function for more information.
        """
        start = time.time()
        now = start
        if log_flag == True and self.active_flag == True:
            try:
                open(file_name)
            except IOError:
                # --- Add functionality to handle empty files --- #
                f = open(file_name, 'w')
                f.write('#time_stamp,coincidences\n')
            while self.active_flag == True:
                coincidences = tdc1_dev.get_counts_and_coincidences(self.int_time)
                now = time.time()
                self.data_is_logged.emit(start, now, coincidences, dev_mode, self.radio_flags)
                try:
                    with open(file_name, 'a+') as f:
                        # Organising data into pairs
                        time_data: str = datetime.now().isoformat()
                        data_pairs = '{},{},{},{},{},{},{},{},{}\n'.format(time_data, *coincidences)
                        f.write(data_pairs)
                    if self.active_flag == False:
                        break
                except PermissionError:
                    tdc1_dev._com.reset_input_buffer()
                    self.permission_error.emit(tdc1_dev)
                    return
        elif log_flag == False:
            while self.active_flag == True:
                coincidences = tdc1_dev.get_counts_and_coincidences(self.int_time)
                now = time.time()
                self.data_is_logged.emit(start, now, coincidences, dev_mode, self.radio_flags)
                if self.active_flag == False:
                        break
        print('terminating pairs log.')
        self.thread_finished.emit(tdc1_dev)

    def log_g2(self, file_name: str, device_path: str, log_flag: bool, \
        dev_mode: str, tdc1_dev: object):
        start = time.time()
        now = start
        if log_flag == True and self.active_flag == True:
            try:
                open(file_name)
            except IOError:
                # --- Add functionality to handle empty files --- #
                f = open(file_name, 'w')
                f.write('#time_stamp,g2\n')
            while self.active_flag == True:
                #print(f'calling g2_dict({self.int_time}, START: {self.ch_start}, STOP: {self.ch_stop}, {self.bin_width}, {self.bins}, {self.offset})')
                g2_dict = tdc1_dev.count_g2(t_acq = self.int_time, ch_start = self.ch_start, ch_stop = self.ch_stop, \
                    bin_width = self.bin_width, bins = self.bins, ch_stop_delay = self.offset)
                now = time.time()
                hist = g2_dict['histogram']
                self.histogram_logged.emit(g2_dict, self.bins, self.bin_width)
                try:
                    with open(file_name, 'a+') as f:
                        # Organising data into pairs
                        time_data: str = datetime.now().isoformat()
                        hist_list = hist.tolist()
                        new_hist = [str(element) for element in hist_list]
                        new_hist.insert(0, time_data)
                        data = ','.join(new_hist) + '\n'
                        f.write(data)
                    if self.active_flag == False:
                        break
                except PermissionError:
                    tdc1_dev._com.reset_input_buffer()
                    self.permission_error.emit(tdc1_dev)
                    return
        elif log_flag == False:
            while self.active_flag == True:
                #print(f'calling g2_dict({self.int_time}, START: {self.ch_start}, STOP: {self.ch_stop}, {self.bin_width}, {self.bins}, {self.offset})')
                g2_dict = tdc1_dev.count_g2(t_acq = self.int_time, ch_start = self.ch_start, ch_stop = self.ch_stop, \
                    bin_width = self.bin_width, bins = self.bins, ch_stop_delay = self.offset)
                now = time.time()
                self.histogram_logged.emit(g2_dict, self.bins, self.bin_width)
                #print(f'calling g2_dict({self.int_time}, {self.ch_start}, {self.ch_stop}, {self.bin_width}, {self.bins}')
                if self.active_flag == False:
                        break
        print('terminating g2 log.')
        self.thread_finished.emit(tdc1_dev)
        
        
class MainWindow(QMainWindow):
    """[summary]
    Main window class containing the main window and its associated methods. 
    Args:
        QMainWindow (QObject): See qt documentation for more info.
    """
    # Send logging parameters to worker method
    logging_requested = QtCore.pyqtSignal(float, str, str, bool, str, object, int, int, int, int)
    
    def __init__(self, *args, **kwargs):
        """[summary]
        Function to initialise the Main Window, which will hold all the subsequent widgets to be created.
        """
        super(MainWindow, self).__init__(*args, **kwargs)

        self._tdc1_dev = None  # tdc1 device object
        self._dev_mode = '' # 'singles', 'pairs', 'g2'
        self._dev_path = '' # Device path, eg. 'COM4'
        self._level = '' # 'NIM', 'TTL'
        self._open_ports = []
        self._dev_selected = False
        self.dev_list = []

        self.log_flag = False  # Flag to track if data is being logged to csv file
        self.acq_flag = False # Track if data is being acquired
        self._radio_flags = [0,0,0,0] # Tracking which radio buttons are selected. All 0s by default
        
        self.logger = None # Variable that will hold the logWorker object
        self.logger_thread = None # Variable that will hold the QThread object
        
        self.initUI() # UI is initialised afer the class variables are defined

        self.integration_time = int(self.integrationSpinBox.text())
        self._logfile_name = '' # Track the logfile(csv) being used by GUI
        self._ch_start = int(self.channelsCombobox1.currentText()) # Start channel for g2
        self._ch_stop = int(self.channelsCombobox2.currentText()) # Stop channel for g2
        self.plotSamples = self.samplesSpinbox.value() # Number of data points to plot
        self.offset = self.offsetSpinbox.value()
        self.bin_width = self.resolutionSpinbox.value()
        self._runtime = self.runtimeSpinbox.value() * 60 # Convert to minutes

        # Variables for GUI 'memory'
        self._dev_path_prev = self.devCombobox.currentText()
        self._dev_mode_prev = self.modesCombobox.currentText()
        self._level_prev = self.levelsComboBox.currentText()
        self.integration_time_prev = self.integration_time
        self.plotSamples_prev = self.plotSamples
        self._ch_start_prev = self._ch_start
        self._ch_stop_prev = self._ch_stop
        self.offset_prev = self.offset
        self.bin_width_prev = self.bin_width
        self._runtime_prev = self._runtime

        self._plot_tab = self.tabs.currentIndex()  # Counts graph = 0, Coincidences graph = 1
        self.idx = min(len(self.y1), self.plotSamples)  # Index for plotting
        self._counts_plotted = False
        self._g2_plotted = False
        self._data_plotted = self._counts_plotted or self._g2_plotted
        self.runtimeCheck = self.runtime_Checkbox.isChecked()
        

    def initUI(self):
        """[summary]
        Contains all the UI elements and associated functionalities.
        """
        defaultFont = QtGui.QFont("Helvetica", 14)
        
        #---------Buttons---------#
        #self.scanForDevice_Button = QtWidgets.QPushButton("Scan for Device", self)
        #elf.scanForDevice_Button.clicked.connect(self.updateDevList)
        #self.scanForDevice_Button.setFixedSize(QSize(115, 35))

        self.liveStart_Button = QtWidgets.QPushButton("Live Start", self)
        self.liveStart_Button.clicked.connect(self.liveStart)
        self.liveStart_Button.setEnabled(False)

        self.selectLogfile_Button = QtWidgets.QPushButton("Select Logfile", self)
        self.selectLogfile_Button.clicked.connect(self.selectLogfile)
        self.selectLogfile_Button.setEnabled(False)

        # setAutoExclusive method is used to toggle the radio buttons independently.
        self.radio1_Button = QRadioButton("Channel 1", self)
        self.radio1_Button.setStyleSheet('color: red; font-size: 14px')
        self.radio1_Button.setAutoExclusive(False)
        self.radio1_Button.toggled.connect(lambda: self.displayPlot1(self.radio1_Button))
        #self.radio1_Button.setEnabled(False)
        self.radio2_Button = QRadioButton("Channel 2", self)
        self.radio2_Button.setStyleSheet('color: green; font-size: 14px')
        self.radio2_Button.setAutoExclusive(False)
        self.radio2_Button.toggled.connect(lambda: self.displayPlot2(self.radio2_Button))
        #self.radio2_Button.setEnabled(False)
        self.radio3_Button = QRadioButton("Channel 3", self)
        self.radio3_Button.setStyleSheet('color: blue; font-size: 14px')
        self.radio3_Button.setAutoExclusive(False)
        self.radio3_Button.toggled.connect(lambda: self.displayPlot3(self.radio3_Button))
        #self.radio3_Button.setEnabled(False)
        self.radio4_Button = QRadioButton("Channel 4", self)
        self.radio4_Button.setStyleSheet('color: black; font-size: 14px')
        self.radio4_Button.setAutoExclusive(False)
        self.radio4_Button.toggled.connect(lambda: self.displayPlot4(self.radio4_Button))
        #self.radio4_Button.setEnabled(False)

        self.runtime_Checkbox = QCheckBox("Timer?")
        #self.runtime_Checkbox.stateChanged.connect(self.updateRuntimeSelection)

        self.clearCountsDataData_Button = QtWidgets.QPushButton("Clear Data", self)
        self.clearCountsDataData_Button.clicked.connect(self.clearCountsDataData)

        self.clearg2DataData_Button = QtWidgets.QPushButton("Clear Data", self)
        self.clearg2DataData_Button.clicked.connect(self.clearg2DataData)

        #---------Buttons---------#


        #---------Labels---------#
        #labelFontSize = "font-size: 18px"
        
        self.deviceLabel = QtWidgets.QLabel("Device:", self)
        self.deviceModeLabel = QtWidgets.QLabel("GUI Mode:", self)

        self.samplesLabel = QtWidgets.QLabel('Plot Samples:', self)
        self.integrationLabel = QtWidgets.QLabel("Integration time (ms):", self)

        self.logfileText = QtWidgets.QTextEdit('', self)
        self.logfileText.setReadOnly(True)

        self.Ch1CountsLabel = QtWidgets.QLabel("0", self)
        self.Ch1CountsLabel.setStyleSheet("color: red; font-size: 108px")
        self.Ch1CountsLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.Ch2CountsLabel = QtWidgets.QLabel("0", self)
        self.Ch2CountsLabel.setStyleSheet("color: green; font-size: 108px")
        self.Ch2CountsLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.Ch3CountsLabel = QtWidgets.QLabel("0", self)
        self.Ch3CountsLabel.setStyleSheet("color: blue; font-size: 108px")
        self.Ch3CountsLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.Ch4CountsLabel = QtWidgets.QLabel("0", self)
        self.Ch4CountsLabel.setStyleSheet("color: black; font-size: 108px")
        self.Ch4CountsLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.startChannelLabel = QtWidgets.QLabel("Start Channel:", self)
        self.stopChannelLabel = QtWidgets.QLabel("Stop Channel:", self)
        self.offsetLabel = QtWidgets.QLabel("Stop Ch Offset:", self)
        self.g2RateLabel = QtWidgets.QLabel("Total Pairs: <br>" + "0")
        self.g2RateLabel.setStyleSheet("font-size: 64px")
        self.g2RateLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.resolutionTextLabel = QtWidgets.QLabel("Bin Width:", self)

        self.runtimeLabel = QtWidgets.QLabel("Total Runtime (mins):", self)
        self.countdownLabel = QtWidgets.QLabel("00:00:00", self)
        self.countdownLabel.setStyleSheet("color: gray; font-size: 24px")

        self.levelsLabel = QtWidgets.QLabel("NIM/TTL:",self)
        #---------Labels---------#


        #---------Interactive Fields---------#
        self.integrationSpinBox = QSpinBox(self)
        self.integrationSpinBox.setRange(0, 65535)  # Max integration time based on tdc1 specs
        self.integrationSpinBox.setValue(1000) # Default 1000ms = 1s
        self.integrationSpinBox.setKeyboardTracking(False) # Makes sure valueChanged signal only fires when you want it to
        self.integrationSpinBox.valueChanged.connect(self.update_intTime)
        self.integrationSpinBox.setEnabled(False)

        self.dev_list = serial_connection.search_for_serial_devices(
            tdc1.TimeStampTDC1.DEVICE_IDENTIFIER)
        try:
            self.dev_list = serial_connection.search_for_serial_devices(tdc1.TimeStampTDC1.DEVICE_IDENTIFIER)
        except:
            pass
        self.devCombobox = QComboBox(self)
        self.devCombobox.addItem('Select your device')
        self.devCombobox.addItems(self.dev_list)
        self.devCombobox.currentTextChanged.connect(self.selectDevice)

        _dev_modes = ['singles', 'pairs', 'g2']
        self.modesCombobox = QComboBox(self)
        self.modesCombobox.addItem('Select mode')
        self.modesCombobox.addItems(_dev_modes)
        self.modesCombobox.currentTextChanged.connect(self.updateDeviceMode)
        self.modesCombobox.setEnabled(False)

        _channels = ['1', '2', '3', '4']
        self.channelsCombobox1 = QComboBox(self)
        self.channelsCombobox1.addItem('Select')
        self.channelsCombobox1.addItems(_channels)
        self.channelsCombobox1.setCurrentIndex(1)
        self.channelsCombobox1.currentTextChanged.connect(self.updateStart)
        #self.channelsCombobox1.setEnabled(False)
        self.channelsCombobox2 = QComboBox(self)
        self.channelsCombobox2.addItem('Select')
        self.channelsCombobox2.addItems(_channels)
        self.channelsCombobox2.setCurrentIndex(3)
        self.channelsCombobox2.currentTextChanged.connect(self.updateStop)
        #self.channelsCombobox2.setEnabled(False)

        self.samplesSpinbox = QSpinBox(self)
        self.samplesSpinbox.setRange(0, 65535)
        self.samplesSpinbox.setValue(501) # Default plot 501 data points
        self.samplesSpinbox.setKeyboardTracking(False)
        self.samplesSpinbox.valueChanged.connect(self.updateBins)
        self.samplesSpinbox.setEnabled(False)

        self.offsetSpinbox = QSpinBox(self)
        self.offsetSpinbox.setRange(-10, 65535)
        self.offsetSpinbox.setKeyboardTracking(False)
        #self.offsetSpinbox.setEnabled(False)
        self.offsetSpinbox.valueChanged.connect(self.updateOffset)

        self.resolutionSpinbox = QSpinBox(self)
        self.resolutionSpinbox.setRange(0, 1000)
        self.resolutionSpinbox.setKeyboardTracking(False)
        self.resolutionSpinbox.setValue(2) # Default 2 ns bin width
        self.resolutionSpinbox.valueChanged.connect(self.updateBinwidth)
        #self.resolutionSpinbox.setEnabled(False)

        self.runtimeSpinbox = QSpinBox(self)
        self.runtimeSpinbox.setRange(0, 65535)
        self.runtimeSpinbox.setKeyboardTracking(False)
        self.runtimeSpinbox.setValue(5) # Default 5 mins
        self.runtimeSpinbox.valueChanged.connect(self.updateRuntime)
        self.runtimeSpinbox.setEnabled(False)

        _levels = ['NIM (-0.5V)', 'TTL (+1.6V)']
        self.levelsComboBox = QComboBox(self)
        self.channelsCombobox2.addItem('Select')
        self.levelsComboBox.addItems(_levels)
        self.levelsComboBox.currentTextChanged.connect(self.updateLevel)
        self.levelsComboBox.setEnabled(False)
        #---------Interactive Fields---------#


        #---------PLOTS---------#
        # Initiating plot data variables
        # Plot 1 - Four channel counts plot
        self.x = []
        self.y1 = []
        self.y2 = []
        self.y3 = []
        self.y4 = []
        self.y_data = [self.y1, self.y2, self.y3, self.y4]

        # Plot 2 - Time difference histogram (Channel cross-correlation)
        self.bins = 501
        self.binsize = 2 # nanoseconds
        self.x0 = np.arange(0, self.bins*self.binsize, self.binsize)
        self.y0 = np.zeros_like(self.x0)
        
        font = QtGui.QFont("Arial", 24)     
        labelStyle = '<span style=\"color:black;font-size:25px\">'

        # Setting up plot window 1 (Plot Widget)
        self.tdcPlot = pg.PlotWidget(title = "Counts Graph")
        self.tdcPlot.setBackground('w')
        self.tdcPlot.setLabel('left', labelStyle + 'Counts')
        self.tdcPlot.setLabel('bottom', labelStyle + 'Time (s)')
        self.tdcPlot.getAxis('left').tickFont = font
        self.tdcPlot.getAxis('bottom').tickFont = font
        self.tdcPlot.getAxis('bottom').setPen(color='k')
        self.tdcPlot.getAxis('left').setPen(color='k')
        self.tdcPlot.showGrid(y=True)
        
        # Setting up plot window 2 (Plot Widget)
        self.tdcPlot2 = pg.PlotWidget(title = "Coincidences Histogram")
        self.tdcPlot2.setBackground('w')
        self.tdcPlot2.setLabel('left', labelStyle + 'Coincidences')
        self.tdcPlot2.setLabel('bottom', labelStyle + 'Time Delay (ns)')
        self.tdcPlot2.getAxis('left').tickFont = font
        self.tdcPlot2.getAxis('bottom').tickFont = font
        self.tdcPlot2.getAxis('bottom').setPen(color='k')
        self.tdcPlot2.getAxis('left').setPen(color='k')
        self.tdcPlot2.showGrid(y=True)

        # Setting up data plots (Plot data item)
        self.lineStyle1 = pg.mkPen(width=2, color='r') # Red
        self.lineStyle2 = pg.mkPen(width=2, color='g') # Green
        self.lineStyle3 = pg.mkPen(width=2, color='b') # Blue
        self.lineStyle4 = pg.mkPen(width=2, color='k') # Black
        self.lineStyle0 = pg.mkPen(width=1, color='r')

        # Plotting the graph - https://pyqtgraph.readthedocs.io/en/latest/plotting.html for organisation of plotting classes
        # Take note: multiple plotDataItems can sit on one plotWidget
        self.linePlot1 = self.tdcPlot.plot(self.x, self.y1, pen=self.lineStyle1)
        self.linePlot2 = self.tdcPlot.plot(self.x, self.y2, pen=self.lineStyle2)
        self.linePlot3 = self.tdcPlot.plot(self.x, self.y3, pen=self.lineStyle3)
        self.linePlot4 = self.tdcPlot.plot(self.x, self.y4, pen=self.lineStyle4)
        self.histogramPlot = self.tdcPlot2.plot(self.x0, self.y0, pen=self.lineStyle0, symbol = 'x', symbolPen = 'b', symbolBrush = 0.2)
        self.linePlots = [self.linePlot1, self.linePlot2, self.linePlot3, self.linePlot4]
        #---------PLOTS---------#

        # Timer
        self.timer = QtCore.QTimer()

        #---------Main Window---------#
        self.setWindowTitle("TDC-1")
        self.move(0, 0)
        #self.setWindowState(QtCore.Qt.WindowMaximized)
        #---------Main Window---------#


        #---------Tabs---------#
        self.tabs = QTabWidget()

        self.tab1 = QWidget()
        self.layout = QGridLayout()
        self.layout.addWidget(self.tdcPlot, 0, 0, 5, 5)
        self.layout.addWidget(self.Ch1CountsLabel, 0, 5)
        self.layout.addWidget(self.Ch2CountsLabel, 1, 5)
        self.layout.addWidget(self.Ch3CountsLabel, 2, 5)
        self.layout.addWidget(self.Ch4CountsLabel, 3, 5)
        self.layout.addWidget(self.clearCountsDataData_Button, 4, 5)
        self.tab1.setLayout(self.layout)
        self.tabs.addTab(self.tab1, "Counts")

        self.tab2 = QWidget()
        self.layout2 = QGridLayout()
        self.layout2.addWidget(self.tdcPlot2, 0, 0, 5, 5)
        self.layout2.addWidget(self.g2RateLabel, 0, 5)
        self.layout2.addWidget(self.clearg2DataData_Button, 4, 5)
        self.tab2.setLayout(self.layout2)
        self.tabs.addTab(self.tab2, "g2")
        self.tabs.currentChanged.connect(self.update_plot_tab)
        #---------Tabs---------#

        #Layout
        self.grid = QGridLayout()
        self.grid.setSpacing(20)
        self.grid.addWidget(self.deviceLabel, 0, 0)
        self.grid.addWidget(self.devCombobox, 0, 1)
        self.grid.addWidget(self.deviceModeLabel, 0, 2)
        self.grid.addWidget(self.modesCombobox, 0, 3, 1, 1)
        self.grid.addWidget(self.runtimeLabel, 0, 4, 1, 1)
        self.grid.addWidget(self.runtimeSpinbox, 0, 5, 1, 1)
        self.grid.addWidget(self.integrationLabel, 1, 0)
        self.grid.addWidget(self.integrationSpinBox, 1, 1)
        self.grid.addWidget(self.levelsLabel, 1, 2)
        self.grid.addWidget(self.levelsComboBox, 1, 3, 1, 1)
        self.grid.addWidget(self.runtime_Checkbox, 1, 4, 1, 1)
        self.grid.addWidget(self.countdownLabel, 1, 5, 1, 1)
        self.grid.addWidget(self.liveStart_Button, 2, 0)
        self.grid.addWidget(self.selectLogfile_Button, 2, 2)
        self.grid.addWidget(self.logfileText, 2, 3)
        self.grid.addWidget(self.tabs, 4, 0, 5, 6)
        
        self.countsGroupbox = QGroupBox('Counts')
        self.singlesLayout = QHBoxLayout()
        self.singlesLayout.addWidget(self.radio1_Button)
        self.singlesLayout.addWidget(self.radio2_Button)
        self.singlesLayout.addWidget(self.radio3_Button)
        self.singlesLayout.addWidget(self.radio4_Button)
        self.countsGroupbox.setLayout(self.singlesLayout)
        self.grid.addWidget(self.countsGroupbox, 3, 0, 1, 2)

        self.g2Groupbox = QGroupBox('g2')
        self.g2SpinLayout = QHBoxLayout()
        self.g2SpinLayout.addWidget(self.startChannelLabel)
        self.g2SpinLayout.addWidget(self.channelsCombobox1)
        self.g2SpinLayout.addWidget(self.stopChannelLabel)
        self.g2SpinLayout.addWidget(self.channelsCombobox2)
        #self.g2LabelLayout = QHBoxLayout()
        self.g2CenterLayout = QHBoxLayout()
        self.g2CenterLayout.addWidget(self.offsetLabel)
        self.g2CenterLayout.addWidget(self.offsetSpinbox)
        self.g2CenterLayout.addWidget(self.resolutionTextLabel)
        self.g2CenterLayout.addWidget(self.resolutionSpinbox)
        self.g2Layout = QVBoxLayout()
        #self.g2Layout.addLayout(self.g2LabelLayout)
        self.g2Layout.addLayout(self.g2SpinLayout)
        self.g2Layout.addLayout(self.g2CenterLayout)
        self.g2Groupbox.setLayout(self.g2Layout)
        self.grid.addWidget(self.g2Groupbox, 3, 2, 1, 2)

        self.grid.addWidget(self.samplesLabel, 3, 4)
        self.grid.addWidget(self.samplesSpinbox, 3, 5)

        #Main Widget (on which the grid is to be implanted)
        self.mainwidget = QWidget()
        self.mainwidget.layout = self.grid
        self.mainwidget.setLayout(self.mainwidget.layout)
        self.mainwidget.setFont(defaultFont)
        self.setCentralWidget(self.mainwidget)


    # Connected to devComboBox.currentTextChanged
    @QtCore.pyqtSlot(str)
    def selectDevice(self, devPath: str):
        if devPath == 'Select your device':
            return
        if self.acq_flag == False:
            self.StrongResetInternalVariables()
            self.resetGUIelements()
            print('Creating TDC1 object.')
            self._tdc1_dev = tdc1.TimeStampTDC1(devPath)
            self._dev_path = devPath
            check = self._tdc1_dev._device_path
            print(f'Device connected at {check}')
            self.enableDevOptions()
            self._dev_selected = True
        elif self.acq_flag == True:
            msgBox = QtWidgets.QMessageBox()
            msgBox.setIcon(QtWidgets.QMessageBox.Information)
            msgBox.setText('Data is currently being collected. Please hit Live Stop button before attempting to change to new device.')
            msgBox.setWindowTitle('Error Selecting Device')
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            self.modesCombobox.setCurrentText(self._dev_mode_prev)

    @QtCore.pyqtSlot()
    def updateDevList(self):
        self.devCombobox.clear()
        self.devCombobox.addItem('Select your device')
        devices = serial_connection.search_for_serial_devices(tdc1.TimeStampTDC1.DEVICE_IDENTIFIER)
        try:
            serial_connection.search_for_serial_devices(tdc1.TimeStampTDC1.DEVICE_IDENTIFIER)
        except:
            pass
        self.devCombobox.addItems(devices)

    # Connected to modesCombobox.currentTextChanged
    @QtCore.pyqtSlot(str)
    def updateDeviceMode(self, newMode: str):
        if newMode == 'Select mode': # If user selects default text
            pass
        elif self._dev_selected == True and self.acq_flag == False and self._data_plotted == True: # Device inactive, data acq not underway, and no data is plotted
            msgBox = QtWidgets.QMessageBox()
            msgBox.setIcon(QtWidgets.QMessageBox.Information)
            msgBox.setText('Any data unsaved to a Logfile will be lost upon changing device mode. Are you sure?')
            msgBox.setWindowTitle('Confirm Device Mode Change')
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            returnValue = msgBox.exec()
            if returnValue == QMessageBox.Ok:
                self.deleteWorkerAndThread()
                self.selectLogfile_Button.setText('Select Logfile')
                self.logfileText.setText('')
                self.log_flag = False
                self.acq_flag = False
                if self._tdc1_dev == None:
                    self._tdc1_dev = tdc1.TimeStampTDC1(self._dev_path)
                if newMode == 'g2':
                    self._tdc1_dev.mode = 'timestamp'
                    self.samplesSpinbox.setEnabled(True)
                else:
                    self._tdc1_dev.mode = newMode # Setting tdc1 mode with @setter
                self._dev_mode = newMode
                print(f'Device at {self._dev_path} is now in {self._dev_mode} mode')
                if newMode == 'singles':
                    self.samplesSpinbox.setEnabled(False)
                if newMode == 'pairs':
                    self.samplesSpinbox.setEnabled(True)
            elif returnValue == QMessageBox.Cancel:
                self.modesCombobox.setCurrentText(self._dev_mode_prev)
        elif self._dev_selected == True and self.acq_flag == False and self._data_plotted == False:
            if self._tdc1_dev == None:
                    self._tdc1_dev = tdc1.TimeStampTDC1(self._dev_path)
            if newMode == 'g2':
                self._tdc1_dev.mode = 'timestamp'
                self.samplesSpinbox.setEnabled(True)
            else:
                self._tdc1_dev.mode = newMode
            self._dev_mode = newMode
            print(f'Device at {self._dev_path} is now in {self._dev_mode} mode')
            if newMode == 'singles':
                    self.samplesSpinbox.setEnabled(False)
            if newMode == 'pairs':
                self.samplesSpinbox.setEnabled(True)
        elif self._dev_selected == False:
            print('Please select a device first')
        
    @QtCore.pyqtSlot('PyQt_PyObject')
    def closethreads_ports_timers(self, dev):
        # if dev._com.isOpen():
        #     dev._com.close()
        # self.logger = None # Destroy logger
        # self.logger_thread = None # and thread...?
        # self._tdc1_dev = None # Destroy tdc1_dev object
        self.stopTimer()
        self.acq_flag = False
        self.modesCombobox.setEnabled(True)
        self.levelsComboBox.setEnabled(True)
        self.devCombobox.setEnabled(True)
        self.runtimeSpinbox.setEnabled(True)
        self.runtime_Checkbox.setEnabled(True)
        self.selectLogfile_Button.setEnabled(True)
        self.liveStart_Button.setText("Live Start")

    @QtCore.pyqtSlot('PyQt_PyObject')
    def logfile_permission_error_reset(self, dev):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(QtWidgets.QMessageBox.Critical)
        msgBox.setText('Ensure logfile is not open in another program.')
        msgBox.setWindowTitle('Permission Error')
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec()
        # if dev._com.isOpen():
        #     dev._com.close()
        # self.logger = None # Destroy logger
        # self.logger_thread = None # and thread...?
        # self._tdc1_dev = None # Destroy tdc1_dev object
        self.stopTimer()
        self.acq_flag = False
        self.modesCombobox.setEnabled(True)
        self.levelsComboBox.setEnabled(True)
        self.devCombobox.setEnabled(True)
        self.runtimeSpinbox.setEnabled(True)
        self.runtime_Checkbox.setEnabled(True)
        self.selectLogfile_Button.setEnabled(True)
        self.liveStart_Button.setText("Live Start")

    # Update plot index on plot tab change
    @QtCore.pyqtSlot()
    def update_plot_tab(self):
        self._plot_tab = self.tabs.currentIndex()

    # Update integration time on spinbox value change
    @QtCore.pyqtSlot(int)
    def update_intTime(self, int_time: int):
        self.integration_time = int_time * 1e-3
        if self.logger:
            self.logger.int_time = int_time * 1e-3

    @QtCore.pyqtSlot(int)
    def updateBins(self, bins: int):
        self.bins = bins
        if self.logger:
            self.logger.bins = bins

    @QtCore.pyqtSlot(int)
    def updateOffset(self, offset: int):
        self.offset = offset
        if self.logger:
            self.logger.offset = offset

    # Click Live Start button to get started!
    @QtCore.pyqtSlot()
    # Connected to self.liveStart_button.clicked
    def liveStart(self):
        """[summary] Performs start/stop functions depending on button state and internal flags. This function is called when
           self.liveStart_button is clicked. Sets all the GUI elements to the right states (hopefully) before issuing a startLogging
           command which starts the actual data collection.
        """
        if self.modesCombobox.currentText() == "Select mode":
            msgBox = QtWidgets.QMessageBox()
            msgBox.setIcon(QtWidgets.QMessageBox.Information)
            msgBox.setText('Please select a GUI mode.')
            msgBox.setWindowTitle('GUI mode?')
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return
        #If currently live plotting, pressing the button stops plotting
        if self.acq_flag is True and self.liveStart_Button.text() == "Live Stop":
            self.endRun()
            self.modesCombobox.setEnabled(True)
            self.levelsComboBox.setEnabled(True)
            self.devCombobox.setEnabled(True)
            self.runtimeSpinbox.setEnabled(True)
            self.runtime_Checkbox.setEnabled(True)
            self._tdc1_dev._com.reset_input_buffer()
        #If not currently live plotting, pressing the button starts plotting
        elif self.acq_flag is False and self.liveStart_Button.text() == "Live Start":
            self.liveStart_Button.setEnabled(False)
            QtCore.QTimer.singleShot(1000, lambda: self.liveStart_Button.setEnabled(True))
            if self._tdc1_dev == None:
                self._tdc1_dev = tdc1.TimeStampTDC1(self.devCombobox.currentText())
            self.acq_flag = True
            if self._data_plotted == True:
                if self.modesCombobox.currentText() == 'g2' and self._g2_plotted == True:
                    msgBox = QtWidgets.QMessageBox()
                    msgBox.setIcon(QtWidgets.QMessageBox.Information)
                    msgBox.setText('A g2 plot already exists. Clear the old plot and start anew?')
                    msgBox.setWindowTitle('Existing g2 Plot')
                    msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                    returnValue = msgBox.exec()
                    if returnValue == QMessageBox.Ok:
                        self.resetg2Plot()
                    else:
                        return
                elif self.modesCombobox.currentText() == 'singles' and self._counts_plotted == True:
                    msgBox = QtWidgets.QMessageBox()
                    msgBox.setIcon(QtWidgets.QMessageBox.Information)
                    msgBox.setText('A Singles plot already exists. Clear the old plot and start anew?')
                    msgBox.setWindowTitle('Existing Singles Plot')
                    msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                    returnValue = msgBox.exec()
                    if returnValue == QMessageBox.Ok:
                        self.resetCountsPlot()
                    else:
                        return
                elif self.modesCombobox.currentText() == 'pairs' and self._counts_plotted == True:
                    msgBox = QtWidgets.QMessageBox()
                    msgBox.setIcon(QtWidgets.QMessageBox.Information)
                    msgBox.setText('A Pairs plot already exists. Clear the old plot and start anew?')
                    msgBox.setWindowTitle('Existing Pairs Plot')
                    msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                    returnValue = msgBox.exec()
                    if returnValue == QMessageBox.Ok:
                        self.resetCountsPlot()
                    else:
                        return
            self.selectLogfile_Button.setEnabled(False)
            self.modesCombobox.setEnabled(False)
            self.levelsComboBox.setEnabled(False)
            self.devCombobox.setEnabled(False)
            self.runtimeSpinbox.setEnabled(False)
            self.runtime_Checkbox.setEnabled(False)
            if self._dev_mode == 'singles' or self._dev_mode == 'pairs':
                self.enableSinglesOptions()
                self.resetRadioButtons()
            elif self._dev_mode == 'g2':
                self.enableg2Options()
            self.liveStart_Button.setText("Live Stop")
            if self.runtime_Checkbox.isChecked():
                self._runtime = self.runtimeSpinbox.value()*60
                self.startTimer()
            self._tdc1_dev._com.reset_input_buffer()
            self.startLogging()


    # Logging
    def startLogging(self):
        """[summary]
        Creation process of worker object and QThread.
        """
        # Create worker instance and a thread
        self.logger = logWorker()
        self.logger_thread = QtCore.QThread(self) # QThread is not a thread, but a thread MANAGER

        # Assign worker to the thread and start the thread
        self.logger.moveToThread(self.logger_thread)
        self.logger_thread.start() # This is where the thread is actually created, I think

        # Connect signals and slots AFTER moving the object to the thread
        self.logging_requested.connect(self.logger.log_which_data)
        self.logger.data_is_logged.connect(self.update_counts_plot_from_thread)
        self.logger.histogram_logged.connect(self.updateHistogram)
        self.logger.thread_finished.connect(self.closethreads_ports_timers)
        self.logger.permission_error.connect(self.logfile_permission_error_reset)

        self.logger.int_time = int(self.integrationSpinBox.text()) * 1e-3 # Convert to seconds
        #self.log_flag = True
        self.logging_requested.emit(self.integration_time, self._logfile_name, self._dev_path, self.log_flag, self._dev_mode, \
            self._tdc1_dev, self._ch_start, self._ch_stop, self.offset, self.bin_width)
        

    @QtCore.pyqtSlot()
    def selectLogfile(self):
        if self.acq_flag == False:
            if self.selectLogfile_Button.text() == 'Select Logfile':
                default_filetype = 'csv'
                start = datetime.now().strftime("%Y%m%d_%Hh%Mm%Ss ") + "_TDC1." + default_filetype
                self._logfile_name = QtWidgets.QFileDialog.getSaveFileName(
                    self, "Save to log file", start)[0]
                self.logfileText.setText(self._logfile_name)
                if self._logfile_name != '':
                    #self.startLogging_Button.setEnabled(True)
                    self.log_flag = True
                    self.selectLogfile_Button.setText('Unselect Logfile')
            elif self.selectLogfile_Button.text() == 'Unselect Logfile':
                self.logfileText.setText('')
                self._logfile_name = ''
                self.log_flag = False
                self.selectLogfile_Button.setText('Select Logfile')


    # Updating data
    # Connected to data_is_logged signal
    @QtCore.pyqtSlot(float, float, tuple, str, list)
    def update_counts_plot_from_thread(self, start: float, now: float, data: tuple, dev_mode: str, radio_flags: list):
        #print(f'data is {data}')
        next_time = now-start
        if len(self.x) == PLT_SAMPLES:
            # If hit sample limit, throw out 1st data point before adding new one
            self.x = self.x[1:]
            self.x.append(next_time)
            self.y1 = self.y1[1:]; self.y2 = self.y2[1:]; self.y3 = self.y3[1:]; self.y4 = self.y4[1:]
            self.y1.append(data[0]); self.y2.append(data[1]); self.y3.append(data[2]); self.y4.append(data[3])
            self.y_data = [self.y1, self.y2, self.y3, self.y4]
        elif len(self.x) < self.plotSamples:
            # Otherwise, just append new data point
            self.x.append(next_time)
            self.y1.append(data[0]); self.y2.append(data[1]); self.y3.append(data[2]); self.y4.append(data[3])
            self.idx = min(len(self.y1), self.plotSamples)
            self.y1 = self.y1[-self.idx:]; self.y2 = self.y2[-self.idx:]; self.y3 = self.y3[-self.idx:]; self.y4 = self.y4[-self.idx:]
            self.y_data = [self.y1, self.y2, self.y3, self.y4]
            self._radio_flags = radio_flags
        elif len(self.x) > self.plotSamples:
            # If user reduces plot samples to less than already plotted, truncate as requested. We truncate one more data point than requested
            # since we add the new one right after.
            cutoff_idx = self.plotSamples + 1
            self.x = self.x[-cutoff_idx:]
            self.x.append(next_time)
            self.y1 = self.y1[-cutoff_idx:]; self.y2 = self.y2[-cutoff_idx:]; self.y3 = self.y3[-cutoff_idx:]; self.y4 = self.y4[-cutoff_idx:]
            self.y1.append(data[0]); self.y2.append(data[1]); self.y3.append(data[2]); self.y4.append(data[3])
            self.y_data = [self.y1, self.y2, self.y3, self.y4]
        if dev_mode == 'singles':
            # Counts labels will show single channel counts
            self.Ch1CountsLabel.setText(str(data[0]))
            self.Ch2CountsLabel.setText(str(data[1]))
            self.Ch3CountsLabel.setText(str(data[2]))
            self.Ch4CountsLabel.setText(str(data[3]))
        elif dev_mode == 'pairs':
            # Counts labels will show Ch 1-3, 1-4, 2-3, 2-4 coincidences
            self.Ch1CountsLabel.setText(str(data[4]))
            self.Ch2CountsLabel.setText(str(data[5]))
            self.Ch3CountsLabel.setText(str(data[6]))
            self.Ch4CountsLabel.setText(str(data[7]))
        self._counts_plotted = True
        self._data_plotted = self._counts_plotted or self._g2_plotted
        self.updatePlots(self._radio_flags)
    
    # Updating plots 1-4
    def updatePlots(self, radio_flags: list):
        for i in range(len(radio_flags)):
            # Only show plots with the Radio button selected
            if radio_flags[i] == 1:
                self.linePlots[i].setData(self.x[-self.idx:], self.y_data[i][-self.idx:])

    # Radio button slots (functions)

    # Channel 1 Radio Button Plotting
    @QtCore.pyqtSlot('PyQt_PyObject')
    def displayPlot1(self, b: QRadioButton):
        if b.isChecked() == True:
            # Possible to clear self.x and self.y1 without disrupting the worker loop?
            self._radio_flags[0] = 1
            self.updatePlots(self._radio_flags)
            self.linePlot1.setPen(self.lineStyle1)
            if self.logger:
                self.logger.radio_flags[0] = 1
        elif b.isChecked() == False:
            self._radio_flags[0] = 0
            self.linePlot1.setPen(None)
            if self.logger:
                self.logger.radio_flags[0] = 0
                
    # Channel 2 Radio Button Plotting
    @QtCore.pyqtSlot('PyQt_PyObject')
    def displayPlot2(self, b: QRadioButton):
        if b.isChecked() == True:
            self._radio_flags[1] = 1
            self.updatePlots(self._radio_flags)
            self.linePlot2.setPen(self.lineStyle2)
            if self.logger:
                self.logger.radio_flags[1] = 1  
        elif b.isChecked() == False:
            self._radio_flags[1] = 0
            self.linePlot2.setPen(None)
            if self.logger:
                self.logger.radio_flags[1] = 0

    # Channel 3 Radio Button Plotting
    @QtCore.pyqtSlot('PyQt_PyObject')
    def displayPlot3(self, b: QRadioButton):
        if b.isChecked() == True:
            self._radio_flags[2] = 1
            self.updatePlots(self._radio_flags)
            self.linePlot3.setPen(self.lineStyle3)
            if self.logger:
                self.logger.radio_flags[2] = 1
        elif b.isChecked() == False:
            self._radio_flags[2] = 0
            self.linePlot3.setPen(None)
            if self.logger:
                self.logger.radio_flags[2] = 0

    # Channel 4 Radio Button Plotting
    @QtCore.pyqtSlot('PyQt_PyObject')
    def displayPlot4(self, b: QRadioButton):
        if b.isChecked() == True:
            self._radio_flags[3] = 1
            self.updatePlots(self._radio_flags)
            self.linePlot4.setPen(self.lineStyle4)
            if self.logger:
                self.logger.radio_flags[3] = 1
        elif b.isChecked() == False:
            self._radio_flags[3] = 0
            self.linePlot4.setPen(None)
            if self.logger:
                self.logger.radio_flags[3] = 0

    @QtCore.pyqtSlot(str)
    def updateStart(self, channel: str):
        cs = int(channel)
        self._ch_start = cs
        if self.acq_flag == True and self.modesCombobox.currentText() == "g2":
            if self.logger:
                self.logger.ch_start = cs
                print('logger start channel is now: ' + str(self.logger.ch_start))

    @QtCore.pyqtSlot(str)
    def updateStop(self, channel: str):
        cs = int(channel)
        self._ch_stop = cs
        if self.acq_flag == True and self.modesCombobox.currentText() == "g2":
            if self.logger:
                self.logger.ch_stop = cs
                print('logger stop channel is now: ' + str(self.logger.ch_stop))

    @QtCore.pyqtSlot(str)
    def updateLevel(self, level: str):
        if level == 'TTL (+1.6V)' and self._tdc1_dev:
            print('entering TTL block')
            self._level = 'TTL'
            print('1')
            self._tdc1_dev.level = 'TTL'
            print(f'Device at {self._dev_path} is now at {self._level} level')
        elif level == 'NIM (-0.5V)' and self._tdc1_dev:
            print('entering NIM block')
            self._level = 'NIM'
            print('1')
            self._tdc1_dev.level = 'NIM'
            print(f'Device at {self._dev_path} is now at {self._level} level')
        elif level == 'Select':
            pass

    # Histogram
    # Connected to histogram_logged signal
    @QtCore.pyqtSlot(dict, int, int)
    def updateHistogram(self, g2_data: dict, bins: int, bin_width: int):
        # {int - ch_start counts, int- ch_stop counts, int - actual acq time, float - time bins, float - histogram values}
        # time bins and histogram vals are both np arrays
        incremental_y = g2_data['histogram']
        incremental_y_int = incremental_y.astype(np.int32)
        beans = len(incremental_y_int)
        self.y0 = self.wonkyAdd(y0 = self.y0, incremental = incremental_y_int)
        self.x0 = np.arange(0, beans*bin_width, bin_width)
        self.histogramPlot.setData(self.x0, self.y0)
        totalpairs = np.sum(self.y0, dtype=np.int32)
        self._g2_plotted = True
        self._data_plotted = self._counts_plotted or self._g2_plotted
        self.g2RateLabel.setText("Total Pairs: " + "<br>" + str(totalpairs))
    
    @staticmethod
    def wonkyAdd(y0: np.array, incremental: np.array):
        if len(y0) == len(incremental):
            y0 += incremental
        elif len(y0) < len(incremental):
            diff = len(incremental) - len(y0)
            pad = np.zeros(diff, dtype = np.int32)
            y0 = np.append(y0, pad)
            y0 += incremental
        elif len(y0) > len(incremental):
            y0 = y0[:len(incremental)]
            y0 += incremental
        return y0

    @QtCore.pyqtSlot(int)
    def updateBinwidth(self, bin_width):
        self.binsize = bin_width
        self.bin_width = bin_width
        if self.logger:
            self.logger.bin_width = bin_width
        self.x0 = np.arange(0, self.bins*self.binsize, bin_width) # Will eventually be overwritten in updateHistogram, but this might help the first cycle.

    @QtCore.pyqtSlot(int)
    def updateRuntime(self, runtime):
        runtime_mins = runtime*60
        self._runtime = runtime_mins
        if self.logger:
            self.logger.runtime = runtime_mins

    def endRun(self):
        self.liveStart_Button.setEnabled(False)
        QtCore.QTimer.singleShot(1000, lambda: self.liveStart_Button.setEnabled(True)) # In milliseconds
        self.acq_flag = False
        self.log_flag = False
        if self.logger:
            self.logger.active_flag = False
        self.stopWorkerAndThread()
        self.stopTimer()
        self.selectLogfile_Button.setEnabled(True)
        self.liveStart_Button.setText("Live Start")

    # Timer
    def startTimer(self):
        time = self.timer.start(1000)
        self.timer.timeout.connect(self.updateTimer)
    
    def stopTimer(self):
        if self.timer.isActive():
            self.timer.stop()
            self.timer.timeout.disconnect()

    def updateTimer(self):
        if self._runtime > 0:
            self.countdownLabel.setStyleSheet("color: black; font-size: 24px")
            self._runtime -= 1
            total_seconds = self._runtime
            hours = total_seconds // 3600
            total_seconds = total_seconds - (hours * 3600)
            minutes = total_seconds // 60
            seconds = total_seconds - (minutes * 60)
            self.countdownLabel.setText("{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds)))
        else:
            self.countdownLabel.setStyleSheet("color: gray; font-size: 24px")
            print(f'Timer is up! Data was collected for {self.runtimeSpinbox.value()} minute(s).')
            self.endRun()

    # RESETS for internal variables

    def StrongResetInternalVariables(self):
        self.integration_time = 1
        self._logfile_name = '' # Track the logfile(csv) being used by GUI
        self.log_flag = False
        self.deleteWorkerAndThread()
        try:
            self._tdc1_dev._com.close()
        except AttributeError:
            print('TDC1 object not yet created.')
        finally:
            self._tdc1_dev = None  # tdc1 device object
            self._dev_mode = ''
            self._dev_path = '' # Device path, eg. 'COM4'

    def WeakResetInternalVariables(self):
        # Excludes resetting variables relating to the device object (device, mode, path)
        self.integration_time = 1
        self._logfile_name = '' # Track the logfile being used by GUI
        self.log_flag = False
        self.deleteWorkerAndThread()

    def stopWorkerAndThread(self):
        QtCore.QTimer.singleShot(1000, self.dummy)
        if self.logger_thread:
            if self.logger:
                self.logger.active_flag = False
                self.logger_thread.quit()
                self.logger_thread.wait()

    def deleteWorkerAndThread(self):
        self.stopWorkerAndThread()
        self.logger = None
        self.logger_thread = None

    # Enabling/Disabling GUI elements

    def enableDevOptions(self):
        self.modesCombobox.setEnabled(True)
        self.levelsComboBox.setEnabled(True)
        self.integrationSpinBox.setEnabled(True)
        self.samplesSpinbox.setEnabled(True)
        self.liveStart_Button.setEnabled(True)
        self.selectLogfile_Button.setEnabled(True)
        self.runtimeSpinbox.setEnabled(True)

    def disableDevOptions(self):
        self.modesCombobox.setEnabled(False)
        self.levelsComboBox.setEnabled(False)
        self.integrationSpinBox.setEnabled(False)
        self.samplesSpinbox.setEnabled(False)
        self.liveStart_Button.setEnabled(False)
        self.selectLogfile_Button.setEnabled(False)

    def enableSinglesOptions(self):
        self.radio1_Button.setEnabled(True)
        self.radio2_Button.setEnabled(True)
        self.radio3_Button.setEnabled(True)
        self.radio4_Button.setEnabled(True)

    def disableSinglesOptions(self):
        self.radio1_Button.setEnabled(False)
        self.radio2_Button.setEnabled(False)
        self.radio3_Button.setEnabled(False)
        self.radio4_Button.setEnabled(False)

    def enableg2Options(self):
        self.channelsCombobox1.setEnabled(True)
        self.channelsCombobox2.setEnabled(True)
        self.offsetSpinbox.setEnabled(True)
        self.resolutionSpinbox.setEnabled(True)

    def disableg2Options(self):
        self.channelsCombobox1.setEnabled(False)
        self.channelsCombobox2.setEnabled(False)
        self.offsetSpinbox.setEnabled(False)
        self.resolutionSpinbox.setEnabled(False)
    
    # For future use
    def resetGUIelements(self):
        self.liveStart_Button.setEnabled(True)
        self.selectLogfile_Button.setEnabled(True)
        self.logfileText.setText('')
        self.selectLogfile_Button.setText('Select Logfile')
        self.resetRadioButtons()
        self.integrationSpinBox.setValue(1000)
        self.samplesSpinbox.setValue(501)
        self.runtimeSpinbox.setValue(5)
        self.modesCombobox.setCurrentText('Select mode')

    def resetRadioButtons(self):
        self.radio1_Button.setChecked(False)
        self.radio2_Button.setChecked(False)
        self.radio3_Button.setChecked(False)
        self.radio4_Button.setChecked(False)

    def resetCountsPlot(self):
        self.x=[]
        self.y1=[]
        self.y2=[]
        self.y3=[]
        self.y4=[]
        self.linePlot1.setData(self.x, self.y1)
        self.linePlot2.setData(self.x, self.y2)
        self.linePlot3.setData(self.x, self.y3)
        self.linePlot4.setData(self.x, self.y4)
        self.resetRadioButtons()
        self._counts_plotted = False
        self._data_plotted = self._counts_plotted or self._g2_plotted

    def resetg2Plot(self):
        self.x0=np.arange(0, self.bins*self.binsize, self.binsize)
        self.y0=np.zeros_like(self.x0)
        self.histogramPlot.setData(self.x0, self.y0)
        self._radio_flags = [0,0,0,0]
        self._g2_plotted = False
        self._data_plotted = self._counts_plotted or self._g2_plotted

    def resetDataAndPlots(self):
        self.resetCountsPlot()
        self.resetg2Plot()

    @QtCore.pyqtSlot()
    def clearCountsDataData(self):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(QtWidgets.QMessageBox.Information)
        msgBox.setText('Any Counts data unsaved to logfile will be lost. Click Ok to confirm.')
        msgBox.setWindowTitle('Confirm Clear Singles.')
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        returnValue = msgBox.exec()
        if returnValue == QMessageBox.Ok:
            self.resetCountsPlot()

    @QtCore.pyqtSlot()
    def clearg2DataData(self):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(QtWidgets.QMessageBox.Information)
        msgBox.setText('Any g2 data unsaved to logfile will be lost. Click Ok to confirm.')
        msgBox.setWindowTitle('Confirm Clear Pairs.')
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        returnValue = msgBox.exec()
        if returnValue == QMessageBox.Ok:
            self.resetg2Plot()
    
    # Dummmy slot for QTimer
    @QtCore.pyqtSlot()
    def dummy(self):
        pass

    def cleanUp(self):
        print('Performing cleanup...')
        self.acq_flag = False
        self.log_flag = False
        if self.logger:
            self.logger.active_flag = False
        self.stopWorkerAndThread()
        self.stopTimer()
        print('Exiting app, bye!')

def main():
        app = QApplication(sys.argv)
        win = MainWindow()
        win.show()
        app.aboutToQuit.connect(win.cleanUp)
        sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()


#####################################
# Things to Note (For Developer)    #
#####################################

# 1. Only communicate with worker via Signals and Slots
#   - Do not call any of its methods from the main thread -> But variables are fine...?


######################
# Code Outline       #
######################

# 1. This code processes and plots data from TDC1 timestamp unit
# 2. There are two classes: logWorker and MainWindow
#   - logWorker handles the data logging to the csv file via a separate thread
#   - MainWindow contains the GUI as well as graph plotting functions

######################
# Update History     #
######################

# v1.3 (26.5.2022)
# Started update history with v1.3.
# Fixed GUI plot not updating after hitting PLT_SAMPLES limit.
# Fixed error when choosing integration time < 1000 ms. Logger was receiving floats when it was expecting int. Logger now expects floats.
# Fixed wrong call to QFileDialog when selecting log file.
# Minor update to GUI states when selecting GUI modes.
# Added level selection.
# Fixed bugs associated with internal states when hitting 'liveStop'.

# v1.3.1 (30.5.2022)
# Fixed counts labels not updating after a while.
# Properly split pairs/g2 functionality.

###################################
# TO CHECK AND FIX IF NEEDED      #
###################################

# Last updated (30.5.2022)
# GUI cannot start after pressing Live Stop with timer in g2 mode