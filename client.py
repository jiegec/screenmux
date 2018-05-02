#!/usr/bin/env python3
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

if len(sys.argv) != 2 and len(sys.argv) != 3:
    print("Usage: python3 client.py [server_ip] [rtmp_server_ip]")
    sys.exit(1)

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(('10.255.255.255', 1))
    client_ip = '{} {}'.format(socket.gethostname(), s.getsockname()[0])
except:
    client_ip = socket.gethostname()
finally:
    s.close()

print('Client identifier: {}'.format(client_ip))

if len(sys.argv) > 2:
    rtmp_ip = sys.argv[2]
else:
    rtmp_ip = sys.argv[1]
server_ip = sys.argv[1]
process = None


def kill_child():
    if process is not None:
        os.kill(process.pid, signal.SIGTERM)
        os.system('killall -9 ffmpeg')


atexit.register(kill_child)


@asyncio.coroutine
def mqtt_coro():
    global process
    global rtmp_ip
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
                print('Server asking {} to push.'.format(payload))
                if payload != client_ip:
                    if not process or process.poll() is not None:
                        print('I am not streaming. Ignoring.')
                    else:
                        print("Stop streaming now")
                        os.system('kill -9 {pid}'.format(pid=process.pid))
                        os.system('killall -9 ffmpeg')
                        process = None
                elif process and process.poll() is None:
                    print(
                        'Server asking me to push. Already streaming, ignoring.')
                else:
                    print('Start streaming')
                    process = subprocess.Popen(["bash", "./client.sh", rtmp_ip])
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
            elif topic == 'rtmp':
                print('Server changing rtmp server addr to {}.'.format(payload))
                rtmp_ip = payload
            elif topic == 'refresh':
                print('Re-registering and publish my status to server')
                yield from C.publish('connect', client_ip.encode('utf-8'), qos=QOS_0)
                if process and process.poll() is None:
                    yield from C.publish('report', 'from {} to {}'.format(client_ip, rtmp_ip).encode('utf-8'), qos=QOS_0)
            elif topic == 'capture':
                print('Server asking {} to push.'.format(payload))
                if payload != client_ip:
                    print('Not asking me to take screenshot. Ignoring.')
                else:
                    screenshot = subprocess.Popen(["bash", "./capture.sh"])
                    screenshot.wait()
                    with open('capture.jpg', mode='rb') as file:
                        content = file.read()
                        yield from C.publish('screenshot', content, qos=QOS_0)

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
