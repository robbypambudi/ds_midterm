import sys
from random import randint

import zmq
from tabulate import tabulate


class RETURN_VALUE:
    ERR_STRING = "ERROR"
    SUCCESS_STRING = "SUCCESS"

    ERR_BYTES = ERR_STRING.encode()
    SUCCESS_BYTES = SUCCESS_STRING.encode()


class Client:
    MAX_REQUESTS_TIMEOUT = 1000

    def __init__(self, endpoint_list: list[str]) -> None:
        self.endpoint_list = endpoint_list
        self.sequence = 0

        # client identifier
        self.client_id = "%04X-%04X" % (randint(0, 0x10000), randint(0, 0x10000))

        # socket configuration
        self.__context = zmq.Context()
        self.__socket = self.__context.socket(zmq.DEALER)

    def destroy(self) -> None:
        # close the socket
        self.__socket.setsockopt(zmq.LINGER, 0)  # Terminate early
        self.__socket.close()
        self.__context.term()

        return

    def connect(self, endpoint: str) -> None:
        self.__socket.connect(endpoint)
        print(f"{self.client_id}: Connected to {endpoint}")

    def send_request(self, request: list):
        reply: list = []
        self.sequence += 1
        msg = [b"", self.client_id.encode(), str(self.sequence).encode()] + request
        print(f"I: Sending request {msg}")

        for server in range(len(self.endpoint_list)):
            self.__socket.send_multipart(msg)
            print(f"I: {self.client_id}: Sent request to {self.endpoint_list[server]}")

        poll = zmq.Poller()
        poll.register(self.__socket, zmq.POLLIN)

        for _ in range(len(self.endpoint_list)):
            socks = dict(poll.poll(self.MAX_REQUESTS_TIMEOUT))
            if socks.get(self.__socket) == zmq.POLLIN:
                temp = self.__socket.recv_multipart()
                if self.sequence == int(temp[2].decode()):
                    reply.append(temp)

        poll.unregister(self.__socket)

        return reply


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(f"E: Syntax: {sys.argv[0]} <server_endpoint>...")
        sys.exit(1)

    client = Client(sys.argv[1:])
    print(f"I: Client started: ID: {client.client_id}")

    for server in client.endpoint_list:
        client.connect(server)

    while True:
        print("List of commands: ")
        print("- HEALTH")
        print("- LIST")
        print("- LIST_ALL")
        print("- DOWNLOAD <filename>")
        print("- EXIT")
        command = input("Enter your message: ").split(" ")
        bytes_command: list[bytes] = []
        for i in range(0, len(command)):
            bytes_command.append(command[i].encode())

        try:
            if command[0] == "EXIT":
                print("I: Exiting program...")
                client.destroy()
                sys.exit(0)
            elif command[0] == "HEALTH":
                headers = ["MESIN", "FILES"]
                data = []

                replies = client.send_request([bytes_command[0]])
                for reply in replies:
                    data.append([reply[1].decode(), reply[4].decode()])

                print(tabulate(data, headers, tablefmt="grid"))
                print("")
            elif command[0] == "LIST" or command[0] == "LIST_ALL":
                headers = ["MESIN", "FILES"]
                data = []

                replies = client.send_request([bytes_command[0]])
                for reply in replies:
                    temp_data = [reply[1].decode()]
                    filenames = ""

                    for i in reply[4:-1]:
                        filenames += i.decode() + ", "
                    filenames += reply[-1].decode()

                    temp_data.append(filenames)
                    data.append(temp_data)

                print(tabulate(data, headers, tablefmt="grid"))
                print("")

            elif command[0] == "DOWNLOAD":
                replies = client.send_request(bytes_command)
                print("Reply: ", replies)
                for r in replies:
                    if r[3] == RETURN_VALUE.SUCCESS_BYTES and len(r) == 4:
                        open(command[1] + "_" + command[2], "wb")
                    elif r[3] == RETURN_VALUE.SUCCESS_BYTES and len(r) != 4:
                        with open(command[1] + "_" + command[2], "wb") as f:
                            for i in range(4, len(r)):
                                f.write(r[i])
            else:
                replies = client.send_request([bytes_command[0]])
                print("Reply: ", replies)
        except Exception as e:
            print(f"E: {e}")
            sys.exit(1)
