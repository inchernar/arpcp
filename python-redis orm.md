# import
```python
import redis

redis_client = redis.Redis(host = '127.0.0.1', port = 6379)
```

# SET

redis -> `set <key> <value>`

python -> 
```python
redis_client[<key>] = [<value>]
# or
redis_client.update(<dict>)
# or
redis_client.mset(<dict>)
```

# GET

redis -> `get <value>`

python ->
```python
redis_client.get(<value>)
# or
[redis_client[k] for k in ("Lebanon", "Norway", "Bahamas")]
```

# MORE

python ->
```python
redis_client.ping()

<value> in redis_client
```