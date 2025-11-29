"""Kubernetes database deployment utilities for Helm chart testing."""

import subprocess
import time
import yaml
from typing import Optional, Dict, Any
from pathlib import Path


class KubernetesDatabase:
    """Manages PostgreSQL database in Kubernetes cluster for testing."""
    
    def __init__(
        self,
        namespace: str = "test-db",
        database: str = "pylight_test",
        user: str = "postgres",
        password: str = "postgres",
        service_name: str = "postgres"
    ):
        self.namespace = namespace
        self.database = database
        self.user = user
        self.password = password
        self.service_name = service_name
        self.connection_string = f"postgresql://{user}:{password}@{service_name}.{namespace}.svc.cluster.local:5432/{database}"
    
    def create_namespace(self) -> bool:
        """Create Kubernetes namespace."""
        try:
            subprocess.run(
                ["kubectl", "create", "namespace", self.namespace],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"Created namespace: {self.namespace}")
            return True
        except subprocess.CalledProcessError as e:
            if "already exists" in e.stderr:
                print(f"Namespace {self.namespace} already exists")
                return True
            print(f"Error creating namespace: {e.stderr}")
            return False
    
    def deploy(self, timeout: int = 300) -> bool:
        """Deploy PostgreSQL to Kubernetes cluster."""
        if not self.create_namespace():
            return False
        
        # Create ConfigMap
        configmap = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": "postgres-config", "namespace": self.namespace},
            "data": {
                "POSTGRES_DB": self.database,
                "POSTGRES_USER": self.user,
                "POSTGRES_PASSWORD": self.password
            }
        }
        
        # Create PersistentVolumeClaim
        pvc = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"name": "postgres-pvc", "namespace": self.namespace},
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "resources": {"requests": {"storage": "1Gi"}}
            }
        }
        
        # Create Deployment
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": "postgres", "namespace": self.namespace},
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": "postgres"}},
                "template": {
                    "metadata": {"labels": {"app": "postgres"}},
                    "spec": {
                        "containers": [{
                            "name": "postgres",
                            "image": "postgres:15-alpine",
                            "ports": [{"containerPort": 5432}],
                            "envFrom": [{"configMapRef": {"name": "postgres-config"}}],
                            "volumeMounts": [{
                                "name": "postgres-storage",
                                "mountPath": "/var/lib/postgresql/data"
                            }]
                        }],
                        "volumes": [{
                            "name": "postgres-storage",
                            "persistentVolumeClaim": {"claimName": "postgres-pvc"}
                        }]
                    }
                }
            }
        }
        
        # Create Service
        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": self.service_name, "namespace": self.namespace},
            "spec": {
                "selector": {"app": "postgres"},
                "ports": [{"port": 5432, "targetPort": 5432}],
                "type": "ClusterIP"
            }
        }
        
        # Apply resources
        resources = [configmap, pvc, deployment, service]
        for resource in resources:
            yaml_content = yaml.dump(resource)
            result = subprocess.run(
                ["kubectl", "apply", "-f", "-"],
                input=yaml_content,
                text=True,
                capture_output=True
            )
            if result.returncode != 0:
                print(f"Error applying resource: {result.stderr}")
                return False
        
        print(f"Deployed PostgreSQL to namespace: {self.namespace}")
        
        # Wait for deployment to be ready
        return self.wait_for_ready(timeout)
    
    def wait_for_ready(self, timeout: int = 300) -> bool:
        """Wait for database pod to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = subprocess.run(
                ["kubectl", "wait", "--for=condition=ready", "pod", "-l", "app=postgres", "-n", self.namespace, "--timeout=30s"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"Database pod in {self.namespace} is ready")
                return True
            time.sleep(5)
        
        print(f"Timeout waiting for database pod in {self.namespace}")
        return False
    
    def is_running(self) -> bool:
        """Check if database pod is running."""
        result = subprocess.run(
            ["kubectl", "get", "pods", "-l", "app=postgres", "-n", self.namespace, "--no-headers"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return False
        return "Running" in result.stdout
    
    def get_connection_string(self) -> str:
        """Get database connection string."""
        return self.connection_string
    
    def cleanup(self) -> bool:
        """Delete namespace and all resources."""
        try:
            subprocess.run(
                ["kubectl", "delete", "namespace", self.namespace],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"Deleted namespace: {self.namespace}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error deleting namespace: {e.stderr}")
            return False


def create_kubernetes_database(
    namespace: str = "test-db",
    **kwargs
) -> KubernetesDatabase:
    """Factory function to create and deploy Kubernetes database."""
    db = KubernetesDatabase(namespace=namespace, **kwargs)
    if db.deploy():
        return db
    raise RuntimeError(f"Failed to deploy Kubernetes database in namespace: {namespace}")

