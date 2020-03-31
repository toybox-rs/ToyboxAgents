#!/bin/bash

# This script expects the be run from the directory that contains the videos
# (e.g., {rootRepository}/analysis
set -eu

agents="Target StayAlive SmarterStayAlive StayAliveJitter"
#agents="StayAliveJitter"

for agent in $agents; do
    output="$agent.mp4"
    # ffmpeg -t 12 -i /dev/zero -vcodec mpeg4 -framerate 24 $output
    echo "Concatenating $agent mp4s into $output"
    touch tmp.txt
    for mp4 in `ls $agent*mp4`; do 
        echo "file '$mp4'" >> tmp.txt
    done
    ffmpeg -f concat -safe 0 -i tmp.txt -c copy $output
    rm tmp.txt
done        
