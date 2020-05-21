#!/bin/bash

# # Black        0;30     Dark Gray     1;30
# # Red          0;31     Light Red     1;31
# # Green        0;32     Light Green   1;32
# # Brown/Orange 0;33     Yellow        1;33
# # Blue         0;34     Light Blue    1;34
# # Purple       0;35     Light Purple  1;35
# # Cyan         0;36     Light Cyan    1;36
# # Light Gray   0;37     White         1;37

# printstep(){
# 	BLUE='\033[1;34m'
# 	NC='\033[0m' # No Color
# 	echo -e "${BLUE}===> $1 <===${NC}"
# }

# # ======================================

ARPCP_DIR=/srv/arpcp
ARPCP_USER=arpcp-user

./agent_install.sh

packages=(
	nginx
	uwsgi
	uwsgi-plugin-python3
)
for package in ${packages[@]}
do
	printstep "installing $package"
	apt install -y $package 2>/dev/null
done

pymodules=(
	Flask==1.1.2
	Jinja2==2.11.2
	Werkzeug==1.0.1
	python-libnmap==0.7.0
)
for pymodule in ${pymodules[@]}
do
	printstep "installing $pymodule python module"
	pip3 install $pymodule
done

files=(
	arpcp-cluster-registrar.py
	arpcp-cluster-registrar.service
	arpcp-cluster-statistician.py
	arpcp-cluster-statistician.service
	webapp
	webapp.py
	webapp.nginx.conf
	webapp.uwsgi.ini
)
for file in ${files[@]}
do
	printstep "copying $file"
	cp -r $file $ARPCP_DIR/$file
	chmod 777 $ARPCP_DIR/$file
	chown $ARPCP_USER:$ARPCP_USER $ARPCP_DIR/$file
done

daemons=(
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
printstep "creating symlink for webapp.uwsgi.ini"
ln -s $ARPCP_DIR/webapp.uwsgi.ini /etc/uwsgi/apps-enabled/webapp.uwsgi.ini
services=(
	nginx
	uwsgi
)
for service in ${services[@]}
do
	printstep "restarting $service"
	systemctl restart $service
done

