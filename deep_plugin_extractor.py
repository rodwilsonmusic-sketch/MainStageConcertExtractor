import os
import plistlib
import zlib
from parse_nskeyedarchiver import parse_nskeyed

concert_dir = "MainStage Concert/MasterMapping March 21-2026.concert"
total_mappings = 0

def scan(d, current_path="", visited=None):
    global total_mappings
    if visited is None:
        visited = set()
        
    obj_id = id(d)
    if obj_id in visited:
        return
    visited.add(obj_id)
    
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, bytes) and v.startswith(b"bplist00"):
                try:
                    unp = parse_nskeyed(v)
                    scan(unp, current_path + "." + str(k), visited)
                except Exception as e:
                    pass
            elif k == "$classname" and "Mapping" in str(v):
                total_mappings += 1
                print(f"Path: {current_path} -> {v}")
            else:
                scan(v, current_path + "." + str(k), visited)
    elif isinstance(d, list):
        for item in d:
            scan(item, current_path + "[]", visited)

for root, _, files in os.walk(concert_dir):
    for filename in files:
        if filename.endswith(".plist") or filename.endswith(".layout"):
            path = os.path.join(root, filename)
            try:
                if filename.endswith(".layout"):
                    with open(path, "rb") as f:
                        data = zlib.decompress(f.read())
                    top = plistlib.loads(data)
                else:
                    with open(path, "rb") as f:
                        top = plistlib.load(f)
                scan(top, path)
            except Exception as e:
                pass

print(f"Total 'Mapping' object instances: {total_mappings}")
