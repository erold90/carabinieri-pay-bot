# utils/health_check.py
"""Health check per monitoraggio"""
import psutil
import os
from database.connection import test_connection

def get_health_status():
    """Ottieni stato salute del bot"""
    status = {
        'status': 'healthy',
        'checks': {}
    }
    
    # Check database
    status['checks']['database'] = test_connection()
    
    # Check memoria
    memory = psutil.virtual_memory()
    status['checks']['memory_percent'] = memory.percent
    status['checks']['memory_available'] = memory.available
    
    # Check CPU
    status['checks']['cpu_percent'] = psutil.cpu_percent(interval=1)
    
    # Overall status
    if not status['checks']['database']:
        status['status'] = 'unhealthy'
    elif memory.percent > 90:
        status['status'] = 'degraded'
    
    return status
