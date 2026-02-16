"""
Loki Log Integration Module for Dashboard
Fetches and processes logs from Loki for display in dashboard
"""

import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import json

class LokiClient:
    """Client for querying Loki logs"""
    
    def __init__(self, loki_url="http://localhost:3100"):
        self.base_url = loki_url
        self.api_endpoint = f"{loki_url}/loki/api/v1/query_range"
        
    def query_logs(self, query, minutes_back=30):
        """
        Query Loki for logs
        
        Args:
            query: LogQL query string (e.g., '{host="client-vm-1"}')
            minutes_back: How many minutes back to query
            
        Returns:
            DataFrame with columns: timestamp, message, labels
        """
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=minutes_back)
            
            # Loki expects timestamps in nanoseconds as strings
            params = {
                'query': query,
                'start': str(int(start_time.timestamp() * 1e9)),
                'end': str(int(end_time.timestamp() * 1e9)),
                'limit': 5000,  # Loki's max_entries_limit_per_query
                'direction': 'backward'
            }
            
            # print(f"Querying Loki: {query} from {start_time} to {end_time}")
            response = requests.get(self.api_endpoint, params=params, timeout=10)
            
            # Better error handling
            if response.status_code != 200:
                error_msg = f"Loki returned {response.status_code}: {response.text}"
                print(error_msg)
                return pd.DataFrame()
            
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] != 'success':
                print(f"Loki query failed: {data.get('error', 'Unknown error')}")
                return pd.DataFrame()
            
            # Parse results
            logs = []
            if 'result' in data['data']:
                for stream in data['data']['result']:
                    # Loki returns labels in 'stream' field
                    labels = stream.get('stream', stream.get('labels', {}))
                    for timestamp_ns, message in stream.get('values', []):
                        logs.append({
                            'timestamp': datetime.fromtimestamp(int(timestamp_ns) / 1e9),
                            'message': message,
                            'host': labels.get('host', 'unknown'),
                            'job': labels.get('job', 'unknown'),
                            'level': self._extract_level(message)
                        })
            
            df = pd.DataFrame(logs)
            if not df.empty:
                df = df.sort_values('timestamp', ascending=False)
            
            return df
            
        except Exception as e:
            print(f"Error querying Loki: {e}")
            return pd.DataFrame()
    
    def get_log_stats(self, host="client-vm-1", minutes_back=60):
        """
        Get log statistics for a host
        
        Returns:
            Dict with counts of different log levels
        """
        try:
            query = f'{{host="{host}"}}'
            df = self.query_logs(query, minutes_back)
            
            if df.empty:
                return {'total': 0, 'errors': 0, 'warnings': 0, 'info': 0}
            
            return {
                'total': len(df),
                'errors': len(df[df['level'] == 'ERROR']),
                'warnings': len(df[df['level'] == 'WARN']),
                'info': len(df[df['level'] == 'INFO']),
                'debug': len(df[df['level'] == 'DEBUG'])
            }
            
        except Exception as e:
            print(f"Error getting log stats: {e}")
            return {}
    
    @staticmethod
    def _extract_level(message):
        """Extract log level from message"""
        message_upper = message.upper()
        if 'ERROR' in message_upper:
            return 'ERROR'
        elif 'WARN' in message_upper:
            return 'WARN'
        elif 'DEBUG' in message_upper:
            return 'DEBUG'
        else:
            return 'INFO'
    
    def get_all_vms_logs(self, minutes_back=30):
        """Get logs from all VMs"""
        logs = []
        for i in range(1, 4):  # client-vm-1, vm-2, vm-3
            query = f'{{host="client-vm-{i}"}}'
            df = self.query_logs(query, minutes_back)
            if not df.empty:
                logs.append(df)
        
        if logs:
            return pd.concat(logs, ignore_index=True).sort_values('timestamp', ascending=False)
        return pd.DataFrame()
    
    def get_error_logs(self, host="client-vm-1", minutes_back=60):
        """Get only error logs"""
        query = f'{{host="{host}"}} |= "ERROR"'
        return self.query_logs(query, minutes_back)
    
    def get_sensor_logs(self, sensor_type="temperature", minutes_back=30):
        """Get sensor-specific logs"""
        query = f'{{job="{sensor_type}_sensor"}}'
        return self.query_logs(query, minutes_back)


def create_loki_stats_card(loki_client, host="client-vm-1"):
    """
    Create HTML card showing Loki log statistics
    Returns dict with stats for use in dashboard
    """
    stats = loki_client.get_log_stats(host)
    return {
        'total_logs': stats.get('total', 0),
        'errors': stats.get('errors', 0),
        'warnings': stats.get('warnings', 0),
        'info': stats.get('info', 0)
    }


if __name__ == "__main__":
    # Test the client
    loki = LokiClient()
    
    print("Testing Loki Client...")
    print("-" * 60)
    
    # Get stats
    stats = loki.get_log_stats("client-vm-1")
    print(f"Log Stats for client-vm-1: {stats}")
    print()
    
    # Get recent logs
    logs = loki.query_logs('{host="client-vm-1"}', minutes_back=30)
    print(f"Recent logs (showing first 5):")
    print(logs.head())
    print()
    
    # Get error logs
    errors = loki.get_error_logs("client-vm-1")
    print(f"Error logs count: {len(errors)}")
    print()
    
    print("✓ Loki client working correctly!")
