# Authors:  Chenxin Xun (cx258)
#           Pengru Lung (pl649)
# Final project, Monday Section
# 2024-12-13

import socket

# Function to handle receiving color data from a client
def sending_color():
    global data
    # Server configuration
    HOST = '10.49.240.92' # Server's IP address
    PORT = 5000      # Port to listen on

    # Create a socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow address reuse
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  
    # Bind the socket to the specified IP and port
    server_socket.bind((HOST, PORT)) 
    # Listen for incoming connections (1 client at a time)
    server_socket.listen(1) 

    print("Server is waiting for a connection...")

    # Accept a connection
    client_socket, client_address = server_socket.accept()
    print(f"Connected by {client_address}")

    # Receive data
    data = client_socket.recv(1024).decode('utf-8')
    print(f"Received: {data}")

    # Close the client and server sockets to clean up resources
    client_socket.close()
    server_socket.close()