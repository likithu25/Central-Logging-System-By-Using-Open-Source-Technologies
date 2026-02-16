import json
import time
import psutil
import os
from datetime import datetime, timezone
from elasticsearch import Elasticsearch

# Load configuration (handle both direct run and script run)
config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'cloud_config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

# Connect to Elasticsearch
es = Elasticsearch(
    config['elasticsearch_url'],
    api_key=config['api_key'],
    verify_certs=True,
    request_timeout=30
)

print("=" * 60)
print("System Health Monitor - Elastic Cloud")
print("=" * 60)
print()

# Verify connection
try:
    info = es.info()
    print(f"✓ Connected to: {info['cluster_name']}")
    print(f"✓ Index: {config['index_name']}")
    print()
    print("Monitoring system health... (Press Ctrl+C to stop)")
    print()
except Exception as e:
    print(f"✗ Connection failed: {e}")
    exit(1)

count = 0

try:
    while True:
        count += 1
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Determine status
        if cpu_percent > 80 or memory.percent > 80:
            status = "critical"
        elif cpu_percent > 60 or memory.percent > 60:
            status = "warning"
        else:
            status = "healthy"
        
        # Create document
        doc = {
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "sensor_type": "system_health",
            "sensor_id": "SYS_001",
            "location": "Local System",
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory.percent, 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "disk_percent": round(disk.percent, 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "status": status,
            "message": f"System Health: CPU {cpu_percent}%, Memory {memory.percent}%"
        }
        
        # Send to Elasticsearch
        result = es.index(index=config['index_name'], document=doc)
        
        print(f"[{count}] CPU: {cpu_percent}% | Memory: {memory.percent}% | Status: {status}")
        
        # Wait 10 seconds
        time.sleep(10)
        
except KeyboardInterrupt:
    print()
    print("=" * 60)
    print(f"Stopped. Sent {count} health reports.")
    print("=" * 60)
except Exception as e:
    print(f"✗ Error: {e}")
