'''
Constant values
'''

# max length of queue name
QNAME_MAX_LEN = 64

QNAME_INVALID_CHARS_RE = r'[^A-Za-z0-9._-]'

# Suffix to append to the queue
QUEUE_SUFFUX = ":Q"

# suffix to append to the queue set
QUEUES = "QUEUES"

# minimum VT - seconds
VT_MIN = 0

# maximum VT - seconds
VT_MAX = 9999999

VT_DEFAULT = 30


# minimum DELAY - seconds
DELAY_MIN = 0

# maximum DELAY - seconds
DELAY_MAX = 9999999

DELAY_DEFAULT = 0


MAXSIZE_MIN = 1024
MAXSIZE_MAX = 65565
MAXSIZE_DEFAULT = MAXSIZE_MAX


SCRIPT_POPMESSAGE = 'local msg = redis.call("ZRANGEBYSCORE", KEYS[1], "-inf", KEYS[2], "LIMIT", "0", "1") if #msg == 0 then return {} end redis.call("HINCRBY", KEYS[1] .. ":Q", "totalrecv", 1) local mbody = redis.call("HGET", KEYS[1] .. ":Q", msg[1]) local rc = redis.call("HINCRBY", KEYS[1] .. ":Q", msg[1] .. ":rc", 1) local o = {msg[1], mbody, rc} if rc==1 then table.insert(o, KEYS[2]) else local fr = redis.call("HGET", KEYS[1] .. ":Q", msg[1] .. ":fr") table.insert(o, fr) end redis.call("ZREM", KEYS[1], msg[1]) redis.call("HDEL", KEYS[1] .. ":Q", msg[1], msg[1] .. ":rc", msg[1] .. ":fr") return o'
SCRIPT_RECEIVEMESSAGE = 'local msg = redis.call("ZRANGEBYSCORE", KEYS[1], "-inf", KEYS[2], "LIMIT", "0", "1") if #msg == 0 then return {} end redis.call("ZADD", KEYS[1], KEYS[3], msg[1]) redis.call("HINCRBY", KEYS[1] .. ":Q", "totalrecv", 1) local mbody = redis.call("HGET", KEYS[1] .. ":Q", msg[1]) local rc = redis.call("HINCRBY", KEYS[1] .. ":Q", msg[1] .. ":rc", 1) local o = {msg[1], mbody, rc} if rc==1 then redis.call("HSET", KEYS[1] .. ":Q", msg[1] .. ":fr", KEYS[2]) table.insert(o, KEYS[2]) else local fr = redis.call("HGET", KEYS[1] .. ":Q", msg[1] .. ":fr") table.insert(o, fr) end return o'
SCRIPT_CHANGEMESSAGEVISIBILITY = 'local msg = redis.call("ZSCORE", KEYS[1], KEYS[2]) if not msg then return 0 end redis.call("ZADD", KEYS[1], KEYS[3], KEYS[2]) return 1'
