import sys
from random import randint

import zmq


class Client:
    REQUEST_TIMEOUT = 1000
    MAX_RETRIES = 3

    def __init__(self, server_endpoint: str) -> None:
        self.server_endpoint = server_endpoint
        self.context = zmq.Context()
        self.client = self.context.socket(zmq.REQ)
        self.client_id = "%04X-%04X" % (randint(0, 0x10000), randint(0, 0x10000))

    def connect(self, msg: str):
        print("I: Trying server at %s..." % self.server_endpoint)

        split_msg = msg.split(" ")
        bytes_msg: list[bytes] = []

        for m in split_msg:
            bytes_msg.append(m.encode())

        # try to connect and send the message
        self.client.connect(self.server_endpoint)
        self.client.send_multipart(bytes_msg)

        # poll for response
        poll = zmq.Poller()
        poll.register(self.client, zmq.POLLIN)
        socks = dict(poll.poll(self.REQUEST_TIMEOUT))

        if socks.get(self.client) == zmq.POLLIN:
            reply = self.client.recv_multipart()
        else:
            reply = ""

        poll.unregister(self.client)
        self.client.close()

        return reply

    def destroy(self) -> None:
        self.client.setsockopt(zmq.LINGER, 0)
        self.client.close()
        self.context.term()


if __name__ == "__main__":
    endpoints = len(sys.argv) - 1

    if endpoints == 0:
        print("I: syntax %s <endpoint> ..." % sys.argv[0])
    elif endpoints == 1:
        endpoint = sys.argv[1]

        client = Client(endpoint)

        for retries in range(client.MAX_RETRIES):
            reply = client.connect("get temp.txt")
            if reply:
                print("I: Server replied OK (%s)" % reply)
                break

            print("W: No response from %s, retrying" % endpoint)
    else:
        for endpoint in sys.argv[1:]:
            client = Client(endpoint)

            for retries in range(client.MAX_RETRIES):
                reply = client.connect(
                    f"hello world, this one is from {client.client_id}"
                )
                if reply:
                    print("I: Server replied OK (%s)" % reply)
                    break

                print("W: No response from %s, retrying" % endpoint)
