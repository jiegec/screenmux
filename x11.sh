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

# Fallback
if [ -z "$DIMENSIONS" ]; then
    XAUTHORITY=$(ps a | awk 'match($0, /Xorg/) {print $0; exit}' | perl -n -e '/Xorg.*\s-auth\s([^\s]+)\s/ && print $1')
    PID=$(ps a | awk 'match($0, /Xorg/) {print $1; exit}')
    DISPLAY=$(lsof -p $PID | awk 'match($9, /^\/tmp\/\.X11-unix\/X[0-9]+$/) {sub("/tmp/.X11-unix/X",":",$9); print $9; exit}')
    export DISPLAY
    export XAUTHORITY
    DIMENSIONS=$(xdpyinfo | grep 'dimensions:' | awk '{print $2;exit}')
fi