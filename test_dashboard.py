import asyncio
import sys
import subprocess

try:
    from fastapi.testclient import TestClient
    from main import app

    def test():
        client = TestClient(app)
        response = client.get("/api/metrics")
        print(f"Metrics Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Metrics keys: {list(data.keys())}")
            print(f"Total spent: {data.get('total_spent')}")
            print(f"Hit rate: {data.get('hit_rate')}")
            print(f"Queries count: {len(data.get('queries', []))}")
        else:
            print(response.text)

    if __name__ == "__main__":
        test()
except ImportError as e:
    print(f"Import Error: {e}")
