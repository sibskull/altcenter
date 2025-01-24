import os, re, subprocess


def parse_os_release(file_name = '/etc/os-release') -> dict:
    os_info = {'PRETTY_NAME': 'Name of Linux not found'}

    try:
        with open(file_name, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                key, value = line.split('=', 1)

                value = value.strip('"')

                os_info[key] = value
    except:
        pass

    if 'PRETTY_NAME' in os_info:
        s = os_info["PRETTY_NAME"].split('(')[0]

        # Делим на слова и версию
        match = re.split(r'( \d)', s, maxsplit=1)

        name = match[0]  # До первой цифры
        rest = match[1] + match[2] if len(match) > 2 else ""  # Остальная часть (с числом)

        os_info["MY_NAME"] = name
        os_info["MY_NAME_REST"] = rest.rstrip()

    return os_info


def get_display_server() -> str:
    session_type = os.getenv('XDG_SESSION_TYPE')
    if session_type:
        return session_type
    else:
        return "Not detected"


def get_cpu_info_from_proc(file_name = '/proc/cpuinfo'):
    cpus = {}

    with open(file_name, 'r') as f:
        cpu_info = f.read()

    # cpu_name = None
    # for line in cpu_info.splitlines():
    #     if line.startswith('model name'):
    #         cpu_name = line.split(':')[1].strip()
    #         if cpu_name not in cpus:
    #             cpus[cpu_name] = {}
    #         continue
    #
    #     if line.startswith('core id'):
    #         core_id = line.split(':')[1].strip()
    #         # if core_id not in cpu:
    #         cpus[cpu_name][core_id] = cpus[cpu_name].get(core_id, 0) + 1
    #
    # print(cpus)
    # result = []
    # for cpu in cpus:
    #     cores = len(cpus[cpu])
    #     threads = sum(cpus[cpu].values())
    #     result.append( (cpu, cores, threads,))
    #     print(cpu, cores, threads)
    #     print(result)

    cpu_id, cpu_name, core_id = None, None, None

    for line in cpu_info.splitlines():
        if line.startswith('physical id'):
            cpu_id = line.split(':')[1].strip()
            continue

        if line.startswith('model name'):
            cpu_name = line.split(':')[1].strip()
            continue

        if line.startswith('core id'):
            core_id = line.split(':')[1].strip()
            continue

        if line.strip() == '':
            if cpu_id != None and cpu_name != None and core_id != None:
                if cpu_id not in cpus:
                    cpus[cpu_id] = {}
                if 'name' not in cpus[cpu_id]:
                    cpus[cpu_id]['name'] = cpu_name
                if 'cores' not in cpus[cpu_id]:
                    cpus[cpu_id]['cores'] = {}
                cpus[cpu_id]['cores'][core_id] = cpus[cpu_id]['cores'].get(core_id, 0) + 1

                cpu_id, cpu_name, core_id = None, None, None


    # print(cpus)
    # print()
    result = []
    for id in cpus:
        cpu = cpus[id]
        cores = len(cpu['cores'])
        threads = sum(cpu['cores'].values())
        result.append( (cpu['name'], cores, threads,))
        # print(cpu['name'], cores, threads)
        # print(result)
        # cpus[id]['cores'] = cores
        # cpus[id]['threads'] = threads
    # print(cpus)
    return result


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
    pass

    def test_parse_os_release(s) -> str:
        os_info = parse_os_release(s)
        s = os_info['PRETTY_NAME']
        ns = f"{os_info['MY_NAME']=}\n{os_info['MY_NAME_REST']=}"
        print(s)
        print(ns)
        print()

    test_parse_os_release('./tests/etc/os-release-regular')
    test_parse_os_release('./tests/etc/os-release-edu')
    test_parse_os_release('./tests/etc/os-release-wsk')
    test_parse_os_release('./tests/etc/os-release-server-v')
    test_parse_os_release('./tests/etc/os-release-xxx')

    # for key, value in os_info.items():
    #     print(f"{key}: {value}")

    text = "ALT Virtualization Server 10.2 10.4 25 56 abc   "
    # text = "ALT Regular"

    match = re.split(r'( \d)', text, maxsplit=1)

    part1 = match[0]
    part2 = match[1] + match[2] if len(match) > 2 else ""
    part2 = part2.rstrip()

    print(f"Часть до первой цифры: '{part1}'")
    print(f"Остальная часть: '{part2}'")
