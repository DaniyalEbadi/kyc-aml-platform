"""
Performance tests using Locust
Run with: locust -f tests/performance/locustfile.py --host=http://localhost:8000
"""
from locust import HttpUser, task, between, constant
import random
import json


class KYCUser(HttpUser):
    """Simulates a KYC platform user"""
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login on start"""
        self.token = None
        self.login()
    
    def login(self):
        """Authenticate and store token"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "admin@parsheid.ir",
            "password": "admin123"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            print(f"Login failed: {response.status_code}")
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}


class APIUser(KYCUser):
    """User that makes API calls"""
    
    @task(10)
    def health_check(self):
        """Health check endpoint"""
        self.client.get("/api/v1/health")
    
    @task(5)
    def get_dashboard_analytics(self):
        """Get dashboard analytics"""
        self.client.get("/api/v1/analytics", headers=self.get_headers())
    
    @task(8)
    def list_applications(self):
        """List applications with pagination"""
        self.client.get("/api/v1/applications?page=1&page_size=20", headers=self.get_headers())
    
    @task(5)
    def list_customers(self):
        """List customers"""
        self.client.get("/api/v1/customers?page=1&page_size=20", headers=self.get_headers())
    
    @task(3)
    def list_cases(self):
        """List cases"""
        self.client.get("/api/v1/cases?page=1&page_size=20", headers=self.get_headers())
    
    @task(3)
    def get_notifications(self):
        """Get notifications"""
        self.client.get("/api/v1/notifications?page=1&page_size=20", headers=self.get_headers())
    
    @task(2)
    def search_global(self):
        """Global search"""
        queries = ["APP-1001", "محمد", "0012345679", "CASE-00001"]
        query = random.choice(queries)
        self.client.get(f"/api/v1/search?q={query}", headers=self.get_headers())
    
    @task(2)
    def get_policies(self):
        """Get policies"""
        self.client.get("/api/v1/policies", headers=self.get_headers())
    
    @task(1)
    def get_audit_events(self):
        """Get audit events"""
        self.client.get("/api/v1/audit?page=1&page_size=50", headers=self.get_headers())
    
    @task(1)
    def get_application_detail(self):
        """Get application detail"""
        # Would need actual application IDs
        pass


class ApplicantUser(KYCUser):
    """Simulates an applicant user"""
    
    def on_start(self):
        self.token = None
        response = self.client.post("/api/v1/auth/login", json={
            "email": "applicant@test.com",
            "password": "password123"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
    
    @task(3)
    def create_application(self):
        """Create new application"""
        response = self.client.post("/api/v1/applications", json={}, headers=self.get_headers())
        if response.status_code == 200:
            self.current_app_id = response.json()["id"]
    
    @task(5)
    def update_application(self):
        """Update application info"""
        if hasattr(self, 'current_app_id'):
            self.client.put(
                f"/api/v1/applications/{self.current_app_id}",
                json={
                    "first_name": "Test",
                    "last_name": "User",
                    "national_id": "0012345679",
                    "occupation": "مهندس",
                },
                headers=self.get_headers()
            )
    
    @task(2)
    def upload_document(self):
        """Upload document"""
        if hasattr(self, 'current_app_id'):
            files = {"file": ("test.jpg", b"fake image data", "image/jpeg")}
            data = {"app_id": self.current_app_id, "doc_type": "national_id"}
            self.client.post("/api/v1/documents/upload", files=files, data=data, headers=self.get_headers())
    
    @task(2)
    def face_verification(self):
        """Face verification"""
        if hasattr(self, 'current_app_id'):
            files = {"selfie": ("selfie.jpg", b"fake selfie", "image/jpeg")}
            data = {"app_id": self.current_app_id}
            self.client.post("/api/v1/verification/face", files=files, data=data, headers=self.get_headers())
    
    @task(1)
    def submit_application(self):
        """Submit application"""
        if hasattr(self, 'current_app_id'):
            self.client.post(
                f"/api/v1/applications/{self.current_app_id}/submit",
                headers=self.get_headers()
            )


class HighLoadUser(KYCUser):
    """User for high load testing"""
    wait_time = constant(0.1)  # Very fast requests
    
    @task(1)
    def rapid_requests(self):
        """Make rapid requests to test rate limiting"""
        endpoints = [
            "/api/v1/health",
            "/api/v1/analytics",
            "/api/v1/applications?page=1&page_size=20",
            "/api/v1/customers?page=1&page_size=20",
        ]
        endpoint = random.choice(endpoints)
        self.client.get(endpoint, headers=self.get_headers())


# Custom load shapes
from locust import LoadTestShape

class StepLoadShape(LoadTestShape):
    """Step load shape for gradual ramp up"""
    step_time = 60  # 1 minute per step
    step_users = 10  # Add 10 users per step
    max_users = 100
    
    def tick(self):
        run_time = self.get_run_time()
        current_step = int(run_time / self.step_time)
        target_users = min(current_step * self.step_users, self.max_users)
        
        if target_users == 0:
            target_users = 1
        
        return (target_users, 5)  # (users, spawn_rate)


class SpikeLoadShape(LoadTestShape):
    """Spike load shape for stress testing"""
    stages = [
        {"duration": 60, "users": 10, "spawn_rate": 2},
        {"duration": 120, "users": 50, "spawn_rate": 10},
        {"duration": 60, "users": 100, "spawn_rate": 20},
        {"duration": 120, "users": 50, "spawn_rate": 10},
        {"duration": 60, "users": 10, "spawn_rate": 5},
    ]
    
    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        return None


class SoakTestShape(LoadTestShape):
    """Long-running soak test"""
    duration = 3600  # 1 hour
    users = 20
    spawn_rate = 2
    
    def tick(self):
        if self.get_run_time() < self.duration:
            return (self.users, self.spawn_rate)
        return None