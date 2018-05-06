#!/usr/bin/env python3
# Copyright (C) 2018 Jiajie Chen
# 
# This file is part of screenmux.
# 
# screenmux is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# screenmux is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with screenmux.  If not, see <http://www.gnu.org/licenses/>.
# 

from hbmqtt.client import MQTTClient, ConnectException, ClientException
from hbmqtt.mqtt.constants import QOS_0
import sys
import os
import socket
import asyncio
import logging
import subprocess
import atexit
import signal
import time
import json

if len(sys.argv) != 2 and len(sys.argv) != 3:
    print("Usage: python3 client.py [server_ip] [rtmp_server_addr]")
    sys.exit(1)

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(('10.255.255.255', 1))
    client_ip = '{} {}'.format(socket.gethostname(), s.getsockname()[0])
except:
    client_ip = socket.gethostname()
finally:
    s.close()


if len(sys.argv) > 2:
    rtmp_addr = sys.argv[2]
else:
    rtmp_addr = 'rtmp://{}/live/screenmux'.format(sys.argv[1])
server_ip = sys.argv[1]
process = None
capture_timer = None

print('Client identifier: {}, pushing to: {}'.format(client_ip, rtmp_addr))


def kill_child():
    if process is not None:
        os.kill(process.pid, signal.SIGTERM)
        os.system('killall -9 ffmpeg')
    sys.exit(0)


atexit.register(kill_child)


@asyncio.coroutine
def capture_coro():
    try:
        C = MQTTClient(config={'auto_reconnect': False})
        yield from C.connect(uri='mqtt://{}/'.format(server_ip))
        while True:
            screenshot = subprocess.Popen(["bash", "./capture.sh"])
            screenshot.wait()
            with open('capture.jpg', mode='rb') as file:
                content = file.read()
                yield from C.publish('screenshot', content, qos=QOS_0)
            print('Captured a new screenshot.')
            yield from asyncio.sleep(2)
    except ClientException:
        print('Capture task: Connection to server lost.')
        pass


@asyncio.coroutine
def mqtt_coro():
    global process, rtmp_addr, capture_timer
    C = MQTTClient(config={'auto_reconnect': False})
    yield from C.connect(uri='mqtt://{}/'.format(server_ip))
    yield from C.subscribe([
        ('push', QOS_0),
        ('stop', QOS_0),
        ('rtmp', QOS_0),
        ('refresh', QOS_0),
        ('capture', QOS_0),
    ])
    yield from C.publish('connect', client_ip.encode('utf-8'), qos=QOS_0)
    atexit.register(lambda: asyncio.get_event_loop().run_until_complete(
        C.publish('disconnect', client_ip.encode('utf-8'))))
    try:
        while 1:
            message = yield from C.deliver_message()
            topic = message.publish_packet.variable_header.topic_name
            payload = message.publish_packet.payload.data.decode('utf-8')
            if topic == 'push':
                msg = json.loads(payload)
                print('Server asking {} to push.'.format(msg['client']))
                if msg['client'] != client_ip:
                    if not process or process.poll() is not None:
                        print('I am not streaming. Ignoring.')
                    else:
                        if rtmp_addr == msg['rtmp']:
                            print("Stop streaming now")
                            os.system('kill -9 {pid}'.format(pid=process.pid))
                            os.system('killall -9 ffmpeg')
                            process = None
                        else:
                            print('Server requested rtmp addr is not mime, ignoring.')
                elif process and process.poll() is None:
                    print('Server asking me to push.')
                    if rtmp_addr == msg['rtmp']:
                        print('Rtmp addr not changed. Ignoring')
                    else:
                        print('Rtmp addr changed to {}. Pushing to the new addr.'.format(
                            msg['rtmp']))
                        print("Stop streaming now.")
                        os.system('kill -9 {pid}'.format(pid=process.pid))
                        os.system('killall -9 ffmpeg')
                        process = None

                        rtmp_addr = msg['rtmp']
                        print('Start streaming to {} with params {}'.format(rtmp_addr, msg['params']))
                        process = subprocess.Popen(
                            ["bash", "./client.sh", rtmp_addr, msg['params']])
                        print('ffmpeg started with PID {}', process.pid)
                else:
                    print('Start streaming')
                    print('With rtmp server addr {} and params {}.'.format(
                        msg['rtmp'], msg['params']))
                    rtmp_addr = msg['rtmp']
                    process = subprocess.Popen(
                        ["bash", "./client.sh", rtmp_addr, msg['params']])
                    print('ffmpeg started with PID {}', process.pid)
            elif topic == 'stop':
                print('Server asking everyone to stop.')
                if not process or process.poll() is not None:
                    print('I am not streaming. Ignoring.')
                else:
                    print("Stop streaming now")
                    os.system('kill -9 {pid}'.format(pid=process.pid))
                    os.system('killall -9 ffmpeg')
                    process = None
                if capture_timer is not None and not capture_timer.done():
                    print('Stopping my capturing.')
                    capture_timer.cancel()
                    capture_timer = None
            elif topic == 'refresh':
                print('Re-registering and publish my status to server')
                yield from C.publish('connect', client_ip.encode('utf-8'), qos=QOS_0)
                if process and process.poll() is None:
                    yield from C.publish('report', 'Pushing: from {} to {}'.format(client_ip, rtmp_addr).encode('utf-8'), qos=QOS_0)
                if capture_timer is not None and not capture_timer.done():
                    yield from C.publish('report', 'Capturing: from {}'.format(client_ip).encode('utf-8'), qos=QOS_0)
            elif topic == 'capture':
                print('Server asking {} to capture.'.format(payload))
                if payload != client_ip:
                    print('Not asking me to take screenshot.')
                    if capture_timer is not None and not capture_timer.done():
                        print('Stopping my capturing.')
                        capture_timer.cancel()
                        capture_timer = None
                    else:
                        print('I am not capturing. Ignoring.')
                else:
                    if capture_timer is not None and not capture_timer.done():
                        print('Capturing task already running.')
                    else:
                        print('Starting capturing task.')
                        capture_timer = asyncio.ensure_future(capture_coro())

        yield from C.disconnect()
    except ClientException:
        print('Connection to server lost.')
        pass


if __name__ == '__main__':
    formatter = "[%(asctime)s] %(name)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.ERROR, format=formatter)
    while True:
        try:
            asyncio.get_event_loop().run_until_complete(mqtt_coro())
        except ConnectException:
            print('Retrying to connect to server')
        time.sleep(1)
