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
print("Application Logger - Elastic Cloud")
print("=" * 60)
print()

# Verify connection
try:
    info = es.info()
    print(f"✓ Connected to: {info['cluster_name']}")
    print(f"✓ Index: {config['index_name']}")
    print()
    print("Generating application logs... (Press Ctrl+C to stop)")
    print()
except Exception as e:
    print(f"✗ Connection failed: {e}")
    exit(1)

# Application log events
log_events = [
    {"level": "DEBUG", "weight": 15},
    {"level": "INFO", "weight": 50},
    {"level": "WARNING", "weight": 20},
    {"level": "ERROR", "weight": 12},
    {"level": "CRITICAL", "weight": 3}
]

applications = ["WebAPI", "DatabaseService", "AuthService", "FileProcessor", "EmailService"]
modules = ["UserController", "DataAccess", "Authentication", "FileHandler", "Scheduler", "CacheManager"]

# Sample log messages by level
messages_by_level = {
    "DEBUG": [
        "Processing request from client",
        "Cache hit for key: user_session",
        "Database query executed in 45ms",
        "API endpoint called: /api/users",
        "Session validated successfully"
    ],
    "INFO": [
        "Application started successfully",
        "User session created",
        "Data sync completed",
        "Backup process finished",
        "Configuration reloaded",
        "Scheduled task executed",
        "API request processed successfully"
    ],
    "WARNING": [
        "High memory usage detected: 75%",
        "API rate limit approaching threshold",
        "Database connection pool running low",
        "Slow query detected: 2.5s",
        "Cache miss rate increased to 15%",
        "Retry attempt 2 of 3"
    ],
    "ERROR": [
        "Database connection timeout",
        "Failed to process file: invalid format",
        "API call failed: external service unavailable",
        "Email delivery failed: SMTP error",
        "File not found: /data/export.csv",
        "Authentication token expired",
        "JSON parsing error in request body"
    ],
    "CRITICAL": [
        "Database connection pool exhausted",
        "Out of memory exception",
        "Unhandled exception in main thread",
        "Disk space critically low: 95% used",
        "Application crash detected",
        "Data corruption detected"
    ]
}

count = 0

try:
    while True:
        count += 1
        
        # Choose log level based on weights
        log_event = random.choices(
            log_events,
            weights=[e['weight'] for e in log_events]
        )[0]
        
        level = log_event['level']
        
        # Generate event details
        app = random.choice(applications)
        module = random.choice(modules)
        message = random.choice(messages_by_level[level])
        
        # Add some context based on level
        if level in ['ERROR', 'CRITICAL']:
            error_codes = ["ERR_001", "ERR_002", "ERR_DB_001", "ERR_AUTH_005", "ERR_FILE_003"]
            error_code = random.choice(error_codes)
            status = "failed"
        else:
            error_code = None
            status = "success" if level in ['DEBUG', 'INFO'] else "warning"
        
        # Create document
        doc = {
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "log_type": "application",
            "log_level": level,
            "application": app,
            "module": module,
            "message": message,
            "status": status,
            "response_time_ms": random.randint(10, 500) if level in ['DEBUG', 'INFO'] else random.randint(500, 3000)
        }
        
        if error_code:
            doc["error_code"] = error_code
        
        # Send to Elasticsearch
        result_es = es.index(index=config['index_name'], document=doc)
        
        # Print with formatting
        if level == 'DEBUG':
            icon = "🔍"
        elif level == 'INFO':
            icon = "ℹ"
        elif level == 'WARNING':
            icon = "⚠"
        elif level == 'ERROR':
            icon = "✗"
        else:
            icon = "🚨"
        
        print(f"[{count}] {icon} [{level}] [{app}] {message[:50]}... | ID: {result_es['_id']}")
        
        # Wait random time (2-6 seconds)
        time.sleep(random.uniform(2, 6))
        
except KeyboardInterrupt:
    print()
    print("=" * 60)
    print(f"Stopped. Sent {count} application log entries.")
    print("=" * 60)
except Exception as e:
    print(f"✗ Error: {e}")
