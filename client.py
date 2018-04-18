#!/usr/bin/env python3
import xmlrpc.client
import sys
import time

if sys.argv[1] == "start":
    proxy = xmlrpc.client.ServerProxy("http://" + sys.argv[2])
    print("Start:")
    print(proxy.start())
if sys.argv[1] == "stop":
    proxy = xmlrpc.client.ServerProxy("http://" + sys.argv[2])
    print("Stop:")
    print(proxy.stop())
if sys.argv[1] == "switch":
    proxy = xmlrpc.client.ServerProxy("http://" + sys.argv[3])
    print("Switch To:")
    print(proxy.start())
    time.sleep(1)
    proxy = xmlrpc.client.ServerProxy("http://" + sys.argv[2])
    print("Switch From:")
    print(proxy.stop())
