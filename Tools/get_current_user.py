import getpass

def get_current_user():
    return getpass.getuser()

if __name__ == "__main__":
    print("Current User:", get_current_user())