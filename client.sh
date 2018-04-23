#!/usr/bin/env bash
# ffmpeg -f alsa -i hw:0 -f x11grab -s `xdpyinfo | grep 'dimensions:'|awk '{print $2}'` -i $DISPLAY -preset ultrafast -vcodec libx264 -tune zerolatency http://$1/feed.ffm
# trap 'kill -TERM $PID' TERM INT

while true; do
    lsmod | grep vboxguest &> /dev/null
    if [ $? == 0 ]; then
        ffmpeg -f x11grab -s 1920x1080 -i $DISPLAY -preset ultrafast -vcodec libx264 -tune zerolatency -b:v 1M -g 10 -f flv rtmp://$1/live/screenmux
    else
        ffmpeg -f fbdev -i /dev/fb0 -s 1920x1080 -preset ultrafast -vcodec libx264 -tune zerolatency -b:v 1M -g 10 -f flv rtmp://$1/live/screenmux
    fi
done;

