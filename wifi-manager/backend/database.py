from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.wifi_manager
networks = db.networks
history = db.history