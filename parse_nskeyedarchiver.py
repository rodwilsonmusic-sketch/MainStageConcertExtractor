import plistlib

def parse_nskeyed(obj):
    if isinstance(obj, bytes):
        try:
            # Check if it's an embedded builtin bplist
            if obj.startswith(b'bplist00'):
                inner = plistlib.loads(obj)
                return parse_nskeyed(inner)
        except Exception:
            pass
        return str(obj) # Fallback for other bytes
            
    if not isinstance(obj, dict):
        if isinstance(obj, list):
            return [parse_nskeyed(x) for x in obj]
        return obj

    # check if it's a keyed archiver dict
    if '$archiver' in obj and obj['$archiver'] == 'NSKeyedArchiver':
        objects = obj['$objects']
        top = obj['$top']['root'] # The starting point is usually top.root
        
        def resolve(uid):
            if isinstance(uid, dict) and isinstance(uid.get('CF$UID'), int):
                idx = uid['CF$UID']
            elif hasattr(uid, 'data') and hasattr(uid, '__class__'):
                # plistlib.UID object in python 3.8+
                idx = uid.data
            else:
                return parse_nskeyed(uid)
                
            val = objects[idx]
            
            if val == '$null':
                return None
            if isinstance(val, (str, int, float, bool, bytes)):
                return parse_nskeyed(val)

            if isinstance(val, dict):
                # could be a custom class or collection
                res = {}
                # Handle classes
                if '$class' in val:
                    cls_idx = val['$class'].data if hasattr(val['$class'], 'data') else val['$class']['CF$UID']
                    cls_obj = objects[cls_idx]
                    res['$classname'] = cls_obj.get('$classname')
                
                # Check for array/dict
                if res.get('$classname') in ['NSArray', 'NSMutableArray']:
                    items = val.get('NS.objects', [])
                    return [resolve(x) for x in items]
                if res.get('$classname') in ['NSDictionary', 'NSMutableDictionary']:
                    keys = val.get('NS.keys', [])
                    vals = val.get('NS.objects', [])
                    return {str(resolve(k)): resolve(v) for k, v in zip(keys, vals)}
                
                for k, v in val.items():
                    if k not in ('$class',):
                        res[k] = resolve(v)
                return res
            
            if isinstance(val, list):
                return [resolve(x) for x in val]
                
            return val
            
        return resolve(top)
        
    else:
        # just a normal dict
        return {k: parse_nskeyed(v) for k, v in obj.items()}

if __name__ == '__main__':
    import sys
    import json
    path = "MainStage Concert/Rack Only -BackStage Master Concert V2-8.concert/Concert.patch/data.plist"
    with open(path, "rb") as f:
        data = plistlib.load(f)
    patch = data.get("patch", {})
    mappings = patch.get("patchMappings")
    
    first_key = list(mappings.keys())[0]
    parsed = parse_nskeyed(mappings[first_key])
    print(json.dumps(parsed, indent=2, default=str))

