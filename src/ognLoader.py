'''
Created on Jan 16, 2018

@author: ibisek
'''

#######[ CONFIGURATION ]#######

SERIAL_PORT = '/dev/rfcomm1'
#SERIAL_PORT = 'COM5'

OGN_ID = '034819'

BIN_FILE = '../bin-files/pokus1blikac.f103.bin'

#########################

import serial

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
    print("line1:", line)
    
    if 'CPU ID' in line:    # expects 3 bytes of lowest CPU id
        com.write(bytes("\n", 'utf-8'))
        com.write(cpuId)
    
    line = readLine(com)
    print("line2:", line)
    
    if 'START ADDR' in line:    # expects 4 bytes 0x08002800
        com.write(bytes("\n", 'utf-8'))
        com.write(bytearray(startAddr)
    
    line = readLine(com)
    print("line3:", line)
         
    if 'DATA LEN' in line:  # expects 3 bytes and length % 4 == 0
        com.write(bytes("\n", 'utf-8'))
        com.write(dataLen)

    line = readLine(com)
    print("line4:", line)
    
    if 'OK' in line:  # expects [DATA LEN] bytes to FLASH
        #com.write(bytearray([0x00, 0x80, 0x00]))    # 32kB
        pass

    line = readLine(com)    # CRC
    print("line5:", line)

def prepare():
    # cpu ID:
    ognId = int("0x"+OGN_ID, 16)
    cpuId = bytearray([(ognId >> 16) & 0xFF, (ognId >> 8) & 0xFF, (ognId & 0xFF)])
    
    # startAddr:
    startAddr = [0x08, 0x00, 0x28, 0x00])
    
    # data & dataLen:
    data = None
    
    print("File to flash: ", BIN_FILE)
    f = open(BIN_FILE, "rb")
    try:
        data = f.read()
    finally:
        f.close()
    
    if data:    # bytearray([0x00, 0x80, 0x00])
        dataLen = len(data)
        print("data length:", dataLen)
        dataLen = dataLen.to_bytes(3, byteorder='big')
        print("dataLen:", dataLen)
        print("dataLen:", type(dataLen)
    
    return (cpuId, startAddr, dataLen, data)    

if __name__ == '__main__':

    (cpuId, startAddr, dataLen, data) = prepare()
#     flash(cpuId, startAddr, dataLen, data)
    
    print("KOHEU.")
    
    