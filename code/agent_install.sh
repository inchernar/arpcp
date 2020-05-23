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

packages=(
	redis
	python3
	python3-pip
)
for package in ${packages[@]}
do
	printstep "installing $package"
	apt install -y $package 2>/dev/null
done

pymodules=(
	PyYAML==5.3
	redis==3.4.1
	setproctitle==1.1.10
)
for pymodule in ${pymodules[@]}
do
	printstep "installing $pymodule python module"
	pip3 install $pymodule
done

printstep "creating $ARPCP_USER user"
useradd -M -s /bin/bash $ARPCP_USER

printstep "creating $ARPCP_DIR directory"
mkdir -m 755 -p $ARPCP_DIR
printstep "setting $ARPCP_USER as owner"
chown $ARPCP_USER:$ARPCP_USER $ARPCP_DIR

files=(
	arpcp.py
	arpcp.service
	arpcp.conf.yml
	procedures.py
	callbacks.py
)
for file in ${files[@]}
do
	printstep "copying $file"
	cp $file $ARPCP_DIR/$file
	chmod 644 $ARPCP_DIR/$file
	chown $ARPCP_USER:$ARPCP_USER $ARPCP_DIR/$file
done

printstep "creating $LOG_DIR directory"
mkdir -m 755 -p $LOG_DIR
chown -R $ARPCP_USER:$ARPCP_USER $LOG_DIR

daemons=(
	arpcp
)
for daemon in ${daemons[@]}
do
	printstep "creating symlink for $daemon.service"
	ln -s $ARPCP_DIR/$daemon.service /etc/systemd/system/$daemon.service
	systemctl daemon-reload
	printstep "enabling & starting $daemon.service"
	# systemctl enable $daemon
	systemctl start $daemon
done

services=(
	redis
)
for service in ${services[@]}
do
	printstep "enabling & starting $service"
	# systemctl enable $daemon
	systemctl start $service
done
