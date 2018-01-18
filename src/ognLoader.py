#!/usr/bin/python3

'''
Tool for flashing STM32F103-based devices with serialLoader.f103

Created on Jan 16, 2018

@author: ibisek
'''


#######[ CONFIGURATION ]#######

#SERIAL_PORT = 'COM5'
SERIAL_PORT = '/dev/rfcomm1'

OGN_ID = '034819'

FILE_NAME = '../bin-files/pokus1blikac.f103.bin'

#########################

DEBUG = False
PROG_START_ADDR = bytearray([0x08, 0x00, 0x28, 0x00]) # (0x1800 = 6kB; 0x2000 = 8kB; 0x2800 = 10kB)

#########################

import os
import re
import sys
import serial
from time import sleep


def calcCrc(data):
    crc = 0
    for b in data:
        crc = crc ^ b
    
    return crc    


def readLine(com):
    line = ""
    while len(line) == 0:
        line += com.readline().decode('utf-8').strip()
        
    return line


'''
@param cpuId           byteArray[3]
@param startAddr     byteArray[4]
@param dataLen       byteArray[3]
@param data             byteArray[dataLen]
'''
def flash(cpuId, startAddr, dataLen, data):
    com = serial.Serial(SERIAL_PORT, baudrate=9600, timeout=1)
    
    com.write(bytes("\nPROG", 'utf-8'))
    line = readLine(com)
    if DEBUG: print("line1:", line)
    
    if 'CPU ID' in line:    # expects 3 bytes of lowest CPU id
        com.write(bytes("\n", 'utf-8'))
        com.write(cpuId)
    
    line = readLine(com)
    if DEBUG: print("line2:", line)
    
    if 'START ADDR' in line:    # expects 4 bytes 0x08002800
        com.write(bytes("\n", 'utf-8'))
        com.write(startAddr)
    
    line = readLine(com)
    if DEBUG: print("line3:", line)
         
    if 'DATA LEN' in line:  # expects 3 bytes and length % 4 == 0
        com.write(bytes("\n", 'utf-8'))
        com.write(dataLen)

    line = readLine(com)
    if DEBUG: print("line4:", line)
    
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
            i += 1
            sleep(1.2)    # give the uC time to store the bytes into flash; yes - it really needs some time
                    
        print(" done.")

    print("Waiting for CRC.. ")
    line = readLine(com)    # CRC
    if DEBUG: print("line5:", line)
    
    pattern = re.compile('\d+')
    mikroCrc = int(pattern.findall(line)[0])

    dataCrc = calcCrc(data)
    print(" file: {}\n device: {}\n".format(mikroCrc, dataCrc))
    
    if mikroCrc == dataCrc:
        print("FLASHing OK")
    else:
        print("FLASHing FAILED")


def prepare(fileName = FILE_NAME):
    # cpu ID:
    ognId = int(OGN_ID, 16)
    cpuId = bytearray([(ognId >> 16) & 0xFF, (ognId >> 8) & 0xFF, (ognId & 0xFF)])
    
    # startAddr:
    startAddr = PROG_START_ADDR
    
    # data & dataLen:
    data = None
    
    print("File to flash: ", fileName)
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
    
    fileName = FILE_NAME
    if len(sys.argv) > 1:
        fileName = sys.argv[1]
    
    if not os.path.isfile(fileName):
        print("File '{}' not found.".format(fileName), file=sys.stderr)
        sys.exit(1)
    
    return fileName


if __name__ == '__main__':
    
    fileName = getFileName()    
    (cpuId, startAddr, dataLen, data) = prepare(fileName)
    flash(cpuId, startAddr, dataLen, data)
