"""
CloudSim API Client
Handles all communication with the FastAPI backend
"""
import requests
from typing import Optional, Dict, Any, List
from PySide6.QtCore import QObject, Signal


class APIClient(QObject):
    """Client for CloudSim backend API"""
    
    # Signals for async operations
    request_started = Signal()
    request_finished = Signal()
    error_occurred = Signal(str)
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__()
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make HTTP request to backend"""
        url = f"{self.base_url}{endpoint}"
        self.request_started.emit()
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            self.request_finished.emit()
            return response.json() if response.content else {}
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to CloudSim backend. Is it running on port 8000?"
            self.error_occurred.emit(error_msg)
            self.request_finished.emit()
            return None
        except requests.exceptions.HTTPError as e:
            error_msg = f"API Error: {e.response.status_code} - {e.response.text}"
            self.error_occurred.emit(error_msg)
            self.request_finished.emit()
            return None
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.error_occurred.emit(error_msg)
            self.request_finished.emit()
            return None
    
    # EC2 API methods
    def list_instances(self, limit: int = 100, offset: int = 0) -> Optional[List[Dict]]:
        """List EC2 instances"""
        response = self._request("GET", f"/api/v1/instances?limit={limit}&offset={offset}")
        return response.get("instances", []) if response else None
    
    def start_instance(self, instance_id: str) -> bool:
        """Start an EC2 instance"""
        response = self._request("POST", f"/api/v1/instances/{instance_id}/start")
        return response is not None
    
    def stop_instance(self, instance_id: str) -> bool:
        """Stop an EC2 instance"""
        response = self._request("POST", f"/api/v1/instances/{instance_id}/stop")
        return response is not None
    
    def terminate_instance(self, instance_id: str) -> bool:
        """Terminate an EC2 instance"""
        response = self._request("DELETE", f"/api/v1/instances/{instance_id}")
        return response is not None
    
    def create_instance(self, data: Dict[str, Any]) -> Optional[Dict]:
        """Create new EC2 instance"""
        response = self._request("POST", "/api/v1/instances", json=data)
        return response
    
    # S3 API methods
    def list_buckets(self) -> Optional[List[Dict]]:
        """List S3 buckets"""
        response = self._request("GET", "/api/v1/s3/buckets")
        return response.get("buckets", []) if response else None
    
    def create_bucket(self, bucket_name: str) -> bool:
        """Create S3 bucket"""
        response = self._request("POST", "/api/v1/s3/buckets", json={"bucket_name": bucket_name})
        return response is not None
    
    def delete_bucket(self, bucket_name: str) -> bool:
        """Delete S3 bucket"""
        response = self._request("DELETE", f"/api/v1/s3/buckets/{bucket_name}")
        return response is not None
    
    def list_objects(self, bucket_name: str, prefix: str = "") -> Optional[List[Dict]]:
        """List objects in S3 bucket"""
        response = self._request("GET", f"/api/v1/s3/buckets/{bucket_name}/objects?prefix={prefix}")
        return response.get("objects", []) if response else None
    
    def upload_object(self, bucket_name: str, key: str, file_path: str) -> bool:
        """Upload object to S3 bucket"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (key, f)}
                url = f"{self.base_url}/api/v1/s3/buckets/{bucket_name}/objects/{key}"
                response = self.session.put(url, files=files)
                response.raise_for_status()
                return True
        except Exception as e:
            self.error_occurred.emit(f"Upload failed: {str(e)}")
            return False
    
    def download_object(self, bucket_name: str, key: str, save_path: str) -> bool:
        """Download object from S3 bucket"""
        try:
            url = f"{self.base_url}/api/v1/s3/buckets/{bucket_name}/objects/{key}"
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            self.error_occurred.emit(f"Download failed: {str(e)}")
            return False
    
    def delete_object(self, bucket_name: str, key: str) -> bool:
        """Delete object from S3 bucket"""
        response = self._request("DELETE", f"/api/v1/s3/buckets/{bucket_name}/objects/{key}")
        return response is not None
    
    # IAM API methods
    def list_users(self) -> Optional[List[Dict]]:
        """List IAM users"""
        response = self._request("GET", "/api/v1/iam/users")
        return response.get("users", []) if response else None
    
    def create_user(self, data: Dict[str, Any]) -> Optional[Dict]:
        """Create IAM user"""
        return self._request("POST", "/api/v1/iam/users", json=data)
    
    def delete_user(self, username: str) -> bool:
        """Delete IAM user"""
        response = self._request("DELETE", f"/api/v1/iam/users/{username}")
        return response is not None
    
    # Lambda API methods
    def list_functions(self) -> Optional[List[Dict]]:
        """List Lambda functions"""
        response = self._request("GET", "/api/v1/lambda/functions")
        return response.get("functions", []) if response else None
    
    def create_function(self, data: Dict[str, Any]) -> Optional[Dict]:
        """Create Lambda function"""
        return self._request("POST", "/api/v1/lambda/functions", json=data)
    
    def invoke_function(self, function_name: str, payload: Dict[str, Any]) -> Optional[Dict]:
        """Invoke Lambda function"""
        return self._request("POST", f"/api/v1/lambda/functions/{function_name}/invoke", json=payload)
    
    def delete_function(self, function_name: str) -> bool:
        """Delete Lambda function"""
        response = self._request("DELETE", f"/api/v1/lambda/functions/{function_name}")
        return response is not None
    
    # RDS API methods
    def list_db_instances(self) -> Optional[List[Dict]]:
        """List RDS database instances"""
        response = self._request("GET", "/api/v1/rds/instances")
        return response.get("instances", []) if response else None
    
    def create_db_instance(self, data: Dict[str, Any]) -> Optional[Dict]:
        """Create RDS database instance"""
        return self._request("POST", "/api/v1/rds/instances", json=data)
    
    def delete_db_instance(self, db_instance_id: str) -> bool:
        """Delete RDS database instance"""
        response = self._request("DELETE", f"/api/v1/rds/instances/{db_instance_id}")
        return response is not None
