import json
import argparse
from pathlib import Path

def translate_mappings(input_file, output_file):
    """
    Translates the raw MainStage aggregated mappings into a clean, lightweight JSON
    for the Midi Assistant Swift App.
    """
    with open(input_file, 'r') as f:
        raw_data = json.load(f)

    clean_mappings = []

    for item in raw_data.get("patchMappings", []):
        source_file = item.get("sourceFile", "")
        map_key = item.get("mapKey", "")
        
        # Strip strange unicode prefix like \u0001IDENTITY:
        clean_name = map_key.replace("\u0001IDENTITY:", "").strip()

        mapping_data = item.get("mapping", {})
        mapping_type = item.get("mappingType", "System")
        
        if not mapping_data:
            continue
            
        # Determine iterator because System mappings are dicts wrapped in \x01NUMBER:X, but Plugin mappings are pure arrays!
        if isinstance(mapping_data, list):
            iterator = enumerate(mapping_data)
        elif isinstance(mapping_data, dict):
            iterator = mapping_data.items()
        else:
            continue
            
        for ref_key, node in iterator:
            if not isinstance(node, dict): 
                continue
                
            # Extract MIDI constraints usually stored in inputControlEvent or root for some layouts
            input_event = node.get("inputControlEvent", {})
            if not input_event:
                if mapping_type == "PluginUI" and "channelID" in node:
                    # Sometimes baseplate directly stores it
                    input_event = node
                else:
                    continue
                
            port_name = input_event.get("MIDIPort", {}).get("name", "Unassigned")
            if not port_name: port_name = "Unassigned"
            
            channel = input_event.get("channelID", 0)
            controller_id = input_event.get("controllerID", -1)
            type_id = input_event.get("type", -1)
            
            target_name = None
            if "Controller" in node:
                t_chan = node["Controller"].get("channelID")
                if t_chan is not None:
                    target_name = f"Routed to CH {t_chan} Layer"
            elif mapping_type == "PluginUI":
                # For plugins, target name corresponds to the channel strip index or plugin slot parameter index.
                target_name = f"Plugin Slot {node.get('slot', '?')} (Param {node.get('parameterIndex_1', '?')})"
            
            import re
            is_uuid = bool(re.match(r'^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$', clean_name, re.IGNORECASE))
            
            clean_mappings.append({
                "sourcePatch": source_file,
                "mapKey": map_key, # THE EXACT UNMODIFIED KEY FOR THE BACKEND
                "controlName": clean_name,
                "portName": port_name,
                "channel": channel,
                "controllerID": controller_id,
                "controlType": type_id,
                "hasScreenControl": is_uuid,
                "targetName": target_name,
                "mappingType": mapping_type,
                "rawRef": str(ref_key) 
            })

    # Wrap in a neat object
    output_obj = {
        "version": "1.0",
        "concertMappings": clean_mappings
    }

    with open(output_file, 'w') as f:
        json.dump(output_obj, f, indent=4)
        
    print(f"Successfully compiled {len(clean_mappings)} mappings for Midi Assistant into {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean MainStage Extract for Midi Assistant")
    parser.add_argument("--input", default="./extracted_data/aggregated_mappings.json", help="Path to aggregated output")
    parser.add_argument("--output", default="./extracted_data/midi_assistant_schema.json", help="Path for clean JSON")
    
    args = parser.parse_args()
    translate_mappings(args.input, args.output)
