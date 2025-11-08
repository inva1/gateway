from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import subprocess
import json
import re
from datetime import datetime
from models import WifiNetwork, ConnectionLog
from database import networks, history
import os

app = FastAPI(title="Raspberry Pi WiFi Manager")

# Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve React build
app.mount("/static", StaticFiles(directory="../frontend/dist"), name="static")

@app.get("/")
async def root():
    return FileResponse("../frontend/dist/index.html")

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr

@app.get("/api/scan")
async def scan_networks():
    code, output = run_command("nmcli -t -f SSID,SIGNAL,SECURITY,IN-USE dev wifi list")
    if code != 0:
        raise HTTPException(500, "Failed to scan")
    
    nets = []
    seen = set()
    for line in output.splitlines():
        if not line.strip(): continue
        parts = line.split(":")
        ssid = parts[0].strip()
        if ssid in seen or ssid == "": continue
        seen.add(ssid)
        nets.append({
            "ssid": ssid,
            "signal": int(parts[1]) if len(parts) > 1 else 0,
            "security": parts[2] if len(parts) > 2 else "",
            "in_use": parts[3] == "*" if len(parts) > 3 else False
        })
    return sorted(nets, key=lambda x: x["signal"], reverse=True)

@app.post("/api/connect")
async def connect(network: WifiNetwork):
    ssid = network.ssid
    password = network.password or ""

    # Delete existing connection if exists
    run_command(f"nmcli connection delete '{ssid}'")

    security_flag = ""
    if network.security and "WPA" in network.security.upper():
        security_flag = "wpa-psk"
    elif "WEP" in network.security.upper():
        security_flag = "wep"
    else:
        security_flag = "none"

    cmd = f"nmcli dev wifi connect '{ssid}' password '{password}'"
    if security_flag == "none":
        cmd = f"nmcli dev wifi connect '{ssid}'"

    code, output = run_command(cmd)
    
    if code != 0:
        raise HTTPException(400, f"Connection failed: {output}")

    # Log connection
    ip = subprocess.run("ip route get 1.1.1.1 | awk '{print $7}'", shell=True, capture_output=True, text=True)
    ip_addr = ip.stdout.strip() if ip.returncode == 0 else None

    log = ConnectionLog(
        ssid=ssid,
        connected_at=datetime.utcnow().isoformat(),
        ip_address=ip_addr,
        signal=next((n["signal"] for n in await scan_networks() if n["ssid"] == ssid), None)
    )
    await history.insert_one(log.dict())

    # Save if password provided
    if password:
        await networks.update_one(
            {"ssid": ssid},
            {"$set": {"password": password, "security": network.security, "last_used": datetime.utcnow()}},
            upsert=True
        )

    return {"status": "connected", "ssid": ssid}

@app.get("/api/saved")
async def get_saved():
    saved = await networks.find().to_list(100)
    return [s async for s in saved]

@app.delete("/api/saved/{ssid}")
async def forget_network(ssid: str):
    run_command(f"nmcli connection delete '{ssid}'")
    await networks.delete_one({"ssid": ssid})
    return {"status": "forgotten"}

@app.get("/api/status")
async def get_status():
    code, output = run_command("nmcli connection show --active")
    if code != 0:
        return {"connected": False}
    
    active = None
    for line in output.splitlines()[1:]:
        parts = line.split()
        if len(parts) > 3 and parts[3] == "wifi":
            active = parts[0]
            break
    
    if not active:
        return {"connected": False}
    
    return {
        "connected": True,
        "ssid": active,
        "ip": subprocess.run("ip route get 1.1.1.1 | awk '{print $7}'", shell=True, capture_output=True, text=True).stdout.strip()
    }

@app.get("/api/history")
async def get_history():
    logs = await history.find().sort("connected_at", -1).limit(20).to_list(20)
    return logs