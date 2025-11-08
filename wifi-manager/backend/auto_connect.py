# backend/auto_connect.py
import subprocess
import asyncio
import motor.motor_asyncio
from database import networks

client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = client.wifi_manager

async def auto_connect():
    saved = await db.networks.find().to_list(100)
    for net in saved:
        ssid = net["ssid"]
        password = net.get("password", "")
        print(f"Trying to connect to saved network: {ssid}")

        cmd = f"nmcli dev wifi connect '{ssid}' password '{password}'"
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            print(f"Connected to {ssid}")
            return
        else:
            print(f"Failed {ssid}: {stderr.decode()}")

    print("No saved network connected.")

if __name__ == "__main__":
    asyncio.run(auto_connect())