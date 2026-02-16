# 🌐 IoT Centralized Logging & Monitoring Dashboard

A comprehensive IoT monitoring solution that collects, processes, and visualizes data from multiple sensors and network devices in real-time. Built with Python, Flask, Dash, Elasticsearch, and Loki for centralized logging.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/your-username/iot-project)](https://github.com/your-username/iot-project/commits/main)

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [API Endpoints](#-api-endpoints)
- [Monitoring Stack](#-monitoring-stack)
- [Security](#-security)
- [Contributing](#-contributing)
- [License](#-license)

## 🚀 Features

### 🔧 Core Functionality
- **Real-time Dashboard**: Interactive web interface with live data visualization
- **Multi-Sensor Support**: Temperature, humidity, motion, and system health monitoring
- **Network Device Monitoring**: Track routers, switches, firewalls, hubs, and modems
- **Centralized Logging**: Aggregates logs from multiple virtual machines via Loki
- **Alert System**: Configurable thresholds with visual indicators
- **Search & Filter**: Real-time data filtering across all metrics
- **Authentication**: Secure user login with JWT tokens

### 📊 Visualization
- **KPI Cards**: Real-time key performance indicators
- **Interactive Charts**: Temperature/humidity trends, system health metrics, motion detection
- **Network Device Status**: Traffic, packet loss, and port utilization
- **Log Tables**: Recent alerts, security events, and application logs
- **Responsive Design**: Professional light theme with minimal padding

### 🛠️ Technical Features
- **Elasticsearch Integration**: Cloud-based data storage and querying
- **MQTT Support**: Lightweight messaging protocol for IoT devices
- **Logstash Pipeline**: Data processing and transformation
- **Loki Integration**: Centralized log aggregation
- **RESTful API**: Authentication and user management endpoints
- **Auto-refresh**: 5-second interval data updates

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   IoT Sensors   │───▶│   MQTT Broker   │───▶│   Logstash      │
│ (Temperature,   │    │  (Mosquitto)    │    │   Pipeline      │
│  Humidity, etc) │    └─────────────────┘    └─────────────────┘
└─────────────────┘                                     │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Network Devices │───▶│   Python        │───▶│  Elasticsearch  │
│ (Router,Switch, │    │  Simulators     │    │    Cloud        │
│   Firewall)     │    └─────────────────┘    └─────────────────┘
└─────────────────┘                                     │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Virtual       │───▶│   Promtail      │───▶│      Loki       │
│   Machines      │    │   Agents        │    │   (Logging)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Web User     │───▶│   Flask Auth    │───▶│   Dash          │
│    Interface    │    │   Server        │    │   Dashboard     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows 10/11, Linux, or macOS
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 10GB free space

### Required Services
- **MongoDB**: For user authentication (local or cloud)
- **Elasticsearch**: Cloud instance (Elastic Cloud recommended)
- **Loki**: For log aggregation (local deployment)
- **MQTT Broker**: Mosquitto or HiveMQ (optional)

### Python Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- `elasticsearch>=8.11.0`
- `paho-mqtt>=1.6.1`
- `pandas>=2.0.0`
- `dash>=2.14.0`
- `plotly>=5.17.0`
- `flask>=2.3.0`
- `pymongo>=4.5.0`
- `pyjwt>=2.8.0`
- And more (see [requirements.txt](requirements.txt))

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/iot-project.git
cd iot-project
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up MongoDB
- Install MongoDB locally or use MongoDB Atlas
- Note your connection string for configuration

### 5. Configure Services
Follow the [Configuration](#-configuration) section below

## ⚙️ Configuration

### 1. Cloud Configuration
Edit `config/cloud_config.json`:

```json
{
    "elasticsearch_url": "https://your-elasticsearch-cluster.es.region.gcp.elastic.cloud:443",
    "api_key": "your-api-key-here",
    "index_name": "iot-logs",
    "kibana_url": "https://your-kibana-url.kb.region.gcp.elastic-cloud.com:443"
}
```

### 2. Environment Variables
Set these environment variables (optional, defaults provided):

```bash
# Authentication
SECRET_KEY=your-secret-key-change-in-production
MONGO_URI=mongodb://localhost:27017/
DB_NAME=iot_project

# Elasticsearch
ELASTICSEARCH_URL=https://your-cluster.es.region.gcp.elastic.cloud:443
ELASTIC_API_KEY=your-api-key
```

### 3. Loki Configuration
Edit `config/promtail-config.yaml`:
- Replace `192.168.1.100` with your Loki server IP
- Update `host` labels for each VM

### 4. MQTT Configuration
Edit `config/mosquitto.conf` if using local broker

## ▶️ Usage

### Starting the System

#### Option 1: Start Everything (Recommended)
```bash
# Windows
scripts\run_all_with_network.bat

# Linux/macOS
./scripts/run_all_with_network.sh
```

This starts:
- Authentication server (Flask + Dash)
- All 7 sensor simulators
- Network device simulator

#### Option 2: Start Components Separately

1. **Start Authentication Server**
```bash
cd auth
python app.py
```

2. **Start Sensor Simulators**
```bash
# Individual simulators
python simulators/temperature_sensor_cloud.py
python simulators/humidity_sensor_cloud.py
python simulators/motion_sensor_cloud.py
python simulators/system_health_cloud.py
python simulators/security_logger_cloud.py
python simulators/application_logger_cloud.py
python simulators/network_devices_cloud.py

# Or use the batch script
scripts/run_all_with_network.bat
```

### Access the Dashboard

1. Open your browser
2. Navigate to: `http://localhost:5000/login`
3. Sign up for a new account or log in
4. Access dashboard at: `http://localhost:5000/dashboard/`

### Default Credentials
- **Login**: `http://localhost:5000/login`
- **Dashboard**: `http://localhost:5000/dashboard/`
- **API Docs**: `http://localhost:5000/api`

## 📁 Project Structure

```
IOTProject/
├── auth/                    # Authentication system
│   ├── app.py              # Flask authentication server
│   ├── config.py           # Auth configuration
│   ├── integrated_app.py   # Integrated Flask+Dash app
│   ├── templates/          # HTML templates
│   │   └── login.html      # Login page
│   └── logout.html         # Logout page
│
├── dashboard/               # Dashboard components
│   ├── dashboard_light_professional.py  # Main dashboard
│   ├── elasticsearch_client.py          # ES data client
│   ├── loki_client.py                   # Loki log client
│   ├── dashboard.html                   # Dashboard template
│   └── centralized-logging-dashboard.json  # Grafana dashboard
│
├── simulators/              # IoT sensor simulators
│   ├── temperature_sensor_cloud.py      # Temperature sensor
│   ├── humidity_sensor_cloud.py         # Humidity sensor
│   ├── motion_sensor_cloud.py           # Motion sensor
│   ├── system_health_cloud.py           # System metrics
│   ├── security_logger_cloud.py         # Security logs
│   ├── application_logger_cloud.py      # Application logs
│   └── network_devices_cloud.py         # Network devices
│
├── config/                  # Configuration files
│   ├── cloud_config.json                # Cloud service config
│   ├── mosquitto.conf                   # MQTT broker config
│   ├── logstash-mqtt.conf               # Logstash pipeline
│   ├── promtail-config.yaml             # Loki client config
│   ├── promtail-vm1-config.yaml         # VM-specific config
│   ├── loki-config.yaml                 # Loki server config
│   ├── grafana-datasource.yaml          # Grafana config
│   └── elastalert_rules/                # Alert rules
│       ├── critical_system_health.yaml
│       ├── failed_login_alert.yaml
│       ├── high_temperature_alert.yaml
│       └── sensor_offline_alert.yaml
│
├── scripts/                 # Utility scripts
│   ├── run_all_with_network.bat         # Start all simulators
│   ├── start_light_dashboard.bat        # Start dashboard only
│   ├── generate_vm_logs.sh              # Generate VM logs
│   ├── iot_sensor_logs.sh               # Sensor log generator
│   └── simple_log_generator.sh          # Simple log tool
│
├── requirements.txt         # Python dependencies
├── test_auth.py            # Authentication tests
└── README.md               # This file
```

## 🔌 API Endpoints

### Authentication API
```
POST /api/signup          # Create new user
POST /api/login           # User login
GET  /api/profile         # Get user profile
PUT  /api/profile         # Update profile
GET  /api/users           # List all users
GET  /api/health          # Health check
```

### Dashboard Routes
```
GET  /login               # Login page
GET  /dashboard/          # Main dashboard
GET  /logout              # Logout
GET  /api                 # API documentation
```

### Example API Usage

**Signup:**
```bash
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com","password":"password123"}'
```

**Login:**
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"password123"}'
```

## 📊 Monitoring Stack

### Data Flow
1. **IoT Sensors** → Send data via MQTT
2. **Logstash** → Processes and enriches data
3. **Elasticsearch** → Stores structured data
4. **Loki** → Aggregates system logs
5. **Dashboard** → Visualizes all data in real-time

### Services Overview

| Service | Purpose | Port | Status |
|---------|---------|------|--------|
| Flask Auth | User authentication | 5000 | ✅ Running |
| Dash Dashboard | Data visualization | 5000 | ✅ Running |
| MongoDB | User database | 27017 | ✅ Required |
| Elasticsearch | Log storage | 443 (Cloud) | ✅ Required |
| Loki | Log aggregation | 3100 | ✅ Required |
| MQTT Broker | IoT messaging | 1883 | ⚠️ Optional |
| Promtail | Log shipping | 9080 | ⚠️ Optional |

### Alert Thresholds
```python
ALERT_RULES = {
    'temperature': {'high': 35°C, 'critical': 45°C, 'low': 18°C},
    'humidity': {'high': 70%, 'critical': 85%, 'low': 30%},
    'cpu': {'warning': 60%, 'critical': 90%},
    'memory': {'warning': 60%, 'critical': 85%},
    'disk': {'warning': 80%, 'critical': 95%},
    'packet_loss': {'warning': 2%, 'critical': 5%}
}
```

## 🔒 Security

### Authentication
- **JWT Tokens**: Secure session management
- **Password Hashing**: PBKDF2 with SHA256
- **HTTP-only Cookies**: Prevent XSS attacks
- **MongoDB Indexing**: Unique email constraint

### Data Protection
- **API Keys**: Secure Elasticsearch access
- **HTTPS**: Encrypted communication (production)
- **Input Validation**: Sanitized user inputs
- **Rate Limiting**: Prevent abuse (planned)

### Best Practices
1. Change `SECRET_KEY` in production
2. Use HTTPS for all communications
3. Rotate API keys regularly
4. Enable MongoDB authentication
5. Use strong passwords (min 6 characters)
6. Monitor login attempts

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Commit with clear messages: `git commit -m "Add feature"`
5. Push to branch: `git push origin feature-name`
6. Create Pull Request

### Code Standards
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings to functions
- Write unit tests for new features
- Keep functions small and focused

### Testing
```bash
# Run authentication tests
python test_auth.py

# Test individual components
python -m pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Common Issues

**MongoDB Connection Failed:**
- Ensure MongoDB is running
- Check connection string in environment variables
- Verify network connectivity

**Elasticsearch Connection Failed:**
- Check API key and URL in `cloud_config.json`
- Verify internet connectivity
- Confirm Elasticsearch cluster is active

**Dashboard Not Loading:**
- Check if Flask server is running on port 5000
- Verify all dependencies are installed
- Check browser console for errors

### Getting Help
- Open an issue on GitHub
- Check existing issues and discussions
- Contact the development team

## 📈 Future Enhancements

- [ ] Real IoT device integration
- [ ] Mobile-responsive dashboard
- [ ] Email/SMS alert notifications
- [ ] Historical data analytics
- [ ] Machine learning anomaly detection
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] Grafana integration
- [ ] Prometheus metrics
- [ ] Backup and recovery system

---

