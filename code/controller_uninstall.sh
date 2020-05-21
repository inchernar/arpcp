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
systemctl stop nginx
printstep "removing symlink for webapp.uwsgi.ini"
rm /etc/uwsgi/apps-enabled/webapp.uwsgi.ini
systemctl stop uwsgi

./agent_uninstall.sh
