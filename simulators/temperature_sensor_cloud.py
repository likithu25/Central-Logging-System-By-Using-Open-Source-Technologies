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
print("Temperature Sensor Simulator - Elastic Cloud")
print("=" * 60)
print()

# Verify connection
try:
    info = es.info()
    print(f"✓ Connected to: {info['cluster_name']}")
    print(f"✓ Version: {info['version']['number']}")
    print(f"✓ Index: {config['index_name']}")
    print()
    print("Generating temperature data... (Press Ctrl+C to stop)")
    print()
except Exception as e:
    print(f"✗ Connection failed: {e}")
    exit(1)

# Simulate temperature sensor
temperature = 25.0
count = 0

try:
    while True:
        count += 1
        
        # Simulate realistic temperature changes
        change = random.uniform(-0.5, 0.5)
        temperature += change
        temperature = max(15.0, min(50.0, temperature))
        
        # Occasionally generate anomalies
        if random.random() < 0.05:  # 5% chance
            temperature += random.uniform(5, 10)
            anomaly = True
        else:
            anomaly = False
        
        # Create document
        doc = {
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "sensor_type": "temperature",
            "sensor_id": "TEMP_001",
            "location": "Server Room A",
            "value": round(temperature, 2),
            "unit": "celsius",
            "status": "anomaly" if anomaly else "normal",
            "message": f"Temperature reading: {temperature:.2f}°C"
        }
        
        # Send to Elasticsearch
        result = es.index(index=config['index_name'], document=doc)
        
        print(f"[{count}] Temperature: {temperature:.2f}°C | Status: {doc['status']} | ID: {result['_id']}")
        
        # Wait 5 seconds
        time.sleep(5)
        
except KeyboardInterrupt:
    print()
    print("=" * 60)
    print(f"Stopped. Sent {count} temperature readings.")
    print("=" * 60)
except Exception as e:
    print(f"✗ Error: {e}")
