import time
import json
import arpcp

def pulse():
	_redis = arpcp.ARPCP.redis()
	if _redis.exists("ARPCP:statistic:status"):
		stat = json.loads(_redis.get("ARPCP:statistic:status"))
		stat["sent_to_agent"].pop(0)
		stat["done"].pop(0)
		stat["error"].pop(0)
	else:
		stat = {
			"sent_to_agent": [0 for i in range(10)],
			"done": [0 for i in range(10)],
			"error": [0 for i in range(10)]
		}
	curr_stat = arpcp.Controller.status_statistics()
	stat["sent_to_agent"].append(curr_stat["sent_to_agent"])
	stat["done"].append(curr_stat["done"])
	stat["error"].append(curr_stat["error"])
	_redis.set("ARPCP:statistic:status", json.dumps(stat))


if __name__ == "__main__":
	while True:
		pulse()
		time.sleep(5)
