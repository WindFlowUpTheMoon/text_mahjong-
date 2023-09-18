from pynats import NATSClient


def receive():
    with NATSClient('nats://localhost:4222') as client:
        client.subscribe('test', callback = handle_test)
        client.wait()

def handle_test(msg):
    msg=msg.payload.decode()
    print(msg)

receive()