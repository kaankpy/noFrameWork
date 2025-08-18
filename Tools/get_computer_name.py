import socket

def get_computer_name():
    return socket.gethostname()

if __name__ == "__main__":
    print("Computer Name:", get_computer_name())