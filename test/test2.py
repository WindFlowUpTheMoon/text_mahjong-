from pynats import NATSClient


with NATSClient('nats://localhost:4222') as client:
    client.subscribe('')