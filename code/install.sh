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

# packages=(
# 	nginx
# 	python3
# 	python3-pip
# 	uwsgi
# 	uwsgi-plugin-python3
# )
# for package in ${packages[@]}
# do
# 	printstep "installing $package"
# 	apt install -y $package 2>/dev/null
# done

# pymodules=(
# 	Flask==1.1.2
# 	Jinja2==2.11.2
# 	PyYAML==5.3
# 	redis==3.4.1
# 	Werkzeug==1.0.1
# 	setproctitle==1.1.10
# 	python-libnmap==0.7.0
# )
# for pymodule in ${pymodules[@]}
# do
# 	printstep "installing $pymodule python module"
# 	pip3 install $pymodule
# done

printstep "creating $ARPCP_USER user"
useradd -M -s /bin/bash $ARPCP_USER

printstep "creating $ARPCP_DIR folder"
mkdir -p $ARPCP_DIR

files=(
	arpcp.py
	arpcp.service
	arpcp-cluster-registrar.py
	arpcp-cluster-registrar.service
	arpcp-cluster-statistician.py
	arpcp-cluster-statistician.service
	arpcp.conf.yml
	# controller.py
	procedures.py
	callbacks.py
	webapp.py
	webapp.nginx.conf
	webapp.uwsgi.ini
)
for file in ${files[@]}
do
	printstep "copying $file"
	cp $file $ARPCP_DIR/$file
done

printstep "setting $ARPCP_USER as owner"
chown -R $ARPCP_USER:$ARPCP_USER $ARPCP_DIR

printstep "setting permissions"
chmod 766 $ARPCP_DIR/*

LOG_FOLDER=/var/log/arpcp
printstep "creating $LOG_FOLDER folder"
mkdir -p $LOG_FOLDER
chown -R $ARPCP_USER:$ARPCP_USER $LOG_FOLDER
chmod 766 $LOG_FOLDER

printstep "creating symlink for webapp.nginx.conf"
ln -s $ARPCP_DIR/webapp.nginx.conf /etc/nginx/sites-enabled/webapp.nginx.conf

printstep "creating symlink for webapp.uwsgi.ini"
ln -s $ARPCP_DIR/webapp.uwsgi.ini /etc/uwsgi/apps-enabled/webapp.uwsgi.ini

services=(
	arpcp
	arpcp-cluster-registrar
	arpcp-cluster-statistician
)
for service in ${services[@]}
do
	printstep "creating symlink for $service.service"
	ln -s $ARPCP_DIR/$service.service /etc/systemd/system/$service.service
	printstep "enabling & starting $service.service"
	# systemctl enable $service
	systemctl start $service
done
