#!/bin/bash

# Black        0;30     Dark Gray     1;30
# Red          0;31     Light Red     1;31
# Green        0;32     Light Green   1;32
# Brown/Orange 0;33     Yellow        1;33
# Blue         0;34     Light Blue    1;34
# Purple       0;35     Light Purple  1;35
# Cyan         0;36     Light Cyan    1;36
# Light Gray   0;37     White         1;37

printstep(){
	BLUE='\033[1;34m'
	NC='\033[0m' # No Color
	echo -e "${BLUE}===> $1 <===${NC}"
}

# ======================================

ARPCP_DIR=/srv/arpcp
LOG_DIR=/var/log/arpcp

### START
printstep "====== START ======"
printstep "creating $ARPCP_DIR directory"
mkdir -m 755 -p $ARPCP_DIR

files=(
	arpcp.py
	arpcp.service
	arpcp.conf.yml
	procedures.py
	callbacks.py
	arpcp-cluster-registrar.py
	arpcp-cluster-registrar.service
	arpcp-cluster-statistician.py
	arpcp-cluster-statistician.service
	static
	webapp.py
	webapp.nginx.conf
	webapp.uwsgi.ini
)
for file in ${files[@]}
do
	printstep "linking $file"
	ln -s -r $file $ARPCP_DIR
done

printstep "creating $LOG_DIR directory"
mkdir -m 755 -p $LOG_DIR

daemons=(
	arpcp
	arpcp-cluster-registrar
	arpcp-cluster-statistician
)
for daemon in ${daemons[@]}
do
	printstep "creating symlink for $daemon.service"
	ln -s $ARPCP_DIR/$daemon.service /etc/systemd/system/$daemon.service
	printstep "enabling & starting $daemon.service"
	# systemctl enable $daemon
	systemctl start $daemon
done

printstep "creating symlink for webapp.nginx.conf"
ln -s $ARPCP_DIR/webapp.nginx.conf /etc/nginx/sites-enabled/webapp.nginx.conf
printstep "starting nginx"
systemctl start nginx

printstep "creating symlink for webapp.uwsgi.ini"
ln -s $ARPCP_DIR/webapp.uwsgi.ini /etc/uwsgi/apps-enabled/webapp.uwsgi.ini
printstep "starting uwsgi"
systemctl start uwsgi
