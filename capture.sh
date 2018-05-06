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


if [ -z "$DISPLAY" ]; then
    ffmpeg -f fbdev -i /dev/fb0 -framerate 1 -s 1920x1080 -y -frames:v 1 capture.jpg
else
    ffmpeg -f x11grab -framerate 1 -s 1920x1080 -i $DISPLAY -y -frames:v 1 capture.jpg
fi

