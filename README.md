Suppose you have two computer A and B wanting to stream to server:

Start a ffserver in the server:
```
ffserver -f ffserver.conf
```

Start a screenmux server in A and B:
```
./server.py server_ip:8090 # The port should be same as HttpPort in ffserver.conf
```

From server, start, stop or switch clients:
```
./client.py start client_a_ip:2323
./client.py stop client_b_ip:2323
./client.py switch client_a_ip:2323 client_b_ip:2323
```

View streaming
```
vlc rtsp://server_ip:5554/stream --loop

You might need to sync your machines' time:
```
sudo ntpdate ntp.tuna.tsinghua.edu.cn
sudo /usr/sbin/VBoxService --timesync-set-start
```
```