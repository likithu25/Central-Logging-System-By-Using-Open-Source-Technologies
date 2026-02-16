"""
Elasticsearch Integration Module for Dashboard
Fetches and processes data from Elasticsearch for display in dashboard
"""

import json
import os
from datetime import datetime, timedelta, timezone
from elasticsearch import Elasticsearch
import pandas as pd


class ElasticsearchClient:
    """Client for querying Elasticsearch data"""
    
    def __init__(self, config_path=None):
        """
        Initialize Elasticsearch client
        
        Args:
            config_path: Path to cloud_config.json (defaults to ../config/cloud_config.json)
        """
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'cloud_config.json')
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.es = Elasticsearch(
            config['elasticsearch_url'],
            api_key=config['api_key'],
            verify_certs=True,
            request_timeout=30
        )
        self.index_name = config['index_name']
        self.config = config
        
    def query_data(self, query_body=None, hours_back=1, size=1000):
        """
        Query Elasticsearch for data
        
        Args:
            query_body: Custom Elasticsearch query (dict). If None, uses default time range query
            hours_back: How many hours back to query (used if query_body is None)
            size: Maximum number of results to return
            
        Returns:
            DataFrame with all document fields
        """
        try:
            if query_body is None:
                query_body = {
                    "query": {
                        "range": {
                            "@timestamp": {
                                "gte": f"now-{hours_back}h",
                                "lte": "now"
                            }
                        }
                    },
                    "size": size,
                    "sort": [{"@timestamp": {"order": "desc"}}]
                }
            
            result = self.es.search(index=self.index_name, body=query_body)
            hits = result['hits']['hits']
            
            if not hits:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame([hit['_source'] for hit in hits])
            if '@timestamp' in df.columns:
                df['@timestamp'] = pd.to_datetime(df['@timestamp'])
            
            return df
            
        except Exception as e:
            print(f"Error querying Elasticsearch: {e}")
            return pd.DataFrame()
    
    def get_sensor_data(self, sensor_type, hours_back=1):
        """
        Get data for a specific sensor type
        
        Args:
            sensor_type: Type of sensor (e.g., 'temperature', 'humidity', 'motion')
            hours_back: How many hours back to query
            
        Returns:
            DataFrame with sensor data
        """
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": f"now-{hours_back}h",
                                    "lte": "now"
                                }
                            }
                        },
                        {
                            "term": {
                                "sensor_type": sensor_type
                            }
                        }
                    ]
                }
            },
            "size": 1000,
            "sort": [{"@timestamp": {"order": "desc"}}]
        }
        
        return self.query_data(query_body=query)
    
    def get_logs_by_type(self, log_type, hours_back=1):
        """
        Get logs by type (e.g., 'application', 'security')
        
        Args:
            log_type: Type of log ('application', 'security', etc.)
            hours_back: How many hours back to query
            
        Returns:
            DataFrame with log data
        """
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": f"now-{hours_back}h",
                                    "lte": "now"
                                }
                            }
                        },
                        {
                            "term": {
                                "log_type": log_type
                            }
                        }
                    ]
                }
            },
            "size": 1000,
            "sort": [{"@timestamp": {"order": "desc"}}]
        }
        
        return self.query_data(query_body=query)
    
    def get_network_devices(self, hours_back=1):
        """
        Get network device data
        
        Args:
            hours_back: How many hours back to query
            
        Returns:
            DataFrame with network device data
        """
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": f"now-{hours_back}h",
                                    "lte": "now"
                                }
                            }
                        },
                        {
                            "terms": {
                                "device_type": ["router", "switch", "firewall", "hub", "modem"]
                            }
                        }
                    ]
                }
            },
            "size": 1000,
            "sort": [{"@timestamp": {"order": "desc"}}]
        }
        
        return self.query_data(query_body=query)
    
    def get_system_health(self, hours_back=1):
        """
        Get system health metrics
        
        Args:
            hours_back: How many hours back to query
            
        Returns:
            DataFrame with system health data
        """
        return self.get_sensor_data('system_health', hours_back)
    
    def get_recent_alerts(self, minutes_back=10):
        """
        Get recent alert data based on threshold violations
        
        Args:
            minutes_back: How many minutes back to query
            
        Returns:
            DataFrame with alert data
        """
        query = {
            "query": {
                "range": {
                    "@timestamp": {
                        "gte": f"now-{minutes_back}m",
                        "lte": "now"
                    }
                }
            },
            "size": 100,
            "sort": [{"@timestamp": {"order": "desc"}}]
        }
        
        return self.query_data(query_body=query)
    
    def search_data(self, search_term, hours_back=1):
        """
        Search data by keyword across multiple fields
        
        Args:
            search_term: Search keyword
            hours_back: How many hours back to query
            
        Returns:
            DataFrame with matching data
        """
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": f"now-{hours_back}h",
                                    "lte": "now"
                                }
                            }
                        },
                        {
                            "multi_match": {
                                "query": search_term,
                                "fields": [
                                    "sensor_type",
                                    "device_type",
                                    "device_name",
                                    "log_type",
                                    "event_type",
                                    "location",
                                    "sensor_id",
                                    "application",
                                    "message"
                                ],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        }
                    ]
                }
            },
            "size": 1000,
            "sort": [{"@timestamp": {"order": "desc"}}]
        }
        
        return self.query_data(query_body=query)
    
    def get_stats(self, hours_back=1):
        """
        Get overall statistics
        
        Args:
            hours_back: How many hours back to query
            
        Returns:
            Dict with statistics
        """
        try:
            df = self.query_data(hours_back=hours_back)
            
            if df.empty:
                return {
                    'total_records': 0,
                    'sensor_types': {},
                    'log_types': {},
                    'device_types': {}
                }
            
            stats = {
                'total_records': len(df),
                'sensor_types': {},
                'log_types': {},
                'device_types': {}
            }
            
            if 'sensor_type' in df.columns:
                stats['sensor_types'] = df['sensor_type'].value_counts().to_dict()
            
            if 'log_type' in df.columns:
                stats['log_types'] = df['log_type'].value_counts().to_dict()
            
            if 'device_type' in df.columns:
                stats['device_types'] = df['device_type'].value_counts().to_dict()
            
            return stats
            
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
    
    def test_connection(self):
        """
        Test Elasticsearch connection
        
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            info = self.es.info()
            return True, f"Connected to: {info['cluster_name']}"
        except Exception as e:
            return False, f"Connection failed: {e}"


def create_elasticsearch_stats_card(es_client, hours_back=1):
    """
    Create stats card from Elasticsearch data
    Returns dict with stats for use in dashboard
    """
    stats = es_client.get_stats(hours_back)
    return {
        'total_records': stats.get('total_records', 0),
        'sensor_types': stats.get('sensor_types', {}),
        'log_types': stats.get('log_types', {}),
        'device_types': stats.get('device_types', {})
    }


if __name__ == "__main__":
    # Test the client
    es_client = ElasticsearchClient()
    
    print("Testing Elasticsearch Client...")
    print("-" * 60)
    
    # Test connection
    success, message = es_client.test_connection()
    print(f"Connection: {message}")
    print()
    
    if success:
        # Get stats
        stats = es_client.get_stats(hours_back=1)
        print(f"Stats (last hour): {stats}")
        print()
        
        # Get recent data
        df = es_client.query_data(hours_back=1, size=10)
        print(f"Recent data (showing first 5):")
        print(df.head())
        print()
        
        # Get temperature data
        temp_data = es_client.get_sensor_data('temperature', hours_back=1)
        print(f"Temperature records: {len(temp_data)}")
        print()
        
        # Get application logs
        app_logs = es_client.get_logs_by_type('application', hours_back=1)
        print(f"Application logs: {len(app_logs)}")
        print()
        
        print("✓ Elasticsearch client working correctly!")
    else:
        print("✗ Cannot test further - connection failed")

