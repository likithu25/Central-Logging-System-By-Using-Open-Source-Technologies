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
print("Motion Sensor Simulator - Elastic Cloud")
print("=" * 60)
print()

# Verify connection
try:
    info = es.info()
    print(f"✓ Connected to: {info['cluster_name']}")
    print(f"✓ Index: {config['index_name']}")
    print()
    print("Generating motion events... (Press Ctrl+C to stop)")
    print()
except Exception as e:
    print(f"✗ Connection failed: {e}")
    exit(1)

count = 0

try:
    while True:
        count += 1
        
        # Simulate motion detection (20% chance)
        motion_detected = random.random() < 0.2
        
        if motion_detected:
            # Create document
            doc = {
                "@timestamp": datetime.now(timezone.utc).isoformat(),
                "sensor_type": "motion",
                "sensor_id": "MOT_001",
                "location": "Entrance Hallway",
                "motion_detected": True,
                "confidence": round(random.uniform(0.7, 1.0), 2),
                "status": "motion",
                "message": "Motion detected in entrance hallway"
            }
            
            # Send to Elasticsearch
            result = es.index(index=config['index_name'], document=doc)
            
            print(f"[{count}] 🚶 MOTION DETECTED | Confidence: {doc['confidence']} | ID: {result['_id']}")
        else:
            print(f"[{count}] ✓ No motion detected")
        
        # Wait 3 seconds
        time.sleep(3)
        
except KeyboardInterrupt:
    print()
    print("=" * 60)
    print(f"Stopped. Sent {count} motion sensor readings.")
    print("=" * 60)
except Exception as e:
    print(f"✗ Error: {e}")
