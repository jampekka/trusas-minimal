#!/usr/bin/env python3.6

import sys
import asyncio
import evdev
import serial
import json
import time
import queue
from concurrent.futures import ThreadPoolExecutor
import select
import os
import socket
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

#BUTTON_DEV = 'BT-005'
BUTTON_DEV = 'IMS-FM800-BK'

def probe_button():
    for path in evdev.list_devices():
        dev = evdev.InputDevice(path)
        if dev.name == BUTTON_DEV:
            return dev
    return None

async def wait_for_device():
    while True:
        dev = probe_button()
        if dev is not None:
            return dev
        await asyncio.sleep(0.1)

async def button_presses():
    while True:
        button = await wait_for_device()
        try:
            async for event in button.async_read_loop():
                if event.type == 1 and event.value == 1:
                    yield event
        except OSError:
            pass

def read_line(controller):
    buf = bytearray()
    c = ''
    while c != b'\n':
        c = controller.read(1)
        buf.extend(c)
    return bytes(buf)

async def serial_reader(device):
    queue = asyncio.Queue()
    def enqueue():
        c = device.read(1)
        queue.put_nowait(c)
    asyncio.get_event_loop().add_reader(device.fileno(), enqueue)
    
    while True:
        yield await queue.get()

async def serial_lines(device):
    buffer = bytearray()
    async for c in serial_reader(device):
        buffer.extend(c)
        if(bytes(c) == b'\n'):
            yield bytes(buffer)
            buffer = bytearray()

async def readlines(fileobj):
    # asyncio has really dropped the ball
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor()

    while True:
        line = (await loop.run_in_executor(executor, fileobj.readline))
        if not line:
            return
        yield line.strip()

async def socket_reader(path):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        os.remove(path)
    except OSError:
        pass
    sock.bind(path)
    
    queue = asyncio.Queue()
    def enqueue():
        c = sock.recv(4096)
        queue.put_nowait(c)
    asyncio.get_event_loop().add_reader(sock.fileno(), enqueue)
    
    while True:
        yield (await queue.get()).decode('utf-8')

    

def write_output(**data):
    hdr = {'ts': time.time()}
    sys.stdout.write(json.dumps([hdr, data]))
    sys.stdout.write('\n')
    sys.stdout.flush()

def write_log(**data):
    hdr = {'ts': time.time()}
    sys.stderr.write(json.dumps([hdr, data]))
    sys.stderr.write('\n')
    sys.stderr.flush()

async def logger(itr):
    async for msg in itr:
        write_output(controller=msg.decode('utf-8'))
        yield msg

async def control_blinder(controller):
    async for event in button_presses():
        controller.write(b'l')
        controller.flush()

async def drain(agen):
    async for _ in agen:
        pass

async def control_mode(controller, cfile):
    async for line in cfile:
        try:
            cmd = json.loads(line)
        except ValueError as e:
            write_log(exception=str(e), input=line)
            continue
        try:
            mode = cmd[1]['set_mode']
        except Exception as e:
            write_log(exception=str(e), command=cmd)
        if mode == 'unblind':
             controller.write(b'u'); controller.flush()
        if mode == 'blind':
            controller.write(b'b'); controller.flush()
        if mode == 'control':
            controller.write(b'c'); controller.flush()
        if mode == 'lift':
            controller.write(b'l'); controller.flush()


def commander(path=None):
    if path is None:
        return readlines(sys.stdin)
    return socket_reader(path)

async def run(control=None):
    cmsgs = commander(control)
    controller = serial.Serial('/dev/ttyACM0')
    controller.baudrate = 9600

    cin = logger(serial_lines(controller))
    controller.write(b'p')
    controller.flush()

    async for line in cin:
        if line.strip() == b'pong': break
    
    controller.write(b'c')
    controller.flush()
    
    await asyncio.gather(drain(cin), control_blinder(controller), control_mode(controller, cmsgs))

def do_run(cpath=None):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(cpath))

if __name__ == '__main__':
    import argh
    argh.dispatch_command(do_run)
