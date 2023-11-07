from pynats import NATSClient


with NATSClient("nats://localhost:4222") as client:
    client.publish('1.startserver', payload = 'hello'.encode())