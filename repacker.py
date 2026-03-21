import os
import plistlib
import json

def edit_mapping_in_plist(concert_path, patch_rel_path, map_identity_key, number_key, new_channel=None, new_port_name=None, replicate_mapping=False):
    """
    Loads a specific data.plist, digs into the specified mapping's embedded bplist,
    edits the channel/port inline inside the NSKeyedArchiver $objects array, 
    repacks the bplist, and saves the data.plist!
    If replicate_mapping is True, generates a new dictionary slot instead of overwriting.
    """
    plist_path = os.path.join(concert_path, patch_rel_path)
    if not os.path.exists(plist_path):
        print(f"Error: Could not find {plist_path}")
        return False

    print(f"Loading top-level {patch_rel_path} ...")
    with open(plist_path, 'rb') as f:
        top_plist = plistlib.load(f)

    # Sanity check structure
    if "patch" not in top_plist or "patchMappings" not in top_plist["patch"]:
        print("Error: patchMappings not found in this data.plist")
        return False
        
    patch_mappings = top_plist["patch"]["patchMappings"]
    
    if map_identity_key not in patch_mappings:
        print(f"Error: {map_identity_key} not in patchMappings.")
        return False
        
    inner_dict = patch_mappings[map_identity_key]
    
    if number_key not in inner_dict:
        print(f"Error: {number_key} not found in the target mapping dict.")
        return False
        
    binary_bplist_data = inner_dict[number_key]
    if not isinstance(binary_bplist_data, bytes) or not binary_bplist_data.startswith(b'bplist00'):
        print("Error: The mapping value is not a valid embedded bplist00 object.")
        return False

    print("Unpacking embedded bplist00 NSKeyedArchiver...")
    inner_plist = plistlib.loads(binary_bplist_data)
    
    if "$objects" not in inner_plist:
        print("Error: Embedded plist is not an NSKeyedArchiver (missing $objects array).")
        return False
        
    objects = inner_plist["$objects"]
    
    # We must scan $objects to find the WsMutableController defining the inputControlEvent
    # A mapping might have multiple WsMutableControllers (one for input, one for target). 
    # Usually the inputControlEvent is referenced by the main mapping object.
    
    # 1. Let's find the main mapping object (e.g. WsActionParameterMapping) first
    # In NSKeyedArchiver, $top['root'] points to it.
    root_uid = inner_plist.get('$top', {}).get('root')
    if root_uid is None:
        return False
        
    root_idx = root_uid.data if hasattr(root_uid, 'data') else root_uid
    root_obj = objects[root_idx]
    
    if not isinstance(root_obj, dict):
        print("Root object is not a dictionary.")
        return False

    # 2. Get the inputControlEvent UID
    input_event_uid = root_obj.get("inputControlEvent")
    if input_event_uid is None:
        print("No inputControlEvent found in the mapping root.")
        return False
        
    input_event_idx = input_event_uid.data if hasattr(input_event_uid, 'data') else input_event_uid
    input_event_obj = objects[input_event_idx]
    
    # Now we are inside the WsMutableController (the input trigger)
    print(f"Found inputControlEvent at $objects[{input_event_idx}].")
    
    # Apply Edits!
    made_changes = False
    
    def apply_edits_to_controller(controller_uid):
        if controller_uid is None: return False
        idx = controller_uid.data if hasattr(controller_uid, 'data') else controller_uid
        obj = objects[idx]
        changed = False
        
        if new_channel is not None:
            old_channel = obj.get("channelID", -1)
            if old_channel != new_channel:
                print(f" -> Changing channelID from {old_channel} to {new_channel} for $objects[{idx}]")
                obj["channelID"] = new_channel
                changed = True
                
        if new_port_name is not None:
            midi_port_uid = obj.get("MIDIPort")
            if midi_port_uid is not None:
                midi_port_idx = midi_port_uid.data if hasattr(midi_port_uid, 'data') else midi_port_uid
                midi_port_obj = objects[midi_port_idx]
                name_uid = midi_port_obj.get("name")
                if name_uid is not None:
                    name_idx = name_uid.data if hasattr(name_uid, 'data') else name_uid
                    old_name = objects[name_idx]
                    if old_name != new_port_name:
                        print(f" -> Changing MIDIPort string from '{old_name}' to '{new_port_name}'")
                        objects[name_idx] = new_port_name
                        if "uniqueID" in midi_port_obj:
                            midi_port_obj["uniqueID"] = -1
                        if "uniqueIDType" in midi_port_obj:
                            midi_port_obj["uniqueIDType"] = 0
                        changed = True
        return changed

    # Modify both the Hardware Input and the Software Target (if it's a translation mapping!)
    print(f"Applying to Input: {root_obj.get('inputControlEvent')}")
    if apply_edits_to_controller(root_obj.get("inputControlEvent")):
        made_changes = True
    print(f"Applying to Target: {root_obj.get('Controller')}")
    if apply_edits_to_controller(root_obj.get("Controller")):
        made_changes = True

    if not made_changes:
        print("No changes required. Aborting save.")
        return True

    print("Repacking embedded NSKeyedArchiver...")
    new_bplist_data = plistlib.dumps(inner_plist, fmt=plistlib.FMT_BINARY)
    
    target_number_key = number_key
    if replicate_mapping:
        # Find next available NUMBER slot in the inner_dict
        existing_numbers = []
        for pk in inner_dict.keys():
            if pk.startswith("\u0001NUMBER:"):
                try:
                    num = int(pk.split(":")[1])
                    existing_numbers.append(num)
                except: pass
        next_num = max(existing_numbers) + 1 if existing_numbers else 0
        target_number_key = f"\u0001NUMBER:{next_num}"
        print(f"Replicating! Injecting entirely new mapping clone at {target_number_key} ...")
    else:
        print(f"Injecting updated bplist back into existing {target_number_key} ...")
        
    inner_dict[target_number_key] = new_bplist_data
    
    print("Saving modified data.plist back to disk...")
    # NOTE: Write to a backup first in a real scenario
    with open(plist_path, 'wb') as f:
        plistlib.dump(top_plist, f, fmt=plistlib.FMT_BINARY)
        
    print("SUCCESS! The mapping has been successfully repacked into the MainStage file.")
    return True

if __name__ == "__main__":
    # Test Run Configuration
    concert_dir = "MainStage Concert/Rack Only -BackStage Master Concert V2-8.concert"
    
    # We target the "All Notes Off" mapping in the Worship Pads patch:
    patch_path = "Concert.patch/Worship Sets.patch/TheresNothing That Our God Can't DO V5.patch/data.plist"
    map_id = "\u0001IDENTITY:All Notes Off" # Contains a UUID string if Screen Control!
    number_id = "\u0001NUMBER:0"
    
    # Let's perform a hypothetical Batch Edit: 
    # Change it to Channel 7 and Port "Midi Assistant Virtual" and REPLICATE IT
    edit_mapping_in_plist(concert_dir, patch_path, map_id, number_id, new_channel=7, new_port_name="Midi Assistant Virtual", replicate_mapping=True)
