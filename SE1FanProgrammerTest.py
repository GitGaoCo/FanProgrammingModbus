###############################################################################
#                               Includes
###############################################################################
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import logging
import time
import TestControl
from itertools import izip_longest
import binascii
import serial
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

WRITE_SINGLE_REG_SER = '00 46'
WRITE_SINGLE_REG     = '06'
READ_MULTI_REG       = '03'

READ_ONE_BYTE       = '00 01'

FAN_ADDRESS_REG     = 'D1 00'
FAN1_ADDRESS_16 = '00 0B'
FAN2_ADDRESS_16 = '00 0C'
FAN3_ADDRESS_16 = '00 0D'
FAN1_ADDRESS_8  = '0B'
FAN2_ADDRESS_8  = '0C'
FAN3_ADDRESS_8  = '0D'

FAN_RESET_REG          = 'D0 00'
FAN_RESET_LOAD_NEWPARM = '00 02'

FAN_SET_SOURCE_REG  = 'D1 01'
FAN_SET_SOURCE_485 = '00 01'

FAN_CONTROL_MODE_PARM1_REG = 'D1 06'
FAN_CONTROL_MODE_PARM1_CLS_LOOP = '00 00'
            
CRC16_MODBUS_TABLE = [
    0x0000, 0xc0c1, 0xc181, 0x0140, 0xc301, 0x03c0, 0x0280, 0xc241,
    0xc601, 0x06c0, 0x0780, 0xc741, 0x0500, 0xc5c1, 0xc481, 0x0440,
    0xcc01, 0x0cc0, 0x0d80, 0xcd41, 0x0f00, 0xcfc1, 0xce81, 0x0e40,
    0x0a00, 0xcac1, 0xcb81, 0x0b40, 0xc901, 0x09c0, 0x0880, 0xc841,
    0xd801, 0x18c0, 0x1980, 0xd941, 0x1b00, 0xdbc1, 0xda81, 0x1a40,
    0x1e00, 0xdec1, 0xdf81, 0x1f40, 0xdd01, 0x1dc0, 0x1c80, 0xdc41,
    0x1400, 0xd4c1, 0xd581, 0x1540, 0xd701, 0x17c0, 0x1680, 0xd641,
    0xd201, 0x12c0, 0x1380, 0xd341, 0x1100, 0xd1c1, 0xd081, 0x1040,
    0xf001, 0x30c0, 0x3180, 0xf141, 0x3300, 0xf3c1, 0xf281, 0x3240,
    0x3600, 0xf6c1, 0xf781, 0x3740, 0xf501, 0x35c0, 0x3480, 0xf441,
    0x3c00, 0xfcc1, 0xfd81, 0x3d40, 0xff01, 0x3fc0, 0x3e80, 0xfe41,
    0xfa01, 0x3ac0, 0x3b80, 0xfb41, 0x3900, 0xf9c1, 0xf881, 0x3840,
    0x2800, 0xe8c1, 0xe981, 0x2940, 0xeb01, 0x2bc0, 0x2a80, 0xea41,
    0xee01, 0x2ec0, 0x2f80, 0xef41, 0x2d00, 0xedc1, 0xec81, 0x2c40,
    0xe401, 0x24c0, 0x2580, 0xe541, 0x2700, 0xe7c1, 0xe681, 0x2640,
    0x2200, 0xe2c1, 0xe381, 0x2340, 0xe101, 0x21c0, 0x2080, 0xe041,
    0xa001, 0x60c0, 0x6180, 0xa141, 0x6300, 0xa3c1, 0xa281, 0x6240,
    0x6600, 0xa6c1, 0xa781, 0x6740, 0xa501, 0x65c0, 0x6480, 0xa441,
    0x6c00, 0xacc1, 0xad81, 0x6d40, 0xaf01, 0x6fc0, 0x6e80, 0xae41,
    0xaa01, 0x6ac0, 0x6b80, 0xab41, 0x6900, 0xa9c1, 0xa881, 0x6840,
    0x7800, 0xb8c1, 0xb981, 0x7940, 0xbb01, 0x7bc0, 0x7a80, 0xba41,
    0xbe01, 0x7ec0, 0x7f80, 0xbf41, 0x7d00, 0xbdc1, 0xbc81, 0x7c40,
    0xb401, 0x74c0, 0x7580, 0xb541, 0x7700, 0xb7c1, 0xb681, 0x7640,
    0x7200, 0xb2c1, 0xb381, 0x7340, 0xb101, 0x71c0, 0x7080, 0xb041,
    0x5000, 0x90c1, 0x9181, 0x5140, 0x9301, 0x53c0, 0x5280, 0x9241,
    0x9601, 0x56c0, 0x5780, 0x9741, 0x5500, 0x95c1, 0x9481, 0x5440,
    0x9c01, 0x5cc0, 0x5d80, 0x9d41, 0x5f00, 0x9fc1, 0x9e81, 0x5e40,
    0x5a00, 0x9ac1, 0x9b81, 0x5b40, 0x9901, 0x59c0, 0x5880, 0x9841,
    0x8801, 0x48c0, 0x4980, 0x8941, 0x4b00, 0x8bc1, 0x8a81, 0x4a40,
    0x4e00, 0x8ec1, 0x8f81, 0x4f40, 0x8d01, 0x4dc0, 0x4c80, 0x8c41,
    0x4400, 0x84c1, 0x8581, 0x4540, 0x8701, 0x47c0, 0x4680, 0x8641,
    0x8201, 0x42c0, 0x4380, 0x8341, 0x4100, 0x81c1, 0x8081, 0x4040]

###############################################################################
#                            Function Definitions
###############################################################################

def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)

def _crc16(data, crc, table):
    """Calculate CRC16 using the given table.
    `data`      - data for calculating CRC, must be a string
    `crc`       - initial value
    `table`     - table for caclulating CRC (list of 256 integers)
    Return calculated value of CRC
    """
    for byte in data:
        tbl_idx = (crc ^ ord(byte)) & 0xff
        
        crc = (table[tbl_idx] ^ (crc >> 8)) & 0xffff  
    
    return crc & 0xffff

def crc16modbus(data, crc = 0xffff):
    """Calculate modbus variant of CRC16.
    `data`      - data for calculating CRC, must be a string
    `crc`       - initial value
    Return calculated value of CRC
    """
    return _crc16(data, crc, CRC16_MODBUS_TABLE)


class clSE1FanConnection(serial.Serial):
    def __init__(self, port):
        super(clSE1FanConnection, self).__init__(port, 
                                                 baudrate = 19200,
                                                 parity   = serial.PARITY_EVEN,
                                                 stopbits = serial.STOPBITS_ONE,
                                                 bytesize = serial.EIGHTBITS,
                                                 timeout  = 0.5)

    def fnSendandCheck(self,msg):
        
        lst_msg_byte = grouper(2, msg.replace(" ", ""))
        
        lstdata = []
        
        for byte in lst_msg_byte:
            lstdata.append(binascii.unhexlify("".join(byte))) 
        
        self.flushInput()
        self.write(lstdata)
        
        time.sleep(0.1)
        reply = self.read(100)
        return binascii.hexlify(reply)
    
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

        self.commport = str(self.settings.value("fan/mb_comm").toString())

        self.TestLogger.info("Connecting to the Modbus Port on {}".format(self.commport))

        self.sercon = clSE1FanConnection(self.commport)

    def fnCloseConnections(self):
        self.TestLogger.info("**************************************************************")
        self.TestLogger.info(" Shutting down connections                                    ")
        self.TestLogger.info("**************************************************************")

        if hasattr(self, 'sercon'):
            self.sercon.close()    
            delattr(self, "sercon")
            

    def fnGetModbudCRC(self, msg):
        #modbus crc calc.....
        msg_nospace = msg.replace(" ", "")
        lst_msg_byte = grouper(2, msg_nospace)
        
        lstdata = []
        for byte in lst_msg_byte:
            lstdata.append(binascii.unhexlify("".join(byte))) 
        
        #print lstdata
        hexstr_crc16 = format(crc16modbus(lstdata),'x').zfill(4).upper()
        
        grped_hexstr_crc16 = grouper(2, hexstr_crc16)
        lst_hexstr_crc16 = []
        for byte in grped_hexstr_crc16:
            lst_hexstr_crc16.append("".join(byte))
        
        return(lst_hexstr_crc16)
    
              

    def fnProgramFan(self, dictFanInfo):
        
        ###############
        self.TestLogger.info("Programming address...")            
        msg = "{} {} {} {}".format(WRITE_SINGLE_REG_SER,
                                   dictFanInfo['seraddress'],
                                   FAN_ADDRESS_REG,
                                   dictFanInfo['address16'])
        
        lst_hexstr_crc16 = self.fnGetModbudCRC(msg)
        #In Modbus... the LSB is sent first 
        sendmsg = msg + ' ' + lst_hexstr_crc16[1] + lst_hexstr_crc16[0]
        
        self.TestLogger.info("Sending command:" + sendmsg)

        reply = self.sercon.fnSendandCheck(sendmsg)
        self.TestLogger.info("Received the following:")
        self.TestLogger.info(reply)       
        self.testcontroller.fnTestBool(dictFanInfo['testcase'][0], len(reply) > 0)
        
        time.sleep(1)
        ###############
        self.TestLogger.info("Load new setting and reset...")             
        msg = "{} {} {} {}".format(WRITE_SINGLE_REG_SER,
                                   dictFanInfo['seraddress'],
                                   FAN_RESET_REG,
                                   FAN_RESET_LOAD_NEWPARM)
        
        lst_hexstr_crc16 = self.fnGetModbudCRC(msg)
        #In Modbus... the LSB is sent first 
        sendmsg = msg + ' ' + lst_hexstr_crc16[1] + lst_hexstr_crc16[0]
        
        self.TestLogger.info("Sending command:" + sendmsg)
        
        reply = self.sercon.fnSendandCheck(sendmsg)
        self.TestLogger.info("Received the following:")
        self.TestLogger.info(reply)
        self.testcontroller.fnTestBool(dictFanInfo['testcase'][1], len(reply) > 0)        
        
        time.sleep(1)
        ################
        self.TestLogger.info("Config Fan set-point source to 485 command...")              
        msg = "{} {} {} {}".format(dictFanInfo['address8'],
                                   WRITE_SINGLE_REG,
                                   FAN_SET_SOURCE_REG,
                                   FAN_SET_SOURCE_485)
        
        lst_hexstr_crc16 = self.fnGetModbudCRC(msg)
        #In Modbus... the LSB is sent first 
        sendmsg = msg + ' ' + lst_hexstr_crc16[1] + lst_hexstr_crc16[0]
        
        self.TestLogger.info("Sending command:" + sendmsg)

        reply = self.sercon.fnSendandCheck(sendmsg)
        self.TestLogger.info("Received the following:")
        self.TestLogger.info(reply)
        self.testcontroller.fnTestBool(dictFanInfo['testcase'][2], len(reply) > 0) 
        
        time.sleep(1)
        ################
        self.TestLogger.info("Config speed control to closed loop...")              
        msg = "{} {} {} {}".format(dictFanInfo['address8'],
                                   WRITE_SINGLE_REG,
                                   FAN_CONTROL_MODE_PARM1_REG,
                                   FAN_CONTROL_MODE_PARM1_CLS_LOOP)
        
        lst_hexstr_crc16 = self.fnGetModbudCRC(msg)
        #In Modbus... the LSB is sent first 
        sendmsg = msg + ' ' + lst_hexstr_crc16[1] + lst_hexstr_crc16[0]
        
        self.TestLogger.info("Sending command:" + sendmsg) 
        
        reply = self.sercon.fnSendandCheck(sendmsg)
        self.TestLogger.info("Received the following:")
        self.TestLogger.info(reply)
        self.testcontroller.fnTestBool(dictFanInfo['testcase'][3], len(reply) > 0) 
        ###############
        
        self.TestLogger.info("Load new setting and reset...")             
        msg = "{} {} {} {}".format(dictFanInfo['address8'],
                                   WRITE_SINGLE_REG,
                                   FAN_RESET_REG,
                                   FAN_RESET_LOAD_NEWPARM)
        
        lst_hexstr_crc16 = self.fnGetModbudCRC(msg)
        #In Modbus... the LSB is sent first 
        sendmsg = msg + ' ' + lst_hexstr_crc16[1] + lst_hexstr_crc16[0]
        
        self.TestLogger.info("Sending command:" + sendmsg)
        
        reply = self.sercon.fnSendandCheck(sendmsg)
        self.TestLogger.info("Received the following:")
        self.TestLogger.info(reply)
        self.testcontroller.fnTestBool(dictFanInfo['testcase'][4], len(reply) > 0)        
        
        time.sleep(1)

        ###############
        
        self.TestLogger.info("Check that control is closed loop...")             
        msg = "{} {} {} {}".format(dictFanInfo['address8'],
                                   READ_MULTI_REG,
                                   FAN_CONTROL_MODE_PARM1_REG,
                                   READ_ONE_BYTE)
        
        lst_hexstr_crc16 = self.fnGetModbudCRC(msg)
        #In Modbus... the LSB is sent first 
        sendmsg = msg + ' ' + lst_hexstr_crc16[1] + lst_hexstr_crc16[0]
        
        self.TestLogger.info("Sending command:" + sendmsg)
        
        reply = self.sercon.fnSendandCheck(sendmsg)
        self.TestLogger.info("Received the following:")
        self.TestLogger.info(reply)
        self.testcontroller.fnTestBool(dictFanInfo['testcase'][5], reply[6:10] == "0000")        
        
        time.sleep(1)        
        
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
            
            self.testcontroller.fnRecordMeasurement('BL601_0',
                                                    self.dictTestSelection['dictSerFan1']['serialnum'])
            
            dictFanInfo = {}
            dictFanInfo['address16']  = FAN1_ADDRESS_16
            dictFanInfo['address8']   = FAN1_ADDRESS_8
            dictFanInfo['seraddress'] = self.dictTestSelection['dictSerFan1']['full_add']
            dictFanInfo['testcase']   = ('BL601_1', 
                                         'BL601_2', 
                                         'BL601_3', 
                                         'BL601_4',
                                         'BL601_5',
                                         'BL601_6')
            self.fnProgramFan(dictFanInfo)

        self.fnCheckAbortFlag() #Check the abort flag after each test            
        
        if self.dictTestSelection['boolRunFan2']: 
            self.TestLogger.info("****************************************")
            self.TestLogger.info("   Programming and Testing Fan 2        ")
            self.TestLogger.info("****************************************")
            self.enumTestStatus = STATUS_FAN2_RUNNING

            self.testcontroller.fnRecordMeasurement('BL602_0',
                                                    self.dictTestSelection['dictSerFan2']['serialnum'])

            dictFanInfo = {}
            dictFanInfo['address16']  = FAN2_ADDRESS_16
            dictFanInfo['address8']   = FAN2_ADDRESS_8
            dictFanInfo['seraddress'] = self.dictTestSelection['dictSerFan2']['full_add']
            dictFanInfo['testcase']   = ('BL602_1',
                                         'BL602_2',
                                         'BL602_3',
                                         'BL602_4',
                                         'BL602_5',
                                         'BL602_6')
            self.fnProgramFan(dictFanInfo)

        self.fnCheckAbortFlag() #Check the abort flag after each test

        if self.dictTestSelection['boolRunFan3']:             
            self.TestLogger.info("****************************************")
            self.TestLogger.info("   Programming and Testing Fan 3        ")
            self.TestLogger.info("****************************************")
            self.enumTestStatus = STATUS_FAN3_RUNNING

            self.testcontroller.fnRecordMeasurement('BL603_0',
                                                    self.dictTestSelection['dictSerFan3']['serialnum'])

            dictFanInfo = {}
            dictFanInfo['address16']  = FAN3_ADDRESS_16
            dictFanInfo['address8']   = FAN3_ADDRESS_8
            dictFanInfo['seraddress'] = self.dictTestSelection['dictSerFan3']['full_add']
            dictFanInfo['testcase']   = ('BL603_1',
                                         'BL603_2',
                                         'BL603_3',
                                         'BL603_4',
                                         'BL603_5',
                                         'BL603_6')
            self.fnProgramFan(dictFanInfo)            

        self.enumTestStatus = STATUS_FINISHED_TEST
        
        self.testcontroller.fnResultsToLogging()

