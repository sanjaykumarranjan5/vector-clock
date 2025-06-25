import requests
import time

nodes = {
    "node1": "http://localhost:5001",
    "node2": "http://localhost:5002",
    "node3": "http://localhost:5003"
}

print("\n🔵 Step 1: Node1 writes x=15")
resp = requests.post(f"{nodes['node1']}/put", json={"key": "x", "value": "15"})
print("Node1 put x=10:", resp.json())
time.sleep(2)

print("\n🟠 Step 2: Node2 writes x=30 (depends on previous write)")
resp = requests.post(f"{nodes['node2']}/put", json={"key": "x", "value": "30"})
print("Node2 put x=20:", resp.json())
time.sleep(2)

print("\n🟣 Step 3: Node3 writes y=90 (independent write)")
resp = requests.post(f"{nodes['node3']}/put", json={"key": "y", "value": "90"})
print("Node3 put y=99:", resp.json())
time.sleep(2)

print("\n📥 Step 4: Read 'x' and 'y' from all nodes")
for name, url in nodes.items():
    try:
        x = requests.get(f"{url}/get", params={"key": "x"}).json()
        y = requests.get(f"{url}/get", params={"key": "y"}).json()
        print(f"{name} stores:\n  x: {x}\n  y: {y}")
    except Exception as e:
        print(f"{name} failed to respond:", str(e))
