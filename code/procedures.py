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

def bash(cmd):
	import subprocess
	p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	res = p.stdout.read().decode('utf-8')
	return res
