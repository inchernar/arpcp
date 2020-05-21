#!/bin/bash

# # Black        0;30     Dark Gray     1;30
# # Red          0;31     Light Red     1;31
# # Green        0;32     Light Green   1;32
# # Brown/Orange 0;33     Yellow        1;33
# # Blue         0;34     Light Blue    1;34
# # Purple       0;35     Light Purple  1;35
# # Cyan         0;36     Light Cyan    1;36
# # Light Gray   0;37     White         1;37

printstep(){
	RED='\033[1;31m'
	NC='\033[0m' # No Color
	echo -e "${RED}===> $1 <===${NC}"
}

# ======================================

ARPCP_DIR=/srv/arpcp
ARPCP_USER=arpcp-user
LOG_DIR=/var/log/arpcp

services=(
	arpcp
)
for service in ${services[@]}
do
	printstep "disabling $service.service"
	systemctl stop $service
	systemctl disable $service
	printstep "removing symlink for $service.service"
	rm /etc/systemd/system/$service.service
done
systemctl daemon-reload

printstep "removing $ARPCP_DIR directory"
rm -r $ARPCP_DIR 2>/dev/null

printstep "removing $ARPCP_USER user"
userdel -fr $ARPCP_USER 2>/dev/null


printstep "removing $LOG_DIR directory"
rm -r $LOG_DIR
