import platform

def get_os_info():
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "python_version": platform.python_version()
    }

if __name__ == "__main__":
    print("OS Info:", get_os_info())