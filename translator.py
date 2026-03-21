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
        
        if not mapping_data:
            continue
            
        for ref_key, node in mapping_data.items():
            
            # Extract MIDI constraints
            input_event = node.get("inputControlEvent", {})
            if not input_event:
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
                "rawRef": ref_key 
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
