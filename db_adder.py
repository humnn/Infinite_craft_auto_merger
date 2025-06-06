from flask import Flask, request, jsonify
from flask_cors import CORS
from flask import request, abort
import threading
import time
import os
import json
from threading import Lock
import re

app = Flask(__name__)
CORS(app)  # Allow Chrome extension cross-origin requests
add_log_lock = Lock()
merge_log_lock = Lock()
seen_merge_log_lock = Lock()
received_data = []
phase = "merge" 
MERGE_COMMANDS_LOG = "merge_command_queue.log"
ADD_COMMANDS_LOG = "add_command_queue.log"
def pop_command_chunked(base_name, lock):
    with lock:
        dir_path = base_name
        meta_path = os.path.join(dir_path, "meta.json")
        if not os.path.exists(meta_path):
            return None

        with open(meta_path, "r") as f:
            meta = json.load(f)

        read_idx = meta["read_file_index"]
        offset = meta["read_line_offset"]

        while True:
            file_path = os.path.join(dir_path, f"{read_idx}.log")

            if not os.path.exists(file_path):
                return None  # No more data

            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if offset >= len(lines):
                # Move to next file (no deletion)
                read_idx += 1
                offset = 0
                meta["read_file_index"] = read_idx
                meta["read_line_offset"] = offset
                with open(meta_path, "w") as f:
                    json.dump(meta, f)
                continue  # 🔁 Retry with next file

            # Return line
            command = json.loads(lines[offset])
            meta["read_line_offset"] = offset + 1
            with open(meta_path, "w") as f:
                json.dump(meta, f)

            return command



def append_command_chunked(command, base_name, lock, max_lines=1000):
    with lock:
        dir_path = base_name
        os.makedirs(dir_path, exist_ok=True)  # 🔹 Create folder if not exists

        meta_path = os.path.join(dir_path, "meta.json")

        # Load or init meta
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                meta = json.load(f)
        else:
            meta = {
                "write_file_index": 1,
                "write_line_count": 0,
                "read_file_index": 1,
                "read_line_offset": 0
            }

        # Prepare file path
        idx = meta["write_file_index"]
        count = meta["write_line_count"]
        file_path = os.path.join(dir_path, f"{idx}.log")

        # Append
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(command) + "\n")

        # Rotate
        count += 1
        if count >= max_lines:
            idx += 1
            count = 0

        # Save updated meta
        meta["write_file_index"] = idx
        meta["write_line_count"] = count

        with open(meta_path, "w") as f:
            json.dump(meta, f)

def load_lines_from_file_chunks(base_dir, parser=lambda x: x.strip(), skip_bad=True):
    data = []

    meta_path = os.path.join(base_dir, "meta.json")
    if not os.path.exists(meta_path):
        print(f"⚠️ No meta.json found in {base_dir}")
        return data

    # Load meta info
    with open(meta_path, "r") as f:
        meta = json.load(f)

    start_file_index = meta.get("read_file_index", 1)
    start_line_offset = meta.get("read_line_offset", 0)

    # Match files like 1.log, 2.log inside the folder
    pattern = re.compile(r"^(\d+)\.log$")
    chunk_files = []
    for fname in os.listdir(base_dir):
        match = pattern.match(fname)
        if match:
            chunk_files.append((int(match.group(1)), fname))

    chunk_files.sort()

    for file_index, fname in chunk_files:
        # Skip older chunks
        if file_index < start_file_index:
            continue

        file_path = os.path.join(base_dir, fname)
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Apply offset only to the first file being read
        offset = start_line_offset if file_index == start_file_index else 0

        for line in lines[offset:]:
            try:
                data.append(parser(line))
            except Exception as e:
                if skip_bad:
                    print(f"⚠️ Skipped line in {fname}: {e}")

    return data

merge_command_queue = load_lines_from_file_chunks(
    base_dir="merge_command",
    parser=json.loads
)
add_command_queue = load_lines_from_file_chunks(
    base_dir="add_command",
    parser=json.loads
)
SEEN_MERGES_LOG = "seen_merges.log"



seen_merges = set(tuple(x) for x in load_lines_from_file_chunks(
    base_dir="seen_merges",
    parser=json.loads
))
def sorted_elements(a: str, b: str):
    return tuple(sorted([a, b], key=lambda x: x.lower()))


LIST_ITEMS_FILE = "list_items.txt"
DEFAULT_ITEMS = ["Water", "Fire", "Wind", "Earth"]

def load_list_items():
    existing = set()
    
    if os.path.exists(LIST_ITEMS_FILE):
        with open(LIST_ITEMS_FILE, "r", encoding="utf-8") as f:
            existing = set(line.strip() for line in f if line.strip())

    # Add missing defaults
    missing_defaults = [item for item in DEFAULT_ITEMS if item not in existing]
    if missing_defaults:
        with open(LIST_ITEMS_FILE, "a", encoding="utf-8") as f:
            for item in missing_defaults:
                f.write(f"{item}\n")
                existing.add(item)

    return list(existing)

def append_list_item(item):
    with open(LIST_ITEMS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{item}\n")

list_items = load_list_items()

def scan_and_queue_merges():
    print("🌀 Merge scanner started")
    idle_cycles = 0
    global seen_merge_log_lock , merge_log_lock

    while True:
        current_len = len(list_items)
        new_found = False

        for i in range(current_len):
            for j in range(current_len):
                first, second = sorted_elements(list_items[i], list_items[j])
                pair = (first, second)
                if pair not in seen_merges:
                    seen_merges.add(pair)
                    append_command_chunked(
                        command=pair,                    # Example: ("Fire", "Water")
                        base_name="seen_merges",        # Folder where logs are stored
                        lock=seen_merge_log_lock             # Use a dedicated lock
                    )
                    command = {
                        "action": "MERGE",
                        "data": {
                            "first": first,
                            "second": second,
                            "saveId": 0
                        }
                    }
                    merge_command_queue.append(command)
                    append_command_chunked(command, "merge_command", merge_log_lock)
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
    global add_log_lock
    data = request.json
    print("🧬 Received merged result from extension:", data)

    item_name = data.get("text")
    if item_name and item_name not in list_items:
        print(f"✅ New item added to list_items: {item_name}")

        # Queue it for DB insertion via extension
        command={
            "action": "ADD_ITEM",
            "data": {
                "discovery":data.get("isNew",""),
                "id": 999,
                "saveId": 0,
                "text": data["text"],
                "emoji": data.get("emoji", "❓"),
                "recipes": data.get("recipes", [])
            }
        }
        add_command_queue.append(command)
        append_command_chunked(command, "add_command", add_log_lock)
        list_items.append(item_name)
        append_list_item(item_name)
        phase = "add"
    else:
        print(f"⚠️ Item '{item_name}' already exists. Skipping ADD_ITEM.")
        phase = "merge"
    return jsonify({"status": "received"}), 200



@app.route('/get_command', methods=['GET'])
def get_command():
    global add_log_lock, merge_log_lock
    print("📥 Extension requested command")

    if request.content_length and request.content_length > 1_000_000:
        abort(413)

    data = request.get_data()

    if not pause:
        # ADD command
        if add_command_queue:
            print("add_command_queue", add_command_queue)
            in_memory = add_command_queue.pop(0)
            on_disk = pop_command_chunked("add_command", add_log_lock)

            if in_memory != on_disk:
                print("❌ FATAL SYNC ERROR in ADD queue")
                raise Exception("ADD queue out of sync")

            print("📤 Sent ADD_ITEM:", on_disk)
            return jsonify(on_disk)

        # MERGE command
        if merge_command_queue:
            in_memory = merge_command_queue.pop(0)
            on_disk = pop_command_chunked("merge_command", merge_log_lock)

            if in_memory != on_disk:
                print("❌ FATAL SYNC ERROR in MERGE queue")
                raise Exception("MERGE queue out of sync")

            print("📤 Sent MERGE:", on_disk)
            return jsonify(on_disk)

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