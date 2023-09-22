from pynats import NATSClient
from time import sleep


class Server:
    def __init__(self):
        self.addr = 'nats://localhost:4222'
        self.create_connection()


    def create_connection(self):
        self.client = NATSClient('nats://localhost:4222')
        self.client.connect()


    def close_connection(self):
        self.client.close()


    def send_msg(self, msg):
        self.client.publish('test', payload = msg.encode())
        # self.client.close()


server = Server()
server.send_msg('hello')
# server.send_msg('world')