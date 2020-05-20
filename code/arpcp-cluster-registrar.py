import time
import arpcp

if __name__ == "__main__":
	while True:
		arpcp.Controller.echo()
		time.sleep(20)
