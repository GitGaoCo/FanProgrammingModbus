###############################################################################
#                               Includes
###############################################################################
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import logging
import time
import TestControl
import math
################################################################################
#                             Constant Data
################################################################################

DICT_ERROR = {'MSG0' : "Test Aborted",
              'MSG1' : "Error Opening Serial Port. Another program maybe accessing it",
              'MSG99': "Unknown Error, please save log file for troubleshooting"}

#STATUS ENUM
STATUS_ERROR        = -1
STATUS_NONE         =  0
STATUS_FAN1_RUNNING =  1 
STATUS_FAN2_RUNNING =  2 
STATUS_FAN3_RUNNING =  3 
STATUS_STARTING_TEST = 11
STATUS_FINISHED_TEST = 12
STATUS_ABORTING_TEST = 13

###############################################################################
#                            Function Definitions
###############################################################################
class TestScript(QThread):

    def __init__(self, parent = None):
        super(TestScript,  self).__init__(parent)
        
        logging.basicConfig(level=logging.DEBUG)
        self.TestLogger = logging.getLogger("Test")
        self.TestLogger.setLevel(logging.DEBUG)        
        self.boolAbortTest = False
        
        #Coupled to this module's global vars for STATUS
        self.enumTestStatus = STATUS_NONE
                
        self.dictTestSelection = {}
        
        #Create the test controller
        self.testcontroller = TestControl.TESTCONTROLER()
        
        #Get port settings from the registry
        self.settings = QSettings()
                
    def run(self):
        self.boolAbortTest = False
        #Run the test script....
        try:
            self.fnInitalizeConnections()
            self.TestScript()
            self.fnCloseConnections()           
        
        except Exception, e:
            logging.exception('Exception occurred during the test script')
            self.enumTestStatus = STATUS_ERROR            
            #Send out the exception to the GUI
            self.emit(SIGNAL("FinishPending"))
            self.emit(SIGNAL("Exception(QString)"), QString(e[0]))
    
            try:
                self.TestLogger.info("Exception Clean-Up: Shutdown Connections")
                self.fnCloseConnections()
            except:
                pass


            self.quit()
        
        #Script Completed Fine
        #Give warning to do any last updates.
        self.emit(SIGNAL("FinishPending"))
        time.sleep(0.5)
        self.quit()  
    
    def fnSetAbortFlag(self):
        logging.info('Aborting the Test at the next Check...')
        self.enumTestStatus = STATUS_ABORTING_TEST
        self.boolAbortTest = True

    def fnCheckAbortFlag(self):
        #logging.info('Checking the the Abort Flag is set')
        if self.boolAbortTest:
            logging.info('Aborting Test...')
            raise Exception, "Test Aborted"
                      
    def fnGetTestStatus(self):
        return self.enumTestStatus

    def fnInitalizeConnections(self):
        self.TestLogger.info("-------------------------------------------------------------")
        self.TestLogger.info(" Initializing connections                                    ")
        self.TestLogger.info("-------------------------------------------------------------")     

        self.TestLogger.info("Connecting to the Modbus Port")

#         self.commport = str(self.settings.value("spb1/ch1comm").toString())

    def fnCloseConnections(self):
        self.TestLogger.info("**************************************************************")
        self.TestLogger.info(" Shutting down connections                                    ")
        self.TestLogger.info("**************************************************************")

#         if hasattr(self, 'commport'):
#             self.commport.fnClose()    
#             delattr(self, "commport")
            

    def TestScript(self):
        self.enumTestStatus = STATUS_STARTING_TEST
        self.TestLogger.info("**************************************************************")
        self.TestLogger.info(" Starting Test Script                                         ")
        self.TestLogger.info("**************************************************************")               
        
        self.testcontroller.fnClearTestItems()
        
        if self.dictTestSelection['boolRunFan1']: 
            self.testcontroller.fnImportTestItemsFromCSV('Fan1Tests.csv')
            
        if self.dictTestSelection['boolRunFan2']: 
            self.testcontroller.fnImportTestItemsFromCSV('Fan2Tests.csv')

        if self.dictTestSelection['boolRunFan3']: 
            self.testcontroller.fnImportTestItemsFromCSV('Fan3Tests.csv')


        if self.dictTestSelection['boolRunFan1']: 
            self.TestLogger.info("****************************************")
            self.TestLogger.info("   Programming and Testing Fan 1        ")
            self.TestLogger.info("****************************************")
            self.enumTestStatus = STATUS_FAN1_RUNNING

        self.fnCheckAbortFlag() #Check the abort flag after each test            
        
        if self.dictTestSelection['boolRunFan2']: 
            self.TestLogger.info("****************************************")
            self.TestLogger.info("   Programming and Testing Fan 2        ")
            self.TestLogger.info("****************************************")
            self.enumTestStatus = STATUS_FAN2_RUNNING

        self.fnCheckAbortFlag() #Check the abort flag after each test

        if self.dictTestSelection['boolRunFan3']:             
            self.TestLogger.info("****************************************")
            self.TestLogger.info("   Programming and Testing Fan 3        ")
            self.TestLogger.info("****************************************")
            self.enumTestStatus = STATUS_FAN3_RUNNING
            

        self.enumTestStatus = STATUS_FINISHED_TEST
        
        self.testcontroller.fnResultsToLogging()

