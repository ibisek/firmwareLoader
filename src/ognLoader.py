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

    OGN_ID = '074812'

    # FILE_NAME = '../bin-files/aaa.bin'
    # FILE_NAME = '../bin-files/512.bin'
    # FILE_NAME = '../bin-files/pokus1blikac.f103-0x2800.bin'
    # FILE_NAME = '../bin-files/ognCube2.f103-0x2800.bin'
    FILE_NAME = '../bin-files/ognCube.bin'

    # FILE_NAME = '/home/ibisek/wqz/prog/stm32/ognCube2.f103/releases/ognCube2.f103-2018-06-01-1134-batt-cihlar.bin'

    #########################

    DEBUG = True
    PROG_START_ADDR = bytearray([0x08, 0x00, 0x28, 0x00])  # (0x1800 = 6kB; 0x2000 = 8kB; 0x2800 = 10kB)
    # PROG_START_ADDR = bytearray([0x08, 0x00, 0x20, 0x00])  # (0x1800 = 6kB; 0x2000 = 8kB; 0x2800 = 10kB)

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

    def flash(self, port, cpuId, startAddr, dataLen, data, blockSize):
        """
        @param cpuId        byteArray[3]
        @param startAddr    byteArray[4]
        @param dataLen      byteArray[3]
        @param data         byteArray[dataLen]
        @param blockSize    1024 for F103, 256 for L152
        """

        com = serial.Serial(port, baudrate=self.BAUD_RATE, timeout=1)

        # for firmwares already supporting RST command:
        print("Executing RST command now..")
        com.write(bytes("\n$CMDRST\n", 'utf-8'))
        sleep(10)  # wait for 8 seconds before flashing..
        lines = self.readOutBuffer(com)
        if self.DEBUG:
            print("Data after RST:", lines)

        if self.DEBUG: print("[INFO] Sending PROG")
        com.write(bytes("\nPROG", 'utf-8'))
        line = self.readLine(com)
        if self.DEBUG: print("\nline1:", line)

        if self.DEBUG: print(f"[INFO] Sending cpuId {cpuId}")
        if 'CPU ID' in line:  # expects 3 bytes of lowest CPU id
            com.write(bytes("\n", 'utf-8'))
            com.write(cpuId)

        line = self.readLine(com)
        if self.DEBUG: print("\nline2:", line)

        if self.DEBUG: print(f"[INFO] Sending startAddr {startAddr}")
        if 'START ADDR' in line:  # expects 4 bytes 0x08002800 (F103) or  0x08002000 (L152)
            com.write(bytes("\n", 'utf-8'))
            com.write(startAddr)

        line = self.readLine(com)
        if self.DEBUG: print("\nline3:", line)

        if self.DEBUG: print(f"[INFO] Seding dataLen: {dataLen}")
        if 'DATA LEN' in line:  # expects 3 bytes and length % 4 == 0
            com.write(bytes("\n", 'utf-8'))
            com.write(dataLen)

        line = self.readLine(com)
        if self.DEBUG: print("\nline4:", line)

        if 'OK' in line:  # expects [DATA LEN] bytes to FLASH
            print("Writing data.. ", end='')

            #         com.timeout = None
            #         numWritten = com.write(data)
            #         com.flush()
            #         print("{} bytes ".format(numWritten), end='')

            i = 0
            lastBlock = False
            while not lastBlock:
                if (i + 1) * blockSize < len(data):
                    buf = data[i * blockSize: (i + 1) * blockSize]
                else:
                    buf = data[i * blockSize:]
                    lastBlock = True

                com.write(buf)

                print(TextColors.WARNING + "#" + TextColors.ENDC, end='')
                sys.stdout.flush()
                i += 1

                if not lastBlock:
                    # Give the uC time to store the bytes into flash.
                    # And yes - it really needs some time (1.2s seems to be reasonable time to write 1kB).
                    # sleep(0.9)
                    sleep(1.2 * (blockSize / 1024))

            print(" done.")

        print("Waiting for CRC.. ")
        line = self.readLine(com)  # CRC
        if self.DEBUG: print("line5:", line)

        pattern = re.compile(r'\d+')
        mikroCrc = int(pattern.findall(line)[0])

        dataCrc = self.calcCrc(data)
        print(" file: {}\n device: {}\n".format(dataCrc, mikroCrc))

        if mikroCrc == dataCrc:
            print(TextColors.BOLD + TextColors.OKGREEN + 'FLASHing OK\n' + TextColors.ENDC)
        else:
            print(TextColors.BOLD + TextColors.FAIL + 'FLASHing FAILED\n' + TextColors.ENDC)

    def prepare(self, fileName=FILE_NAME, ognId=OGN_ID):
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


def getPort():
    port = OgnLoader.SERIAL_PORT
    if len(sys.argv) > 1:
        port = sys.argv[1]

    print('Using port ' + TextColors.BOLD + port + TextColors.ENDC)

    return port


def getFileName():
    fileName = OgnLoader.FILE_NAME
    if len(sys.argv) > 2:
        fileName = sys.argv[2]

    if not os.path.isfile(fileName):
        print("File '{}' not found.".format(fileName), file=sys.stderr)
        sys.exit(1)

    return fileName


def getOgnId():
    ognId = OgnLoader.OGN_ID
    if len(sys.argv) > 3:
        ognId = str(sys.argv[3]).encode('ascii').decode('ascii')

    print('Using OGN ID ' + TextColors.BOLD + ognId + TextColors.ENDC)

    return ognId


def getBlockSize():
    blockSize = 1024
    if len(sys.argv) > 4:
        blockSize = int(str(sys.argv[4]).encode('ascii').decode('ascii'))

    print('Using BLOCK_SIZE ' + TextColors.BOLD + str(blockSize) + TextColors.ENDC)

    return blockSize


if __name__ == '__main__':
    loader = OgnLoader()

    port = getPort()
    fileName = getFileName()
    ognId = getOgnId()
    blockSize = getBlockSize()

    (cpuId, startAddr, dataLen, data) = loader.prepare(fileName, ognId)
    loader.flash(port=port, cpuId=cpuId, startAddr=startAddr, dataLen=dataLen, data=data, blockSize=blockSize)
