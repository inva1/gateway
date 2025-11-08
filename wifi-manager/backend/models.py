from pydantic import BaseModel
from typing import Optional

class WifiNetwork(BaseModel):
    ssid: str
    password: Optional[str] = None
    security: Optional[str] = "wpa"  # wpa, wep, none
    is_saved: bool = False

class ConnectionLog(BaseModel):
    ssid: str
    connected_at: str
    ip_address: Optional[str] = None
    signal: Optional[int] = None