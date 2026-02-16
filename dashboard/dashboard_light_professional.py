import json
import time
from datetime import datetime, timedelta, timezone
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import os
import sys

# Import clients
sys.path.insert(0, os.path.dirname(__file__))
from loki_client import LokiClient
from elasticsearch_client import ElasticsearchClient

# Initialize Elasticsearch client
try:
    es_client = ElasticsearchClient()
    success, message = es_client.test_connection()
    if success:
        print(f"✓ {message}")
        print(f"✓ Index: {es_client.index_name}")
    else:
        print(f"✗ {message}")
        es_client = None
except Exception as e:
    print(f"✗ Elasticsearch client initialization failed: {e}")
    es_client = None

# Initialize Loki client
try:
    loki_client = LokiClient(loki_url="http://localhost:3100")
    print("✓ Connected to Loki at http://localhost:3100")
except Exception as e:
    print(f"✗ Loki connection failed: {e}")
    loki_client = None

# ALERT THRESHOLDS
ALERT_RULES = {
    'temperature': {'high': 35, 'critical': 45, 'low': 18},
    'humidity': {'high': 70, 'critical': 85, 'low': 30},
    'cpu': {'warning': 60, 'critical': 90},
    'memory': {'warning': 60, 'critical': 85},
    'disk': {'warning': 80, 'critical': 95},
    'packet_loss': {'warning': 2, 'critical': 5}
}

print("=" * 60)
print("🎨 Professional Light Theme IoT Dashboard")
print("=" * 60)
print()

# Verify connections
if es_client is None:
    print("✗ Elasticsearch connection failed. Dashboard may not function properly.")
    print()
else:
    print()

# Initialize Dash app
app = dash.Dash(__name__, 
                requests_pathname_prefix='/dashboard/',
                suppress_callback_exceptions=True)
app.title = "IoT & Network Monitoring Dashboard"

# Function to integrate with Flask server  
def init_app(flask_app):
    """Initialize Dash app with Flask server by mounting Dash WSGI app"""
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    
    # Mount the Dash app at /dashboard/ path
    flask_app.wsgi_app = DispatcherMiddleware(flask_app.wsgi_app, {
        '/dashboard': app.server
    })
    
    return app

# PROFESSIONAL LIGHT THEME COLORS
COLORS = {
    'background': '#f8f9fa',      # Light gray background
    'card': '#ffffff',            # White cards
    'text': '#2c3e50',           # Dark blue-gray text
    'primary': '#3498db',        # Professional blue
    'accent': '#e74c3c',         # Red accent
    'success': '#27ae60',        # Green
    'warning': '#f39c12',        # Orange
    'danger': '#e74c3c',         # Red
    'info': '#3498db',           # Blue
    'border': '#dee2e6',         # Light border
    'shadow': 'rgba(0,0,0,0.08)' # Subtle shadow
}

# Dashboard layout with professional light theme and minimal padding
app.layout = html.Div([
    # Store for search filter
    dcc.Store(id='search-filter', data=''),
    
    # Location component for logout redirect
    dcc.Location(id='url', refresh=True),
    
    # Header Section (Minimal Padding)
    html.Div([
        html.Div([
            html.Div([
                html.H1("🌐 Centralized Logging Dashboard", 
                        style={
                            'textAlign': 'center', 
                            'color': COLORS['primary'], 
                            'margin': '0',
                            'padding': '15px 0 5px 0',
                            'fontSize': '32px',
                            'fontWeight': '600'
                        }),
                html.P("Real-time logs from all Virtual Machines via Loki", 
                      style={
                          'textAlign': 'center',
                          'color': COLORS['text'],
                          'margin': '0',
                          'fontSize': '14px',
                          'opacity': '0.8'
                      }),
                html.P("System Logs • Application Logs • Security Events",
                       style={
                           'textAlign': 'center', 
                           'color': COLORS['text'], 
                           'fontSize': '14px',
                           'margin': '0',
                           'padding': '0 0 15px 0',
                           'opacity': '0.8'
                       })
            ], style={'flex': '1'}),
            html.Div([
                html.A('🚪 Logout',
                    href='/logout',
                    target='_self',
                    style={
                        'padding': '10px 25px',
                        'backgroundColor': COLORS['danger'],
                        'color': 'white',
                        'border': 'none',
                        'borderRadius': '5px',
                        'cursor': 'pointer',
                        'fontSize': '14px',
                        'fontWeight': '600',
                        'boxShadow': '0 2px 5px rgba(0,0,0,0.2)',
                        'transition': 'all 0.3s',
                        'textDecoration': 'none',
                        'display': 'inline-block',
                        'position': 'absolute',
                        'top': '20px',
                        'right': '30px'
                    }
                )
            ])
        ], style={'position': 'relative', 'display': 'flex', 'alignItems': 'center'})
    ], style={
        'backgroundColor': COLORS['card'],
        'borderBottom': f'3px solid {COLORS["primary"]}',
        'marginBottom': '15px',
        'boxShadow': f'0 2px 4px {COLORS["shadow"]}'
    }),
    
    # Search Bar Section (Minimal Padding)
    html.Div([
        html.Div([
            html.Label("🔍 Search:", 
                      style={
                          'color': COLORS['text'], 
                          'fontSize': '14px', 
                          'marginRight': '10px', 
                          'fontWeight': '600'
                      }),
            dcc.Input(
                id='search-input',
                type='text',
                placeholder='Search: temperature, humidity, motion, router, firewall, location, app name... (filters all data & graphs)',
                style={
                    'width': '550px',
                    'padding': '8px 12px',
                    'fontSize': '13px',
                    'border': f'1px solid {COLORS["border"]}',
                    'borderRadius': '5px',
                    'marginRight': '10px',
                    'outline': 'none'
                }
            ),
            html.Button('Search', 
                       id='search-button',
                       n_clicks=0,
                       style={
                           'padding': '8px 20px',
                           'backgroundColor': COLORS['primary'],
                           'color': 'white',
                           'border': 'none',
                           'borderRadius': '5px',
                           'cursor': 'pointer',
                           'marginRight': '8px',
                           'fontSize': '13px',
                           'fontWeight': '500'
                       }),
            html.Button('Show All', 
                       id='reset-button',
                       n_clicks=0,
                       style={
                           'padding': '8px 20px',
                           'backgroundColor': COLORS['border'],
                           'color': COLORS['text'],
                           'border': 'none',
                           'borderRadius': '5px',
                           'cursor': 'pointer',
                           'fontSize': '13px',
                           'fontWeight': '500'
                       })
        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'})
    ], style={
        'padding': '12px',
        'backgroundColor': COLORS['card'],
        'borderRadius': '5px',
        'marginBottom': '15px',
        'boxShadow': f'0 1px 3px {COLORS["shadow"]}'
    }),
    
    # Search Status Indicator
    html.Div(id='search-status', style={'marginBottom': '10px'}),
    
    # Alert Banner (Minimal Padding)
    html.Div(id='alert-banner', style={
        'marginBottom': '15px'
    }),
    
    # Main Content Grid (Minimal Padding & Margin)
    html.Div([
        # Main Content - Metrics & Charts (Full Width)
        html.Div([
            # KPI Cards Row
            html.Div(id='kpi-cards', style={'marginBottom': '15px'}),
            
            # Charts Row - Temperature/Humidity and System Health side by side (with wrapper for conditional display)
            html.Div(id='charts-row-wrapper', children=[
                # Temperature & Humidity Chart
                html.Div(id='temp-humidity-wrapper', children=[
                    html.H3("🌡️ Temperature & Humidity Trends", 
                           style={
                               'color': COLORS['text'], 
                               'fontSize': '16px',
                               'margin': '0 0 10px 0',
                               'fontWeight': '600'
                           }),
                    dcc.Graph(id='temp-humidity-chart', 
                             config={'displayModeBar': False},
                             style={'height': '280px'})
                ], style={
                    'backgroundColor': COLORS['card'],
                    'padding': '12px',
                    'borderRadius': '5px',
                    'boxShadow': f'0 1px 3px {COLORS["shadow"]}',
                    'border': f'1px solid {COLORS["border"]}',
                    'width': '45%',
                    'display': 'inline-block',
                    'verticalAlign': 'top',
                    'marginRight': '1%'
                }),
                
                # System Health Chart
                html.Div(id='system-health-wrapper', children=[
                    html.H3("💻 System Health (CPU, Memory, Disk)", 
                           style={
                               'color': COLORS['text'], 
                               'fontSize': '16px',
                               'margin': '0 0 10px 0',
                               'fontWeight': '600'
                           }),
                    dcc.Graph(id='system-health-chart', 
                             config={'displayModeBar': False},
                             style={'height': '280px'})
                ], style={
                    'backgroundColor': COLORS['card'],
                    'padding': '12px',
                    'borderRadius': '5px',
                    'boxShadow': f'0 1px 3px {COLORS["shadow"]}',
                    'border': f'1px solid {COLORS["border"]}',
                    'width': '45%',
                    'maxWidth': '40%',
                    'display': 'inline-block',
                    'verticalAlign': 'top'
                }),
            ], style={'marginBottom': '15px'}),
            
            # Motion Detection Chart (with wrapper for conditional display)
            html.Div(id='motion-wrapper', children=[
                html.H3("🚶 Motion Detection Activity", 
                       style={
                           'color': COLORS['text'], 
                           'fontSize': '16px',
                           'margin': '0 0 10px 0',
                           'fontWeight': '600'
                       }),
                dcc.Graph(id='motion-chart', 
                         config={'displayModeBar': False},
                         style={'height': '250px'})
            ], style={
                'backgroundColor': COLORS['card'],
                'padding': '12px',
                'borderRadius': '5px',
                'marginBottom': '15px',
                'boxShadow': f'0 1px 3px {COLORS["shadow"]}',
                'border': f'1px solid {COLORS["border"]}'
            }),
            
            # Network Devices Section
            html.Div(id='network-devices-section', style={'marginBottom': '15px'}),
            
        ], style={'width': '100%', 'marginBottom': '15px'}),
        
        # Alerts & Logs Row (Full Width - 3 columns)
        html.Div([
            # Recent Alerts, Security Events, and Application Logs in same row
            html.Div([
                # Recent Alerts
                html.Div([
                    html.H3("⚠️ Recent Alerts", 
                           style={
                               'color': COLORS['text'], 
                               'fontSize': '16px',
                               'margin': '0 0 10px 0',
                               'fontWeight': '600'
                           }),
                    html.Div(id='alerts-table')
                ], style={
                    'backgroundColor': COLORS['card'],
                    'padding': '12px',
                    'borderRadius': '5px',
                    'boxShadow': f'0 1px 3px {COLORS["shadow"]}',
                    'border': f'1px solid {COLORS["border"]}',
                    'width': '32%',
                    'display': 'inline-block',
                    'verticalAlign': 'top',
                    'marginRight': '1.5%'
                }),
                
                # Security Events
                html.Div([
                    html.H3("🔒 Security Events", 
                           style={
                               'color': COLORS['text'], 
                               'fontSize': '16px',
                               'margin': '0 0 10px 0',
                               'fontWeight': '600'
                           }),
                    html.Div(id='security-logs')
                ], style={
                    'backgroundColor': COLORS['card'],
                    'padding': '12px',
                    'borderRadius': '5px',
                    'boxShadow': f'0 1px 3px {COLORS["shadow"]}',
                    'border': f'1px solid {COLORS["border"]}',
                    'width': '25%',
                    'display': 'inline-block',
                    'verticalAlign': 'top',
                    'marginRight': '1.5%'
                }),
                
                # Application Logs
                html.Div([
                    html.H3("📋 Application Logs", 
                           style={
                               'color': COLORS['text'], 
                               'fontSize': '16px',
                               'margin': '0 0 10px 0',
                               'fontWeight': '600'
                           }),
                    html.Div(id='app-logs')
                ], style={
                    'backgroundColor': COLORS['card'],
                    'padding': '12px',
                    'borderRadius': '5px',
                    'boxShadow': f'0 1px 3px {COLORS["shadow"]}',
                    'border': f'1px solid {COLORS["border"]}',
                    'width': '25%',
                    'display': 'inline-block',
                    'verticalAlign': 'top'
                }),
            ], style={'marginBottom': '15px'}),
            
            # Loki Logs Section
            html.Div(id='loki-logs-section', style={
                'marginTop': '15px',
                'backgroundColor': COLORS['card'],
                'padding': '12px',
                'borderRadius': '5px',
                'boxShadow': f'0 1px 3px {COLORS["shadow"]}',
                'border': f'1px solid {COLORS["border"]}'
            })
            
        ], style={'width': '100%'}),
        
    ], style={'padding': '0 15px'}),
    
    # Auto-refresh interval
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # 5 seconds
        n_intervals=0
    )
    
], style={
    'backgroundColor': COLORS['background'],
    'minHeight': '100vh',
    'padding': '0',
    'margin': '0',
    'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
})

# Callback for search functionality
@app.callback(
    Output('search-filter', 'data'),
    [Input('search-button', 'n_clicks'),
     Input('reset-button', 'n_clicks')],
    [State('search-input', 'value')]
)
def update_search_filter(search_clicks, reset_clicks, search_value):
    ctx = dash.callback_context
    if not ctx.triggered:
        return ''
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'reset-button':
        return ''
    elif button_id == 'search-button' and search_value:
        return search_value.lower()
    
    return ''

# Main dashboard update callback
@app.callback(
    [Output('search-status', 'children'),
     Output('alert-banner', 'children'),
     Output('kpi-cards', 'children'),
     Output('temp-humidity-chart', 'figure'),
     Output('system-health-chart', 'figure'),
     Output('motion-chart', 'figure'),
     Output('network-devices-section', 'children'),
     Output('alerts-table', 'children'),
     Output('security-logs', 'children'),
     Output('app-logs', 'children'),
     Output('loki-logs-section', 'children'),
     Output('temp-humidity-wrapper', 'style'),
     Output('system-health-wrapper', 'style'),
     Output('motion-wrapper', 'style')],
    [Input('interval-component', 'n_intervals'),
     Input('search-filter', 'data')]
)
def update_dashboard(n, search_filter):
    try:
        # Query data from last hour using Elasticsearch client
        if es_client is None:
            return get_no_data_components(search_filter)
        
        # Use search_data if filter is provided, otherwise query_data
        if search_filter:
            df = es_client.search_data(search_filter, hours_back=1)
        else:
            df = es_client.query_data(hours_back=1, size=1000)
        
        # Store original count for search status
        original_count = len(df)
        
        # Apply search filter - Strict filtering (show only what matches)
        if search_filter:
            df = df[df.apply(lambda row: 
                search_filter in str(row.get('sensor_type', '')).lower() or
                search_filter in str(row.get('device_type', '')).lower() or
                search_filter in str(row.get('device_name', '')).lower() or
                search_filter in str(row.get('log_type', '')).lower() or
                search_filter in str(row.get('event_type', '')).lower() or
                search_filter in str(row.get('location', '')).lower() or
                search_filter in str(row.get('sensor_id', '')).lower() or
                search_filter in str(row.get('application', '')).lower() or
                search_filter in str(row.get('message', '')).lower(),
                axis=1
            )]
        
        if df.empty:
            return get_no_results_components(search_filter)
        
        # Create search status indicator
        if search_filter:
            filtered_count = len(df)
            search_status = html.Div([
                html.Span(f"🔍 Search Active: '{search_filter}' | ", 
                         style={'fontWeight': 'bold', 'color': COLORS['primary']}),
                html.Span(f"Showing {filtered_count} of {original_count} records | ", 
                         style={'color': COLORS['text']}),
                html.Span("Only matching data shown • Other graphs/cards hidden", 
                         style={'color': COLORS['warning'], 'fontStyle': 'italic'})
            ], style={
                'backgroundColor': '#e3f2fd',
                'padding': '10px 15px',
                'borderRadius': '5px',
                'textAlign': 'center',
                'fontSize': '13px',
                'border': f'1px solid {COLORS["primary"]}'
            })
        else:
            search_status = html.Div()
        
        # Generate components
        alert_banner = generate_alert_banner(df)
        kpi_cards = generate_kpi_cards(df)
        temp_hum_chart = generate_temp_humidity_chart(df)
        system_chart = generate_system_health_chart(df)
        motion_chart = generate_motion_chart(df)
        network_section = generate_network_section(df)
        alerts_table = generate_alerts_table(df)
        security_logs = generate_security_logs(df)
        app_logs = generate_app_logs(df)
        
        # Generate Loki logs section
        loki_logs_section = generate_loki_logs_section(search_filter)
        
        # Determine visibility styles based on filtered data
        # Base style for visible sections
        visible_style = {
            'backgroundColor': COLORS['card'],
            'padding': '12px',
            'borderRadius': '5px',
            'boxShadow': f'0 1px 3px {COLORS["shadow"]}',
            'border': f'1px solid {COLORS["border"]}'
        }
        
        # Check if we have data for each section
        has_temp_humidity = len(df[df['sensor_type'].isin(['temperature', 'humidity'])]) > 0 if 'sensor_type' in df.columns else False
        has_system_health = len(df[df['sensor_type'] == 'system_health']) > 0 if 'sensor_type' in df.columns else False
        has_motion = len(df[df['sensor_type'] == 'motion']) > 0 if 'sensor_type' in df.columns else False
        
        # Temperature/Humidity wrapper style
        temp_hum_style = {**visible_style, 'width': '45%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginRight': '1%'} if has_temp_humidity else {'display': 'none'}
        
        # System Health wrapper style
        system_style = {**visible_style, 'width': '45%', 'display': 'inline-block', 'verticalAlign': 'top'} if has_system_health else {'display': 'none'}
        
        # Motion wrapper style
        motion_style = {**visible_style, 'marginBottom': '15px'} if has_motion else {'display': 'none'}
        
        return search_status, alert_banner, kpi_cards, temp_hum_chart, system_chart, motion_chart, network_section, alerts_table, security_logs, app_logs, loki_logs_section, temp_hum_style, system_style, motion_style
        
    except Exception as e:
        import traceback
        print(f"Error updating dashboard: {e}")
        print(traceback.format_exc())
        return get_error_components(str(e))

def generate_alert_banner(df):
    """Generate alert banner for critical issues"""
    alerts = check_alerts(df)
    
    if not alerts:
        return html.Div([
            html.Div([
                html.Span("✅ ", style={'fontSize': '18px'}),
                html.Span("All Systems Operational", 
                         style={'fontSize': '14px', 'fontWeight': '600'})
            ])
        ], style={
            'backgroundColor': '#d4edda',
            'color': '#155724',
            'padding': '12px',
            'borderRadius': '5px',
            'textAlign': 'center',
            'border': '1px solid #c3e6cb'
        })
    
    return html.Div([
        html.Div([
            html.Div([
                html.Span(f"{alert['icon']} ", style={'fontSize': '16px', 'marginRight': '8px'}),
                html.Span(f"{alert['message']}", style={'fontSize': '13px', 'fontWeight': '500'})
            ], style={
                'backgroundColor': alert['color'],
                'color': 'white',
                'padding': '8px 15px',
                'borderRadius': '5px',
                'marginBottom': '6px',
                'display': 'inline-block',
                'marginRight': '8px'
            })
            for alert in alerts[:5]
        ])
    ], style={'textAlign': 'center'})

def check_alerts(df):
    """Check for alert conditions"""
    alerts = []
    current_time = datetime.now(timezone.utc)
    recent_df = df[df['@timestamp'] >= (current_time - timedelta(seconds=30))]
    
    if recent_df.empty:
        return alerts
    
    # Temperature alerts
    temp_data = recent_df[recent_df['sensor_type'] == 'temperature']
    if not temp_data.empty:
        # Check for temperature or value field
        if 'temperature' in temp_data.columns:
            latest_temp = temp_data.iloc[0]['temperature']
        elif 'value' in temp_data.columns:
            latest_temp = temp_data.iloc[0]['value']
        else:
            latest_temp = None
        
        if latest_temp is not None:
            if latest_temp >= ALERT_RULES['temperature']['critical']:
                alerts.append({
                    'icon': '🔥',
                    'message': f'CRITICAL: Temperature at {latest_temp:.1f}°C',
                    'severity': 'CRITICAL',
                    'color': COLORS['danger']
                })
            elif latest_temp >= ALERT_RULES['temperature']['high']:
                alerts.append({
                    'icon': '⚠️',
                    'message': f'WARNING: Temperature at {latest_temp:.1f}°C',
                    'severity': 'WARNING',
                    'color': COLORS['warning']
                })
    
    # Humidity alerts
    hum_data = recent_df[recent_df['sensor_type'] == 'humidity']
    if not hum_data.empty:
        # Check for humidity or value field
        if 'humidity' in hum_data.columns:
            latest_hum = hum_data.iloc[0]['humidity']
        elif 'value' in hum_data.columns:
            latest_hum = hum_data.iloc[0]['value']
        else:
            latest_hum = None
        
        if latest_hum is not None:
            if latest_hum >= ALERT_RULES['humidity']['critical']:
                alerts.append({
                    'icon': '💧',
                    'message': f'CRITICAL: Humidity at {latest_hum:.1f}%',
                    'severity': 'CRITICAL',
                    'color': COLORS['danger']
                })
            elif latest_hum >= ALERT_RULES['humidity']['high']:
                alerts.append({
                    'icon': '⚠️',
                    'message': f'WARNING: Humidity at {latest_hum:.1f}%',
                    'severity': 'WARNING',
                    'color': COLORS['warning']
                })
    
    # System health alerts
    sys_data = recent_df[recent_df['sensor_type'] == 'system_health']
    if not sys_data.empty:
        latest_sys = sys_data.iloc[0]
        
        cpu = latest_sys.get('cpu_percent', 0)
        if cpu >= ALERT_RULES['cpu']['critical']:
            alerts.append({
                'icon': '🔴',
                'message': f'CRITICAL: CPU at {cpu:.1f}%',
                'severity': 'CRITICAL',
                'color': COLORS['danger']
            })
        elif cpu >= ALERT_RULES['cpu']['warning']:
            alerts.append({
                'icon': '⚠️',
                'message': f'WARNING: CPU at {cpu:.1f}%',
                'severity': 'WARNING',
                'color': COLORS['warning']
            })
        
        memory = latest_sys.get('memory_percent', 0)
        if memory >= ALERT_RULES['memory']['critical']:
            alerts.append({
                'icon': '🔴',
                'message': f'CRITICAL: Memory at {memory:.1f}%',
                'severity': 'CRITICAL',
                'color': COLORS['danger']
            })
        elif memory >= ALERT_RULES['memory']['warning']:
            alerts.append({
                'icon': '⚠️',
                'message': f'WARNING: Memory at {memory:.1f}%',
                'severity': 'WARNING',
                'color': COLORS['warning']
            })
        
        disk = latest_sys.get('disk_percent', 0)
        if disk >= ALERT_RULES['disk']['critical']:
            alerts.append({
                'icon': '🔴',
                'message': f'CRITICAL: Disk at {disk:.1f}%',
                'severity': 'CRITICAL',
                'color': COLORS['danger']
            })
        elif disk >= ALERT_RULES['disk']['warning']:
            alerts.append({
                'icon': '⚠️',
                'message': f'WARNING: Disk at {disk:.1f}%',
                'severity': 'WARNING',
                'color': COLORS['warning']
            })
    
    return alerts

def generate_kpi_cards(df):
    """Generate KPI cards with minimal padding"""
    recent_df = df[df['@timestamp'] >= (datetime.now(timezone.utc) - timedelta(minutes=5))]
    
    # Calculate KPIs
    temp_data = recent_df[recent_df['sensor_type'] == 'temperature']
    if not temp_data.empty:
        if 'temperature' in temp_data.columns:
            avg_temp = temp_data['temperature'].mean()
        elif 'value' in temp_data.columns:
            avg_temp = temp_data['value'].mean()
        else:
            avg_temp = 0
    else:
        avg_temp = 0
    
    hum_data = recent_df[recent_df['sensor_type'] == 'humidity']
    if not hum_data.empty:
        if 'humidity' in hum_data.columns:
            avg_hum = hum_data['humidity'].mean()
        elif 'value' in hum_data.columns:
            avg_hum = hum_data['value'].mean()
        else:
            avg_hum = 0
    else:
        avg_hum = 0
    
    motion_data = recent_df[recent_df['sensor_type'] == 'motion']
    motion_count = motion_data[motion_data['motion_detected'] == 1].shape[0] if not motion_data.empty and 'motion_detected' in motion_data.columns else 0
    
    sys_data = recent_df[recent_df['sensor_type'] == 'system_health']
    avg_cpu = sys_data['cpu_percent'].mean() if not sys_data.empty and 'cpu_percent' in sys_data.columns else 0
    
    network_data = recent_df[recent_df['device_type'].isin(['router', 'switch', 'firewall', 'hub', 'modem'])] if 'device_type' in recent_df.columns else pd.DataFrame()
    active_devices = network_data['device_name'].nunique() if not network_data.empty and 'device_name' in network_data.columns else 0
    
    total_logs = len(recent_df)
    
    kpis = [
        {'icon': '🌡️', 'title': 'Avg Temp', 'value': f'{avg_temp:.1f}°C', 'color': COLORS['danger'] if avg_temp > 35 else COLORS['success']},
        {'icon': '💧', 'title': 'Avg Humidity', 'value': f'{avg_hum:.1f}%', 'color': COLORS['info']},
        {'icon': '🚶', 'title': 'Motion Events', 'value': str(motion_count), 'color': COLORS['warning']},
        {'icon': '💻', 'title': 'Avg CPU', 'value': f'{avg_cpu:.1f}%', 'color': COLORS['danger'] if avg_cpu > 60 else COLORS['success']},
        {'icon': '🌐', 'title': 'Network Devices', 'value': str(active_devices), 'color': COLORS['primary']},
        {'icon': '📊', 'title': 'Total Logs', 'value': str(total_logs), 'color': COLORS['text']},
    ]
    
    return html.Div([
        html.Div([
            html.Div([
                html.Div(kpi['icon'], style={'fontSize': '28px', 'marginBottom': '5px'}),
                html.Div(kpi['value'], style={
                    'fontSize': '20px',
                    'fontWeight': 'bold',
                    'color': kpi['color'],
                    'marginBottom': '3px'
                }),
                html.Div(kpi['title'], style={
                    'fontSize': '11px',
                    'color': COLORS['text'],
                    'opacity': '0.7'
                })
            ], style={
                'backgroundColor': COLORS['card'],
                'padding': '12px',
                'borderRadius': '5px',
                'textAlign': 'center',
                'width': '15%',
                'display': 'inline-block',
                'marginRight': '10px',
                'boxShadow': f'0 1px 3px {COLORS["shadow"]}',
                'border': f'1px solid {COLORS["border"]}'
            })
            for kpi in kpis
        ])
    ])

def generate_temp_humidity_chart(df):
    """Generate temperature and humidity chart"""
    temp_data = df[df['sensor_type'] == 'temperature'].sort_values('@timestamp').tail(50)
    hum_data = df[df['sensor_type'] == 'humidity'].sort_values('@timestamp').tail(50)
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Temperature can be in 'temperature' or 'value' field
    if not temp_data.empty:
        if 'temperature' in temp_data.columns:
            temp_values = temp_data['temperature']
        elif 'value' in temp_data.columns:
            temp_values = temp_data['value']
        else:
            temp_values = None
        
        if temp_values is not None:
            fig.add_trace(
                go.Scatter(
                    x=temp_data['@timestamp'],
                    y=temp_values,
                    name='Temperature',
                    line=dict(color=COLORS['danger'], width=2),
                    mode='lines+markers',
                    marker=dict(size=4)
                ),
                secondary_y=False
            )
    
    # Humidity can be in 'humidity' or 'value' field
    if not hum_data.empty:
        if 'humidity' in hum_data.columns:
            hum_values = hum_data['humidity']
        elif 'value' in hum_data.columns:
            hum_values = hum_data['value']
        else:
            hum_values = None
        
        if hum_values is not None:
            fig.add_trace(
                go.Scatter(
                    x=hum_data['@timestamp'],
                    y=hum_values,
                    name='Humidity',
                    line=dict(color=COLORS['info'], width=2),
                    mode='lines+markers',
                    marker=dict(size=4)
                ),
                secondary_y=True
            )
    
    fig.update_xaxes(title_text="Time", showgrid=True, gridcolor='#e0e0e0')
    fig.update_yaxes(title_text="Temperature (°C)", secondary_y=False, showgrid=True, gridcolor='#e0e0e0')
    fig.update_yaxes(title_text="Humidity (%)", secondary_y=True, showgrid=False)
    
    fig.update_layout(
        margin=dict(l=40, r=40, t=10, b=40),
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(size=11, color=COLORS['text']),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode='x unified'
    )
    
    return fig

def generate_system_health_chart(df):
    """Generate system health chart"""
    sys_data = df[df['sensor_type'] == 'system_health'].sort_values('@timestamp').tail(50)
    
    fig = go.Figure()
    
    if not sys_data.empty and 'cpu_percent' in sys_data.columns:
        fig.add_trace(go.Scatter(
            x=sys_data['@timestamp'],
            y=sys_data['cpu_percent'],
            name='CPU %',
            line=dict(color='#e74c3c', width=2),
            mode='lines+markers',
            marker=dict(size=4)
        ))
        
        if 'memory_percent' in sys_data.columns:
            fig.add_trace(go.Scatter(
                x=sys_data['@timestamp'],
                y=sys_data['memory_percent'],
                name='Memory %',
                line=dict(color='#3498db', width=2),
                mode='lines+markers',
                marker=dict(size=4)
            ))
        
        if 'disk_percent' in sys_data.columns:
            fig.add_trace(go.Scatter(
                x=sys_data['@timestamp'],
                y=sys_data['disk_percent'],
                name='Disk %',
                line=dict(color='#27ae60', width=2),
                mode='lines+markers',
                marker=dict(size=4)
            ))
    
    fig.update_xaxes(title_text="Time", showgrid=True, gridcolor='#e0e0e0')
    fig.update_yaxes(title_text="Usage (%)", showgrid=True, gridcolor='#e0e0e0')
    
    fig.update_layout(
        margin=dict(l=40, r=40, t=10, b=40),
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(size=11, color=COLORS['text']),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode='x unified'
    )
    
    return fig

def generate_motion_chart(df):
    """Generate motion detection chart"""
    motion_data = df[df['sensor_type'] == 'motion'].sort_values('@timestamp').tail(100)
    
    fig = go.Figure()
    
    if not motion_data.empty and 'motion_detected' in motion_data.columns:
        fig.add_trace(go.Scatter(
            x=motion_data['@timestamp'],
            y=motion_data['motion_detected'],
            name='Motion',
            mode='lines+markers',
            line=dict(color='#9b59b6', width=2, shape='hv'),
            marker=dict(size=8, symbol='square'),
            fill='tozeroy',
            fillcolor='rgba(155,89,182,0.2)'
        ))
    
    fig.update_xaxes(title_text="Time", showgrid=True, gridcolor='#e0e0e0')
    fig.update_yaxes(title_text="Detected", showgrid=True, gridcolor='#e0e0e0', tickvals=[0, 1])
    
    fig.update_layout(
        margin=dict(l=40, r=40, t=10, b=40),
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(size=11, color=COLORS['text']),
        hovermode='x unified'
    )
    
    return fig

def generate_network_section(df):
    """Generate network devices section"""
    if 'device_type' not in df.columns:
        return html.Div("No network devices data available", 
                       style={'color': COLORS['text'], 'textAlign': 'center', 'padding': '15px'})
    
    network_data = df[df['device_type'].isin(['router', 'switch', 'firewall', 'hub', 'modem'])]
    
    if network_data.empty:
        return html.Div("No network devices data available", 
                       style={'color': COLORS['text'], 'textAlign': 'center', 'padding': '15px'})
    
    # Get latest data for each device
    devices_info = []
    for device_name in network_data['device_name'].unique():
        device_df = network_data[network_data['device_name'] == device_name].sort_values('@timestamp')
        if not device_df.empty:
            latest = device_df.iloc[-1]
            devices_info.append({
                'name': device_name,
                'type': latest['device_type'],
                'status': latest.get('device_status', latest.get('status', 'unknown')),
                'traffic_in': latest.get('traffic_in_mbps', 0),
                'traffic_out': latest.get('traffic_out_mbps', 0),
                'packet_loss': latest.get('packet_loss_percent', 0),
                'port_util': latest.get('port_utilization_percent', 0)
            })
    
    device_cards = []
    for device in devices_info:
        status_color = COLORS['success'] if device['status'] == 'online' else COLORS['danger']
        
        device_cards.append(
            html.Div([
                html.Div([
                    html.Span(f"{'🌐' if device['type'] == 'router' else '🔀' if device['type'] == 'switch' else '🛡️' if device['type'] == 'firewall' else '📡' if device['type'] == 'hub' else '📶'} ", 
                             style={'fontSize': '20px', 'marginRight': '8px'}),
                    html.Span(device['name'], style={'fontSize': '14px', 'fontWeight': '600', 'color': COLORS['text']})
                ], style={'marginBottom': '8px'}),
                
                html.Div([
                    html.Span('●', style={'color': status_color, 'marginRight': '5px'}),
                    html.Span(device['status'].upper(), style={'fontSize': '11px', 'fontWeight': '600', 'color': status_color})
                ], style={'marginBottom': '8px'}),
                
                html.Div([
                    html.Div(f"↓ {device['traffic_in']:.1f} Mbps", 
                            style={'fontSize': '11px', 'color': COLORS['info'], 'marginBottom': '3px'}),
                    html.Div(f"↑ {device['traffic_out']:.1f} Mbps", 
                            style={'fontSize': '11px', 'color': COLORS['success'], 'marginBottom': '3px'}),
                    html.Div(f"📦 Loss: {device['packet_loss']:.1f}%", 
                            style={'fontSize': '11px', 'color': COLORS['warning'] if device['packet_loss'] > 2 else COLORS['text'], 'marginBottom': '3px'}),
                    html.Div(f"🔌 Ports: {device['port_util']:.1f}%", 
                            style={'fontSize': '11px', 'color': COLORS['text']})
                ])
            ], style={
                'backgroundColor': COLORS['card'],
                'padding': '10px',
                'borderRadius': '5px',
                'width': '15%',
                'display': 'inline-block',
                'marginRight': '10px',
                'marginBottom': '10px',
                'verticalAlign': 'top',
                'boxShadow': f'0 1px 3px {COLORS["shadow"]}',
                'border': f'1px solid {COLORS["border"]}'
            })
        )
    
    return html.Div([
        html.H3("🌐 Network Devices Status", 
               style={
                   'color': COLORS['text'], 
                   'fontSize': '16px',
                   'margin': '0 0 10px 0',
                   'fontWeight': '600'
               }),
        html.Div(device_cards)
    ], style={
        'backgroundColor': COLORS['card'],
        'padding': '12px',
        'borderRadius': '5px',
        'boxShadow': f'0 1px 3px {COLORS["shadow"]}',
        'border': f'1px solid {COLORS["border"]}'
    })

def generate_alerts_table(df):
    """Generate recent alerts table"""
    alert_records = []
    
    # If Elasticsearch has data, use it
    if not df.empty and '@timestamp' in df.columns:
        alerts_df = df[df['@timestamp'] >= (datetime.now(timezone.utc) - timedelta(minutes=10))].copy()
        
        for _, row in alerts_df.iterrows():
            if row.get('sensor_type') == 'temperature':
                temp = row.get('temperature') or row.get('value', 0)
                if temp >= ALERT_RULES['temperature']['critical']:
                    alert_records.append({
                        'Time': row['@timestamp'].strftime('%H:%M:%S'),
                        'Type': 'Temperature',
                        'Severity': 'CRITICAL',
                        'Message': f'Temperature: {temp:.1f}°C'
                    })
                elif temp >= ALERT_RULES['temperature']['high']:
                    alert_records.append({
                        'Time': row['@timestamp'].strftime('%H:%M:%S'),
                        'Type': 'Temperature',
                        'Severity': 'WARNING',
                        'Message': f'Temperature: {temp:.1f}°C'
                    })
            
            if row.get('sensor_type') == 'humidity':
                hum = row.get('humidity') or row.get('value', 0)
                if hum >= ALERT_RULES['humidity']['critical']:
                    alert_records.append({
                        'Time': row['@timestamp'].strftime('%H:%M:%S'),
                        'Type': 'Humidity',
                        'Severity': 'CRITICAL',
                        'Message': f'Humidity: {hum:.1f}%'
                    })
                elif hum >= ALERT_RULES['humidity']['high']:
                    alert_records.append({
                        'Time': row['@timestamp'].strftime('%H:%M:%S'),
                        'Type': 'Humidity',
                        'Severity': 'WARNING',
                        'Message': f'Humidity: {hum:.1f}%'
                    })
    
    # If no alerts from Elasticsearch, try Loki
    if not alert_records and loki_client:
        try:
            import re
            loki_logs = loki_client.query_logs('{host=~".+"}', minutes_back=10)
            if not loki_logs.empty:
                for _, row in loki_logs.iterrows():
                    msg = row['message']
                    timestamp = row['timestamp']
                    
                    # Extract temperature
                    temp_match = re.search(r'[Tt]emperature[:\s=]+(\d+\.?\d*)', msg)
                    if temp_match:
                        temp = float(temp_match.group(1))
                        if temp >= ALERT_RULES['temperature']['critical']:
                            alert_records.append({
                                'Time': timestamp.strftime('%H:%M:%S'),
                                'Type': 'Temperature',
                                'Severity': 'CRITICAL',
                                'Message': f'Temperature: {temp:.1f}°C'
                            })
                        elif temp >= ALERT_RULES['temperature']['high']:
                            alert_records.append({
                                'Time': timestamp.strftime('%H:%M:%S'),
                                'Type': 'Temperature',
                                'Severity': 'WARNING',
                                'Message': f'Temperature: {temp:.1f}°C'
                            })
                    
                    # Extract humidity
                    hum_match = re.search(r'[Hh]umidity[:\s=]+(\d+\.?\d*)', msg)
                    if hum_match:
                        hum = float(hum_match.group(1))
                        if hum >= ALERT_RULES['humidity']['critical']:
                            alert_records.append({
                                'Time': timestamp.strftime('%H:%M:%S'),
                                'Type': 'Humidity',
                                'Severity': 'CRITICAL',
                                'Message': f'Humidity: {hum:.1f}%'
                            })
                        elif hum >= ALERT_RULES['humidity']['high']:
                            alert_records.append({
                                'Time': timestamp.strftime('%H:%M:%S'),
                                'Type': 'Humidity',
                                'Severity': 'WARNING',
                                'Message': f'Humidity: {hum:.1f}%'
                            })
        except Exception as e:
            print(f"Error getting alerts from Loki: {e}")
    
    if not alert_records:
        return html.Div("No alerts triggered", 
                       style={'color': COLORS['success'], 'fontSize': '12px', 'textAlign': 'center', 'padding': '15px'})
    
    alert_table_df = pd.DataFrame(alert_records).head(10)
    
    return dash_table.DataTable(
        data=alert_table_df.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in alert_table_df.columns],
        style_cell={
            'textAlign': 'left',
            'padding': '8px',
            'fontSize': '11px',
            'border': f'1px solid {COLORS["border"]}'
        },
        style_header={
            'backgroundColor': COLORS['primary'],
            'color': 'white',
            'fontWeight': 'bold',
            'fontSize': '12px'
        },
        style_data_conditional=[
            {
                'if': {'filter_query': '{Severity} = "CRITICAL"'},
                'backgroundColor': '#f8d7da',
                'color': '#721c24'
            },
            {
                'if': {'filter_query': '{Severity} = "WARNING"'},
                'backgroundColor': '#fff3cd',
                'color': '#856404'
            }
        ]
    )

def generate_security_logs(df):
    """Generate security logs"""
    logs = []
    
    # If Elasticsearch has security data, use it
    if not df.empty and 'log_type' in df.columns and '@timestamp' in df.columns:
        security_data = df[df['log_type'] == 'security'].sort_values('@timestamp', ascending=False).head(5)
        for _, row in security_data.iterrows():
            severity_color = {
                'INFO': COLORS['success'],
                'WARNING': COLORS['warning'],
                'ERROR': COLORS['danger'],
                'CRITICAL': COLORS['danger']
            }.get(row.get('severity', 'INFO'), COLORS['text'])
            
            logs.append(
                html.Div([
                    html.Div([
                        html.Span(row['@timestamp'].strftime('%H:%M:%S'), 
                                 style={'fontSize': '10px', 'color': COLORS['text'], 'opacity': '0.7', 'marginRight': '8px'}),
                        html.Span(row.get('severity', 'INFO'), 
                                 style={'fontSize': '10px', 'fontWeight': 'bold', 'color': severity_color, 'marginRight': '8px'}),
                    ]),
                    html.Div(row.get('message', 'No message')[:60] + '...', 
                            style={'fontSize': '11px', 'color': COLORS['text'], 'marginTop': '3px'})
                ], style={
                    'padding': '8px',
                    'marginBottom': '6px',
                    'backgroundColor': COLORS['background'],
                    'borderRadius': '3px',
                    'borderLeft': f'3px solid {severity_color}'
                })
            )
    
    # If no security logs from Elasticsearch, try Loki (ERROR and CRITICAL logs)
    if not logs and loki_client:
        try:
            loki_logs = loki_client.query_logs('{host=~".+"}', minutes_back=60)
            if not loki_logs.empty:
                security_logs = loki_logs[loki_logs['level'].isin(['ERROR', 'CRITICAL'])].head(5)
                for _, row in security_logs.iterrows():
                    severity_color = COLORS['danger'] if row['level'] in ['ERROR', 'CRITICAL'] else COLORS['warning']
                    logs.append(
                        html.Div([
                            html.Div([
                                html.Span(row['timestamp'].strftime('%H:%M:%S'), 
                                         style={'fontSize': '10px', 'color': COLORS['text'], 'opacity': '0.7', 'marginRight': '8px'}),
                                html.Span(row['level'], 
                                         style={'fontSize': '10px', 'fontWeight': 'bold', 'color': severity_color, 'marginRight': '8px'}),
                            ]),
                            html.Div(row['message'][:60] + '...', 
                                    style={'fontSize': '11px', 'color': COLORS['text'], 'marginTop': '3px'})
                        ], style={
                            'padding': '8px',
                            'marginBottom': '6px',
                            'backgroundColor': COLORS['background'],
                            'borderRadius': '3px',
                            'borderLeft': f'3px solid {severity_color}'
                        })
                    )
        except Exception as e:
            print(f"Error getting security logs from Loki: {e}")
    
    if not logs:
        return html.Div("No security events", 
                       style={'color': COLORS['text'], 'fontSize': '12px', 'textAlign': 'center', 'padding': '15px'})
    
    return html.Div(logs)

def generate_app_logs(df):
    """Generate application logs"""
    logs = []
    
    # If Elasticsearch has application data, use it
    if not df.empty and 'log_type' in df.columns and '@timestamp' in df.columns:
        app_data = df[df['log_type'] == 'application'].sort_values('@timestamp', ascending=False).head(5)
        for _, row in app_data.iterrows():
            level_color = {
                'INFO': COLORS['info'],
                'WARNING': COLORS['warning'],
                'ERROR': COLORS['danger'],
                'DEBUG': COLORS['text']
            }.get(row.get('log_level', 'INFO'), COLORS['text'])
            
            logs.append(
                html.Div([
                    html.Div([
                        html.Span(row['@timestamp'].strftime('%H:%M:%S'), 
                                 style={'fontSize': '10px', 'color': COLORS['text'], 'opacity': '0.7', 'marginRight': '8px'}),
                        html.Span(row.get('log_level', 'INFO'), 
                                 style={'fontSize': '10px', 'fontWeight': 'bold', 'color': level_color, 'marginRight': '8px'}),
                    ]),
                    html.Div(row.get('message', 'No message')[:60] + '...', 
                            style={'fontSize': '11px', 'color': COLORS['text'], 'marginTop': '3px'})
                ], style={
                    'padding': '8px',
                    'marginBottom': '6px',
                    'backgroundColor': COLORS['background'],
                    'borderRadius': '3px',
                    'borderLeft': f'3px solid {level_color}'
                })
            )
    
    # If no app logs from Elasticsearch, try Loki (INFO and DEBUG logs)
    if not logs and loki_client:
        try:
            loki_logs = loki_client.query_logs('{host=~".+"}', minutes_back=60)
            if not loki_logs.empty:
                app_logs = loki_logs[loki_logs['level'].isin(['INFO', 'DEBUG'])].head(5)
                for _, row in app_logs.iterrows():
                    level_color = COLORS['info'] if row['level'] == 'INFO' else COLORS['text']
                    logs.append(
                        html.Div([
                            html.Div([
                                html.Span(row['timestamp'].strftime('%H:%M:%S'), 
                                         style={'fontSize': '10px', 'color': COLORS['text'], 'opacity': '0.7', 'marginRight': '8px'}),
                                html.Span(row['level'], 
                                         style={'fontSize': '10px', 'fontWeight': 'bold', 'color': level_color, 'marginRight': '8px'}),
                            ]),
                            html.Div(row['message'][:60] + '...', 
                                    style={'fontSize': '11px', 'color': COLORS['text'], 'marginTop': '3px'})
                        ], style={
                            'padding': '8px',
                            'marginBottom': '6px',
                            'backgroundColor': COLORS['background'],
                            'borderRadius': '3px',
                            'borderLeft': f'3px solid {level_color}'
                        })
                    )
        except Exception as e:
            print(f"Error getting application logs from Loki: {e}")
    
    if not logs:
        return html.Div("No application logs", 
                       style={'color': COLORS['text'], 'fontSize': '12px', 'textAlign': 'center', 'padding': '15px'})
    
    return html.Div(logs)

def get_no_data_components(search_filter=''):
    """Return components when no data is available"""
    # Create search status if filter is active
    if search_filter:
        search_status = html.Div([
            html.Span(f"🔍 Search Active: '{search_filter}' | ", 
                     style={'fontWeight': 'bold', 'color': COLORS['primary']}),
            html.Span("Searching Loki logs only (no Elasticsearch data)", 
                     style={'color': COLORS['text']})
        ], style={
            'backgroundColor': '#e3f2fd',
            'padding': '10px 15px',
            'borderRadius': '5px',
            'textAlign': 'center',
            'fontSize': '13px',
            'border': f'1px solid {COLORS["primary"]}'
        })
    else:
        search_status = html.Div()
    
    no_data_msg = html.Div("", 
                          style={'textAlign': 'center', 'padding': '20px', 'color': COLORS['text'], 'fontSize': '14px'})
    empty_fig = go.Figure()
    empty_fig.update_layout(paper_bgcolor='white', plot_bgcolor='white')
    
    # Hidden styles - hide all Elasticsearch sections
    hidden_style = {'display': 'none'}
    
    # Generate alerts, security logs, and app logs from Loki
    empty_df = pd.DataFrame()  # Empty DataFrame to trigger Loki fallback
    alerts_table = generate_alerts_table(empty_df)
    security_logs = generate_security_logs(empty_df)
    app_logs = generate_app_logs(empty_df)
    
    # Show Loki logs even if Elasticsearch has no data
    loki_logs = generate_loki_logs_section(search_filter)
    
    return (search_status, no_data_msg, html.Div(), empty_fig, empty_fig, empty_fig, html.Div(), alerts_table, security_logs, app_logs, loki_logs, hidden_style, hidden_style, hidden_style)

def get_no_results_components(search_term):
    """Return components when search returns no results"""
    search_status = html.Div([
        html.Span(f"🔍 Search Active: '{search_term}' | ", 
                 style={'fontWeight': 'bold', 'color': COLORS['danger']}),
        html.Span("No matching results found", 
                 style={'color': COLORS['text']})
    ], style={
        'backgroundColor': '#ffebee',
        'padding': '10px 15px',
        'borderRadius': '5px',
        'textAlign': 'center',
        'fontSize': '13px',
        'border': f'1px solid {COLORS["danger"]}'
    })
    
    no_results_msg = html.Div(f"No results found for '{search_term}'. Try different search terms.", 
                              style={'textAlign': 'center', 'padding': '50px', 'color': COLORS['text']})
    empty_fig = go.Figure()
    empty_fig.update_layout(paper_bgcolor='white', plot_bgcolor='white')
    
    # Hidden styles
    hidden_style = {'display': 'none'}
    
    # Try to get Loki logs even if search has no results (pass search term for filtering)
    loki_logs = generate_loki_logs_section(search_term)
    
    return (search_status, no_results_msg, no_results_msg, empty_fig, empty_fig, empty_fig, no_results_msg, no_results_msg, no_results_msg, no_results_msg, loki_logs, hidden_style, hidden_style, hidden_style)

def get_error_components(error_msg):
    """Return components when an error occurs"""
    error_div = html.Div(f"Error: {error_msg}", 
                        style={'textAlign': 'center', 'padding': '50px', 'color': COLORS['danger']})
    empty_fig = go.Figure()
    empty_fig.update_layout(paper_bgcolor='white', plot_bgcolor='white')
    
    # Hidden styles for error state
    hidden_style = {'display': 'none'}
    
    # Show error message in Loki section too
    loki_error = html.Div(f"Dashboard error occurred: {error_msg}", 
                         style={'color': COLORS['danger'], 'padding': '15px'})
    
    return (html.Div(), error_div, error_div, empty_fig, empty_fig, empty_fig, error_div, error_div, error_div, error_div, loki_error, hidden_style, hidden_style, hidden_style)

def generate_temp_humidity_chart_from_logs(temp_data, humidity_data, chart_type):
    """Generate temperature or humidity chart from parsed log data"""
    import plotly.graph_objs as go
    from datetime import datetime
    
    fig = go.Figure()
    
    if chart_type == 'temperature' and temp_data:
        # Group by host
        hosts = {}
        for item in temp_data:
            host = item['host']
            if host not in hosts:
                hosts[host] = {'timestamps': [], 'values': []}
            hosts[host]['timestamps'].append(item['timestamp'])
            hosts[host]['values'].append(item['value'])
        
        # Add trace for each host
        for host, data in hosts.items():
            fig.add_trace(go.Scatter(
                x=data['timestamps'],
                y=data['values'],
                mode='lines+markers',
                name=host,
                line=dict(width=2),
                marker=dict(size=4)
            ))
        
        fig.update_layout(
            title={'text': '🌡️ Temperature (°C)', 'font': {'size': 14, 'color': COLORS['text']}},
            xaxis={'title': 'Time', 'gridcolor': COLORS['border']},
            yaxis={'title': 'Temperature (°C)', 'gridcolor': COLORS['border']},
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=50, r=20, t=40, b=40),
            height=250,
            showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
    
    elif chart_type == 'humidity' and humidity_data:
        # Group by host
        hosts = {}
        for item in humidity_data:
            host = item['host']
            if host not in hosts:
                hosts[host] = {'timestamps': [], 'values': []}
            hosts[host]['timestamps'].append(item['timestamp'])
            hosts[host]['values'].append(item['value'])
        
        # Add trace for each host
        for host, data in hosts.items():
            fig.add_trace(go.Scatter(
                x=data['timestamps'],
                y=data['values'],
                mode='lines+markers',
                name=host,
                line=dict(width=2),
                marker=dict(size=4)
            ))
        
        fig.update_layout(
            title={'text': '💧 Humidity (%)', 'font': {'size': 14, 'color': COLORS['text']}},
            xaxis={'title': 'Time', 'gridcolor': COLORS['border']},
            yaxis={'title': 'Humidity (%)', 'gridcolor': COLORS['border']},
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=50, r=20, t=40, b=40),
            height=250,
            showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
    
    return fig

def generate_motion_chart_from_logs(motion_data):
    """Generate motion detection chart from parsed log data"""
    import plotly.graph_objs as go
    
    fig = go.Figure()
    
    if motion_data:
        # Group by host
        hosts = {}
        for item in motion_data:
            host = item['host']
            if host not in hosts:
                hosts[host] = {'timestamps': [], 'values': []}
            hosts[host]['timestamps'].append(item['timestamp'])
            hosts[host]['values'].append(item['value'])
        
        # Add trace for each host
        for host, data in hosts.items():
            fig.add_trace(go.Scatter(
                x=data['timestamps'],
                y=data['values'],
                mode='lines+markers',
                name=host,
                line=dict(width=2, shape='hv'),
                marker=dict(size=6, symbol='square'),
                fill='tozeroy',
                fillcolor='rgba(155,89,182,0.2)'
            ))
        
        fig.update_layout(
            title={'text': '🚶 Motion Detection', 'font': {'size': 14, 'color': COLORS['text']}},
            xaxis={'title': 'Time', 'gridcolor': COLORS['border']},
            yaxis={'title': 'Detected', 'gridcolor': COLORS['border'], 'tickvals': [0, 1], 'ticktext': ['No', 'Yes']},
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=50, r=20, t=40, b=40),
            height=250,
            showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
    
    return fig

def generate_loki_logs_section(search_filter=''):
    """Generate Loki logs section with recent logs from all VMs"""
    if loki_client is None:
        return html.Div([
            html.H3("🔍 Loki Centralized Logs", 
                   style={
                       'color': COLORS['text'], 
                       'fontSize': '16px',
                       'margin': '0 0 10px 0',
                       'fontWeight': '600'
                   }),
            html.Div("⚠️ Loki connection failed. Logs from local storage not available.",
                    style={'color': COLORS['danger'], 'padding': '15px', 'textAlign': 'center'})
        ])
    
    try:
        # Get logs from all VMs (6 hours to match Grafana)
        # Try multiple queries to find logs
        # Note: Loki requires .+ (not .*) for non-empty-compatible matchers
        logs_df = loki_client.query_logs('{host=~".+"}', minutes_back=360)
        
        # If no logs with host label, try job label
        if logs_df.empty:
            logs_df = loki_client.query_logs('{job=~".+"}', minutes_back=360)
        
        # Apply search filter if provided
        if search_filter and not logs_df.empty:
            logs_df = logs_df[logs_df.apply(lambda row:
                search_filter in str(row.get('host', '')).lower() or
                search_filter in str(row.get('job', '')).lower() or
                search_filter in str(row.get('level', '')).lower() or
                search_filter in str(row.get('message', '')).lower(),
                axis=1
            )]
        
        if logs_df.empty:
            return html.Div([
                html.H3("🔍 Loki Centralized Logs", 
                       style={
                           'color': COLORS['text'], 
                           'fontSize': '16px',
                           'margin': '0 0 10px 0',
                           'fontWeight': '600'
                       }),
                html.Div("No logs available in the last 6 hours. Make sure Promtail is running on VMs.",
                        style={'color': COLORS['text'], 'padding': '15px', 'textAlign': 'center'})
            ])
        
        # Parse temperature, humidity, and motion from log messages
        import re
        temp_data = []
        humidity_data = []
        motion_data = []
        
        for _, row in logs_df.iterrows():
            msg = row['message']
            timestamp = row['timestamp']
            host = row.get('host', 'unknown')
            
            # Extract temperature (patterns: "Temperature: 22.46°C" or "TEMP=22.46°C")
            temp_match = re.search(r'[Tt]emperature[:\s=]+(\d+\.?\d*)', msg)
            if temp_match:
                temp_data.append({
                    'timestamp': timestamp,
                    'value': float(temp_match.group(1)),
                    'host': host
                })
            
            # Extract humidity (patterns: "Humidity: 49.87%" or "HUMIDITY=49.87%")
            humidity_match = re.search(r'[Hh]umidity[:\s=]+(\d+\.?\d*)', msg)
            if humidity_match:
                humidity_data.append({
                    'timestamp': timestamp,
                    'value': float(humidity_match.group(1)),
                    'host': host
                })
            
            # Extract motion (patterns: "Motion: 1" or "MOTION=1" or "motion detected")
            motion_match = re.search(r'[Mm]otion[:\s=]+(\d+)', msg)
            if motion_match:
                motion_data.append({
                    'timestamp': timestamp,
                    'value': int(motion_match.group(1)),
                    'host': host
                })
            elif 'motion detected' in msg.lower():
                motion_data.append({
                    'timestamp': timestamp,
                    'value': 1,
                    'host': host
                })
        
        # Prepare data for display
        display_df = logs_df.head(20).copy()
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        display_df['level'] = display_df['level'].fillna('INFO')
        
        # Create display columns
        display_data = []
        for _, row in display_df.iterrows():
            display_data.append({
                'Time': row['timestamp'],
                'Host': row.get('host', 'unknown'),
                'Level': row['level'],
                'Job': row.get('job', 'unknown'),
                'Message': row['message'][:100] + '...' if len(row['message']) > 100 else row['message']
            })
        
        # Create stats (6 hours to match data range)
        stats = {
            'total': len(logs_df),
            'errors': len(logs_df[logs_df['level'] == 'ERROR']),
            'warnings': len(logs_df[logs_df['level'] == 'WARN']),
            'info': len(logs_df[logs_df['level'] == 'INFO'])
        }
        
        return html.Div([
            html.H3("🔍 Loki Centralized Logs", 
                   style={
                       'color': COLORS['text'], 
                       'fontSize': '16px',
                       'margin': '0 0 10px 0',
                       'fontWeight': '600'
                   }),
            
            # Log statistics
            html.Div([
                html.Div([
                    html.Div([
                        html.Div(f"{stats.get('total', 0)}", 
                                style={'fontSize': '24px', 'fontWeight': 'bold', 'color': COLORS['primary']}),
                        html.Div("Total Logs (6h)", style={'fontSize': '11px', 'color': COLORS['text'], 'marginTop': '4px'})
                    ], style={'textAlign': 'center', 'padding': '10px', 'flex': 1}),
                    html.Div([
                        html.Div(f"{stats.get('errors', 0)}", 
                                style={'fontSize': '24px', 'fontWeight': 'bold', 'color': COLORS['danger']}),
                        html.Div("Errors", style={'fontSize': '11px', 'color': COLORS['text'], 'marginTop': '4px'})
                    ], style={'textAlign': 'center', 'padding': '10px', 'flex': 1}),
                    html.Div([
                        html.Div(f"{stats.get('warnings', 0)}", 
                                style={'fontSize': '24px', 'fontWeight': 'bold', 'color': COLORS['warning']}),
                        html.Div("Warnings", style={'fontSize': '11px', 'color': COLORS['text'], 'marginTop': '4px'})
                    ], style={'textAlign': 'center', 'padding': '10px', 'flex': 1}),
                    html.Div([
                        html.Div(f"{stats.get('info', 0)}", 
                                style={'fontSize': '24px', 'fontWeight': 'bold', 'color': COLORS['info']}),
                        html.Div("Info", style={'fontSize': '11px', 'color': COLORS['text'], 'marginTop': '4px'})
                    ], style={'textAlign': 'center', 'padding': '10px', 'flex': 1}),
                ], style={'display': 'flex', 'marginBottom': '15px', 'backgroundColor': '#f5f5f5', 'borderRadius': '5px'})
            ]),
            
            # Temperature, Humidity, and Motion Charts
            html.Div([
                # Temperature Chart
                html.Div([
                    dcc.Graph(
                        figure=generate_temp_humidity_chart_from_logs(temp_data, humidity_data, 'temperature'),
                        config={'displayModeBar': False},
                        style={'height': '250px'}
                    )
                ], style={
                    'width': '32%',
                    'display': 'inline-block',
                    'verticalAlign': 'top',
                    'marginRight': '2%'
                }) if temp_data else html.Div(),
                
                # Humidity Chart
                html.Div([
                    dcc.Graph(
                        figure=generate_temp_humidity_chart_from_logs(temp_data, humidity_data, 'humidity'),
                        config={'displayModeBar': False},
                        style={'height': '250px'}
                    )
                ], style={
                    'width': '32%',
                    'display': 'inline-block',
                    'verticalAlign': 'top',
                    'marginRight': '2%'
                }) if humidity_data else html.Div(),
                
                # Motion Chart
                html.Div([
                    dcc.Graph(
                        figure=generate_motion_chart_from_logs(motion_data),
                        config={'displayModeBar': False},
                        style={'height': '250px'}
                    )
                ], style={
                    'width': '32%',
                    'display': 'inline-block',
                    'verticalAlign': 'top'
                }) if motion_data else html.Div()
            ], style={'marginBottom': '15px'}) if (temp_data or humidity_data or motion_data) else html.Div(),
            
            # Recent logs table
            html.Div([
                html.Div("Recent Logs (Last 20)", 
                        style={'fontSize': '12px', 'fontWeight': 'bold', 'marginBottom': '10px', 'color': COLORS['text']}),
                dash_table.DataTable(
                    data=display_data,
                    columns=[{'name': col, 'id': col} for col in ['Time', 'Host', 'Level', 'Job', 'Message']],
                    style_cell={
                        'textAlign': 'left',
                        'padding': '8px',
                        'fontSize': '11px',
                        'border': f'1px solid {COLORS["border"]}',
                        'overflow': 'hidden',
                        'textOverflow': 'ellipsis',
                        'maxWidth': '500px'
                    },
                    style_header={
                        'backgroundColor': COLORS['primary'],
                        'color': 'white',
                        'fontWeight': 'bold',
                        'fontSize': '12px',
                        'border': f'1px solid {COLORS["border"]}'
                    },
                    style_data_conditional=[
                        {
                            'if': {'column_id': 'Level', 'filter_query': '{Level} = ERROR'},
                            'backgroundColor': '#ffebee',
                            'color': COLORS['danger']
                        },
                        {
                            'if': {'column_id': 'Level', 'filter_query': '{Level} = WARN'},
                            'backgroundColor': '#fff3e0',
                            'color': COLORS['warning']
                        }
                    ],
                    page_size=10,
                    style_as_list_view=False
                )
            ])
        ])
        
    except Exception as e:
        print(f"Error generating Loki logs: {e}")
        return html.Div(f"Error loading logs: {str(e)}", 
                       style={'color': COLORS['danger'], 'padding': '15px'})



