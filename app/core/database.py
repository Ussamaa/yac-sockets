"""
MongoDB connection management
Async MongoDB connection for previous close prices
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings


# Global MongoDB client
mongo_client = None
database = None


async def connect_to_mongo():
    """Connect to MongoDB on startup"""
    global mongo_client, database
    mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = mongo_client[settings.MONGODB_DB_NAME]
    
    # Test connection
    try:
        await database.command('ping')
        print(f"✅ Connected to MongoDB: {settings.MONGODB_DB_NAME}")
        
        # Create indexes for daily_closes collection
        await _create_indexes()
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        raise


async def _create_indexes():
    """Create database indexes for optimal performance"""
    global database
    if database is None:
        return
    
    try:
        # Create compound unique index on symbol + date for daily_closes
        await database.daily_closes.create_index(
            [("symbol", 1), ("date", 1)], 
            unique=True
        )
        
        # Create index on date for cleanup queries
        await database.daily_closes.create_index("date")
        
        print("✅ Database indexes created")
    except Exception as e:
        print(f"⚠️ Error creating indexes: {e}")


async def close_mongo_connection():
    """Close MongoDB connection on shutdown"""
    global mongo_client
    if mongo_client:
        mongo_client.close()
        print("❌ MongoDB connection closed")


def get_database():
    """Get database instance"""
    return database
