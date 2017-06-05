#!/usr/bin/env python3
import argh
import serial
import serial.tools.list_ports
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
#import obd
import time
import json
import sys

def read_until_prompt(device):
    buffer = bytearray()
    while True:
        data = device.read(device.in_waiting or 1)
        buffer.extend(data)
        lines = buffer.split(b'\r')
        for line in lines[:-1]:
            line = line.strip()
            if len(line) > 0:
                yield line
        buffer = lines[-1]
        if b'>' in buffer:
            break

def read_one(device):
    buffer = bytearray()
    c = ''
    while True:
        c = device.read(1)
        if c == b'\r': break
        buffer.extend(c)
    return buffer

def commander(device):
    def command(cmd):
        device.write(cmd)
        device.write(b'\r')
        device.flush()
        for line in read_until_prompt(device):
            yield line
    return command

BAUDRATES = [
        230400,
        #115200,
        #57600,
        38400,
        9600]

def detect_baudrate(device):
        """
        Detect the baud rate at which a connected ELM32x interface is operating.
        Returns boolean for success.

        Copied from pyodb
        """

        # before we change the timout, save the "normal" value
        timeout = device.timeout
        device.timeout = 0.5 # we're only talking with the ELM, so things should go quickly

        for baud in BAUDRATES:
            device.baudrate = baud
            device.flushInput()
            device.flushOutput()

            # Send a nonsense command to get a prompt back from the scanner
            # (an empty command runs the risk of repeating a dangerous command)
            # The first character might get eaten if the interface was busy,
            # so write a second one (again so that the lone CR doesn't repeat
            # the previous command)
            device.write(b"\x7F\x7F\r\n")
            device.flush()
            response = device.read(1024)
            logger.debug("Response from baud %d: %s" % (baud, repr(response)))

            # watch for the prompt character
            if response.endswith(b">"):
                logger.debug("Choosing baud %d" % baud)
                device.timeout = timeout # reinstate our original timeout
                return True


        logger.debug("Failed to choose baud")
        device.timeout = timeout # reinstate our original timeout
        return False


def configure_interface(device_path):
    device = serial.Serial(port=device_path,
            parity=serial.PARITY_NONE,
            stopbits=1,
            bytesize=8,
            timeout=10)
    assert detect_baudrate(device)
    cmd = commander(device)
    list(cmd(b'at d'))
    list(cmd(b'at e0'))
    list(cmd(b'at s0'))
    list(cmd(b'at l0'))
    list(cmd(b'at caf0'))
    #list(cmd(b'at d1'))
    list(cmd(b'at h1'))
    version = list(cmd(b'at i'))[0]

    TARGET_BAUDRATE = BAUDRATES[0]
    if device.baudrate == TARGET_BAUDRATE:
        logger.debug("Device already at target baudrate %i"%TARGET_BAUDRATE)
        return device
    
    list(cmd(b'at brt c8'))
    # Set baud rate
    device.write(b"at brd %x\r"%(4000000//TARGET_BAUDRATE))
    device.flushOutput()
    reply = bytes(read_one(device))
    assert reply == b'OK'
    device.baudrate = TARGET_BAUDRATE

    assert bytes(read_one(device)) == version
    assert list(cmd(b''))[0] == b"OK"
    logger.debug("Device configured to baud rate %i"%TARGET_BAUDRATE)
    return device


def find_elm327():
    for port in serial.tools.list_ports.comports():
        if("FT232R USB UART" in port.description):
            return port.device
    raise RuntimeError("ELM327 device not found")

def dump(device_path=None):
    if device_path is None:
        device_path = find_elm327()
    device = configure_interface(device_path)
    #device.close()
    #elm = obd.OBD(device_path, baudrate=device.baudrate)
    #device = elm.interface._ELM327__port
    #protocol = elm.interface._ELM327__protocol
    cmd = commander(device)
    list(cmd(b'at d'))
    list(cmd(b'at e0'))
    list(cmd(b'at s0'))
    list(cmd(b'at l0'))
    list(cmd(b'at m0'))
    list(cmd(b'at caf0'))
    #list(cmd(b'at d1'))
    list(cmd(b'at h1'))
    #print(list(cmd(b'at tp 9')))
    #cmd = commander(device)
    #print(list(cmd(b'at i')))
    device.write(b'at ma\r')
    device.flush()
    seen = set()
    for line in read_until_prompt(device):
        #print(line.decode())
        d = bytes(line).decode('utf-8')
        d = json.dumps([{'ts': time.time()}, {'can': d}])
        sys.stdout.write(d); sys.stdout.write('\n')
        sys.stdout.flush()
        """
        continue
        if d in seen:
            continue
        seen.add(d)
        print(d)

        continue
        for msg in protocol([line.decode()]):
            for frame in msg.frames:
                #pid = (frame.data[:2])
                d = bytes(frame.data)
                if d in seen:
                    continue
                seen.add(d)
                print(d)
                #print(frame.rx_id, frame.tx_id, frame.type, frame.data)
                #print(dir(frame))
        """
   
if __name__ == '__main__':
    argh.dispatch_command(dump)
