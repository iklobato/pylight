"""HTTP client utilities for API testing."""

import requests
import logging
from typing import Dict, Any, Optional
import time


class APIClient:
    """Client for making HTTP requests to Pylight API."""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> requests.Response:
        """Make GET request."""
        url = f"{self.base_url}{endpoint}"
        return self.session.get(url, params=params, headers=headers, timeout=self.timeout)
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> requests.Response:
        """Make POST request."""
        url = f"{self.base_url}{endpoint}"
        return self.session.post(url, data=data, json=json, headers=headers, timeout=self.timeout)
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> requests.Response:
        """Make PUT request."""
        url = f"{self.base_url}{endpoint}"
        return self.session.put(url, data=data, json=json, headers=headers, timeout=self.timeout)
    
    def delete(self, endpoint: str, headers: Optional[Dict[str, str]] = None) -> requests.Response:
        """Make DELETE request."""
        url = f"{self.base_url}{endpoint}"
        return self.session.delete(url, headers=headers, timeout=self.timeout)
    
    def health_check(self) -> bool:
        """Check if API is healthy."""
        try:
            response = self.get("/health")
            return response.status_code == 200
        except Exception as e:
            return False
    
    def wait_for_ready(self, timeout: int = 60, interval: int = 2) -> bool:
        """Wait for API to be ready with detailed error reporting."""
        import logging
        logger = logging.getLogger(__name__)
        
        start_time = time.time()
        attempt = 0
        last_error = None
        
        while time.time() - start_time < timeout:
            attempt += 1
            elapsed = time.time() - start_time
            
            try:
                response = self.get("/health")
                if response.status_code == 200:
                    logger.info(f"API ready after {elapsed:.1f}s ({attempt} attempts)")
                    return True
                else:
                    last_error = f"Health check returned status {response.status_code}"
                    logger.debug(f"Attempt {attempt}: {last_error}")
            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection refused: {str(e)}"
                logger.debug(f"Attempt {attempt}: {last_error}")
            except requests.exceptions.Timeout as e:
                last_error = f"Request timeout: {str(e)}"
                logger.debug(f"Attempt {attempt}: {last_error}")
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.debug(f"Attempt {attempt}: {last_error}")
            
            # Log progress every 10 seconds
            if attempt % (10 // interval) == 0:
                logger.info(f"Waiting for API... ({elapsed:.1f}s elapsed, attempt {attempt})")
            
            time.sleep(interval)
        
        # Timeout reached - provide detailed error message
        error_msg = (
            f"API did not become ready within {timeout}s after {attempt} attempts.\n"
            f"Base URL: {self.base_url}\n"
            f"Last error: {last_error or 'Unknown error'}\n"
            f"To troubleshoot:\n"
            f"  1. Check if Pylight is running: curl {self.base_url}/health\n"
            f"  2. Check Pylight logs: tail -50 tests/external_db/reports/pylight.stderr.log\n"
            f"  3. Verify database connection in Pylight config"
        )
        logger.error(error_msg)
        return False
    
    def get_list(self, table_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get list of items from a table."""
        response = self.get(f"/api/{table_name}", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_item(self, table_name: str, item_id: int) -> Dict[str, Any]:
        """Get single item by ID."""
        response = self.get(f"/api/{table_name}/{item_id}")
        response.raise_for_status()
        return response.json()
    
    def create_item(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new item."""
        response = self.post(f"/api/{table_name}", json=data)
        response.raise_for_status()
        return response.json()
    
    def update_item(self, table_name: str, item_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing item."""
        response = self.put(f"/api/{table_name}/{item_id}", json=data)
        response.raise_for_status()
        return response.json()
    
    def delete_item(self, table_name: str, item_id: int) -> bool:
        """Delete item."""
        response = self.delete(f"/api/{table_name}/{item_id}")
        return response.status_code in [200, 204]

