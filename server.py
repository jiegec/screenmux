#!/usr/bin/env python3
import logging
import asyncio
import aioconsole
import os
import sys
from asyncio.streams import StreamWriter, FlowControlMixin
from hbmqtt.broker import Broker
from hbmqtt.client import MQTTClient
from hbmqtt.mqtt.constants import QOS_0
from tkinter import *
from tkinter import messagebox

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

client_ips = set()
clients = None
server = None
current_pushing = None


@asyncio.coroutine
def broker_coro():
    config = load(open('hbmqtt.yaml', 'r'), Loader=Loader)
    broker = Broker(config)
    yield from broker.start()


@asyncio.coroutine
def mqtt_coro():
    global server
    server = MQTTClient()
    yield from server.connect(uri='mqtt://localhost/')
    yield from server.subscribe([
        ('connect', QOS_0),
        ('disconnect', QOS_0),
        ('report', QOS_0),
    ])
    yield from server.publish('refresh', b'')
    while 1:
        message = yield from server.deliver_message()
        topic = message.publish_packet.variable_header.topic_name
        payload = message.publish_packet.payload.data.decode('utf-8')
        if topic == 'connect':
            print('Client {} is connected'.format(payload))
            client_ips.add(payload)
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
            current_pushing['text'] = 'Pushing: {}'.format(payload)
    yield from server.disconnect()


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
            print('refresh: ask all clients to register again and report its pushing status')


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
    current_pushing['text'] = 'Pushing: None'
    asyncio.ensure_future(server.publish('refresh', b''))


def do_push():
    global clients, server, client_ips
    if clients.curselection():
        client = clients.get(clients.curselection())
        print(client)
        asyncio.ensure_future(server.publish('push', client.encode('utf-8')))
        current_pushing['text'] = 'Pushing: None'
        asyncio.ensure_future(server.publish('refresh', b''))
    else:
        messagebox.showerror("screenmux", "Choose a client ip first")


def do_stop():
    global clients, server, client_ips
    asyncio.ensure_future(server.publish('stop', b''))
    current_pushing['text'] = 'Pushing: None'
    asyncio.ensure_future(server.publish('refresh', b''))


if __name__ == '__main__':
    formatter = "[%(asctime)s] :: %(levelname)s :: %(name)s :: %(message)s"
    logging.basicConfig(level=logging.ERROR, format=formatter)
    asyncio.ensure_future(broker_coro())
    asyncio.ensure_future(stdin_coro())
    asyncio.ensure_future(mqtt_coro())

    root = Tk()
    root.resizable(width=False, height=False)
    root.geometry('800x600')
    root.title('screenmux')
    clients = Listbox(root)
    clients.pack(fill=BOTH, expand=1)
    refresh = Button(root, text='Refresh', command=do_refresh)
    refresh.pack()
    push = Button(root, text='Push', command=do_push)
    push.pack()
    stop = Button(root, text='Stop', command=do_stop)
    stop.pack()
    current_pushing = Label(root, text='Pushing: None')
    current_pushing.pack()

    asyncio.ensure_future(run_tk(root))
    asyncio.get_event_loop().run_forever()
