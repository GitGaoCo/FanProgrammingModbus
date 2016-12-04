__version__ = "x.x.x"
###############################################################################
# Copyright (c) 2013 Schneider Electric.  All rights reserved.
# 
# This source file is proprietary to Schneider Electric Industries SAS or its 
# affiliated companies and protected by copyright. The reproduction, in whole 
# or in part, by anyone without the written approval of Schneider Electric 
# is prohibited.
#
# FILE NAME:  TestControl.py
#
# PURPOSE:
#     This file contains functions that are common across scripts so that 
#     they can be reused.
# 
#
#
# FUNCTION(S):
#
#     local:
#
# NOTES:
#
# CHANGE HISTORY :
# 1.10   Oct  02, 2013   Francis Kwok - Added stop time to write to csv function.
# 1.08   Oct  10, 2012   Francis Kwok - Re-factored package a bit so it can be created
#                                       without a csv file.
# 1.07   May  31, 2012   Kin Ming Li  - Added fnGetFileNum for consistent file numbering
# 1.06   Feb  15, 2011   Francis Kwok - Added ability to stamp the test suite versions 
# 1.05   Jan  20, 2010   Francis Kwok - Expanded the MEAS field in fnResultsToLogging
#                                       to accommodate version string size
# 1.04   Dec  30, 2009   Francis Kwok - Added option to show string for the 
#                                       fnTestBool test.
# 1.03   Dec  17, 2009   Francis Kwok - Strip leading/trailing white space from
#                                       serial numbers.
# 1.02   Nov  24, 2009   Francis Kwok - Fixed bool test
#                                     - Added RPC function to send out test count
# 1.01   June 29, 2009   Francis Kwok - Added a function to test boolean tests.
# 1.00   June 19, 2009   Francis Kwok - Creation.
#
# $Log: TestControl.py
##############################################################################

##############################################################################
#                               Logging Module Setup
###############################################################################
import logging
#create logger
if __name__ == "__main__":  
    logging.basicConfig(level=logging.DEBUG)

TestLogger = logging.getLogger("TstCtrl")
TestLogger.setLevel(logging.DEBUG)

###############################################################################
#                               Includes
###############################################################################
import csv
import datetime
import os
import time
import prettytable
###############################################################################
#                             Constant Data
###############################################################################

class TESTCONTROLER(object):
    
    def __init__(self, csvfile = None, logfile = '' ):
        """Constructor for the Test Controller """

        self.testsuiteversion = __version__ = "x.x.x"
        self.logfilename = logfile.strip()
        self.startdatetime = str(datetime.datetime.now())
        self.stopdatetime = None

        self.passcount = 0
        self.failcount = 0
        self.testcount = 0
        self.dictTestItems = {}
        self.path = None

        if csvfile:
            self.fnImportTestItemsFromCSV(csvfile)
    
    def fnClearTestItems(self):
        self.dictTestItems = {}
        self.passcount = 0
        self.failcount = 0
        self.testcount = 0        
        self.path = None
        
    def fnImportTestItemsFromCSV(self, csvfile = None):
        #Load up the csv file information into the test item dictionary.
        #If there is already items in the dictionary, it will add new ones.
        tempdict = {}

        if csvfile:
        
            DictReader = csv.DictReader(open(csvfile))
            for Dictionary in DictReader:
                tempdict[Dictionary['TCID']] = Dictionary
                self.dictTestItems.update(tempdict)
        else:
            raise Exception, "No CSV file specified..."
        
    def PassCurrentPassCount(self):
        """Returns the current pass count"""
        return self.passcount
    
    def PassCurrentFailCount(self):
        """Returns the current fail count"""
        return self.failcount
    
    def PassTestCount(self):
        """Returns the how many tests there are in the script """
        #count the number of tests
        self.testcount = 0
        keys = self.dictTestItems.keys()
        for key in keys:
            testtype = self.dictTestItems[key]['Type'] 
            if (testtype == 'Test') or (testtype == 'SetPoint'):
                self.testcount = self.testcount + 1        
        return self.testcount
    
    def PassCurrentStatus(self):
        """Returns the status dictionary that contains current test information"""
        return self.dictTestItems


    def fnGetFileNum(self):
        
        basename = self.logfilename
        
        self.filenum = 0
        while os.path.exists(self.path+str(basename)+'_'+str(self.filenum)+'.csv') or os.path.exists(self.path+str(basename)+str(self.filenum)+'.log'):
            self.filenum += 1
        return self.filenum

    def fnWriteToCsv(self, csvfilenamepath):
        """Log to csv file"""
        listTestFieldNames = ['TCID', 'Min', 'Max', 'Descript', 'Type', 'Prop', 'Meas', 'Result']
        
        DictWriter = csv.DictWriter(open(csvfilenamepath, 'w'), listTestFieldNames,  lineterminator = '\n')
        
        KeyList = self.dictTestItems.keys()
        
        for key in sorted(KeyList):        
            DictWriter.writerow(self.dictTestItems[key])
        
        
    def fnIncrementPassCount(self):
        self.passcount = self.passcount + 1

    def fnIncrementFailCount(self):
        self.failcount = self.failcount + 1

    def fnRecordMeasurement(self,  key,  measurement):
        TestItem = self.dictTestItems[key]
        TestItem['Meas'] = measurement
        
        msg = "Recording Information for Test Case: " + key + ":" + TestItem['Descript'] + '; Property: ' + TestItem['Prop']
        TestLogger.info(msg)
        
    def fnTestBool(self,  key,  boolMeas, strResult = None):
        TestItem = self.dictTestItems[key]
        
        if strResult:             
            TestItem['Meas'] = str(strResult)
        else:
            TestItem['Meas'] = boolMeas       
        
        TestLogger.info("Testing Test Case: " + key + ":" + TestItem['Descript'] + '; Property: ' + TestItem['Prop'])        
        TestLogger.info("Expected the True/False Test to be:" + str(bool(int(TestItem['Max']))))
        TestLogger.info("Measured Value: " + str(boolMeas))        
       
        if (bool(int(TestItem['Max'])) == bool(boolMeas)):
            self.fnIncrementPassCount()
            TestItem['Result'] = 'Pass'
            TestLogger.info('Test Pass')
        else:
            self.fnIncrementFailCount()
            TestItem['Result'] = 'FAIL'
            TestLogger.info('Test FAIL')

    def fnTestDiff(self, key,  expected , measurement):
        TestItem = self.dictTestItems[key]
        absdiff = abs(expected - measurement)
        
        TestItem['Meas'] = absdiff
        
        TestLogger.info("Testing Test Case: " + key + ":" + TestItem['Descript'] + '; Property: ' + TestItem['Prop'])
        TestLogger.info("Expected Value should be: %s" %(str(expected)))
        TestLogger.info("Measured Value is: %s" %(str(measurement)))
        TestLogger.info("Testing Difference is between " + str(TestItem['Min']) + ' and ' +  str(TestItem['Max']))
        TestLogger.info("Absolute Difference is: " + str(absdiff))
        
        if self.fninMaxMin(absdiff,TestItem['Max'], TestItem['Min']):
            self.fnIncrementPassCount()
            TestItem['Result'] = 'Pass'
            TestLogger.info('Test Pass')
        else:
            self.fnIncrementFailCount()
            TestItem['Result'] = 'FAIL'
            TestLogger.info('Test FAIL')

    def fnTestMeasurement(self, key,  measurement):
        TestItem = self.dictTestItems[key]
        TestItem['Meas'] = measurement

        TestLogger.info("Testing Test Case: " + key + ":"  + TestItem['Descript'] + '; Property: ' + TestItem['Prop'])
        TestLogger.info("Testing value is between " + str(TestItem['Min']) + ' and ' +  str(TestItem['Max']))
        TestLogger.info("Measured Value: " + str(measurement))
               
        if self.fninMaxMin(measurement, TestItem['Max'], TestItem['Min']):
            self.fnIncrementPassCount()
            TestItem['Result'] = 'Pass'
            TestLogger.info('Test Pass')
        else:
            self.fnIncrementFailCount()
            TestItem['Result'] = 'FAIL'
            TestLogger.info('Test FAIL')

    def fnCheckPass(self,  key):
        """Checks if a test has passed."""
        TestItem = self.dictTestItems[key]
        if TestItem['Result'] == 'Pass':
            return True
        else:
            return False

    def fnResultsToLogging(self):
        table = prettytable.PrettyTable(['TESTID', 'DESCRIPTION' , 'PROP','MIN', 'MAX', 'MEAS',  "RESULT"])
        table.align["DESCRIPTION"] = "l" # Left align DESCRIPTION

        KeyList = self.dictTestItems.keys()
        
        for key in sorted(KeyList):
            
            currenttest = self.dictTestItems[key]
            
            if currenttest['Result'] == '':
                currenttest['Result'] = "NotTested"
            if currenttest['Meas'] == '':
                currenttest['Meas'] = "None"           
            
            table.add_row([currenttest['TCID'], 
                          currenttest['Descript'],
                          currenttest['Prop'],
                          currenttest['Min'],
                          currenttest['Max'],
                          currenttest['Meas'],
                          currenttest['Result']])           

        for line in (table.get_string().split('\n')):
            TestLogger.info("'" + line + "'")
        TestLogger.info("TEST PASS: %i" % self.passcount)
        TestLogger.info("TEST FAIL: %i" % self.failcount)
        
    def fninMaxMin(self, value, maximum, minimum):
        value = float(value)
        minimum = float(minimum)
        maximum = float(maximum)

        if (value >= minimum) and (value <= maximum):
            return True
        else:
            return False

            
if __name__ == "__main__":
    TestSuiteFile = 'ProductionSelfTest.csv'
    Serial = '12312312'
    spb9_testcontrol = TESTCONTROLER(TestSuiteFile,  Serial)
    
    spb9_testcontrol.fnTestMeasurement('1_1_1', 3.2313123)
    spb9_testcontrol.fnResultsToLogging()
    print spb9_testcontrol.PassTestCount()
    spb9_testcontrol.fnWriteToCsv()
    time.sleep(3600)

