import zmq
from random import randint

class Client: 
  MAX_RETRIES = 10
  MAX_REQUESTS_TIMEOUT = 3000

  def __init__(self):
    self.servers = 0
    self.sequence = 0
    self.context = zmq.Context()
    self.socket = self.context.socket(zmq.REQ) 
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
    msg = [b""] + list(request)
    self.socket.send_multipart(msg)

    poll = zmq.Poller()
    poll.register(self.socket, zmq.POLLIN)

    socks = dict(poll.poll(self.MAX_REQUESTS_TIMEOUT))
    if socks.get(self.socket) == zmq.POLLIN:
      reply = self.socket.recv_multipart()
    else:
      reply = None
    return reply

if __name__ == '__main__':
  server_list = [
    "tcp://192.168.18.71:5555",
    "tcp://192.168.18.71:5557",
  ]
  
  client = Client()
  
  endpoint = len(server_list) - 1
  print("%s: Trying to connect to server..." % client.client_id)
  client.connect(server_list[endpoint])
  
  while endpoint >= 0:
    try :
      # List Command
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
              print("Server: %s" % reply[i].decode())
            else:
              print("Message: %s" % reply[i].decode())
      
    except Exception as e:
      print("E: Couldn't connect to server %s" % server_list[endpoint])
      print("E: %s" % e)
      endpoint -= 1
      client.connect(server_list[endpoint])
      continue