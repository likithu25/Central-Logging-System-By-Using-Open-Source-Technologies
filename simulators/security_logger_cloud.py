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
print("Security Events Logger - Elastic Cloud")
print("=" * 60)
print()

# Verify connection
try:
    info = es.info()
    print(f"✓ Connected to: {info['cluster_name']}")
    print(f"✓ Index: {config['index_name']}")
    print()
    print("Generating security logs... (Press Ctrl+C to stop)")
    print()
except Exception as e:
    print(f"✗ Connection failed: {e}")
    exit(1)

# Security event types
security_events = [
    {"type": "login_success", "severity": "INFO", "weight": 60},
    {"type": "login_failed", "severity": "WARNING", "weight": 25},
    {"type": "unauthorized_access", "severity": "ERROR", "weight": 10},
    {"type": "suspicious_activity", "severity": "CRITICAL", "weight": 5}
]

usernames = ["admin", "user01", "john_doe", "alice", "bob", "system", "guest", "root"]
ip_addresses = [
    "192.168.1.100", "192.168.1.101", "192.168.1.102", 
    "10.0.0.50", "10.0.0.51", "203.0.113.10",
    "198.51.100.25", "172.16.0.100"
]

locations = ["Server Room A", "Office Building", "Data Center", "Remote VPN", "Local Network"]

count = 0

try:
    while True:
        count += 1
        
        # Choose event type based on weights
        event = random.choices(
            security_events,
            weights=[e['weight'] for e in security_events]
        )[0]
        
        # Generate event details
        username = random.choice(usernames)
        source_ip = random.choice(ip_addresses)
        location = random.choice(locations)
        
        # Create log message based on event type
        if event['type'] == 'login_success':
            message = f"User '{username}' logged in successfully from {source_ip}"
            action = "login"
            result = "success"
        elif event['type'] == 'login_failed':
            message = f"Failed login attempt for user '{username}' from {source_ip}"
            action = "login"
            result = "failed"
        elif event['type'] == 'unauthorized_access':
            resource = random.choice(["/admin/users", "/secure/data", "/config/system", "/api/private"])
            message = f"Unauthorized access attempt to '{resource}' by user '{username}' from {source_ip}"
            action = "access"
            result = "denied"
        else:  # suspicious_activity
            message = f"Suspicious activity detected: Multiple failed attempts from {source_ip}"
            action = "security_alert"
            result = "blocked"
        
        # Create document
        doc = {
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "log_type": "security",
            "event_type": event['type'],
            "severity": event['severity'],
            "username": username,
            "source_ip": source_ip,
            "location": location,
            "action": action,
            "result": result,
            "message": message,
            "log_level": event['severity']
        }
        
        # Send to Elasticsearch
        result_es = es.index(index=config['index_name'], document=doc)
        
        # Print with color coding
        if event['severity'] == 'INFO':
            icon = "✓"
        elif event['severity'] == 'WARNING':
            icon = "⚠"
        elif event['severity'] == 'ERROR':
            icon = "✗"
        else:
            icon = "🚨"
        
        print(f"[{count}] {icon} [{event['severity']}] {message[:60]}... | ID: {result_es['_id']}")
        
        # Wait random time (3-8 seconds)
        time.sleep(random.uniform(3, 8))
        
except KeyboardInterrupt:
    print()
    print("=" * 60)
    print(f"Stopped. Sent {count} security log entries.")
    print("=" * 60)
except Exception as e:
    print(f"✗ Error: {e}")
