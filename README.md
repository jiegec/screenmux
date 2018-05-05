# Screenmux

A C/S tool to control live screen streming of multiple clients.

## Requirements
* Linux with framebuffer (`/dev/fb0`) enabled on client
* python >= 3.5 with asyncio
* ffmpeg
* nginx >= 1.10 with rtmp module on server

## Usage

### Server 
Install nginx first: 
```bash
sudo apt install nginx-full libnginx-mod-rtmp
```

Add the following to nginx configuration file then start it.
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

Start the controller:
```bash
$ pip3 install -r requirements.txt
$ ./server.py
client_a_ip joined
client_b_ip joined
> push client_a_ip
> stop
> rtmp rtmp_server_addr
```

### Client
First change the hostnames of the clients so that they are distinguishable. Then start the controlee:
```bash
pip3 install -r requirements.txt
# For testing purpose only, you should use a supervisor like systemd to manage the client process in case it dies
./client.py server_ip
```
Please ensure that the user used to start `client.py` have permission to read framebuffer, i.e., in `video` group or be root.

### Viewer
View streaming
```bash
vlc rtmp://server_ip/live/screenmux --loop
```

### Notice
You might need to sync your machines' time if confused by strange problems:
```bash
sudo ntpdate ntp.tuna.tsinghua.edu.cn
sudo /usr/sbin/VBoxService --timesync-set-start
```