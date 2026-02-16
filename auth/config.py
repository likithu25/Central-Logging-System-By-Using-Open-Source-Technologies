"""
Configuration file for authentication service
"""
import os

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
    DB_NAME = os.environ.get('DB_NAME', 'iot_project')
    JWT_EXPIRATION_HOURS = 24
    
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    MONGO_URI = 'mongodb://localhost:27017/'
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Use environment variables for production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    MONGO_URI = os.environ.get('MONGO_URI')
    
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in production")
    if not MONGO_URI:
        raise ValueError("MONGO_URI must be set in production")

class TestConfig(Config):
    """Test configuration"""
    TESTING = True
    DB_NAME = 'iot_project_test'
    
# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'test': TestConfig,
    'default': DevelopmentConfig
}
