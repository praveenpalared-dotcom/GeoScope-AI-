import requests
import json

r = requests.get('http://127.0.0.1:8000/satellite/scenes/SCENE_9e8c86c9/tiles').json()
for t in r['tiles']:
    b = t['bounds']
    print(f"{t['id']}: W={b['west']} S={b['south']} E={b['east']} N={b['north']}")
    print(f"  Width: {b['east'] - b['west']} Height: {b['north'] - b['south']}")
