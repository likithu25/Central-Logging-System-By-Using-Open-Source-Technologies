"""
Integrated Flask + Dash Application
Single server on port 5000 with authentication and dashboard
"""
from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson import ObjectId
import jwt
import datetime
import os
from functools import wraps

# Import the Dash app
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'dashboard'))

# Create Flask server first
server = Flask(__name__)
CORS(server)

# Configuration
server.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
server.config['MONGO_URI'] = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')

# MongoDB setup
mongo_client = MongoClient(server.config['MONGO_URI'])
db = mongo_client['iot_project']
users_collection = db['users']

# Create unique index on email
users_collection.create_index('email', unique=True)

print("=" * 60)
print("🔐 Integrated IoT Application Server")
print("=" * 60)
print(f"MongoDB: {server.config['MONGO_URI']}")
print(f"Database: {db.name}")
print()

# Token decorator - supports both header and cookie tokens
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Try to get token from Authorization header first
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
            else:
                try:
                    token = auth_header.split(" ")[1]
                except IndexError:
                    pass
        
        # If no header token, try cookie
        if not token:
            token = request.cookies.get('token')
        
        if not token:
            return jsonify({'message': 'Token is missing!', 'success': False}), 401
        
        try:
            # Decode token
            data = jwt.decode(token, server.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = users_collection.find_one({'_id': ObjectId(data['user_id'])})
            
            if not current_user:
                return jsonify({'message': 'User not found!', 'success': False}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!', 'success': False}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!', 'success': False}), 401
        except Exception as e:
            return jsonify({'message': f'Token error: {str(e)}', 'success': False}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# ==================== AUTHENTICATION ROUTES ====================

@server.route('/')
def home():
    """Redirect to login page"""
    return redirect('/login')

@server.route('/login')
def login_page():
    """Serve login page"""
    return send_from_directory('templates', 'login.html')

@server.route('/dashboard')
def dashboard_redirect():
    """Redirect /dashboard to /dashboard/ for Dash app with auth check"""
    # Check if user has valid token in cookie
    token = request.cookies.get('token')
    
    # Also check Authorization header
    if not token and 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        elif ' ' in auth_header:
            token = auth_header.split(' ')[1]
    
    if not token:
        return redirect('/login')
    
    try:
        # Verify token
        jwt.decode(token, server.config['SECRET_KEY'], algorithms=["HS256"])
        return redirect('/dashboard/')
    except jwt.ExpiredSignatureError:
        return redirect('/login')
    except jwt.InvalidTokenError:
        return redirect('/login')
    except Exception as e:
        print(f"Dashboard redirect error: {e}")
        return redirect('/login')

@server.before_request
def check_dashboard_auth():
    """Check authentication for dashboard routes - only allow access after login"""
    # Skip auth check for login, logout, API, and static files
    skip_paths = [
        '/', '/login', '/logout',
        '/api', '/_', '/assets', '/static',
        '/favicon.ico'
    ]
    
    # Check if path should be skipped
    should_skip = False
    for skip_path in skip_paths:
        if request.path.startswith(skip_path):
            should_skip = True
            break
    
    if should_skip:
        return None
    
    # Protect all dashboard routes (including /dashboard and /dashboard/)
    # But allow Dash internal routes (/_dash-*, /_reload, etc.)
    if request.path.startswith('/dashboard'):
        # Allow Dash internal routes without auth
        if request.path.startswith('/dashboard/_'):
            return None
        
        token = request.cookies.get('token')
        
        # Also check Authorization header as fallback
        if not token and 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
            elif ' ' in auth_header:
                token = auth_header.split(' ')[1]
        
        if not token:
            # No token found, redirect to login
            return redirect('/login')
        
        try:
            # Verify token is valid
            decoded = jwt.decode(token, server.config['SECRET_KEY'], algorithms=["HS256"])
            # Token is valid, allow access
            return None
        except jwt.ExpiredSignatureError:
            # Token expired, redirect to login
            return redirect('/login')
        except jwt.InvalidTokenError:
            # Invalid token, redirect to login
            return redirect('/login')
        except Exception as e:
            # Any other error, redirect to login
            print(f"Auth error for {request.path}: {e}")  # Debug print
            return redirect('/login')
    
    return None

@server.route('/logout')
def logout():
    """Logout page - clears tokens and redirects to login"""
    response = server.make_response('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Logging out...</title>
        <style>
            body {
                font-family: 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                color: white;
                text-align: center;
            }
            h1 { font-size: 48px; margin-bottom: 20px; }
            p { font-size: 20px; }
        </style>
    </head>
    <body>
        <div>
            <h1>👋 Logging out...</h1>
            <p>Redirecting to login page...</p>
        </div>
        <script>
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            document.cookie = 'token=; path=/; max-age=0';
            setTimeout(function() {
                window.location.href = '/login';
            }, 1500);
        </script>
    </body>
    </html>
    ''')
    response.set_cookie('token', '', expires=0)
    return response

@server.route('/api')
def api_home():
    """API home endpoint"""
    return jsonify({
        'message': 'IoT Authentication API',
        'version': '1.0',
        'endpoints': {
            'GET /': 'Login page',
            'GET /login': 'Login page',
            'GET /logout': 'Logout and clear tokens',
            'GET /dashboard': 'IoT Monitoring Dashboard',
            'POST /api/signup': 'Create new user account',
            'POST /api/login': 'Login and get token',
            'GET /api/profile': 'Get user profile (requires token)',
            'PUT /api/profile': 'Update user profile (requires token)',
            'GET /api/users': 'List all users (requires token)'
        }
    })

@server.route('/api/signup', methods=['POST'])
def signup():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'message': f'{field.capitalize()} is required!',
                    'success': False
                }), 400
        
        name = data.get('name').strip()
        email = data.get('email').strip().lower()
        password = data.get('password')
        
        # Validate email format
        if '@' not in email or '.' not in email:
            return jsonify({
                'message': 'Invalid email format!',
                'success': False
            }), 400
        
        # Validate password strength
        if len(password) < 6:
            return jsonify({
                'message': 'Password must be at least 6 characters long!',
                'success': False
            }), 400
        
        # Check if user already exists
        if users_collection.find_one({'email': email}):
            return jsonify({
                'message': 'User with this email already exists!',
                'success': False
            }), 409
        
        # Hash password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        # Create user document
        user = {
            'name': name,
            'email': email,
            'password': hashed_password,
            'created_at': datetime.datetime.utcnow(),
            'updated_at': datetime.datetime.utcnow()
        }
        
        # Insert into database
        result = users_collection.insert_one(user)
        
        # Generate token
        token = jwt.encode({
            'user_id': str(result.inserted_id),
            'email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, server.config['SECRET_KEY'], algorithm='HS256')
        
        # Create response with token in cookie
        response = jsonify({
            'message': 'User registered successfully!',
            'success': True,
            'user': {
                'id': str(result.inserted_id),
                'name': name,
                'email': email
            },
            'token': token
        })
        
        # Set token as cookie (accessible by both server and client)
        response.set_cookie('token', token, max_age=86400, httponly=False, secure=False, samesite='Lax', path='/')
        
        return response, 201
        
    except Exception as e:
        return jsonify({
            'message': f'Error during signup: {str(e)}',
            'success': False
        }), 500

@server.route('/api/login', methods=['POST'])
def login():
    """Login user and return token"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({
                'message': 'Email and password are required!',
                'success': False
            }), 400
        
        email = data.get('email').strip().lower()
        password = data.get('password')
        
        # Find user
        user = users_collection.find_one({'email': email})
        
        if not user:
            return jsonify({
                'message': 'Invalid email or password!',
                'success': False
            }), 401
        
        # Check password
        if not check_password_hash(user['password'], password):
            return jsonify({
                'message': 'Invalid email or password!',
                'success': False
            }), 401
        
        # Generate token
        token = jwt.encode({
            'user_id': str(user['_id']),
            'email': user['email'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, server.config['SECRET_KEY'], algorithm='HS256')
        
        # Create response with token in cookie
        response = jsonify({
            'message': 'Login successful!',
            'success': True,
            'user': {
                'id': str(user['_id']),
                'name': user['name'],
                'email': user['email']
            },
            'token': token
        })
        
        # Set token as cookie (accessible by both server and client)
        response.set_cookie('token', token, max_age=86400, httponly=False, secure=False, samesite='Lax', path='/')
        
        return response, 200
        
    except Exception as e:
        return jsonify({
            'message': f'Error during login: {str(e)}',
            'success': False
        }), 500

@server.route('/api/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """Get user profile"""
    try:
        return jsonify({
            'success': True,
            'user': {
                'id': str(current_user['_id']),
                'name': current_user['name'],
                'email': current_user['email'],
                'created_at': current_user.get('created_at'),
                'updated_at': current_user.get('updated_at')
            }
        }), 200
    except Exception as e:
        return jsonify({
            'message': f'Error fetching profile: {str(e)}',
            'success': False
        }), 500

@server.route('/api/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """Update user profile"""
    try:
        data = request.get_json()
        
        # Prepare update data
        update_data = {}
        
        if data.get('name'):
            update_data['name'] = data.get('name').strip()
        
        if data.get('password'):
            if len(data.get('password')) < 6:
                return jsonify({
                    'message': 'Password must be at least 6 characters long!',
                    'success': False
                }), 400
            update_data['password'] = generate_password_hash(data.get('password'), method='pbkdf2:sha256')
        
        if not update_data:
            return jsonify({
                'message': 'No update data provided!',
                'success': False
            }), 400
        
        update_data['updated_at'] = datetime.datetime.utcnow()
        
        # Update user
        users_collection.update_one(
            {'_id': current_user['_id']},
            {'$set': update_data}
        )
        
        # Get updated user
        updated_user = users_collection.find_one({'_id': current_user['_id']})
        
        return jsonify({
            'message': 'Profile updated successfully!',
            'success': True,
            'user': {
                'id': str(updated_user['_id']),
                'name': updated_user['name'],
                'email': updated_user['email']
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'message': f'Error updating profile: {str(e)}',
            'success': False
        }), 500

@server.route('/api/users', methods=['GET'])
@token_required
def get_users(current_user):
    """Get all users (requires authentication)"""
    try:
        users = users_collection.find({}, {'password': 0})  # Exclude password field
        
        users_list = []
        for user in users:
            users_list.append({
                'id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'created_at': user.get('created_at')
            })
        
        return jsonify({
            'success': True,
            'count': len(users_list),
            'users': users_list
        }), 200
        
    except Exception as e:
        return jsonify({
            'message': f'Error fetching users: {str(e)}',
            'success': False
        }), 500

@server.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check MongoDB connection
        mongo_client.admin.command('ping')
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 503

# ==================== DASH INTEGRATION ====================

# Import Dash app components after Flask is created
import json
import time
from datetime import datetime, timedelta, timezone
from elasticsearch import Elasticsearch
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd

# Load Elasticsearch configuration
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

# ALERT THRESHOLDS
ALERT_RULES = {
    'temperature': {'high': 35, 'critical': 45, 'low': 18},
    'humidity': {'high': 70, 'critical': 85, 'low': 30},
    'cpu': {'warning': 60, 'critical': 90},
    'memory': {'warning': 60, 'critical': 85},
    'disk': {'warning': 80, 'critical': 95},
    'packet_loss': {'warning': 2, 'critical': 5}
}

# Verify Elasticsearch connection
try:
    info = es.info()
    print(f"✓ Elasticsearch: {info['cluster_name']}")
    print(f"✓ Index: {config['index_name']}")
    print()
except Exception as e:
    print(f"✗ Elasticsearch connection failed: {e}")

# Create Dash app with Flask server
app = dash.Dash(__name__, server=server, url_base_pathname='/dashboard/', suppress_callback_exceptions=True)

# Import the rest of the dashboard code
dashboard_path = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'dashboard_light_professional.py')
with open(dashboard_path, 'r', encoding='utf-8') as f:
    dashboard_code = f.read().split('if __name__')[0]
exec(dashboard_code)

if __name__ == '__main__':
    print("🚀 Starting Integrated Server on http://localhost:5000")
    print("   - Login: http://localhost:5000/login")
    print("   - Dashboard: http://localhost:5000/dashboard/")
    print("   - API: http://localhost:5000/api")
    print()
    server.run(debug=True, host='0.0.0.0', port=5000)
