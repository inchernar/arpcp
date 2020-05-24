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
ARPCP_USER=arpcp-user
LOG_DIR=/var/log/arpcp

### START
printstep "====== START ======"
printstep "creating $ARPCP_DIR directory"
mkdir -m 755 -p $ARPCP_DIR

printstep "creating $ARPCP_USER user"
useradd -M -s /bin/bash $ARPCP_USER

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
	webapp.py
	webapp.nginx.conf
	webapp.uwsgi.ini
)
for file in ${files[@]}
do
	printstep "linking $file"
	ln -s $PWD/$file $ARPCP_DIR/$file
done

printstep "linking static folder"
mkdir -p $ARPCP_DIR/static
ln -s $PWD/static/index.html $ARPCP_DIR/static/index.html
mkdir -p $ARPCP_DIR/static/js
ln -s $PWD/static/js/d3.v5.js $ARPCP_DIR/static/js/d3.v5.js
ln -s $PWD/static/js/axios.js $ARPCP_DIR/static/js/axios.js
ln -s $PWD/static/js/main.js $ARPCP_DIR/static/js/main.js
mkdir -p $ARPCP_DIR/static/css
ln -s $PWD/static/css/style.css $ARPCP_DIR/static/css/style.css
mkdir -p $ARPCP_DIR/static/images
ln -s $PWD/static/images/agent_off.svg $ARPCP_DIR/static/images/agent_off.svg
ln -s $PWD/static/images/agent_on.svg $ARPCP_DIR/static/images/agent_on.svg
ln -s $PWD/static/images/controller.svg $ARPCP_DIR/static/images/controller.svg

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
