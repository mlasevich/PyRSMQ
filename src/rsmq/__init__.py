''' 
Python Implementation of the Redis Simple Message Queue  serverless(*) queue service

(* requires only Redis server)

Based on:

  * Original Node.js version: https://github.com/smrchy/rsmq
  * Java port: https://github.com/igr/jrsmq

'''

from .rsmq import RedisSMQ
