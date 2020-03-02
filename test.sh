framedir='frames'
agentclass='Target'
#mkdir -p $framedir
#rm $framedir/*
python3 -m agents.breakout.stayalive $framedir $agentclass
ffmpeg -y -i frames/${agentclass}%05d.png -vcodec mpeg4 -framerate 24 breakout_${agentclass}.mp4
open breakout_${agentclass}.mp4