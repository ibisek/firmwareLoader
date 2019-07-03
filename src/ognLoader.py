#!/usr/bin/python3

'''
Tool for flashing STM32F103-based devices with serialLoader.f103

Created on Jan 16, 2018

@author: ibisek
'''

import os
import re
import sys
import serial
from time import sleep

class TextColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class OgnLoader(object):

    #######[ CONFIGURATION ]#######

    # SERIAL_PORT = 'COM5'
    # SERIAL_PORT = '/dev/ttyUSB0'
    SERIAL_PORT = '/dev/rfcomm0'
    BAUD_RATE = 115200

    OGN_ID = '173153'

    # FILE_NAME = '../bin-files/aaa.bin'
    # FILE_NAME = '../bin-files/512.bin'
    # FILE_NAME = '../bin-files/pokus1blikac.f103-0x2800.bin'
    FILE_NAME = '../bin-files/ognCube2.f103-0x2800.bin'

    # FILE_NAME = '/home/ibisek/wqz/prog/stm32/ognCube2.f103/releases/ognCube2.f103-2018-06-01-1134-batt-cihlar.bin'

    #########################

    DEBUG = True
    PROG_START_ADDR = bytearray([0x08, 0x00, 0x28, 0x00]) # (0x1800 = 6kB; 0x2000 = 8kB; 0x2800 = 10kB)

    #########################


    def calcCrc(self, data):
        crc = 0
        for b in data:
            crc = crc ^ b

        return crc


    def readLine(self, com):
        line = ""
        while len(line) == 0:
            try:
                line += com.readline().decode('utf-8').strip()
            except UnicodeDecodeError:
                # after RST there is gibberish as bootloader first tries to setup speed
                pass

        return line
    
    def readOutBuffer(self, com):
        data = com.read_all()
        
        return data

    '''
    @param cpuId           byteArray[3]
    @param startAddr     byteArray[4]
    @param dataLen       byteArray[3]
    @param data             byteArray[dataLen]
    '''
    def flash(self, cpuId, startAddr, dataLen, data):
        com = serial.Serial(self.SERIAL_PORT, baudrate=self.BAUD_RATE, timeout=1)
        
        # for firmwares already supporting RST command:
        print("Executing RST command now..")
        com.write(bytes("\n$CMDRST\n", 'utf-8'))
        sleep(10)    # wait for 8 seconds before flashing.. 
        lines = self.readOutBuffer(com)
        if self.DEBUG:
            print("Data after RST:", lines)

        com.write(bytes("\nPROG", 'utf-8'))
        line = self.readLine(com)
        if self.DEBUG: print("line1:", line)

        if 'CPU ID' in line:    # expects 3 bytes of lowest CPU id
            com.write(bytes("\n", 'utf-8'))
            com.write(cpuId)

        line = self.readLine(com)
        if self.DEBUG: print("line2:", line)

        if 'START ADDR' in line:    # expects 4 bytes 0x08002800
            com.write(bytes("\n", 'utf-8'))
            com.write(startAddr)

        line = self.readLine(com)
        if self.DEBUG: print("line3:", line)

        if 'DATA LEN' in line:  # expects 3 bytes and length % 4 == 0
            com.write(bytes("\n", 'utf-8'))
            com.write(dataLen)

        line = self.readLine(com)
        if self.DEBUG: print("line4:", line)

        if 'OK' in line:  # expects [DATA LEN] bytes to FLASH
            print("Writing data.. ", end='')

    #         com.timeout = None
    #         numWritten = com.write(data)
    #         com.flush()
    #         print("{} bytes ".format(numWritten), end='')

            BLOCK_SIZE = 1024
            i = 0
            lastBlock= False
            while not lastBlock:
                if (i+1)*BLOCK_SIZE < len(data):
                    buf = data[i*BLOCK_SIZE: (i+1)*BLOCK_SIZE]
                else:
                    buf = data[i*BLOCK_SIZE:]
                    lastBlock = True

                com.write(buf)

                print("#", end='')
                sys.stdout.flush()
                i += 1

                if not lastBlock:
                    sleep(0.9)    # give the uC time to store the bytes into flash; yes - it really needs some time (1.2s seems to be viable minimum)

            print(" done.")

        print("Waiting for CRC.. ")
        line = self.readLine(com)    # CRC
        if self.DEBUG: print("line5:", line)

        pattern = re.compile('\d+')
        mikroCrc = int(pattern.findall(line)[0])

        dataCrc = self.calcCrc(data)
        print(" file: {}\n device: {}\n".format(dataCrc, mikroCrc))

        if mikroCrc == dataCrc:
            print(TextColors.OKGREEN + 'FLASHing OK\n' + TextColors.ENDC)
        else:
            print(TextColors.FAIL + 'FLASHing FAILED\n' + TextColors.ENDC)


    def prepare(self, fileName = FILE_NAME, ognId=OGN_ID):
        # cpu ID:
        ognId = int(ognId, 16)
        cpuId = bytearray([(ognId >> 16) & 0xFF, (ognId >> 8) & 0xFF, (ognId & 0xFF)])

        # startAddr:
        startAddr = self.PROG_START_ADDR

        # data & dataLen:
        data = None

        print("File to flash:", fileName)
        f = open(fileName, "rb")
        try:
            data = f.read()
        finally:
            f.close()

        if data:
            dataLen = len(data)
            print("Data length: {} B".format(dataLen))
            dataLen = dataLen.to_bytes(3, byteorder='big')  # bytearray([0x00, 0x80, 0x00])

        return (cpuId, startAddr, dataLen, data)

def getFileName():
    fileName = OgnLoader.FILE_NAME
    if len(sys.argv) > 1:
        fileName = sys.argv[1]

    if not os.path.isfile(fileName):
        print("File '{}' not found.".format(fileName), file=sys.stderr)
        sys.exit(1)

    return fileName

def getOgnId():
    ognId = OgnLoader.OGN_ID
    if len(sys.argv) > 2:
        ognId = str(sys.argv[2]).encode('ascii').decode('ascii')

    print('Using OGN ID ' + TextColors.BOLD +  ognId + TextColors.ENDC)

    return ognId


if __name__ == '__main__':

    loader = OgnLoader()

    fileName = getFileName()
    ognId = getOgnId()

    (cpuId, startAddr, dataLen, data) = loader.prepare(fileName, ognId)
    loader.flash(cpuId, startAddr, dataLen, data)
