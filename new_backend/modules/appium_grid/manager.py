import subprocess
import time
import socket
import os
import requests

appium_servers = []
_appium_processes = {}

# 🔥 IMPORTANT: FULL PATH TO APPIUM
APPIUM_PATH = "C:\\Users\\ABDUL SAMAD\\AppData\\Roaming\\npm\\appium.cmd"


# ─────────────────────────────────────────────
# GET DEVICES
# ─────────────────────────────────────────────
def get_connected_devices():
    try:
        result = subprocess.run(
            "adb devices",
            shell=True,
            capture_output=True,
            text=True
        )

        lines = result.stdout.strip().split("\n")[1:]
        devices = []

        for line in lines:
            if "\tdevice" in line:
                devices.append(line.split("\t")[0])

        print(f"📱 Devices → {devices}")
        return devices

    except Exception as e:
        print(f"❌ ADB ERROR: {e}")
        return []


# ─────────────────────────────────────────────
# CHECK PORT
# ─────────────────────────────────────────────
def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


# ─────────────────────────────────────────────
# WAIT FOR APPIUM
# ─────────────────────────────────────────────
def wait_for_appium(port):
    url = f"http://127.0.0.1:{port}/status"

    for i in range(60):
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                print(f"✅ APPIUM READY → port {port}")
                return True
        except:
            pass

        print(f"⏳ WAITING APPIUM port:{port} ({i+1}/60)")
        time.sleep(1)

    raise Exception(f"❌ APPIUM NOT STARTED → port {port}")


# ─────────────────────────────────────────────
# START APPIUM
# ─────────────────────────────────────────────
def start_appium_servers():
    global appium_servers, _appium_processes

    # 🔥 CHECK APPIUM EXISTS
    if not os.path.exists(APPIUM_PATH):
        raise Exception(f"❌ Appium not found at: {APPIUM_PATH}")

    devices = get_connected_devices()

    if not devices:
        raise Exception("❌ NO DEVICES FOUND")

    print("\n🚀 STARTING APPIUM GRID\n")

    BASE_PORT = 4723
    servers = []

    for i, device in enumerate(devices):
        port = BASE_PORT + (i * 2)

        print(f"\n📱 Device → {device}")
        print(f"🔌 Port   → {port}")

        # Kill port if busy
        if is_port_open(port):
            print(f"⚠️ Port {port} busy. Killing...")
            subprocess.run(f"npx kill-port {port}", shell=True)
            time.sleep(2)

        try:
            log_file = open(f"appium_{port}.log", "w")
            
            proc = subprocess.Popen(
            [
                APPIUM_PATH,
                "-p", str(port),
                "--base-path", "/",
                "--session-override",
                "--log-level", "error"
            ],
                stdout=log_file,
                stderr=log_file,
                creationflags=subprocess.CREATE_NEW_CONSOLE  # 🔥 important for Windows
            )

            print(f"🧠 PID → {proc.pid}")

            # 🔥 Check crash immediately
            time.sleep(3)
            if proc.poll() is not None:
                out, err = proc.communicate()
                print("❌ Appium crashed!")
                print(out)
                print(err)
                raise Exception("Appium failed to start")

            wait_for_appium(port)

            _appium_processes[port] = proc

            servers.append({
                "device": device,
                "port": port,
                "pid": proc.pid
            })

            print(f"✅ Started → {device} on {port}")

        except Exception as e:
            print(f"❌ Failed for {device}: {e}")
            raise

    appium_servers = servers

    print("\n🔥 APPIUM GRID READY\n")
    for s in servers:
        print(f"{s['device']} → {s['port']}")

    return servers


# ─────────────────────────────────────────────
# STOP APPIUM
# ─────────────────────────────────────────────
def stop_appium_servers():
    global appium_servers, _appium_processes

    print("\n🛑 STOPPING APPIUM\n")

    for port, proc in _appium_processes.items():
        try:
            proc.terminate()
            proc.wait(timeout=3)
            print(f"✅ Stopped → {port}")
        except:
            proc.kill()

    appium_servers = []
    _appium_processes = {}

    print("✅ ALL STOPPED\n")


# ─────────────────────────────────────────────
# GET PROCESS
# ─────────────────────────────────────────────
def get_appium_process(port):
    return _appium_processes.get(port)