#!/usr/bin/env bash

lsmod | grep vboxguest &> /dev/null
if [ $? == 0 ]; then
    ffmpeg -f x11grab -framerate 1 -s 1920x1080 -i $DISPLAY -y -frames:v 1 capture.jpg
else
    ffmpeg -f fbdev -i /dev/fb0 -framerate 1 -s 1920x1080 -y -frames:v 1 capture.jpg
fi

