import asyncio
import logging
from app.services.sync_services.sync_manager import SyncManager
from app.core.database import get_db

# 配置日志
logging.basicConfig(level=logging.INFO)

async def test_statistics():
    manager = SyncManager()
    
    print("Testing get_service_list...")
    services = manager.get_service_list()
    for s in services:
        print(f"Service: {s['key']}, Implemented: {s['implemented']}")
    
    services_to_test = ['limit_prices', 'audit_opinions', 'financial_indicators', 'industry_classification']
    
    for service_key in services_to_test:
        print(f"\nTesting {service_key}...")
        stats = await manager.get_data_statistics(service_key)
        print(f"Result: {stats}")

if __name__ == "__main__":
    asyncio.run(test_statistics())
