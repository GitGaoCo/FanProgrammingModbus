################################################################################
# Copyright (c) 2017 Schneider Electric Solar Inverters USA, Inc.  
# 
# No part of this document may be reproduced in any form or disclosed to third 
# parties without the express written consent of: 
# Schneider Electric Solar Inverters USA, Inc.
#
# FILE NAME:  
#     SConstruct
#
# PURPOSE:
#   Used to build the program to program the SE1 fans.
#   
#      
#    
# NOTES:
#
# CHANGE HISTORY:
# $Log: SConstruct $
#    
################################################################################

###############################################################################
#                           Included Modules                                  #
###############################################################################
import os
import sys
import subprocess
import re
import fileinput
#monitor_stdout = sys.stdout
################################################################################
#                                       Defines                                #
################################################################################
GUISOURCEFILE = 'SE1FanProgrammer.pyw'
SOURCEFILES = Glob('*.py')
SOURCEFILES += Glob('*.pyw')
#PyInstaller Spec File
SPECFILE = 'SE1FanProgrammer.spec'

#Version Reg-ex Patterns
SRC_PATTERN = re.compile('(^__version__\s=\s")([x\d].[x\d].[x\d]+)(")')
VER_PATTERN = re.compile('([x\d].[x\d].[x\d]+)')

# Inno installer stuff...
ISSFILE = 'SE1FanProgrammer.iss'
ISS_PATTERN = re.compile(r'(AppVerName=SE1 Fan Programmer V)')

INNO_LOCATION = None
INNO_TEST_LOCATION_1 = r'C:\Program Files\Inno Setup 5\ISCC.exe'
INNO_TEST_LOCATION_2 = r'C:\Program Files (x86)\Inno Setup 5\ISCC.exe'

if os.path.exists(INNO_TEST_LOCATION_1):
    INNO_LOCATION = '\"' + INNO_TEST_LOCATION_1 + '\" {}'
elif os.path.exists(INNO_TEST_LOCATION_2):
    INNO_LOCATION = '\"' + INNO_TEST_LOCATION_2 + '\" {}'
elif not INNO_LOCATION:
    raise Exception, "Inno Setup was not found on system"

################################################################################
#                    General Purpose Function Definitions                      #
################################################################################

def fnVersionFormatValid(versionstring):
    if VER_PATTERN.match(versionstring):
        return
    else:
        raise Exception, 'Not correct version format'

def fnReplaceVersionInLine(file,  repattern,  version):
    
    boolFoundAReplacment = False
      
    for line in fileinput.input(file, inplace=1):
        matchstring = repattern.match(line)
        if matchstring:
            line = VER_PATTERN.sub( version , line )
            boolFoundAReplacment = True
            #monitor_stdout.write(version)
            #monitor_stdout.write(line)
        sys.stdout.write(line)    
    fileinput.close()

    assert boolFoundAReplacment, "Pattern to replace not found"

################################################################################
#                        Script Start                                          #
################################################################################
vars = Variables()
vars.Add('SWVERSION', 'Sets the version in the form of x.x.x', 'x.x.x')

#Create environment
env = Environment(variables = vars)
Help(vars.GenerateHelpText(env))

print 'Building Software Version:' + env['SWVERSION']
fnVersionFormatValid(env['SWVERSION'])

#Change the version in the source files
fnReplaceVersionInLine( ISSFILE, ISS_PATTERN, env['SWVERSION'] )
fnReplaceVersionInLine( GUISOURCEFILE, SRC_PATTERN, env['SWVERSION'])
    
#Building the program
gui_depends = (SOURCEFILES, GUISOURCEFILE , ISSFILE, SPECFILE)
gui_targets = ('dist/bms_simulator/BMS_Simulator.exe')
gui_clean_files = [r'./dist', r'./build', r'./~', r'*.pyc']
gui_command = env.Command( gui_targets, gui_depends, 'C:\Python27\Scripts\pyinstaller.exe --noconfirm {}'.format(SPECFILE) )
env.Clean(gui_command , gui_clean_files)

#Building the Installer
installer_depends = ('.\dist', ISSFILE)
installer_targets = ('Output\SE1FanProg_V.exe')
installer_command = env.Command( installer_targets , installer_depends , INNO_LOCATION.format(ISSFILE))
installer_clean_files = Glob(r'.\Output')
env.Clean(installer_command , installer_clean_files)

#Copy the file and rename
rename_depends = ('Output\SE1FanProg_V.exe')
rename_targets = 'SE1FanProg_V' + env['SWVERSION'] + '.exe'
rename_clean_files = Glob('SE1FanProg_V*.exe')
rename_command = env.Command( rename_targets , rename_depends , Copy("$TARGET", "$SOURCE") )
env.Clean(rename_command , rename_clean_files)

