import os, re, subprocess


def parse_os_release() -> dict:
    os_info = {}
    with open('/etc/os-release', 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            key, value = line.split('=', 1)

            value = value.strip('"')

            os_info[key] = value

    return os_info


def get_display_server() -> str:
    session_type = os.getenv('XDG_SESSION_TYPE')
    if session_type:
        return session_type
    else:
        return "Not detected"


def get_cpu_info_from_proc():
    with open("/proc/cpuinfo", "r") as f:
        cpu_info = f.read()

    cpu_name = None
    for line in cpu_info.splitlines():
        if line.startswith("model name"):
            cpu_name = line.split(":")[1].strip()
            break

    num_cores = cpu_info.count("processor")

    return cpu_name, num_cores


def get_memory_info_from_free():
    try:
        result = subprocess.run(['free', '-b'], capture_output=True, text=True)
        memory_info = result.stdout

        lines = memory_info.splitlines()
        total_memory = int(lines[1].split()[1])
        used_memory = int(lines[1].split()[2])
        free_memory = int(lines[1].split()[3])

        return total_memory, used_memory, free_memory
    except FileNotFoundError:
        return "free command not found", None, None


def get_video_info_from_inxi():
    try:
        result = subprocess.run(['inxi', '-G', '-c'], capture_output=True, text=True)
        output = result.stdout
#         output = """Graphics:
#   Device-1: Intel CometLake-H GT2 [UHD Graphics] driver: i915 v: kernel
#   Device-2: NVIDIA TU116M [GeForce GTX 1660 Ti Mobile] driver: nouveau
#     v: kernel
#   Device-3: Chicony HP Wide Vision HD Camera driver: uvcvideo type: USB
#   Display: x11 server: X.Org v: 1.21.1.14 driver: X:
#     loaded: modesetting,nouveau unloaded: fbdev,vesa dri: iris,nouveau gpu: i915
#     resolution: 1920x1080~60Hz
#   API: EGL v: 1.5 drivers: iris,nouveau,swrast
#     platforms: gbm,x11,surfaceless,device
#   API: OpenGL v: 4.6 compat-v: 4.3 vendor: intel mesa v: 24.2.6
#     renderer: Mesa Intel UHD Graphics (CML GT2)
# """
        gpu_info = re.findall(r'Device-\d+:\s*(.*?)\s*driver:\s*(\S+)\s*v:\s*(\S+)', output)
        # for device in gpu_info:
        #     device_name, driver, version = device
        #     print(f"Устройство: {device_name}\nДрайвер: {driver}\nВерсия: {version}\n")

        return gpu_info
    except FileNotFoundError:
        return "inxi command not found", None, None

if __name__ == "__main__":
    os_info = parse_os_release()
    for key, value in os_info.items():
        print(f"{key}: {value}")
