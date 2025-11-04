#! /bin/bash
##---------------------------------------------------------------------------------
## Company:        OST - Ostschweizer Fachhochschule 
## Department:     IMES – Institut fuer Mikroelektronik, Embedded Systems und Sensorik
## Author:         Roman Willi
##
## Creation Date:  01.04.2025
## Script Name:    mount_Digital_Design.sh
## Project Name:   
## Description:    Mountet Unterrichtsserver in user home
##
## Revision:
## Revision        01 - File Created
##---------------------------------------------------------------------------------

# Path of the symbolic link
link_path=~/Digital_Design
mount_path="smb://sifs09.ost.ch/bsc.et/unterricht/module_BSc/Digital_Design"
mount_point="$XDG_RUNTIME_DIR/gvfs/smb-share:server=sifs09.ost.ch,share=bsc.et/unterricht/module_BSc/Digital_Design"

export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$UID/bus"

echo "Unmounting $mount_path..."
gio mount -u "$mount_path"

echo "Removing the link $link_path..."
[ -L "$link_path" ] && unlink "$link_path"

echo "Mounting: $mount_path"
gio mount "$mount_path"

# Warte, bis Mountpoint wirklich da ist (max. 10 Sekunden)
echo -n "Warte auf Mountpoint..."
for i in {1..10}; do
    if [ -d "$mount_point" ]; then
        echo " gefunden."
        break
    fi
    echo -n "."
    sleep 1
done

if [ ! -d "$mount_point" ]; then
    echo "❌ Fehler: Mountpoint nicht gefunden!"
    exit 1
fi

echo "Creating symlink: $link_path"
ln -s "$mount_point" "$link_path"

if [ -e "$link_path" ]; then
	echo "✅ The link $link_path is working"
	code&
else
	echo "❌ The link $link_path is not working"
	exit 1
fi


# Manual Use
# ----------

# MOUNT, LINK
#gio mount cifs smb://sifs09.ost.ch/bsc.et/unterricht/module_BSc/Digital_Design
#ln -s "$XDG_RUNTIME_DIR/gvfs/smb-share:server=sifs09.ost.ch,share=bsc.et/unterricht/module_BSc/Digital_Design" ~/Digital_Design

# UNMOUNT, UNLINK
#gio mount -u smb://sifs09.ost.ch/bsc.et/unterricht/module_BSc/Digital_Design
#unlink ~/Digital_Design
