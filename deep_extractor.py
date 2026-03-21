import os
import plistlib
import zlib
from parse_nskeyedarchiver import parse_nskeyed

concert_dir = "MainStage Concert/MasterMapping March 21-2026.concert"
total_mappings = 0
mapping_types = set()

def scan_dict_for_bplists(d, current_path=""):
    global total_mappings, mapping_types
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, bytes) and v.startswith(b"bplist00"):
                try:
                    unpacked = parse_nskeyed(v)
                    if isinstance(unpacked, dict):
                        # Look for mappings explicitly!
                        # Some mappings are directly inside the dict
                        cname = unpacked.get("$classname", "")
                        if "Mapping" in cname:
                            total_mappings += 1
                            mapping_types.add(cname)
                            
                        # Some mappings are wrapped in NUMBER:0 keys
                        for inner_k, inner_v in unpacked.items():
                            if isinstance(inner_k, str) and inner_k.startswith("\x01NUMBER:"):
                                total_mappings += 1
                                if isinstance(inner_v, dict):
                                    mapping_types.add(inner_v.get("$classname", "Unknown"))
                except Exception as e:
                    pass
            elif isinstance(v, dict):
                scan_dict_for_bplists(v, current_path + "." + str(k))
            elif isinstance(v, list):
                for item in v:
                    scan_dict_for_bplists(item, current_path + "." + str(k) + "[]")
    elif isinstance(d, list):
        for item in d:
            scan_dict_for_bplists(item, current_path + "[]")

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
                scan_dict_for_bplists(top)
            except Exception as e:
                pass

print(f"Total mappings found universally: {total_mappings}")
print(f"Mapping types: {mapping_types}")
