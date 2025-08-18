import shutil

def get_storage_info(path="/"):
    total, used, free = shutil.disk_usage(path)
    gb = 1024 ** 3
    return {
        "total_gb": total / gb,
        "used_gb": used / gb,
        "free_gb": free / gb
    }

if __name__ == "__main__":
    storage = get_storage_info()
    print(f"Total Storage: {storage['total_gb']:.2f} GB")
    print(f"Used Storage: {storage['used_gb']:.2f} GB")
    print(f"Free Storage: {storage['free_gb']:.2f} GB")