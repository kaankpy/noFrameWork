import platform
import subprocess

def get_gpu_info():
    try:
        if platform.system() == "Windows":
            result = subprocess.check_output(
                ["wmic", "path", "win32_VideoController", "get", "name"],
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                universal_newlines=True
            )
            lines = [line.strip() for line in result.splitlines() if line.strip() and "Name" not in line]
            return lines if lines else ["Unavailable"]
        elif platform.system() == "Linux":
            result = subprocess.check_output(
                ["lspci"],
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                universal_newlines=True
            )
            gpus = [line for line in result.splitlines() if "VGA compatible controller" in line or "3D controller" in line]
            return gpus if gpus else ["Unavailable"]
        else:
            return ["Unavailable"]
    except Exception:
        return ["Unavailable"]

if __name__ == "__main__":
    print("GPU Info:", get_gpu_info())