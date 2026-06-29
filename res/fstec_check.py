#!/usr/bin/python3

import os
import json
import subprocess

TAB_VALUES = (
    40,
    20,
    20,
    20,
    50
)

sysctl_dict = {
    "kernel.dmesg_restrict": ("1", None),
    "kernel.kptr_restrict": ("2", None),
    "kernel.randomize_va_space": ("2", "kernel:CONFIG_COMPAT_BRK=n"),
    "kernel.yama.ptrace_scope": ("3", None),
    "kernel.kexec_load_disabled": ("1", None),
    "kernel.unprivileged_bpf_disabled": ("2", None),
    "kernel.perf_event_paranoid": ("3", None),
    "vm.unprivileged_userfaultfd": ("0", None),
    "vm.mmap_min_addr": ("4096", "boot:CONFIG_DEFAULT_MMAP_MIN_ADDR=4096"),
    "fs.protected_symlinks": ("1", None),
    "fs.protected_hardlinks": ("1", None),
    "fs.protected_fifos": ("2", None),
    "fs.protected_regular": ("2", None),
    "fs.suid_dumpable": ("0", None),
    "user.max_user_namespaces": ("0", None),
    "dev.tty.ldisc_autoload": ("0", "kernel:CONFIG_LDISC_AUTOLOAD=n"),
    "net.core.bpf_jit_harden": ("2", None)
}

sudo_calls = [
    "fs.protected_symlinks",
    "fs.protected_hardlinks",
    "fs.protected_fifos",
    "fs.protected_regular",
    "net.core.bpf_jit_harden"
]

cmdline_dict = {
    "init_on_alloc": (None, "kernel:CONFIG_INIT_ON_ALLOC_DEFAULT_ON=y"),
    "slab_nomerge": (None, "kernel:CONFIG_SLAB_MERGE_DEFAULT=n"),
    "iommu": ("force", None),
    "iommu.strict": ("1", None),
    "iommu.passthrough": ("0", None),
    "randomize_kstack_offset": ("1", "kernel:CONFIG_RANDOMIZE_KSTACK_OFFSET_DEFAULT=y"),
    "mitigations": ("auto,nosmt", None),
    "vsyscall": ("none", "kernel:CONFIG_LEGACY_VSYSCALL_NONE=y"),
    "debugfs": ("no-mount", "kernel:CONFIG_DEBUG_FS_DISALLOW_MOUNT=y"),
    "tsx": ("off", "kernel:CONFIG_X86_INTEL_TSX_MODE_OFF=y")
}

kernel_dict = {
    "CONFIG_INIT_ON_ALLOC_DEFAULT_ON": ("y", "boot:init_on_alloc"),
    "CONFIG_SLAB_MERGE_DEFAULT": ("n", "boot:slab_nomerge"),
    "CONFIG_RANDOMIZE_KSTACK_OFFSET_DEFAULT": ("y", "boot:randomize_kstack_offset=1"),
    "CONFIG_LEGACY_VSYSCALL_NONE": ("y", "boot:vsyscall=none"),
    "CONFIG_LDISC_AUTOLOAD": ("n", "sysctl:dev.tty.ldisc_autoload=0"),
    "CONFIG_X86_INTEL_TSX_MODE_OFF": ("y", "boot:tsx=off"),
    "CONFIG_COMPAT_BRK": ("n", "sysctl:kernel.randomize_va_space=2"),
    "CONFIG_DEBUG_FS_DISALLOW_MOUNT": ("y", "boot:debugfs=no-mount"),
    "CONFIG_DEBUG_FS": ("n", None)
}


def sanitize_str(input_str) -> str:
    return "" if input_str is None else str(input_str)


def compare_sysctl():
    rows = []

    for key, ref_val in sysctl_dict.items():
        ret = subprocess.run(['/sbin/sysctl', key],
                             stderr=subprocess.DEVNULL,
                             stdout=subprocess.PIPE).stdout.decode('utf-8')
        if (os.geteuid() != 0) and (key in sudo_calls) or not ret:
            cur_val, cur_result = "unknown", "unknown"
        else:
            cmd, cur_val = ret.split()[0], ret.split()[2]
            cur_result = "OK" if cur_val == ref_val[0] else "FAIL"

        rows.append([
            key,
            cur_val,
            ref_val[0],
            cur_result,
            ref_val[1] if ref_val[1] else ''
        ])

    return rows


def compare_cmdline():
    rows = []

    ret = subprocess.run(['cat', '/proc/cmdline'], stdout=subprocess.PIPE).stdout.decode('utf-8').split()
    ret_dict = {}

    for item in ret:
        split_item = item.split('=')
        ret_dict[split_item[0]] = split_item[1] if len(split_item) == 2 else None

    for key, ref_val in cmdline_dict.items():
        if key in ret_dict.keys():
            cur_result = "OK" if ret_dict[key] == ref_val[0] else "FAIL"

            rows.append([
                sanitize_str(key),
                sanitize_str(ret_dict[key]),
                sanitize_str(ref_val[0]),
                sanitize_str(cur_result),
                sanitize_str(ref_val[1])
            ])
        else:
            ref_val_tmp = ref_val[0] if ref_val[0] else "no value"

            rows.append([
                sanitize_str(key),
                "not present",
                sanitize_str(ref_val_tmp),
                "FAIL",
                sanitize_str(ref_val[1])
            ])

    return rows


def compare_config():
    rows = []

    uname = subprocess.run(['uname', '-r'], stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    config_path = os.path.expanduser(f"/boot/config-{uname}")

    if not os.path.exists(config_path):
        rows.append([
            "config not found",
            "",
            "",
            "",
            ""
        ])
        return rows

    for key, ref_val in kernel_dict.items():
        ret = subprocess.run(['grep', '-w', key, config_path],
                             stdout=subprocess.PIPE).stdout.decode('utf-8').split()
        if not ret:
            rows.append([
                key,
                "None",
                ref_val[0],
                "FAIL",
                ref_val[1] if ref_val[1] else ''
            ])
            continue
        elif len(ret) == 1:
            split_ret = ret[0].split('=')
            cur_result = "OK" if split_ret[1] == ref_val[0] else "FAIL"

            rows.append([
                key,
                split_ret[1],
                ref_val[0],
                cur_result,
                ref_val[1] if ref_val[1] else ''
            ])
        else:
            rows.append([
                key,
                "is not set",
                ref_val[0],
                "FAIL",
                ref_val[1] if ref_val[1] else ''
            ])

    return rows


if __name__ == "__main__":
    data = {
        "boot": compare_cmdline(),
        "sysctl": compare_sysctl(),
        "kernel": compare_config()
    }

    with open("/tmp/altcenter_fstec_check.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    os.chmod("/tmp/altcenter_fstec_check.json", 0o644)