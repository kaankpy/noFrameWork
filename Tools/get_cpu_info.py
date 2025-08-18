import multiprocessing
import platform

def get_cpu_info():
    return {
        "cpu_count": multiprocessing.cpu_count(),
        "processor": platform.processor()
    }

if __name__ == "__main__":
    print("CPU Info:", get_cpu_info())