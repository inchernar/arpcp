#!/bin/bash

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
