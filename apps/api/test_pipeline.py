import requests
import json
import time

BASE_URL = 'http://127.0.0.1:8000'

scene_2_id = "SCENE_5622c942"

print("\nCreating Temporal Pair with SCENE_9e8c86c9 and", scene_2_id)
r = requests.post(f"{BASE_URL}/temporal/pair", json={
    "before_scene_id": "SCENE_9e8c86c9",
    "after_scene_id": scene_2_id
})
pair_res = r.json()
print("Pair result:", pair_res)

if pair_res.get('status') != 'success':
    print("Failed to create pair. Trying reverse order...")
    r = requests.post(f"{BASE_URL}/temporal/pair", json={
        "before_scene_id": scene_2_id,
        "after_scene_id": "SCENE_9e8c86c9"
    })
    pair_res = r.json()
    print("Reverse Pair result:", pair_res)

if 'pair_id' not in pair_res:
    print("Still failed:", pair_res)
    exit(1)

pair_id = pair_res['pair_id']

print("\nRunning Change Detection on Pair", pair_id)
r = requests.post(f"{BASE_URL}/change-detection/run", json={
    "pair_id": pair_id
})
print("Detection result:", r.json())
