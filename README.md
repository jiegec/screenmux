README
=====================

Suppose you have two computers A and B wanting to stream to server:

(preferred) Use nginx to relay rtmp:
=====================
```
$ sudo apt install nginx-full libnginx-mod-rtmp
```

Add the following to /etc/nginx/nginx.conf:
```
rtmp {
        server {
                listen 1935;
                chunk_size 4096;

                application live {
                        live on;
                        record off;
                }
        }
}
```

Start a screenmux client in A and B:
```
$ pip3 install -r requiredments.txt
$ ./client.py server_ip
```

From server, start, stop or switch clients:
```
$ pip3 install -r requiredments.txt
$ ./server.py
client_a_ip joined
client_b_ip joined
> push client_a_ip
> stop
> rtmp rtmp_server_addr
```

View streaming
```
vlc rtmp://server_ip/live/screenmux --loop
```

You might need to sync your machines' time:
```
sudo ntpdate ntp.tuna.tsinghua.edu.cn
sudo /usr/sbin/VBoxService --timesync-set-start
```

(legacy) Use ffserver to relay http
=======================

You might need an old version of screenmux prior to 2018-04-22.

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
```

You might need to sync your machines' time:
```
sudo ntpdate ntp.tuna.tsinghua.edu.cn
sudo /usr/sbin/VBoxService --timesync-set-start
```
