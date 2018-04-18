#!/usr/bin/env python3
import xmlrpc.client
import sys

if sys.argv[1] == "start":
    proxy = xmlrpc.client.ServerProxy("http://" + sys.argv[2])
    print(proxy.start())
if sys.argv[1] == "stop":
    proxy = xmlrpc.client.ServerProxy("http://" + sys.argv[2])
    print(proxy.stop())
if sys.argv[1] == "switch":
    proxy = xmlrpc.client.ServerProxy("http://" + sys.argv[3])
    print(proxy.start())
    proxy = xmlrpc.client.ServerProxy("http://" + sys.argv[2])
    print(proxy.stop())
