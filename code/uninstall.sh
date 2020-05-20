#!/bin/bash

printstep(){
	RED='\033[1;31m'
	NC='\033[0m' # No Color
	echo -e "${RED}===> $1 <===${NC}"
}

# ======================================

ARPCP_DIR=/srv/arpcp
ARPCP_USER=arpcp-user

services=(
	arpcp
	arpcp-cluster-registrar
	arpcp-cluster-statistician
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

printstep "removing symlink for webapp.nginx.conf"
rm /etc/nginx/sites-enabled/webapp.nginx.conf

printstep "removing symlink for webapp.uwsgi.ini"
rm /etc/uwsgi/apps-enabled/webapp.uwsgi.ini

printstep "removing $ARPCP_DIR folder"
rm -r $ARPCP_DIR 2>/dev/null

printstep "removing $ARPCP_USER user"
userdel -fr $ARPCP_USER 2>/dev/null

LOG_FOLDER=/var/log/arpcp
printstep "removing $LOG_FOLDER folder"
rm -r $LOG_FOLDER
