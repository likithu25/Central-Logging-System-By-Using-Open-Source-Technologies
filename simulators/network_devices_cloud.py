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
print("Network Devices Simulator - Elastic Cloud")
print("=" * 60)
print()

# Verify connection
try:
    info = es.info()
    print(f"✓ Connected to: {info['cluster_name']}")
    print(f"✓ Index: {config['index_name']}")
    print()
    print("Simulating network devices... (Press Ctrl+C to stop)")
    print()
except Exception as e:
    print(f"✗ Connection failed: {e}")
    exit(1)

# Network device configurations
DEVICES = {
    'router': {
        'id': 'RTR_001',
        'name': 'Core Router',
        'location': 'Server Room',
        'ports': 24
    },
    'switch': {
        'id': 'SWH_001',
        'name': 'Access Switch',
        'location': 'Office Floor 1',
        'ports': 48
    },
    'firewall': {
        'id': 'FWL_001',
        'name': 'Edge Firewall',
        'location': 'DMZ',
        'ports': 8
    },
    'hub': {
        'id': 'HUB_001',
        'name': 'Network Hub',
        'location': 'Conference Room',
        'ports': 16
    },
    'modem': {
        'id': 'MDM_001',
        'name': 'ISP Modem',
        'location': 'Network Closet',
        'ports': 4
    }
}

def generate_network_data(device_type, device_config):
    """Generate realistic network device metrics"""
    
    # Traffic metrics (Mbps)
    if device_type == 'router':
        traffic_in = round(random.uniform(50, 500), 2)
        traffic_out = round(random.uniform(30, 300), 2)
        packet_loss = round(random.uniform(0, 2), 2)
    elif device_type == 'switch':
        traffic_in = round(random.uniform(100, 800), 2)
        traffic_out = round(random.uniform(80, 700), 2)
        packet_loss = round(random.uniform(0, 0.5), 2)
    elif device_type == 'firewall':
        traffic_in = round(random.uniform(200, 1000), 2)
        traffic_out = round(random.uniform(150, 800), 2)
        packet_loss = round(random.uniform(0, 1), 2)
    elif device_type == 'hub':
        traffic_in = round(random.uniform(10, 100), 2)
        traffic_out = round(random.uniform(10, 100), 2)
        packet_loss = round(random.uniform(1, 5), 2)
    else:  # modem
        traffic_in = round(random.uniform(20, 200), 2)
        traffic_out = round(random.uniform(10, 100), 2)
        packet_loss = round(random.uniform(0, 3), 2)
    
    # Port utilization
    active_ports = random.randint(1, device_config['ports'])
    port_utilization = round((active_ports / device_config['ports']) * 100, 2)
    
    # Connection metrics
    active_connections = random.randint(10, 500)
    dropped_packets = random.randint(0, 100)
    error_rate = round(random.uniform(0, 0.5), 2)
    
    # Determine status
    if packet_loss > 3 or error_rate > 0.3:
        status = "critical"
    elif packet_loss > 1 or error_rate > 0.1:
        status = "warning"
    else:
        status = "healthy"
    
    # Firewall-specific metrics
    blocked_threats = 0
    allowed_connections = 0
    if device_type == 'firewall':
        blocked_threats = random.randint(0, 50)
        allowed_connections = random.randint(100, 1000)
        if blocked_threats > 30:
            status = "warning"
    
    return {
        "@timestamp": datetime.now(timezone.utc).isoformat(),
        "sensor_type": "network_device",
        "device_type": device_type,
        "sensor_id": device_config['id'],
        "device_name": device_config['name'],
        "location": device_config['location'],
        "traffic_in_mbps": traffic_in,
        "traffic_out_mbps": traffic_out,
        "packet_loss_percent": packet_loss,
        "active_ports": active_ports,
        "total_ports": device_config['ports'],
        "port_utilization_percent": port_utilization,
        "active_connections": active_connections,
        "dropped_packets": dropped_packets,
        "error_rate_percent": error_rate,
        "blocked_threats": blocked_threats if device_type == 'firewall' else None,
        "allowed_connections": allowed_connections if device_type == 'firewall' else None,
        "status": status,
        "message": f"{device_config['name']} - Traffic In: {traffic_in} Mbps, Packet Loss: {packet_loss}%"
    }

count = 0

try:
    while True:
        count += 1
        
        # Generate data for all network devices
        for device_type, device_config in DEVICES.items():
            doc = generate_network_data(device_type, device_config)
            
            # Send to Elasticsearch
            result = es.index(index=config['index_name'], document=doc)
            
            print(f"[{count}] {device_config['name']} | "
                  f"Traffic: ↓{doc['traffic_in_mbps']} ↑{doc['traffic_out_mbps']} Mbps | "
                  f"Loss: {doc['packet_loss_percent']}% | "
                  f"Status: {doc['status']}")
        
        print()
        # Wait 8 seconds
        time.sleep(8)
        
except KeyboardInterrupt:
    print()
    print("=" * 60)
    print(f"Stopped. Sent {count * len(DEVICES)} network device reports.")
    print("=" * 60)
except Exception as e:
    print(f"✗ Error: {e}")
