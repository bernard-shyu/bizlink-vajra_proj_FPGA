#!/bin/bash
#----------------------------------------------------------------------------
if [ "$1" = "-h" ]; then
	# Ref: https://en.wikipedia.org/wiki/List_of_common_resolutions
	echo -e "`basename $0` [ VNC_geometry (Default: 1280x800) ]\n\t" \
		"VNC_geometry: 1280x800 / 1920x1080 / 2048x1280 / 2560x1440 / 2880x1620 / 3200x2048 / 3840x2160 \n";
	exit
fi

echo "kill previous VNC Server instances"
for i in `seq 1 9`; do 
	vncserver -kill :$i               > /dev/null  2>&1
done

i=9	# while other VNC-ports might be used elsewhere, port 9 should always be used here.
sudo rm -f /tmp/.X$i-lock         > /dev/null  2>&1
sudo rm -f /tmp/.X11-unix/X$i     > /dev/null  2>&1

# Common geometry: 1280x800 / 1920x1080 / 2048x1280 / 2560x1440
VNC_GEOMETRY=${VNC_GEOMETRY:=1920x1080}      # externally defined export VNC_GEOMETRY
VNC_GEOMETRY=${1:-$VNC_GEOMETRY}            # input parameter %1 for VNC_GEOMETRY
VNC_LOCAL=${VNC_LOCAL:=""}                  # VNC_LOCAL="-localhost" or ""
VNC_PORT=${VNC_PORT:="9"}                   # VNC_PORT: 1 ~ 15

cd $HOME
vncserver :$VNC_PORT $VNC_LOCAL -depth 24 -geometry $VNC_GEOMETRY
