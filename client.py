import os
import sys
import time
import socket
import struct

data_request_size = int(sys.argv[1])

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("10.0.2.2", 12345))

packed = struct.pack("!i", data_request_size)

start_time = time.time()
client_socket.sendall(packed)

amount_received = 0

while amount_received < data_request_size:
    data = client_socket.recv(1024)
    amount_received += len(data)

print("\tTotal time:", time.time() - start_time, "seconds")
print("\tAmount bytes received:", amount_received)

client_socket.close()
