from flask import Flask, request, jsonify
from flask_cors import CORS
from flask import request, abort
import threading
import requests
import time


app = Flask(__name__)
CORS(app)  # Allow Chrome extension cross-origin requests

received_data = []
merge_command_queue = []
add_command_queue = []
seen_merges = set()
phase = "merge" 
def sorted_elements(a: str, b: str):
    return tuple(sorted([a, b], key=lambda x: x.lower()))
list_items=["Water","Fire","Wind","Earth"]



def scan_and_queue_merges():
    print("🌀 Merge scanner started")
    idle_cycles = 0

    while True:
        current_len = len(list_items)
        new_found = False

        for i in range(current_len):
            for j in range(current_len):
                first, second = sorted_elements(list_items[i], list_items[j])
                pair = (first, second)
                if pair not in seen_merges:
                    seen_merges.add(pair)
                    merge_command_queue.append({
                        "action": "MERGE",
                        "data": {
                            "first": first,
                            "second": second,
                            "saveId": 0
                        }
                    })
                    new_found = True

        if not new_found:
            idle_cycles += 1
            if idle_cycles >= 5:
                print("✅ Merge scan complete. Sleeping...")
        else:
            idle_cycles = 0

        time.sleep(1)



threading.Thread(target=scan_and_queue_merges, daemon=True).start()

@app.route('/merged_result', methods=['POST'])
def merged_result():
    data = request.json
    print("🧬 Received merged result from extension:", data)

    item_name = data.get("text")
    if item_name and item_name not in list_items:
        print(f"✅ New item added to list_items: {item_name}")

        # Queue it for DB insertion via extension
        add_command_queue.append({
            "action": "ADD_ITEM",
            "data": {
                "id": 999,
                "saveId": 0,
                "text": data["text"],
                "emoji": data.get("emoji", "❓"),
                "recipes": data.get("recipes", [])
            }
        })
        list_items.append(item_name)
        phase = "add"
    else:
        print(f"⚠️ Item '{item_name}' already exists. Skipping ADD_ITEM.")
        phase = "merge"
    return jsonify({"status": "received"}), 200



@app.route('/get_command', methods=['GET'])
def get_command():
    print("📥 Extension requested command")
    if request.content_length and request.content_length > 1_000_000:
        abort(413)  # Payload Too Large
    data = request.get_data()
    if pause==False:
        if add_command_queue:
            print("add_command_queue",add_command_queue)
            command = add_command_queue.pop(0)
            print("📤 Sent ADD_ITEM:", command)
            return jsonify(command)
        if merge_command_queue:
            command = merge_command_queue.pop(0)
            print("📤 Sent MERGE:", command)
            return jsonify(command)
    return jsonify({"status": "no_command"}), 200




def run_server():
    app.run(port=5000)



# Start Flask in background thread
pause=False
def user_inputs():
    global pause
    while 1:
        x=str(input())
        if x=="a":
            pause =True
            print("Paused")
        if x=="r":
            pause =False
            print("active")

threading.Thread(target=user_inputs, daemon=True).start()
threading.Thread(target=run_server, daemon=True).start()

while 1:
    pass