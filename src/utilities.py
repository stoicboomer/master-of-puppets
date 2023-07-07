import os
import psutil
import subprocess
import io
import socket
import platform
import json

def getMachineInfo():
    cpu = psutil.cpu_freq()
    return {
        "hostname": platform.node(),
        "arch": platform.machine(),
        "system": platform.system(),
        "platform": platform.platform(),
        "ram": psutil.virtual_memory().total // (2 ** 20),
        "cpuFreq": { "current": round(cpu.current), "max": cpu.max },
    }

def execCommand(cmd):
    r = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = r.stdout.read()
    stderr = r.stderr.read()

    return (stdout.decode(), stderr.decode())
