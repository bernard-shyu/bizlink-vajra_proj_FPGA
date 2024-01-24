#!/bin/bash
#----------------------------------------------------------------------------
if [ "$1" = "-h" ]; then
	echo -e "`dirname $0` [ VNC_geometry ] \n" \
		"\tVNC_geometry: 1280x800 / 1920x1080 / 2048x1280 / 2560x1440  Default: 1280x800\n";
	exit
fi

echo "kill previous VNC Server instances"
for i in `seq 1 9`; do 
	vncserver -kill :$i               > /dev/null  2>&1
#	sudo rm -f /tmp/.X$i-lock         > /dev/null  2>&1
#	sudo rm -f /tmp/.X11-unix/X$i     > /dev/null  2>&1
done

# Common geometry: 1280x800 / 1920x1080 / 2048x1280 / 2560x1440
VNC_GEOMETRY=${VNC_GEOMETRY:=1280x800}      # externally defined export VNC_GEOMETRY
VNC_GEOMETRY=${1:-$VNC_GEOMETRY}            # input parameter %1 for VNC_GEOMETRY
VNC_LOCAL=${VNC_LOCAL:=""}                  # VNC_LOCAL="-localhost" or ""
VNC_PORT=${VNC_PORT:="9"}                   # VNC_PORT: 1 ~ 15

cd $HOME
vncserver :$VNC_PORT $VNC_LOCAL -depth 24 -geometry $VNC_GEOMETRY
