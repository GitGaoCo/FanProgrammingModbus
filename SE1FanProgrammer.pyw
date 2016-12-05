# -*- coding: utf-8 -*-
###############################################################################
# (c) 2016 Schneider Electric SE. All rights reserved.
# All trademarks are owned or licensed by Schneider Electric SE,
# its subsidiaries or affiliated companies.
# 
# FILE NAME:  SE1FanProgrammer.pyw
#
# PURPOSE:
#     This program is used to program the fans in SE1 during manufacturing.
#     It uses the pyqt GUI framework.
#
#
# FUNCTION(S):
#
#     local:
#
# NOTES:
#
# CHANGE HISTORY :
# 0.0.1   Dec2016 Francis Kwok - Created
#
##############################################################################

###############################################################################
#                               Includes
###############################################################################
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import qrc_resources
import sys
import platform
import copy
import SE1FanProgrammerTest
import time
import re

import ctypes
myappid = u'schneider-electric.fan.programmer' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

###############################################################################
#                               Logging Module Setup
###############################################################################
# It's something I don't understand.... We have to leave logging not imported
# to see the logging and print messages from the threads in the text window...
# 
# import logging
# if __name__ == "__main__":  
#     logging.basicConfig(level=logging.DEBUG)

###############################################################################
#                             Constant Data
###############################################################################
__version__ = "x.x.x"

SERNUM_PATT = re.compile('^(\\d\\d)([0-5][0-9])00([A-Z0-9]{4})')
SERNUM_INIT_STATUS = 'Please enter valid serial number:'

###############################################################################
#                            Function/Class Definitions
###############################################################################

##  Class providing a table to display the test results.
class ResultsTable(QTableWidget):
    """
    Class providing a table to display the test results.  Sub-classed from a QTableWidget.
    """
    ##  Object Constructor
    def __init__(self, parent = None):
        """
        Constructor
        """
        super(ResultsTable, self).__init__()
        self.dictTestItems = {}

    def fnResetforNewTest(self):
        self.dictTestItems = {}
        self.clearContents()

    ##  Checks if results table has changed
    ##  @param self The object pointer.
    ##  @param newtabledict The dictionary received from the script.
    def setTableDictionary(self, newtabledict):
        """Checks if the results table had changed.  If it has, then emit the TableDictChanged signal"""
        if newtabledict != self.dictTestItems:

            self.dictTestItems = copy.deepcopy(newtabledict)  #need deep copy for future compares to work
            self.emit(SIGNAL("TableDictChanged"))

    ##  Refresh the results table
    ##  @param self The object pointer.
    def fnRefreshTable(self):
        """Used to refresh the results table contents when there was a change"""
        self.clear()
        self.setRowCount(len(self.dictTestItems))
        self.setColumnCount(8)
        HorizontalHeaders = QStringList(["TCID", "Min", "Max", "Description", "Type", "Prop", "Meas", "Result"])
        self.setHorizontalHeaderLabels(HorizontalHeaders)

        row = 0
        for entry in sorted(self.dictTestItems.keys()):
            self.setItem(row, 0, QTableWidgetItem(self.dictTestItems[entry]['TCID']))
            self.setItem(row, 1, QTableWidgetItem(self.dictTestItems[entry]['Min']))
            self.setItem(row, 2, QTableWidgetItem(self.dictTestItems[entry]['Max']))
            self.setItem(row, 3,  QTableWidgetItem(self.dictTestItems[entry]['Descript']))
            self.setItem(row, 4,  QTableWidgetItem(self.dictTestItems[entry]['Type']))
            self.setItem(row, 5,  QTableWidgetItem(self.dictTestItems[entry]['Prop']))
            self.setItem(row, 6,  QTableWidgetItem(str(self.dictTestItems[entry]['Meas'])))
            if self.dictTestItems[entry]['Result'] == 'Pass':
                item = QTableWidgetItem('Pass')
                item.setBackground(QColor(0x00,0x95,0x30))
            elif self.dictTestItems[entry]['Result'] == 'FAIL':
                item = QTableWidgetItem('FAIL')
                item.setBackgroundColor(QColor(0xF9,0x42,0x3A))
            else:
                item = QTableWidgetItem('')
                #item.setBackgroundColor(QColor(0xFF,0xD1,0x00)) #maybe do this on last pass..
            self.setItem(row, 7, item )

            row = row + 1

        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.horizontalHeader().setStretchLastSection(True)

class COMCfgDialog(QDialog):
    def __init__(self, parent = None):
        #Don't want the Help Icon...
        super(COMCfgDialog, self).__init__(parent, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)

        self.settings = QSettings()
        
        ########Modbus COMM PORTS########
        self.FanMBPortGroupBox  = QGroupBox("")
        self.FanMBPortCliQLabel = QLabel("Fan Modbus Port:")
        self.FanMBPortLineEdit  = QLineEdit()
        
        self.FanMBPortGridLayout =  QGridLayout()
        self.FanMBPortGridLayout.addWidget(self.FanMBPortCliQLabel,0,0,)
        self.FanMBPortGridLayout.addWidget(self.FanMBPortLineEdit,0,1,)
        self.FanMBPortGroupBox.setLayout(self.FanMBPortGridLayout)

        ########Save/Restore Buttons########
        self.SaveButton    = QPushButton("Save")
        self.RestoreButton = QPushButton("Restore")
        buttonlayout = QHBoxLayout()
        buttonlayout.addWidget(self.RestoreButton)
        buttonlayout.addWidget(self.SaveButton)
        
        self.ButtonGroupBox = QGroupBox("")
        self.ButtonGroupBox.setLayout(buttonlayout)
        
        v1layout = QVBoxLayout()
        v1layout.addWidget(self.FanMBPortGroupBox)
        v1layout.addWidget(self.ButtonGroupBox)
        v1layout.addStretch()

        layout = QHBoxLayout()
        layout.addLayout(v1layout)

        layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(layout)
        self.setWindowTitle("COM Port Configuration")

        #self.setFixedSize(self.frameGeometry().width(),self.frameGeometry().height())
        #self.setFixedSize(self.sizeHint())
        
        self.connect(self.SaveButton,  SIGNAL("clicked()"), self.fnSaveCurrentSettings)
        self.connect(self.RestoreButton,  SIGNAL("clicked()"), self.fnRestoreSettings) 
               
        self.fnRestoreSettings()

        
    def fnRestoreSettings(self):
        self.FanMBPortLineEdit.setText(self.settings.value("fan/mb_comm").toString())
        
    def fnSaveCurrentSettings(self):
        self.settings.setValue("fan/mb_comm",  self.FanMBPortLineEdit.text())
        

    def closeEvent(self, event):
        if self.fnValidSavedCommSettings():
            event.accept()
        else:
            event.ignore()

    def fnDisplayError(self,  str):
        ErrorMessageBox = QMessageBox()

        newfont = QFont()
        newfont.setPointSize(10)
        ErrorMessageBox.setFont(newfont)

        ErrorMessageBox.setIcon(QMessageBox.Warning)
        ErrorMessageBox.setWindowTitle("Error")
        ErrorMessageBox.setText(str)
        ErrorMessageBox.exec_()

    def fnValidSavedCommSettings(self):
        commpatt = re.compile('com[0-9]+', re.IGNORECASE)
        
        returnvalue = True
        
        lstCommPorts = ["fan/mb_comm"]
        
        for port in lstCommPorts:
            
            if commpatt.match(self.settings.value(port).toString()):
                pass
            else:
                returnvalue = False
                self.fnDisplayError("Saved port for " + port + " is not formated correctly. Format should 'com1' or 'COM1'") 


        return returnvalue
    
class Logger(QObject):
    printSig = pyqtSignal(QString)
    clearSig = pyqtSignal()
    
    def __init__(self):
        QObject.__init__(self)
        self.stdout = sys.stdout
        self.count = 0
    
    def write(self, text):
        if self.count > 200:
            self.clearSig.emit()
            self.count = 0        
        self.printSig.emit(text)
        self.count = self.count+1
    
    def close(self):
        self.stdout.close()

##  Class that creates the Main Window for the application
class MainWindow(QMainWindow):
    """Class that creates the Main Window for the application.  Subclasses from QMainWindow."""
    
    # GREEN2:  #009530  SE Spruce Green
    # GREY6:   #262E38  SE Dark Grey
    # GREY11:  #404A54  SE Light Grey
    # GREY1:   #C5C7C4  SE Ultra Light Grey
    # RED1:    #F9423A  SE Red 
    # YELLOW1: #FFD100  SE Yellow 
              
    ## Object Constructor
    ## @param self The object pointer.
    ## @param parent Widget parent if any
    def __init__(self, parent = None, logger = None):
        super(MainWindow, self).__init__(parent)
        
        self.setStyleSheet("""QMenuBar { background-color: #009530 }
                              QMenuBar::item { color: #FFFFFF;
                                               background-color: transparent;
                                             }
                              QMenuBar::item:selected { border: 1px solid #FFFFFF;
                                                        border-radius: 3px;
                                                      }
                              QMenu { color: #000000;
                                      background-color: #FFFFFF;
                                      font-family: "Arial Rounded MT", Arial, Helvetica, sans-serif;
                                    }
                              QMenu::item:selected { color: #FFFFFF;
                                      background-color: #262E38;
                                    }
                             
                             QPushButton::checked {
                                 background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                                   stop: 0 #262E38, stop: 1 #404A54);
                                                   color: #FFFFFF;
                                                   border: 2px solid #009530;
                                                   border-radius: 2px;
                                                 }
                             
                             QPushButton::pressed {
                                background-color: qlineargradient(x1: 0, 
                                                                  y1: 0, 
                                                                  x2: 0, 
                                                                  y2: 1,
                                                                  stop: 0 #262E38, 
                                                                  stop: 1 #404A54);
                                color: #FFFFFF;
                                border-color:#009530;
                                border-radius: 2px;
                                                   border-style: solid;
                                                   border-radius: 2px;
                                                 }
                           """);
        
        self.logger = logger
        
               
        #Setup the Window Title
        self.setWindowTitle("SE1 Fan Programmer")

        #Create Log Dock Widget        
        logDockWidget = QDockWidget("Toggle Log View", self)
        logDockWidget.setObjectName("LogDockWidget")
        logDockWidget.setAllowedAreas(Qt.NoDockWidgetArea)
        logDockWidget.setFloating(True)
        logDockWidget.close()
        
        self.textDisplayArea = QTextEdit()
        self.textDisplayArea.setLineWrapMode(QTextEdit.NoWrap)
        self.textDisplayArea.setReadOnly(True)
        font = QFont('Consolas')
        font.setStyleHint(QFont.TypeWriter)
        font.setPointSize(9)
        self.textDisplayArea.setFont(font)
        
        logDockWidget.setWidget(self.textDisplayArea)
        self.addDockWidget(Qt.BottomDockWidgetArea, logDockWidget)

        #Create status bar
        self.status = self.statusBar()
        self.status.showMessage("Ready")

        #Create actions
        #Note: that is creates the connections too...
        helpAboutAction = self.createAction("&About...", slot = self.helpAbout, icon = "help.ico")
        toggleLogWindowAction = logDockWidget.toggleViewAction()  #Class has helper to create an Action for us.
        toggleLogWindowAction.setIcon(QIcon(":/openbook.ico"))
        commSettingsAction = self.createAction("COM Settings", slot = self.fnOpenCOMCfgDialog, icon = "serial.ico")
        quitAction         = self.createAction("E&xit",  slot = qApp.quit, icon = "close.ico" )
        saveTableAction   = self.createAction("Save Table as CSV",  slot = self.fnSaveTableCsv, icon = "save.ico")
        saveLogAction   = self.createAction("Save Log to File",  slot = self.fnSaveLog, icon = "book.ico")
        
        #Create Menu
        fileMenu = self.menuBar().addMenu("&File")
        editMenu = self.menuBar().addMenu("Edit")
        helpMenu = self.menuBar().addMenu("&Help")
        
        #Help Menu
        self.addActions(helpMenu, (helpAboutAction, None))
        
        #Edit Menu
        self.addActions(editMenu, (commSettingsAction, None))
        
        #File Menu
        self.addActions(fileMenu,  (toggleLogWindowAction, saveLogAction, saveTableAction, quitAction, None))
        
        #Draw the widgets....

        self.fnDrawTestControlsWidgets()

        self.fnDrawFan1Widgets()
        self.fnDrawFan2Widgets()
        self.fnDrawFan3Widgets()        
        
        #Create the table widget
        self.TableWidget = ResultsTable()
        
        # Main layout
        layout = QVBoxLayout()        
        layout.addWidget(self.TestControlsGroupBox)
        layout.addWidget(self.Fan1GroupBox)
        layout.addWidget(self.Fan2GroupBox)
        layout.addWidget(self.Fan3GroupBox)
        layout.addWidget(self.TableWidget)
        #layout.addStretch()
        
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)        

        #Create the the test thread
        self.TestThread = SE1FanProgrammerTest.TestScript()
        self.lock = QReadWriteLock()
        
        #Update Test Info Timer
        self.TestInfoTimer = QTimer()
        self.TestInfoTimer.setSingleShot(False)
        self.TestInfoTimer.setInterval(1000) #1 second refresh
                
        #Make connections
        #Logger Related Connections...
        self.connect(self.logger,  SIGNAL("printSig(QString)"),  self.fnAppend)
        #The logger class sends a clearSig after 200 chars.
        #self.connect(self.logger,  SIGNAL("clearSig()"),  self.fnClearLogger)

        self.connect(self.TestThread,  SIGNAL("started()"), self.TestInfoTimer, SLOT("start()"))
        self.connect(self.TestThread, SIGNAL("finished()"), self.TestInfoTimer, SLOT("stop()") )
        self.connect(self.TestInfoTimer, SIGNAL("timeout()"), self.fnUpdateTestInformation)
        self.connect(self.TableWidget,  SIGNAL("TableDictChanged"), self.TableWidget.fnRefreshTable )
        
        self.connect(self.StartButton, SIGNAL("clicked()"), self.fnRunScript)         
        self.connect(self.TestThread,  SIGNAL("Exception(QString)"),  self.fnDisplayError)
        self.connect(self.TestThread,  SIGNAL("FinishPending"),  self.fnUpdateTestInformation)
        self.connect(self.TestThread,  SIGNAL("FinishPending"),  self.fnTestDone)

        self.connect(self.BL601ProgEnableButton, SIGNAL("clicked()"), 
                     lambda grpbox = self.Fan1GroupBox : self.fnCheckSerialNumber(grpbox))
        self.connect(self.BL602ProgEnableButton, SIGNAL("clicked()"),
                     lambda grpbox = self.Fan2GroupBox : self.fnCheckSerialNumber(grpbox))
        self.connect(self.BL603ProgEnableButton, SIGNAL("clicked()"),
                     lambda grpbox = self.Fan3GroupBox : self.fnCheckSerialNumber(grpbox))

        self.connect(self.AbortButton, SIGNAL("clicked()"), self.TestThread.fnSetAbortFlag)
                
        #Setup the Settings so it saves and restores last settings
        self.settings = QSettings()
        
        size = self.settings.value("MainWindow/Size", QVariant(QSize(300, 100))).toSize()
        self.resize(size)
        
        position = self.settings.value("MainWindow/Position", QVariant(QPoint(0, 0))).toPoint()
        self.move(position)
        
        self.restoreState(self.settings.value("MainWindow/State").toByteArray())

    def fnCheckSerialNumber(self, grpbox):
        if grpbox.buttonref.isChecked():
            print 'pressed'
            entered_sn =  str(grpbox.lineref.text())
            
            matchObj = SERNUM_PATT.match(entered_sn)
            
            if matchObj:
                year_dec   = matchObj.group(1)
                year_full  = '20' + year_dec
                mth_dec    = matchObj.group(2)
                seq_ascii  = matchObj.group(3)
                
                year_hex =  format(int(year_dec), 'x').zfill(2).upper()
                mth_hex  = format(int(mth_dec), 'x').zfill(2).upper()
                seq_hex1 = format(ord(seq_ascii[0:1]), 'x').zfill(2).upper()
                seq_hex2 = format(ord(seq_ascii[1:2]), 'x').zfill(2).upper()
                seq_hex3 = format(ord(seq_ascii[2:3]), 'x').zfill(2).upper()
                seq_hex4 = format(ord(seq_ascii[3:4]), 'x').zfill(2).upper()   
                
                print "{} {} {} {} {} {}".format(year_hex, 
                                                mth_hex, 
                                                seq_hex1, 
                                                seq_hex2, 
                                                seq_hex3, 
                                                seq_hex4)
                
                grpbox.lineref.setEnabled(False)
                grpbox.setTitle(grpbox.prefix + 
                                "Year Code:"  +
                                year_full     +
                                "   Week Code:"  +
                                mth_dec       +
                                "   Seq Num:"    +
                                seq_ascii)
                                
            else:
                #did not match regex, bring button back up
                grpbox.buttonref.setChecked(False)
                grpbox.setTitle(grpbox.prefix + SERNUM_INIT_STATUS)
            
        else:
            grpbox.lineref.setEnabled(True)
            grpbox.setTitle(grpbox.prefix + SERNUM_INIT_STATUS)
            
    def fnSaveLog(self):
        default_fileName = time.strftime("%Y%m%d-%H%M%S") + '.log'
        
        fileName = QFileDialog.getSaveFileName(self, 'Save Results Table to...', 
                                                     './DebugLogs/{}'.format(default_fileName), 
                                                     "log files (*.log);;All Files (*)")
        if fileName:
            #print fileName        
            f = open(fileName,"w") #opens file with name of "test.txt"
            f.write(self.textDisplayArea.toPlainText())
            f.close()

    def fnSaveTableCsv(self):
        
        default_fileName = time.strftime("%Y%m%d-%H%M%S") + '.csv'
        
        fileName = QFileDialog.getSaveFileName(self, 'Save Results Table to...', 
                                                     './TestResults/{}'.format(default_fileName), 
                                                     "CSV files (*.csv);;All Files (*)")
        
        if fileName:
            #print fileName

            #Check if there is already a file with the same name.
            #if os.path.exists(fileName):
            #    print 'Choose a different file name'
            self.TestThread.testcontroller.fnWriteToCsv(fileName)    
                
    def fnOpenCOMCfgDialog(self):
        #Create COMCfgDialog
        self.commcfgdialog = COMCfgDialog()       
        self.commcfgdialog.exec_() 
        
    def fnRunScript(self):
        self.PassFailLabel.setText("")
        self.TableWidget.fnResetforNewTest()
        self.textDisplayArea.clear()
        self.StartButton.setEnabled(False)
        self.AbortButton.setEnabled(True)
        self.TestThread.dictTestSelection = self.fnGetTestSelection()
        self.TestThread.start()

    def fnGetTestSelection(self):
        #TestSelectionButtonsStruct
        dictTestSelection = {}
        dictTestSelection['boolRunFan1'] = self.BL601ProgEnableButton.isChecked()
        dictTestSelection['boolRunFan2'] = self.BL602ProgEnableButton.isChecked()
        dictTestSelection['boolRunFan3'] = self.BL603ProgEnableButton.isChecked()
        return dictTestSelection
    
    def fnUpdateTestInformation(self):
        TestStatus     = None
        TestInfomation = None

        self.lock.lockForRead()
        try:
            TestStatus        = self.TestThread.fnGetTestStatus()
            TestInfomation    = self.TestThread.testcontroller.PassCurrentStatus()
        except AttributeError:
            pass  #object wasn't created yet.
        self.lock.unlock()
        
        #Update Table
        if TestInfomation:
            self.TableWidget.setTableDictionary(TestInfomation)        

        #Update Status Message
        if TestStatus:
            if TestStatus == SE1FanProgrammerTest.STATUS_STARTING_TEST:
                self.PassFailLabel.setText("<h1>Starting up the program...</h1>")
            elif TestStatus == SE1FanProgrammerTest.STATUS_FAN1_RUNNING:
                self.PassFailLabel.setText("<h1>Programming FAN1...</h1>")
            elif TestStatus == SE1FanProgrammerTest.STATUS_FAN2_RUNNING:
                self.PassFailLabel.setText("<h1>Programming FAN2...</h1>")
            elif TestStatus == SE1FanProgrammerTest.STATUS_FAN3_RUNNING:
                self.PassFailLabel.setText("<h1>Programming FAN3...</h1>")
            elif TestStatus == SE1FanProgrammerTest.STATUS_ABORTING_TEST:
                self.PassFailLabel.setText("<h1>Aborting Pending... Finishing this fan...</h1>")  
                                 
    def fnTestDone(self):
        time.sleep(2.0)
        self.StartButton.setEnabled(True)
        self.AbortButton.setEnabled(False)
        self.TableWidget.fnRefreshTable()
        
        self.lock.lockForRead()
        
        testpass = self.TestThread.testcontroller.PassCurrentPassCount()
        testfail = self.TestThread.testcontroller.PassCurrentFailCount()
        testtotal = self.TestThread.testcontroller.PassTestCount()

        if testpass == testtotal:
            self.PassFailLabel.setText(u"<span style=\"color:#009530\"><h1>PASS</h1><span>")
        elif ((testpass + testfail) <  testtotal):
            self.PassFailLabel.setText(u"<span style=\"color:#F9423A\"><h1>FAIL</h1><span>")    #not complete whole suite
        elif (testfail >  0):
            self.PassFailLabel.setText(u"<span style=\"color:#F9423A\"><h1>FAIL</h1><span>")    #One or more test fail
        else:
            self.PassFailLabel.setText(u"<span style=\"color:#F9423A\"><h1>FAIL</h1><span>")  #Catch all...
        
        self.lock.unlock()

    def fnDisplayError(self, str):
        ErrorMessageBox = QMessageBox()

        newfont = QFont()
        newfont.setPointSize(20)
        ErrorMessageBox.setFont(newfont)

        ErrorMessageBox.setIcon(QMessageBox.Warning)
        ErrorMessageBox.setWindowTitle("Error")
        ErrorMessageBox.setText(str)
        ErrorMessageBox.exec_()

    
    ###########################################################################
    #        Widget Layout Functions
    ###########################################################################
    def fnDrawTestControlsWidgets(self): 

        self.TestResultLabel = QLabel("<h1>Status:</h1>")
        self.PassFailLabel = QLabel("")
        
        #Start Buttons
        ButtonText = QString(u"Start")
        self.StartButton = QPushButton(ButtonText)
        newfont = QFont()
        newfont.setPointSize(20)
        self.StartButton.setFont(newfont)

        #Abort Button
        ButtonText = QString(u"Abort")
        self.AbortButton = QPushButton(ButtonText)
        newfont = QFont()
        newfont.setPointSize(20)
        self.AbortButton.setFont(newfont)
        self.AbortButton.setEnabled(False)

        self.TestConstrolsPositionList = [
        {'x':0,'y':0,'widget':self.TestResultLabel},{'x':0,'y':1,'widget': None},
        {'x':1,'y':0,'widget':self.PassFailLabel }, {'x':1,'y':1,'widget': None},
        {'x':2,'y':0,'widget':self.StartButton},    {'x':2,'y':1,'widget':self.AbortButton }]

        self.TestConstrolsGridLayout = QGridLayout()
        
        for pos in self.TestConstrolsPositionList:
            if pos['widget']:
                self.TestConstrolsGridLayout.addWidget(pos['widget'], pos['x'], pos['y'])

        self.TestControlsGroupBox = QGroupBox("Test Controls")
        self.TestControlsGroupBox.setLayout(self.TestConstrolsGridLayout)

    def fnDrawFan1Widgets(self):
        self.BL601LineEdit = QLineEdit()
        self.BL601LineEdit.setFixedWidth(200)
                
        self.BL601ProgEnableButton = QPushButton("Program Internal Fan")
        self.BL601ProgEnableButton.setFixedWidth(200)
        self.BL601ProgEnableButton.setCheckable(True)

        self.BL601StatusLabel = QLabel()

        self.Fan1HLayout = QHBoxLayout()
        self.Fan1HLayout.addWidget(self.BL601LineEdit)
        self.Fan1HLayout.addStretch()
        self.Fan1HLayout.addWidget(self.BL601ProgEnableButton)
        
        self.Fan1GroupBox = QGroupBox()
        self.Fan1GroupBox.prefix = "(BL601) "
        self.Fan1GroupBox.setTitle(self.Fan1GroupBox.prefix + SERNUM_INIT_STATUS)
        self.Fan1GroupBox.setLayout( self.Fan1HLayout )
        self.Fan1GroupBox.buttonref = self.BL601ProgEnableButton
        self.Fan1GroupBox.lineref   = self.BL601LineEdit
                 
    def fnDrawFan2Widgets(self): 
        
        self.BL602LineEdit = QLineEdit()
        self.BL602LineEdit.setFixedWidth(200)

        self.BL602ProgEnableButton = QPushButton("Program External Top Fan")
        self.BL602ProgEnableButton.setFixedWidth(200)
        self.BL602ProgEnableButton.setCheckable(True)
        
        self.Fan2HLayout = QHBoxLayout()
        self.Fan2HLayout.addWidget(self.BL602LineEdit)
        self.Fan2HLayout.addStretch()
        self.Fan2HLayout.addWidget(self.BL602ProgEnableButton)

        self.Fan2GroupBox = QGroupBox()
        self.Fan2GroupBox.prefix = "(BL602) "
        self.Fan2GroupBox.setTitle(self.Fan2GroupBox.prefix + SERNUM_INIT_STATUS)
        self.Fan2GroupBox.setLayout( self.Fan2HLayout ) 
        self.Fan2GroupBox.buttonref = self.BL602ProgEnableButton
        self.Fan2GroupBox.lineref   = self.BL602LineEdit

    def fnDrawFan3Widgets(self): 
        self.BL603LineEdit = QLineEdit()
        self.BL603LineEdit.setFixedWidth(200)
        
        self.BL603ProgEnableButton = QPushButton("Program External Bottom Fan")
        self.BL603ProgEnableButton.setFixedWidth(200)
        self.BL603ProgEnableButton.setCheckable(True)
        
        self.Fan3HLayout = QHBoxLayout()
        self.Fan3HLayout.addWidget(self.BL603LineEdit)
        self.Fan3HLayout.addStretch()
        self.Fan3HLayout.addWidget(self.BL603ProgEnableButton)

        
        self.Fan3GroupBox = QGroupBox()
        self.Fan3GroupBox.prefix = "(BL603) "
        self.Fan3GroupBox.setTitle(self.Fan3GroupBox.prefix + SERNUM_INIT_STATUS)
        self.Fan3GroupBox.setLayout( self.Fan3HLayout )
        
        self.Fan3GroupBox.buttonref = self.BL603ProgEnableButton
        self.Fan3GroupBox.lineref   = self.BL603LineEdit

    ###########################################################################
    #        Logging Related Class Methods
    ###########################################################################
    def fnAppend(self, message):
        """Used to append stuff to the Text Edit Box in the Log Window"""
        cursor = self.textDisplayArea.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(message)
        cursor.endEditBlock()
        self.textDisplayArea.setTextCursor(cursor)

    def fnClearLogger(self):
        """Used to clear the Log window"""
        self.textDisplayArea.clear()
        
    ###########################################################################
    #             Helper Functions....
    ###########################################################################
    ##  Helper Function used to add an list of Action Object to another widget
    ## @param self The object pointer.
    ## @param target The target widget you want to add actions too
    ## @param actions The list of actions you want to add to an widget
    def addActions(self, target, actions):
        """Helper Function used to add an list of Action Object to another widget"""
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)
                             
    ## Creates an action object and configures the possible parameters
    ## @param self The object pointer.
    ## @param text The name of the action
    ## @param slot Assign an optional slot to the action
    ## @param shortcut Assign an optional shortcut to the action
    ## @param icon Assign an optional icon to the action
    ## @param tip Assign an optional status bar tip to the action
    ## @param checkable Indicate if the action is checkable or not
    ## @param signal Assign an optional signal to the action
    def createAction(self, text, slot=None, shortcut=None, icon=None,
                     tip=None, checkable=False, signal="triggered()"):
        """Creates an action object and configures the possible parameters"""
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action


    ###########################################################################
    #             Menu Bar Functions
    ###########################################################################   
    ## This function is called when the window is closed and the close event is generated
    ## @param self The object pointer.
    ## @param event The close event is passed to the function
    def closeEvent(self, event):
        """When the window is closed, the current window state, size and 
           position are saved to the registry"""

        # Save Main Window settings
        self.settings.setValue("MainWindow/Size",     QVariant(self.size()))
        self.settings.setValue("MainWindow/Position", QVariant(self.pos()))
        self.settings.setValue("MainWindow/State",    QVariant(self.saveState()))
                
        event.accept()

    ## Displays the Help information for the program
    ## @param self The object pointer.
    def helpAbout(self):
        """Displays the Help information for the program"""
        QMessageBox.about(self, "About SE1 Fan Programmer",
                """<b>SE1 Fan Programmer</b> v %s
                <p>Copyright &copy; 2016 Schneider Electric Inc. 
                All rights reserved.
                <p>This program is used to program the SE1 fans during manufacturing.
                <p>Python %s - Qt %s - PyQt %s on %s""" % (
                __version__, platform.python_version(),
                QT_VERSION_STR, PYQT_VERSION_STR, platform.system()))


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName("Schneider Electric Inc.")
    app.setOrganizationDomain("schneider-electric.com")
    app.setApplicationName("SE1 Fan Programmer")
    app.setWindowIcon(QIcon(":/fan.ico"))
    
    #pipe all the stdout and stderr to the LoggerWidget
    logger = Logger()
    sys.stdout =  logger
    sys.stderr =  logger

    form = MainWindow(logger = logger)
    form.show()

    app.exec_()    

main()

