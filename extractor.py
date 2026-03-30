import os
import sys
import plistlib
import json
import zlib
from pathlib import Path

def parse_nskeyed(obj):
    """
    Recursively parse and flatten Plist objects, including NSKeyedArchiver 
    structures and embedded binary plists.
    """
    if isinstance(obj, bytes):
        try:
            # Check if it's an embedded builtin bplist
            if obj.startswith(b'bplist00'):
                inner = plistlib.loads(obj)
                return parse_nskeyed(inner)
        except Exception:
            pass
        # If it's pure binary data, representation as string may be needed
        return f"<binary data: {len(obj)} bytes>"
        
    if hasattr(obj, 'data') and type(obj).__name__ == 'UID':
        return {"$UID": obj.data}

            
    if not isinstance(obj, dict):
        if isinstance(obj, list):
            return [parse_nskeyed(x) for x in obj]
        return obj

    # check if it's a keyed archiver dict
    if '$archiver' in obj and obj['$archiver'] == 'NSKeyedArchiver':
        objects = obj.get('$objects', [])
        top = obj.get('$top', {}).get('root', None)
        
        resolved_cache = {}
        resolving_set = set()
        
        def resolve(uid):
            if isinstance(uid, dict) and isinstance(uid.get('CF$UID'), int):
                idx = uid['CF$UID']
            elif hasattr(uid, 'data') and hasattr(uid, '__class__'):
                # plistlib.UID object in python 3.8+
                idx = uid.data
            else:
                return parse_nskeyed(uid)
                
            if idx >= len(objects):
                return f"<Invalid UID: {idx}>"
            
            # Cycle Breaking and Memoization
            if idx in resolved_cache:
                return resolved_cache[idx]
            if idx in resolving_set:
                return f"<CircularReference UID:{idx}>"
            
            resolving_set.add(idx)
            val = objects[idx]
            result = None
            
            if val == '$null':
                result = None
            elif isinstance(val, (str, int, float, bool, bytes)):
                result = parse_nskeyed(val)
            elif isinstance(val, dict):
                res = {}
                if '$class' in val:
                    cls_ref = val['$class']
                    cls_idx = cls_ref.data if hasattr(cls_ref, 'data') else cls_ref.get('CF$UID', 0)
                    if cls_idx < len(objects):
                        cls_obj = objects[cls_idx]
                        if isinstance(cls_obj, dict):
                            res['$classname'] = cls_obj.get('$classname', 'UnknownClass')
                
                # Handling common collections
                classname = res.get('$classname')
                if classname in ['NSArray', 'NSMutableArray']:
                    items = val.get('NS.objects', [])
                    result = [resolve(x) for x in items]
                elif classname in ['NSDictionary', 'NSMutableDictionary']:
                    keys = val.get('NS.keys', [])
                    vals = val.get('NS.objects', [])
                    result = {str(resolve(k)): resolve(v) for k, v in zip(keys, vals)}
                elif classname in ['NSMutableString', 'NSString']:
                    result = resolve(val.get('NS.string', val.get('NS.bytes', '')))
                else:
                    # Custom objects
                    for k, v in val.items():
                        if k not in ('$class',):
                            res[k] = resolve(v)
                    result = res
            elif isinstance(val, list):
                result = [resolve(x) for x in val]
            else:
                result = val
            
            resolving_set.discard(idx)
            resolved_cache[idx] = result
            return result
            
        if top is not None:
            return resolve(top)
        else:
            return {"error": "No root object in NSKeyedArchiver"}
        
    else:
        # just a normal dict
        return {k: parse_nskeyed(v) for k, v in obj.items()}

def try_load_plist(filepath):
    """
    Attempt to load a regular plist or zlib compressed plist (like .layout or .plistZ).
    """
    with open(filepath, 'rb') as f:
        data = f.read()

    # Try zlib decompression first
    try:
        decompressed = zlib.decompress(data)
        data = decompressed
    except Exception:
        pass # Probably not zlib compressed
        
    try:
        return plistlib.loads(data)
    except Exception as e:
        print(f"Failed to parse {filepath} as plist: {e}")
        return None

def extract_concert_files(concert_path, output_dir):
    """
    Recursively iterate through the concert bundle and evaluate mapping plists.
    """
    concert_dir = Path(concert_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # We will aggregate specifically mappings here,
    # but also dump complete json translations for understanding.
    aggregate_mappings = {
        "patchMappings": [],
        "screenControls": []
    }

    for root, dirs, files in os.walk(concert_dir):
        for file in files:
            if file.endswith('.plist') or file.endswith('.plistZ') or file.endswith('.layout') or file.endswith('.patch'):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, concert_dir)
                
                print(f"Parsing: {rel_path} ...")
                raw_plist = try_load_plist(filepath)
                if not raw_plist:
                    continue
                    
                parsed_json = parse_nskeyed(raw_plist)
                
                # Check for mappings to aggregate
                if isinstance(parsed_json, dict):
                    # For data.plist inside patches
                    if "patch" in parsed_json and isinstance(parsed_json["patch"], dict):
                        # 1. System patchMappings
                        patch_mappings = parsed_json["patch"].get("patchMappings")
                        if isinstance(patch_mappings, dict):
                            for map_key, map_val in patch_mappings.items():
                                aggregate_mappings["patchMappings"].append({
                                    "sourceFile": rel_path,
                                    "mapKey": map_key,
                                    "mapping": map_val,
                                    "mappingType": "System"
                                })
                        
                        # 2. Audio Plugin and Screen Layout virtual mappings inside engineNode
                        engine_node = parsed_json["patch"].get("engineNode")
                        if isinstance(engine_node, dict):
                            param_map = engine_node.get("parameterMappingMap")
                            if isinstance(param_map, dict):
                                store_dict = param_map.get("storeDict")
                                if isinstance(store_dict, dict):
                                    for str_key, str_val in store_dict.items():
                                        aggregate_mappings["patchMappings"].append({
                                            "sourceFile": rel_path,
                                            "mapKey": str_key, # These are natively arrays of dicts instead of NUMBER: wrapper
                                            "mapping": str_val,
                                            "mappingType": "PluginUI"
                                        })
                
                # Dump JSON representation of the file
                out_filepath = out_dir / f"{rel_path}.json"
                out_filepath.parent.mkdir(parents=True, exist_ok=True)
                
                with open(out_filepath, 'w') as f:
                    json.dump(parsed_json, f, indent=2)

    # Dump the specifically aggregated mappings
    with open(out_dir / "aggregated_mappings.json", 'w') as f:
        json.dump(aggregate_mappings, f, indent=2)

    print(f"\nExtraction complete! Files translated to JSON and aggregated in: {out_dir}")

def extract_concert(concert_path, output_dir):
    """
    Main entrypoint for extraction prototyping.
    """
    if not os.path.exists(concert_path):
        print(f"Error: Could not find {concert_path}")
        return
        
    print(f"Starting extraction for: {concert_path}")
    extract_concert_files(concert_path, output_dir)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 extractor.py <path_to_concert_file>")
        sys.exit(1)
        
    target_concert = sys.argv[1]
    output_folder = "./extracted_data"
    
    os.makedirs(output_folder, exist_ok=True)
    extract_concert(target_concert, output_folder)
