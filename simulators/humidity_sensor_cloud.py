import json
import time
import random
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
print("Humidity Sensor Simulator - Elastic Cloud")
print("=" * 60)
print()

# Verify connection
try:
    info = es.info()
    print(f"✓ Connected to: {info['cluster_name']}")
    print(f"✓ Index: {config['index_name']}")
    print()
    print("Generating humidity data... (Press Ctrl+C to stop)")
    print()
except Exception as e:
    print(f"✗ Connection failed: {e}")
    exit(1)

# Simulate humidity sensor
humidity = 60.0
count = 0

try:
    while True:
        count += 1
        
        # Simulate realistic humidity changes
        change = random.uniform(-2.0, 2.0)
        humidity += change
        humidity = max(20.0, min(95.0, humidity))
        
        # Determine status
        if humidity > 80:
            status = "high"
        elif humidity < 30:
            status = "low"
        else:
            status = "normal"
        
        # Create document
        doc = {
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "sensor_type": "humidity",
            "sensor_id": "HUM_001",
            "location": "Server Room A",
            "value": round(humidity, 2),
            "unit": "percent",
            "status": status,
            "message": f"Humidity reading: {humidity:.2f}%"
        }
        
        # Send to Elasticsearch
        result = es.index(index=config['index_name'], document=doc)
        
        print(f"[{count}] Humidity: {humidity:.2f}% | Status: {status} | ID: {result['_id']}")
        
        # Wait 5 seconds
        time.sleep(5)
        
except KeyboardInterrupt:
    print()
    print("=" * 60)
    print(f"Stopped. Sent {count} humidity readings.")
    print("=" * 60)
except Exception as e:
    print(f"✗ Error: {e}")
