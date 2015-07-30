#!/usr/bin/python3
'''
    QBI Meunier Tracker APP: GUI for tracker.py (trackerapp.py)
    **************************************************************
    Description: This script was developed for Andreas in the Meunier Lab at QBI.  It analyses particle tracking information and produces plots.
    
    Requirements: Python3, PyQt5, matplotlib, numpy, plotly
    UI files: created in Qt Designer, loaded dynamically with uic
    Input: CSV Output file from Tracking program (Metamorph)
    Output: CSV file with processed data, PNG files if Plotting
    
    Copyright (C) 2015  QBI Software, The University of Queensland

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
    '''
__author__ = "Liz Cooper-Williams (QBI)"
__date__ = "$15/06/2015 11:03:33 AM$"
__version__ = 1.0

import csv
import os
import sys, time
#from threading import Thread
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import QSettings
from tracking import Tracker, Coord
import matplotlib.pyplot as plt
##Removed in compiled version (unable to locate plotly\\graph_reference\\graph_objs_meta.json)
#import plotly.plotly as py
#import plotly.tools as tls
#from plotly.graph_objs import *

# create a progressBar while running plotter
class progress(QtWidgets.QDialog):
    signal = QtCore.pyqtSignal(int)
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.finished = False
        # Set up the user interface from Designer.
        self.ui = uic.loadUi("tracker_progress.ui", self)
        #self.ui.btnStart.clicked.connect(self.start)
        self.ui.btnStop.clicked.connect(self.stop)
        #initialise
       # self.update(0)
        #Add Thread
       # self.threadobj = Worker()
       # self.threadobj.notify.connect(self.update)
    
    
    def update(self, i):
        self.ui.progressBar.setValue(i)

    def total(self,total):
        self.ui.progressBar.setMaximum(total)
   
    def stop(self):
        #self.signal.emit(1)
        self.finished = True
        self.close()
        
    def closeEvent(self, event):
        self.stop()
        self.close()
        
class MyApp(QtWidgets.QMainWindow):
    notify = QtCore.pyqtSignal(int)
    def __init__(self):
        super(MyApp, self).__init__()
        self.ui = uic.loadUi("tracker.ui", self)
        #Load Config
        self.settings = QSettings('.config.ini', QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False)
        #load ini
        # Initial window size/pos last saved if available
        self.resize(self.settings.value('size', QtCore.QSize(670,560)))
        self.move(self.settings.value('pos', QtCore.QPoint(50, 50)))
        self.ui.txtInput.setText(self.settings.value('datafile', '.'))
        self.ui.txtOutputdir.setText(self.settings.value('outputdir', '.'))
        if (len(self.ui.txtInput.text()) > 5 and len(self.ui.txtOutputdir.text()) > 5 and len(self.ui.txtOutputfile.text()) > 5):
                self.ui.btnRunScript.setEnabled(True)
        ##TEMPORARY: Disabled Plotly due to error with build
        self.ui.checkBoxPlotly.setEnabled(False)
        #Set actions
        self.ui.btnRunScript.clicked.connect(self.runscript)
        self.ui.btnFileBrowser.clicked.connect(self.popupInput)
        self.ui.btnFolderBrowser.clicked.connect(self.popupOutput)
        self.ui.btnClear.clicked.connect(self.clearfields)
        self.ui.toolButtonHelp.clicked.connect(self.helpdialog)
        #Setup ProgressBar
        self.progress = progress(self)
        self.finished = False
        #Allow save fig
        self.fig = None
         

    def loadparams(self):
        paramslist = QtGui.QStandardItemModel(self.ui.listOutput)
        numplots = 0 #default none
        #Check input
        plotfrom = int(self.ui.spinPlotFrom.value())
        plotto = int(self.ui.spinPlotTo.value())
        #Plot first plot
        if (plotfrom <= 1 and plotto <= 1 and plotfrom != plotto):
            plotfrom = 1
            plotto = 2
        elif plotfrom == 0 and plotfrom != plotto:
            plotfrom = 1
        else :
            plotto += 1
        #swap if values are incorrect
        if plotto < plotfrom:
            tmp = plotfrom
            plotfrom = plotto
            plotto = tmp
        if (self.ui.checkBoxAllPlots.isChecked()):
            numplots = -1
        else:
            numplots = plotto - plotfrom
        #Set params
        outputparams = {
                "Input" : self.ui.txtInput.text(),
                "OutputDir" : self.ui.txtOutputdir.text(),
                "OutputFname" : self.ui.txtOutputfile.text(),
                "OutputFile": self.ui.txtOutputdir.text() + os.path.sep + self.ui.txtOutputfile.text(),
                "Decimals" : int(self.ui.spinDec.value()),
                "Plots" : numplots,
                "from" : plotfrom,
                "to" : plotto
        }

        #Display settings
        opstring = "Input: " + outputparams['Input']
        params = QtGui.QStandardItem(opstring)
        paramslist.appendRow(params)
        opstring = "Output: " + outputparams['OutputFile']
        params = QtGui.QStandardItem(opstring)
        paramslist.appendRow(params)
        opstring = "Decimals: " + str(outputparams['Decimals'])
        params = QtGui.QStandardItem(opstring)
        paramslist.appendRow(params)
        if numplots < 0 :
            plotsval = 'All'
        elif numplots == 0 :
            plotsval = 'None'
        else :
            plotsval = str(outputparams['from']) + " to " + str(outputparams['to'])
        opstring = "Plots: " + plotsval
        params = QtGui.QStandardItem(opstring)
        paramslist.appendRow(params)
        self.ui.listOutput.setModel(paramslist)

        #Check valid entries
        valid = True
        for op, opval in outputparams.items():
            if (opval is None):
                valid = False
                break
        if (not valid):
            return None
        else:
            return outputparams

    def clearfields(self):
        for widget in self.ui.centralwidget.children():
            if isinstance(widget, QtWidgets.QLineEdit):
                widget.setText('')
            if isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(False)
            if isinstance(widget, QtWidgets.QListView):
                widget.clear()
            if isinstance(widget, QtWidgets.QSpinBox):
                widget.setValue(widget.minimum())

    def popupInput(self):
        browser = QtWidgets.QFileDialog(self)
        browser.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        fname = browser.getOpenFileName(self, 'Choose a data file', self.settings.value('datafile', '.'),
                'CSV files (*.csv)')
        if fname:
            self.ui.txtInput.setText(str(fname[0]))
            #Check if both files selected
            if self.ui.txtOutputdir.text():
                self.ui.btnRunScript.setEnabled(True)

    def popupOutput(self):
        browser2 = QtWidgets.QFileDialog(self)
        browser2.setFileMode(QtWidgets.QFileDialog.Directory)
        browser2.setOption(QtWidgets.QFileDialog.ShowDirsOnly)
        dname = browser2.getExistingDirectory(self, 'Select output folder','')
        if dname:
            self.ui.txtOutputdir.setText(dname)
            #Check if both files selected
            if self.ui.txtInput.text():
                self.ui.btnRunScript.setEnabled(True)


    def runscript(self):
        params = self.loadparams();
        if (params is None):
            self.updateStatus("***ERROR: Settings invalid, exiting ***")
            return 0
        #setup Tracker
        tracker = Tracker()

        #Check input file has correct headings
        validinput = tracker.checkinputheaders(params['Input'])
        if (not validinput):
            self.updateStatus("***ERROR: Input file not valid, exiting ***")
            self.updateStatus("Order of rows (with/without headers) should be:")
            for hdr in tracker.inputheaders:
                self.updateStatus(hdr)
            return 0
         
        #Generate output file
        tracker.numdecimal = int(params['Decimals'])
        self.updateStatus("Starting ...")
        tracker.load_input(params['Input'])
        self.updateStatus("... Input loaded ...")
        outputfilename = params['OutputFile']
        msg = tracker.write_output(outputfilename)
        self.updateStatus(msg)
                
        #Generate plots (if required)
        if ( "Completed" in msg) and (tracker.counter > 0):
            self.updateStatus("TOTAL ROWS: " + str(tracker.counter))
            self.updateStatus("TOTAL TRACKS: " + str(len(tracker.plotter)))
            plotnum = int(params['Plots'])
            msgs = []
            #All plots
            if (plotnum < 0):
                plotnum = len(tracker.plotter)
                params['from'] = 1
                params['to'] = plotnum + 1
            
            if (plotnum > 0):
                outputdir = params['OutputDir'] + os.path.sep
                tracker.set_outputdir(outputdir)
                tracker.set_fromplot(params['from'])
                tracker.set_toplot(params['to'])
                self.updateStatus("Creating " + str(plotnum) +" plots")

                #Extract subset
                r = range(params['from'], params['to'])
                #Run plots in a thread
                self.startPlots(tracker, r)
                

            #Save settings
            self.settings.setValue('datafile', params['Input'])
            self.settings.setValue('outputdir', params['OutputDir'])
        else:
            self.updateStatus("Error occurred - please check data files")
    
    '''Create plots from output data - requires loaded tracker and range of plot numbers to plot
    '''
    def startPlots(self, tracker, plotrange):
        self.updateStatus("Output plots to " + tracker.outputdir)
        msgs =[]
        self.progress.total(len(plotrange))
        self.progress.finished = False
        self.progress.show()
        self.notify.connect(self.progress.update)
       
        #run plots
        tracker.init_allplots()
        totalplots = 0
        if (self.ui.checkBoxMatlab.isChecked() or self.ui.checkBoxPlotly.isChecked()):
           totalplots = 1
        i = 0
        for trak in plotrange:
            if (self.progress.finished == False):
                i += 1
                self.progress.update(i)
                QtWidgets.QApplication.processEvents()
                msg = tracker.plottrack(trak, totalplots)
                self.updateStatus(msg)
        self.progress.stop()
        #create total plot - Matlab
        if (totalplots > 0):
            self.fig = plt.figure(tracker.alltracks + 1)
            mytitle = "All " + str(tracker.alltracks) + " tracks (" + str(len(tracker.allx)) + " points)"
            lines = plt.quiver(tracker.allx,tracker.ally,tracker.allrho,tracker.alltheta)
            plt.setp(lines, color='b', antialiased=True)
            #plt.linewidth(0.2)
            #plt.markers.set_markersize(1)
            plt.xlabel('x')
            plt.ylabel('y')
            plt.title(mytitle)
            #save to file
            filename = tracker.outputdir + "Tracks_" + str(plotrange[0]) + "to" + str(plotrange[-1]) + ".png"
            self.fig.savefig(filename, dpi=300, orientation='landscape',format='png')
            self.updateStatus("Total Plot saved to " + filename)
            
            if (self.ui.checkBoxMatlab.isChecked()):
                plt.show()
           
            #create total plot
            #####Plotly needs an account - follow instructions: https://plot.ly/python/getting-started/
            
            ## TEMPORARY: REMOVED DUE TO ERROR WITH BUILD
            #if (self.ui.checkBoxPlotly.isChecked()):
             #   plotly_fig = tls.mpl_to_plotly(fig)
                #TODO: Need to create meshgrids from sorted data
                #quiver = tls.TraceFactory.create_quiver(tracker.allx,tracker.ally,tracker.allrho,tracker.alltheta)
                #data = Data([quiver])
                #plotly_fig = Figure(data=data)
             #   unique_url = py.plot(plotly_fig, filename = mytitle)
             #   self.updateStatus("Plotly Plot saved to " + unique_url)
           # plt.close()
                     
           
            
    def updateStatus(self, txtout):
        statusoutput = self.ui.listOutput.model()
        status = QtGui.QStandardItem(txtout)
        statusoutput.appendRow(status)

    def helpdialog(self):
        dialog = QtWidgets.QDialog()
        dialog.ui = uic.loadUi("tracker_help.ui", dialog)
        dialog.show()

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, 'Message', "Are you sure you want to quit?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if (reply == QtWidgets.QMessageBox.Yes):
            event.accept()
            # Write window size and position to config file
            self.settings.setValue("size", self.size())
            self.settings.setValue("pos", self.pos())
            self.progress.close()
            if (self.fig is not None):
                plt.close(self.fig)
        else:
            event.ignore()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = MyApp()
    MainWindow.show()
    
    sys.exit(app.exec_())
