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
                    result = [resolve(x) for x in items]
                elif res.get('$classname') in ['NSDictionary', 'NSMutableDictionary']:
                    keys = val.get('NS.keys', [])
                    vals = val.get('NS.objects', [])
                    result = {str(resolve(k)): resolve(v) for k, v in zip(keys, vals)}
                else:    
                    for k, v in val.items():
                        if k not in ('$class',):
                            res[k] = resolve(v)
                    result = res
            elif isinstance(val, list):
                result = [resolve(x) for x in val]
            else:
                result = val
                
            resolving_set.remove(idx)
            resolved_cache[idx] = result
            return result
            
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

