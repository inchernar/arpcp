# == Procedures for tests =============

def add(a, b):
	return float(a + b)

def sub(a, b):
	return float(a - b)

def multiple(a, b):
	return float(a * b)

def divide(a, b):
	return float(a / b)

# =====================================

# def bash(cmd):
# 	import subprocess
# 	p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
# 	res = p.stdout.read().decode('utf-8')
# 	return res

def long_task(_):
	import time
	time.sleep(10)
	return 'result of long_task()'

# def reboot(_):
# 	import subprocess
# 	p = subprocess.Popen('reboot', shell=True, stdout=subprocess.PIPE)
# 	res = p.stdout.read().decode('utf-8')
# 	return res

def get_time(_):
	import subprocess
	p = subprocess.Popen('date +%T', shell=True, stdout=subprocess.PIPE)
	res = p.stdout.read().decode('utf-8')
	return res

# def set_time(date):
# 	import subprocess
# 	p = subprocess.Popen(f'date +%T -s {date}', shell=True, stdout=subprocess.PIPE)
# 	res = p.stdout.read().decode('utf-8')
# 	return res

def ls(folder):
	import subprocess
	p = subprocess.Popen(f'ls -l {folder}', shell=True, stdout=subprocess.PIPE)
	res = p.stdout.read().decode('utf-8')
	return res

def memory_usage(_):
	def meminfo():
		from collections import OrderedDict
		meminfo=OrderedDict()

		with open('/proc/meminfo') as f:
			for line in f:
				meminfo[line.split(':')[0]] = line.split(':')[1].strip()
		return meminfo
	meminfo = meminfo()
	return f'Total memory: {meminfo["MemTotal"]}\nFree memory: {meminfo["MemFree"]}'

def running_processes(_):
	def process_list():
		import os
		pids = []
		for subdir in os.listdir('/proc'):
			if subdir.isdigit():
				pids.append(subdir)
		return pids
	pids = process_list()
	return f'Total number of running processes: {len(pids)}'