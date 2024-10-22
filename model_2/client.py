import time
import zmq
from random import randint

class Client: 
  MAX_RETRIES = 10
  MAX_REQUESTS_TIMEOUT = 3000

  def __init__(self, servers):
    self.servers = 0
    self.sequence = 0
    self.context = zmq.Context()
    self.socket = self.context.socket(zmq.DEALER)
    self.client_id = "%04X-%04X" % (randint(0, 0x10000), randint(0, 0x10000))

    
  def destroy(self):
    self.socket.setsockopt(zmq.LINGER, 0)  # Terminate early
    self.socket.close()
    self.context.term()
  
  def connect(self, endpoint):
    self.socket.connect(endpoint)
    self.servers += 1
    print("%s: Connected to %s" % (self.client_id, endpoint))
  
  def request(self, *request):
    self.sequence += 1
    msg = [b"", str(self.sequence).encode()] + list(request)
    
    for server in range(self.servers):
        self.socket.send_multipart(msg)

    poll = zmq.Poller()
    poll.register(self.socket, zmq.POLLIN)

    socks = dict(poll.poll(self.MAX_REQUESTS_TIMEOUT))
    
    reply = None
    endtime = time.time() + self.MAX_REQUESTS_TIMEOUT / 1000
    while time.time() < endtime:
      socks = dict(poll.poll((endtime - time.time()) * 1000))
      if socks.get(self.socket) == zmq.POLLIN:
        reply = self.socket.recv_multipart()
        # assert len(reply) == 3
        sequence = int(reply[1])
        if sequence == self.sequence:
          break
    return reply

if __name__ == '__main__':
  server_list = [
    "tcp://192.168.1.43:5555",
    "tcp://192.168.1.43:5556",
    "tcp://192.168.1.43:5557",
  ]
  
  client = Client(servers=server_list)
  
  endpoint = len(server_list) - 1
  print("%s: Trying to connect to server..." % client.client_id)

  for server in server_list:
      client.connect(server)
  
  print("List of commands: ")
  print("- HEALTH")
  print("- LIST")
  print("- LIST_ALL")
  print("- DOWNLOAD <filename>")
  print("- EXIT")
  while True:
      command = input("Enter your message: ")
      if (input == "EXIT"):
          raise Exception("Exiting the program")
      
      if command.startswith("DOWNLOAD"):
          command = command.split(" ")
          reply = client.request(command[0].encode(), command[1].encode())
          
          with open(f"client_{command[1]}", "wb") as f:
              f.write(reply[0])
          
          print(f"Downloaded {command[1]}")
          continue
      else:
          reply = client.request(command.encode())   
          if not reply:
              print("E: No response from server")
              break
          for i in range(len(reply)):
              if i == 0:
                  continue
              else:
                  print("Message: %s" % reply[i].decode())
    