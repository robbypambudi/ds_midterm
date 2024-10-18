import sys

import zmq

REQUEST_TIMEOUT = 1000
MAX_RETRIES = 3


def try_request(ctx: zmq.Context, endpoint: str, request: str):
    print("I: Trying echo service at %s..." % endpoint)

    client = ctx.socket(socket_type=zmq.REQ)
    client.setsockopt(zmq.LINGER, 0)
    client.connect(endpoint)
    client.send_string(request)

    poll = zmq.Poller()
    poll.register(client, zmq.POLLIN)

    socks = dict(poll.poll(REQUEST_TIMEOUT))
    if socks.get(client) == zmq.POLLIN:
        reply = client.recv_multipart()
    else:
        reply = ""

    poll.unregister(client)
    client.close()

    return reply


context = zmq.Context()
request = "Hello world"
reply = None

endpoints = len(sys.argv) - 1
if endpoints == 0:
    print("I: syntax %s <endpoint> ..." % sys.argv[0])
elif endpoints == 1:
    endpoint = sys.argv[1]
    for retries in range(MAX_RETRIES):
        reply = try_request(context, endpoint, request)
        if reply:
            break

        print("W: No response from %s, retrying" % endpoint)
else:
    for endpoint in sys.argv[1:]:
        reply = try_request(context, endpoint, request)
        if reply:
            break

        print("W: No response from %s" % endpoint)

if reply:
    print("Service is running OK")
