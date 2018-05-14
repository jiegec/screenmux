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

_term() {
    kill -TERM "$child" 2>/dev/null
    exit 0
}
trap _term SIGTERM

. x11.sh

while true; do
    if [ -z "$DIMENSIONS" ]; then
        ffmpeg -f fbdev -i /dev/fb0 $2 -f flv $1 &
        child=$!
        wait "$child"
    else
        ffmpeg -f x11grab -s $DIMENSIONS -i $DISPLAY $2 -f flv $1 &
        child=$!
        wait "$child"
    fi
done;

