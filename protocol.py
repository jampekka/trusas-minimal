#!/usr/bin/env python3.6

import argh
import socket
import json
import time
import os
import asyncio
import random
import sys
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
import subprocess
import datetime

def encode(**data):
    hdr = dict(time=time.time())
    return json.dumps([hdr, data]).encode('utf-8')

def output(**data):
    sys.stdout.write(encode(**data).decode())
    sys.stdout.write('\n')
    sys.stdout.flush()
    
def log_warning(**data):
    sys.stderr.write(encode(**data).decode())
    sys.stderr.write('\n')
    sys.stderr.flush()
    
async def readlines(fileobj):
    # asyncio has really dropped the ball
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor()

    while True:
        line = (await loop.run_in_executor(executor, fileobj.readline))
        if not line:
            return
        yield line.strip()

async def tailf(path):
    process = await asyncio.create_subprocess_exec("tail", "-n0", "-F", path, stdout=subprocess.PIPE)
    while True:
        yield await process.stdout.readline()

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

async def jsons(itr):
    async for line in itr:
        try:
            yield json.loads(line)
        except ValueError as e:
            log_warning(message="Json parse error %s"%str(e), data=line)

class EventDispatcher:
    def __init__(self, commander):
        self.listeners = []
        self.commander = commander
        asyncio.get_event_loop().create_task(self._handle())
    
    async def _handle(self):
        async for msg in self.commander:
            for listener in self.listeners:
                listener(msg)


    def once(self, func):
        def tmp(*args, **kwargs):
            self.off(tmp)
            func(*args, **kwargs)
        self.on(tmp)

    def on(self, f):
        self.listeners.append(f)

    def off(self, f):
        self.listeners.remove(f)
            

async def run(blinder_path, blinder_log, control_path, logfile):
    # TODO: Read the log
    loop = asyncio.get_event_loop()

    bsock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    cmsgs = jsons(socket_reader(control_path))
    events = EventDispatcher(cmsgs)
    blinder_events = EventDispatcher(jsons(tailf(blinder_log)))
    
    def blinder(mode):
        bsock.sendto(encode(set_mode=mode), blinder_path)
    
    # Wait for the blinder process to start up. It's a hack.
    for i in range(10):
        try:
            blinder("unblind")
        except FileNotFoundError:
            await asyncio.sleep(0.1)
            continue
        break

    current_block = -1
    sequence = [("intro", None)]
    block_duration = 5*60.0 # TODO: Check this
    
    training = [('blind', block_duration), ('unblind', block_duration)]
    random.shuffle(training)

    n_blocks = 3
    blocks = [('blind', block_duration)]*n_blocks + [('unblind', block_duration)]*n_blocks
    random.shuffle(blocks)
    sequence += training
    sequence += blocks
    output(sequence=sequence)

    def wait_event(src, filter):
        ret = asyncio.get_event_loop().create_future()
        def handle(msg):
            try:
                if(filter(msg)):
                    src.off(handle)
                    ret.set_result(msg)
            except:
                pass
        src.on(handle)
        return ret

    
    async def start_intro(end):
        blinder("unblind")
        def cmd(c):
            blinder(c['command'])
        events.on(cmd)
        end.add_done_callback(lambda _: events.off(cmd))

    async def start_unblind(end):
        blinder("unblind")
    
    async def start_blind(end):
        blinder("control")
        output(message="Press the blinder to start")
        await wait_event(blinder_events, lambda d: d[1]['controller'].strip() == 'Lifting')
    scenarios = dict(intro=start_intro, unblind=start_unblind, blind=start_blind)

    async def run_next_block():
        nonlocal current_block
        current_block += 1
        block_type = sequence[current_block]
        output(block_init=current_block, block_type=block_type)
        output(message="Click start to start the block")
        await wait_event(events, lambda d: d['command'] == 'start')
        delay = block_type[1]

        onend = asyncio.get_event_loop().create_future()
        await scenarios[block_type[0]](onend)
        end_time = None
        if delay:
            end_time = time.time() + delay
        output(block_start=current_block, block_type=block_type, end_time=end_time)

        if delay:
            output(message="Block running until %s"%datetime.datetime.fromtimestamp(end_time))
            await asyncio.sleep(delay)
        else:
            output(message="Click end to end current block")
            await wait_event(events, lambda d: d['command'] == 'end')
        
        onend.set_result(True)
        output(block_end=current_block, block_type=block_type)
        output(message="Block ended")
    
    while True:
        await run_next_block()
        if current_block >= len(sequence): break
    blinder("unblind")
    output(message="Experiment done")
        
        




def do_run(blinder_path, blinder_log, control_path, logfile):
    asyncio.get_event_loop().run_until_complete(run(blinder_path, blinder_log, control_path, logfile))
    
if __name__ == '__main__':
    argh.dispatch_command(do_run)
