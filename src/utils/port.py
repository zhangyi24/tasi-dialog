import socket

# https://stackoverflow.com/questions/44875422/how-to-pick-a-free-port-for-a-subprocess

def free_port():
    """
    Determines a free port using sockets.
    """
    free_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    free_socket.bind(('0.0.0.0', 0))
    free_socket.listen(5)
    port = free_socket.getsockname()[1]
    free_socket.close()
    return port

def port_open(port)
    a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    location = ("127.0.0.1", port)
    result_of_check = a_socket.connect_ex(location)
    # 0 means port open
    return result_of_check
    
if __name__ == "__main__":
    print(free_port())