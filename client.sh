#!/usr/bin/env bash
# ffmpeg -f alsa -i hw:0 -f x11grab -s `xdpyinfo | grep 'dimensions:'|awk '{print $2}'` -i $DISPLAY -preset ultrafast -vcodec libx264 -tune zerolatency http://$1/feed.ffm
# trap 'kill -TERM $PID' TERM INT

while true; do
    lsmod | grep vboxguest &> /dev/null
    if [ $? == 0 ]; then
        ffmpeg -f x11grab -s `xdpyinfo | grep 'dimensions:'|awk '{print $2}'` -i $DISPLAY -preset ultrafast -vcodec libx264 -tune zerolatency http://$1/feed.ffm
    else
        ffmpeg -f fbdev -i /dev/fb0 -preset ultrafast -vcodec libx264 -tune zerolatency http://$1/feed.ffm
    fi
done;

