""""
Read data from CO2 sensor
"""

import time
import logging

import serial

MHZ19_SIZE = 9
MZH19_READ = [0xff, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79]
MZH19_RESET = [0xff, 0x01, 0x87, 0x00, 0x00, 0x00, 0x00, 0x00, 0x78]
MHZ19_DISABLE_ABC = [0xff, 0x01, 0x79, 0x00, 0x00, 0x00, 0x00, 0x00, 0x86]

def send_data(data, serial_device):
    """Send data to device"""

    ser = serial.Serial(port=serial_device,
                        baudrate=9600,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        bytesize=serial.EIGHTBITS)
    ser.write(data)

    return None

def disable_ABC_logic(serial_device):
    """Disable automatic baseline correction"""

    send_data(MHZ19_DISABLE_ABC, serial_device)

    return None

def reset_mh_z19(serial_device):
    """reset to zero"""    

    logger = logging.getLogger(__name__)

    send_data(MZH19_RESET, serial_device)

    return None

def read_mh_z19(serial_device):
    """ Read the CO2 PPM concenration from a MH-Z19 sensor"""

    result = read_mh_z19_with_temperature(serial_device)
    if result is None:
        return None
    ppm, temp = result
    return ppm


def read_mh_z19_with_temperature(serial_device):
    """ Read the CO2 PPM concenration and temperature from a MH-Z19 sensor"""

    logger = logging.getLogger(__name__)

    sbuf = bytearray()
    starttime = time.time()
    finished = False
    timeout = 2
    res = None
    send_data(MZH19_READ, serial_device)
    while not finished:
        mytime = time.time()
        if mytime - starttime > timeout:
            logger.error("read timeout after %s seconds, read %s bytes",
                         timeout, len(sbuf))
            return None

        if ser.inWaiting() > 0:
            sbuf += ser.read(1)

            if len(sbuf) == MHZ19_SIZE:
                logger.debug("Finished reading data %s", sbuf)

                received_checksum = sbuf[-1]
                logger.debug("received_checksum: %s", received_checksum)
                # checksum: (NOT (Byte1+Byte1+Byte2+Byte3+Byte5+Byte6+Byte7)) + 1
                calculated_checksum = (~sum(bytearray(sbuf[1:8])) & 0xFF) + 1
                logger.debug("calculated_checksum: %s", calculated_checksum)
                if sbuf[0] != 0xFF or received_checksum != calculated_checksum:
                    logger.error('bad checksum for data: %s received: %s calculated: %s',
                                 sbuf, received_checksum, calculated_checksum)
                    return None

                res = (sbuf[2]*256 + sbuf[3], sbuf[4] - 40)
                finished = True

        else:
            time.sleep(.1)
            logger.debug("Serial waiting for data, buffer length=%s",
                         len(sbuf))

    return res
