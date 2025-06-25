
from flask import Flask, request, jsonify
import os
import requests
import threading
import time

app = Flask(__name__)

NODE_ID = int(os.getenv("NODE_ID", 0))
TOTAL_NODES = 3
vector_clock = [0] * TOTAL_NODES
store = {}
buffer = []

PEERS = {
    0: "http://node1:5000",
    1: "http://node2:5000",
    2: "http://node3:5000"
}

def merge(vc1, vc2):
    return [max(a, b) for a, b in zip(vc1, vc2)]

def is_causally_ready(incoming_vc, local_vc, sender_id):
    for i in range(TOTAL_NODES):
        if i == sender_id:
            if incoming_vc[i] != local_vc[i] + 1:
                return False
        else:
            if incoming_vc[i] > local_vc[i]:
                return False
    return True

@app.route('/put', methods=['POST'])
def put():
    global vector_clock
    data = request.json
    key = data['key']
    value = data['value']

    vector_clock[NODE_ID] += 1
    store[key] = (value, vector_clock[:])

    for peer_id, peer_url in PEERS.items():
        if peer_id != NODE_ID:
            try:
                requests.post(f"{peer_url}/replicate", json={
                    "key": key,
                    "value": value,
                    "vc": vector_clock[:],
                    "sender_id": NODE_ID
                })
            except Exception as e:
                print(f"Failed to replicate to node {peer_id}: {e}")

    return jsonify({"msg": "Value stored with causal consistency", "vc": vector_clock})

@app.route('/replicate', methods=['POST'])
def replicate():
    global store, vector_clock
    data = request.json
    key, value, vc, sender_id = data["key"], data["value"], data["vc"], data["sender_id"]

    if is_causally_ready(vc, vector_clock, sender_id):
        vector_clock = merge(vector_clock, vc)
        store[key] = (value, vc)
        return jsonify({"msg": "Replicated"})
    else:
        buffer.append(data)
        return jsonify({"msg": "Buffered due to causal dependency"})

@app.route('/get', methods=['GET'])
def get():
    key = request.args.get('key')
    if key in store:
        return jsonify({"key": key, "value": store[key][0], "vc": store[key][1]})
    return jsonify({"msg": "Key not found"}), 404

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "store": store,
        "vc": vector_clock,
        "buffered_msgs": len(buffer)
    })

def buffer_check():
    while True:
        for data in buffer[:]:
            if is_causally_ready(data["vc"], vector_clock, data["sender_id"]):
                store[data["key"]] = (data["value"], data["vc"])
                vector_clock = merge(vector_clock, data["vc"])
                buffer.remove(data)
        time.sleep(1)

if __name__ == '__main__':
    threading.Thread(target=buffer_check, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
