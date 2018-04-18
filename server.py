#!/usr/bin/env python3
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import subprocess
import os
import signal
import sys
import atexit

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

process = None
addr = sys.argv[1]

# Create server
server = SimpleXMLRPCServer(("0.0.0.0", 2323))
server.register_introspection_functions()

def kill_child():
    if process is not None:
        os.kill(process.pid, signal.SIGTERM)
        os.system('killall -9 ffmpeg')

atexit.register(kill_child)

def start():
    global process
    if process and process.poll() is None:
        return "Already streaming"
    print("Start streaming")
    process = subprocess.Popen(["bash", "./client.sh", addr])
    return process.pid

server.register_function(start, 'start')

def stop():
    global process
    if not process or process.poll() is not None:
        return "Not streaming"
    print("Stop streaming")
    # os.system('pkill -TERM -P {pid}'.format(pid=os.getpid()))
    # os.system('pkill -9 -P {pid}'.format(pid=process.pid))
    # os.system('kill {}'.format(pid=process.pid))
    os.system('kill -9 {pid}'.format(pid=process.pid))
    os.system('killall -9 ffmpeg')
    process = None
    return "Killed"
server.register_function(stop, 'stop')

# Run the server's main loop
server.serve_forever()
