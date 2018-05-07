#!/usr/bin/env bash
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

DIMENSIONS=$(xdpyinfo | grep 'dimensions:' | awk '{print $2;exit}')

# Debian
if [ -z "$DIMENSIONS" ]; then
    DISPLAY=$(w -hs | awk -v tty="$(cat /sys/class/tty/tty0/active)" '$2 == tty && $3 != "-" {print $3; exit}')
    USER=$(w -hs | awk -v tty="$(cat /sys/class/tty/tty0/active)" '$2 == tty && $3 != "-" {print $1; exit}')
    eval XAUTHORITY=~$USER/.Xauthority
    export DISPLAY
    export XAUTHORITY
    DIMENSIONS=$(xdpyinfo | grep 'dimensions:' | awk '{print $2;exit}')
fi

# GDM + Archlinux
if [ -z "$DIMENSIONS" ]; then
    DISPLAY=$(w -hs | awk 'match($2, /:[0-9]+/) {print $2; exit}')
    USER=$(w -hs | awk 'match($2, /:[0-9]+/) {print $1; exit}')
    eval XAUTHORITY=/run/user/$(id -u $USER)/gdm/Xauthority
    export DISPLAY
    export XAUTHORITY
    DIMENSIONS=$(xdpyinfo | grep 'dimensions:' | awk '{print $2;exit}')
fi

if [ -z "$DIMENSIONS" ]; then
    ffmpeg -f fbdev -i /dev/fb0 -framerate 1 -y -frames:v 1 capture.jpg
else
    ffmpeg -f x11grab -s $DIMENSIONS -framerate 1 -i $DISPLAY -y -frames:v 1 capture.jpg
fi

