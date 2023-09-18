from pynats import NATSClient
from time import sleep


def send_hello():
    with NATSClient('nats://localhost:4222') as client:
        client.publish('test',payload='hello'.encode())
        client.wait()

send_hello()