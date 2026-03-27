import json
import uuid

OUTPUT_FILE = "/Volumes/Music1/GeminiProjects/ConcertExtractorUtility/b3_organ_plugin.json"

def gen_id():
    return str(uuid.uuid4()).upper()

# Helper function to append standard port mapping
def build_output(type_name, ctrl_val, ch, is_note=False):
    out = {
        "id": gen_id(),
        "type": type_name,
        "channel": ch,
        "port": "Session 1 Network"
    }
    # User noted we missed note numbers because we didn't specify the right key. 
    # For CCs we use "control", for Notes we use "noteNumber"
    if is_note:
        out["noteNumber"] = ctrl_val
    else:
        out["control"] = ctrl_val
    return out

def extract_b3_organ():
    
    # ROW 1: Large Knobs & Toggles
    # 70x70 bounding boxes
    row1_controls = [
        {"id": gen_id(), "name": "Percussion", "displayType": "toggleButton", "outputs": [build_output("cc", 75, 15)], "frameWidth": 70, "frameHeight": 70},
        {"id": gen_id(), "name": "2nd/3rd Perc", "displayType": "toggleButton", "outputs": [build_output("cc", 78, 15)], "frameWidth": 70, "frameHeight": 70},
        {"id": gen_id(), "name": "Perc Level", "displayType": "knob", "outputs": [build_output("cc", 76, 15)], "frameWidth": 70, "frameHeight": 70},
        {"id": gen_id(), "name": "Perc Time", "displayType": "knob", "outputs": [build_output("cc", 77, 15)], "frameWidth": 70, "frameHeight": 70},
        {"id": gen_id(), "name": "Balance", "displayType": "knob", "outputs": [build_output("cc", 79, 15)], "frameWidth": 70, "frameHeight": 70},
        {"id": gen_id(), "name": "Chorus", "displayType": "toggleButton", "outputs": [build_output("cc", 21, 15)], "frameWidth": 70, "frameHeight": 70},
        {"id": gen_id(), "name": "Distortion", "displayType": "knob", "outputs": [build_output("cc", 22, 15)], "frameWidth": 70, "frameHeight": 70},
        {"id": gen_id(), "name": "Reverb", "displayType": "knob", "outputs": [build_output("cc", 73, 15)], "frameWidth": 70, "frameHeight": 70},
        {"id": gen_id(), "name": "Octave Shift Up", "displayType": "toggleButton", "outputs": [build_output("cc", 72, 15)], "frameWidth": 70, "frameHeight": 70}
    ]
    
    top_row = {
        "id": gen_id(),
        "label": "Modifiers",
        "axis": "horizontal",
        "controls": row1_controls
    }

    # ROW 2: Vibrato/Chorus Knob (Left) + Drawbars (Right)
    # The user asked to convert the 7 Vertical Buttons to a "Rotary Nutched Knob" and "make it bigger" (120x120).
    vc_knob = {
        "id": gen_id(),
        "name": "Vibrato/Chorus",
        "displayType": "steppedKnob",
        "menuOptions": ["V1", "C1", "V2", "C2", "V3", "C3", "OFF"],
        "outputs": [build_output("cc", 10, 15)], 
        "frameWidth": 120,
        "frameHeight": 120
    }
    
    # 9 Drawbars explicitly mapped as "drawbar" with hex colors correctly assigned to B3 standard
    drawbar_configs = [
        {"label": "16'", "color": "#8B4513"},
        {"label": "5 1/3'", "color": "#8B4513"},
        {"label": "8'", "color": "#FFFFFF"},
        {"label": "4'", "color": "#FFFFFF"},
        {"label": "2 2/3'", "color": "#000000"},
        {"label": "2'", "color": "#FFFFFF"},
        {"label": "1 3/5'", "color": "#000000"},
        {"label": "1 1/3'", "color": "#000000"},
        {"label": "1'", "color": "#FFFFFF"}
    ]
    
    drawbars = []
    for i, config in enumerate(drawbar_configs):
        drawbars.append({
            "id": gen_id(),
            "name": config["label"],
            "displayType": "drawbar",
            "color": config["color"],
            "defaultValue": 0.5,
            "formatScript": "return Math.round(value * 8).toString();",
            "outputs": [build_output("cc", 80 + i, 15)]
        })
        
    middle_row = {
        "id": gen_id(),
        "label": "Organ Engine",
        "axis": "horizontal",
        "controls": [vc_knob] + drawbars
    }

    # ROW 3: Presets (2 rows of 6) + Leslie Button (Large)
    # Preset frameWidth: 60, frameHeight: 40
    presets_1_to_6 = []
    for i in range(6):
        presets_1_to_6.append({
            "id": gen_id(),
            "name": f"Preset {i+1}",
            "displayType": "momentaryButton",
            "outputs": [build_output("note", 24 + i, 15, is_note=True)],
            "frameWidth": 60,
            "frameHeight": 40
        })
        
    presets_7_to_12 = []
    for i in range(6, 12):
        presets_7_to_12.append({
            "id": gen_id(),
            "name": f"Preset {i+1}",
            "displayType": "momentaryButton",
            "outputs": [build_output("note", 24 + i, 15, is_note=True)],
            "frameWidth": 60,
            "frameHeight": 40
        })

    # The 2 rows of 6 wrap inside a vertical subPanel
    preset_grid_panel = {
        "id": gen_id(),
        "label": "Preset Grid",
        "axis": "vertical",
        "subPanels": [
            {
                "id": gen_id(),
                "label": "Row A",
                "axis": "horizontal",
                "controls": presets_1_to_6
            },
            {
                "id": gen_id(),
                "label": "Row B",
                "axis": "horizontal",
                "controls": presets_7_to_12
            }
        ]
    }

    # Leslie Button (Large: 80x90)
    leslie_button = {
        "id": gen_id(),
        "name": "Leslie Fast/Slow",
        "displayType": "toggleButton",
        "outputs": [build_output("cc", 19, 15)],
        "frameWidth": 80,
        "frameHeight": 90, # Tall enough to match the 2 rows of 6 presets (40 + 40 + spacing)
        "color": "#FF2222"
    }

    bottom_row = {
        "id": gen_id(),
        "label": "Performance",
        "axis": "horizontal",
        "subPanels": [preset_grid_panel],
        "controls": [leslie_button]
    }

    # Assemble Final Page
    page = {
        "id": gen_id(),
        "name": "B3 Organ",
        "panels": [
            top_row,
            middle_row,
            bottom_row
        ]
    }

    plugin_json = {
        "id": gen_id(),
        "name": "B3 Organ",
        "layoutType": "paged",
        "skin": "B3OrganPlugin",
        "controls": [],
        "permanentPanels": [],
        "pages": [page]
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(plugin_json, f, indent=2)

    print(f"✅ Generated {OUTPUT_FILE} completely matching the new B3 Layout geometry.")

if __name__ == "__main__":
    extract_b3_organ()
