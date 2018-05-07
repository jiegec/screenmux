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

import logging
import asyncio
import aioconsole
import os
import sys
import json
import socket
from asyncio.streams import StreamWriter, FlowControlMixin
from hbmqtt.broker import Broker
from hbmqtt.client import MQTTClient
from hbmqtt.mqtt.constants import QOS_0
from tkinter import *
from tkinter import messagebox
from PIL import ImageTk, Image

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

client_ips = list()
clients = None
server = None
current_pushing = None
screenshot = None
rtmp_addr = None
rtmp_addr2 = None
params = None


@asyncio.coroutine
def broker_coro():
    config = load(open('hbmqtt.yaml', 'r'), Loader=Loader)
    broker = Broker(config)
    yield from broker.start()


@asyncio.coroutine
def mqtt_coro():
    global server, client_ips
    server = MQTTClient()
    yield from server.connect(uri='mqtt://localhost/')
    yield from server.subscribe([
        ('connect', QOS_0),
        ('disconnect', QOS_0),
        ('report', QOS_0),
        ('screenshot', QOS_0),
    ])
    while 1:
        message = yield from server.deliver_message()
        topic = message.publish_packet.variable_header.topic_name
        if topic == 'screenshot':
            # print(repr(message.publish_packet.payload.data))
            with open('screenshot.jpg', 'wb') as file:
                file.write(message.publish_packet.payload.data)
            img = Image.open('screenshot.jpg')
            width, height = img.size
            win_width = screenshot.winfo_width()
            win_height = screenshot.winfo_height()
            new_width = min(win_width, win_height * width / height)
            new_height = new_width * height / width
            img = img.resize((int(new_width), int(new_height)),
                             Image.ANTIALIAS)
            image = ImageTk.PhotoImage(img)
            screenshot.create_image(win_width/2, win_height/2, image=image, anchor=CENTER, tags="IMG")
            continue
        payload = message.publish_packet.payload.data.decode('utf-8')
        if topic == 'connect':
            print('Client {} is connected'.format(payload))
            if payload not in client_ips:
                client_ips.append(payload)
                client_ips.sort()
                clients.delete(0, END)
                for ip in client_ips:
                    clients.insert(END, ip)
        elif topic == 'disconnect':
            print('Client {} is disconnected'.format(payload))
            if payload in client_ips:
                client_ips.remove(payload)
            clients.delete(0, END)
            for ip in client_ips:
                clients.insert(END, ip)
        elif topic == 'report':
            print('Client reported status: {}'.format(payload))
            current_pushing['text'] += '{}\n'.format(payload)
    yield from server.disconnect()


'''
async def stdin_coro():
    C = MQTTClient()
    await C.connect(uri='mqtt://localhost/')
    while 1:
        command = await aioconsole.ainput('> ')
        parts = command.split(' ')
        if len(parts) == 1 and parts[0] == 'list':
            for client_ip in client_ips:
                print(client_ip)
        elif len(parts) == 1 and parts[0] == 'stop':
            await C.publish('stop', b'')
        elif len(parts) == 1 and parts[0] == 'refresh':
            await C.publish('refresh', b'')
        elif len(parts) == 2 and parts[0] == 'push':
            await C.publish('push', parts[1].encode('utf-8'))
        elif len(parts) == 2 and parts[0] == 'rtmp':
            await C.publish('rtmp', parts[1].encode('utf-8'))
        else:
            print('list: list all connected ips')
            print('push [client_ip]: ask client_ip to push to server')
            print('stop: ask all clients to stop pushing')
            print('rtmp [rtmp_addr]: ask clients to push to new rtmp addr')
            print(
                'refresh: ask all clients to register again and report its pushing status')
'''


@asyncio.coroutine
def run_tk(root, interval=0.05):
    try:
        while True:
            root.update()
            yield from asyncio.sleep(interval)
    except TclError as e:
        if "application has been destroyed" not in e.args[0]:
            raise
        else:
            sys.exit(0)


def do_refresh():
    global clients, server, client_ips
    clients.delete(0, END)
    client_ips.clear()
    current_pushing['text'] = ''
    asyncio.ensure_future(server.publish('refresh', b''))


@asyncio.coroutine
def push_coro(client, rtmp, params):
    global server
    content = {'rtmp': rtmp, 'client': client, 'params': params}
    yield from server.publish('push', json.dumps(content).encode('utf-8'))
    yield from server.publish('refresh', b'')


def do_push_real(real_rtmp_addr):
    global clients, server, client_ips, params
    if clients.curselection():
        client = clients.get(clients.curselection())
        rtmp = real_rtmp_addr.get()
        current_pushing['text'] = ''
        print('Asking {} to push to {} with params {}'.format(client, rtmp, params.get()))
        asyncio.ensure_future(push_coro(client, rtmp, params.get()))

def do_push():
    global rtmp_addr
    do_push_real(rtmp_addr)

def do_push2():
    global rtmp_addr2
    do_push_real(rtmp_addr2)

def do_capture():
    global clients, server, client_ips
    if clients.curselection():
        client = clients.get(clients.curselection())
        screenshot_client['text'] = client
        asyncio.ensure_future(server.publish(
            'capture', client.encode('utf-8')))
        current_pushing['text'] = ''
        asyncio.ensure_future(server.publish('refresh', b''))
    else:
        messagebox.showerror("screenmux", "Choose a client first")


def do_stop():
    global clients, server, client_ips
    asyncio.ensure_future(server.publish('stop', b''))
    current_pushing['text'] = 'Pushing: None'
    asyncio.ensure_future(server.publish('refresh', b''))


if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        server_addr = '{} {}'.format(socket.gethostname(), s.getsockname()[0])
    except:
        server_addr = socket.gethostname()
    finally:
        s.close()
    print('This server runs at {}'.format(server_addr))
    formatter = "[%(asctime)s] :: %(levelname)s :: %(name)s :: %(message)s"
    logging.basicConfig(level=logging.ERROR, format=formatter)
    asyncio.ensure_future(broker_coro())
    # asyncio.ensure_future(stdin_coro())
    asyncio.ensure_future(mqtt_coro())

    root = Tk()
    # root.resizable(width=False, height=False)
    root.geometry('800x800')
    root.title('screenmux')
    clients = Listbox(root)
    clients.bind('<<ListboxSelect>>', lambda e: do_capture())
    clients.grid(row=0, column=0, columnspan=2, sticky=N+E+S+W)

    refresh = Button(root, text='Refresh', command=do_refresh)
    refresh.grid(row=1, column=0)
    stop = Button(root, text='Stop', command=do_stop)
    stop.grid(row=1, column=1)

    param_label = Label(root, text='Additional FFmpeg params:')
    param_label.grid(row=2, column=0)
    params = Entry(root)
    params.insert(0, '-s 1920x1080 -r 15 -preset ultrafast -vcodec libx264 -tune zerolatency -b:v 3M -g 10')
    params.grid(row=2, column=1, sticky=N+E+S+W)

    push = Button(root, text='Push', command=do_push)
    push.grid(row=3, column=0)
    rtmp_addr = Entry(root)
    rtmp_addr.insert(0, 'rtmp://thu-skyworks.org/live/screenmux1')
    rtmp_addr.grid(row=3, column=1, sticky=N+E+S+W)

    push2 = Button(root, text='Push', command=do_push2)
    push2.grid(row=4, column=0)
    rtmp_addr2 = Entry(root)
    rtmp_addr2.insert(0, 'rtmp://thu-skyworks.org/live/screenmux2')
    rtmp_addr2.grid(row=4, column=1, sticky=N+E+S+W)

    screenshot = Canvas(root)
    screenshot.grid(row=5, column=0, columnspan=2, sticky=N+E+S+W)
    screenshot_client = Label(root)
    screenshot_client.grid(row=6, column=0, columnspan=2, sticky=N+E+S+W)
    current_pushing = Label(root, text='Pushing: None')
    current_pushing.grid(row=7, column=0, columnspan=2, sticky=N+E+S+W)
    for x in range(2):
        Grid.columnconfigure(root, x, weight=1)

    Grid.rowconfigure(root, 0, weight=1)
    Grid.rowconfigure(root, 5, weight=5)

    root.lift()
    asyncio.ensure_future(run_tk(root))
    asyncio.get_event_loop().run_forever()
