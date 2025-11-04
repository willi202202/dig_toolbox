#! /bin/bash
##---------------------------------------------------------------------------------
## Company:        OST - Ostschweizer Fachhochschule 
## Department:     IMES – Institut fuer Mikroelektronik, Embedded Systems und Sensorik
## Author:         Roman Willi
##
## Creation Date:  01.04.2025
## Script Name:    unmount_Digital_Microelectronics.sh
## Project Name:   
## Description:    Unmountet Unterrichtsserver
##
## Revision:
## Revision        01 - File Created
##---------------------------------------------------------------------------------

# Path of the symbolic link
link_path=~/Digital_Microelectronics
mount_path="smb://sifs09.ost.ch/bsc.et/unterricht/module_BSc/Digital_Microelectronics"
mount_point="$XDG_RUNTIME_DIR/gvfs/smb-share:server=sifs09.ost.ch,share=bsc.et/unterricht/module_BSc/Digital_Microelectronics"

echo "Unmounting $mount_path..."
gio mount -u "$mount_path"
echo "Removing the link $link_path..."
unlink "$link_path"

# Manual Use
# ----------

# MOUNT, LINK
#gio mount cifs smb://sifs09.ost.ch/bsc.et/unterricht/module_BSc/Digital_Microelectronics
#ln -s "$XDG_RUNTIME_DIR/gvfs/smb-share:server=sifs09.ost.ch,share=bsc.et/unterricht/module_BSc/Digital_Design" ~/Digital_Microelectronics

# UNMOUNT, UNLINK
#gio mount -u smb://sifs09.ost.ch/bsc.et/unterricht/module_BSc/Digital_Microelectronics
#unlink ~/Digital_Microelectronics
