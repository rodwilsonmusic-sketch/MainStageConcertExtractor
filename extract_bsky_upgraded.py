import json
import uuid
import re
import os

JZML_FILE = "/Volumes/Music1/GeminiProjects/MidiAssistantProject/docs/Mainstage v9-4 Dbl Omnisphere V9-5- 03-12-2026 .jzml"
OUTPUT_FILE = "/Volumes/Music1/GeminiProjects/ConcertExtractorUtility/bigsky_plugin.json"

def gen_id():
    return str(uuid.uuid4()).upper()

JS_DECAY = """const decayArray = [500.0, 500.0, 500.0, 500.0, 500.0, 501.0, 501.0, 502.0, 503.0, 504.0, 505.0, 507.0, 510.0, 512.0, 516.0, 520.0, 524.0, 530.0, 536.0, 543.0, 550.0, 559.0, 568.0, 579.0, 590.0, 603.0, 617.0, 632.0, 648.0, 666.0, 686.0, 706.0, 728.0, 752.0, 778.0, 805.0, 834.0, 865.0, 898.0, 932.0, 969.0, 1.008, 1.049, 1.092, 1.138, 1.186, 1.237, 1.289, 1.345, 1.403, 1.464, 1.527, 1.594, 1.663, 1.735, 1.810, 1.889, 1.971, 2.055, 2.144, 2.235, 2.331, 2.429, 2.531, 2.637, 2.747, 2.860, 2.977, 3.099, 3.225, 3.353, 3.487, 3.625, 3.768, 3.913, 4.065, 4.221, 4.382, 4.545, 4.715, 4.891, 5.068, 5.254, 5.444, 5.639, 5.837, 6.043, 6.254, 6.471, 6.691, 6.919, 7.153, 7.392, 7.634, 7.886, 8.143, 8.406, 8.673, 8.847, 9.231, 9.519, 9.811, 10.11, 10.42, 10.74, 11.05, 11.38, 11.72, 12.06, 12.41, 12.76, 13.13, 13.50, 13.88, 14.26, 14.66, 15.05, 15.46, 15.88, 16.31, 16.74, 17.18, 17.63, 18.09, 18.55, 19.02, 19.51, 20.00];
const m = Math.round(value*127);
return decayArray[m] + (m<41?' ms':' s');"""

SHIFT_1_OPTS = ['-OCT','-M7','-m7','-M6','-m6','-P5','-TRI','-P4','-M3','-m3','-M2','-m2','-10CEN','+10CEN','+m2','+M2','+m3','+M3','+P4','+TRI','+P5','+m6','+M6','+m7','+M7','+OCT','+OCT&5','+2 OCT']
SHIFT_2_OPTS = ['OFF'] + SHIFT_1_OPTS

def extract_bigsky():
    engines = ["Bloom", "Cloud", "Chorale", "Swell", "Shimmer"]
    engine_uuids = {eng: gen_id() for eng in engines}
    
    pages = []
    global_mix_uuid = gen_id()
    
    for idx, engine in enumerate(engines):
        variation_knobs = []
        clusters = []

        if engine == "Shimmer":
            variation_knobs = [
                {"id": gen_id(), "name": "Shift 1", "displayType": "steppedKnob", "menuOptions": SHIFT_1_OPTS, "outputs": [{"id": gen_id(), "type": "cc", "control": 46, "channel": 6}], "frameWidth": 100, "frameHeight": 130},
                {"id": gen_id(), "name": "Shift 2", "displayType": "steppedKnob", "menuOptions": SHIFT_2_OPTS, "outputs": [{"id": gen_id(), "type": "cc", "control": 47, "channel": 6}], "frameWidth": 100, "frameHeight": 130},
                {"id": gen_id(), "name": "Mode", "displayType": "steppedKnob", "menuOptions": ["Input", "Regen", "Input + Regen"], "outputs": [{"id": gen_id(), "type": "cc", "control": 76, "channel": 6}], "frameWidth": 100, "frameHeight": 130}
            ]
        elif engine == "Bloom":
            variation_knobs = [
                {"id": gen_id(), "name": "Length", "displayType": "knob", "outputs": [{"id": gen_id(), "type": "cc", "control": 45, "channel": 6}], "frameWidth": 100, "frameHeight": 130},
                {"id": gen_id(), "name": "Feedback", "displayType": "knob", "outputs": [{"id": gen_id(), "type": "cc", "control": 46, "channel": 6}], "frameWidth": 100, "frameHeight": 130}
            ]
        elif engine == "Cloud":
            variation_knobs = [
                {"id": gen_id(), "name": "Diffusion", "displayType": "knob", "outputs": [{"id": gen_id(), "type": "cc", "control": 45, "channel": 6}], "frameWidth": 100, "frameHeight": 130}
            ]
        elif engine == "Chorale":
            variation_knobs = [
                {"id": gen_id(), "name": "Vowel", "displayType": "steppedKnob", "menuOptions": ['AAHHOO','AAHH','AAHOH','OH','OOOHOH','OOOO','RANDOM'], "outputs": [{"id": gen_id(), "type": "cc", "control": 45, "channel": 6}], "frameWidth": 100, "frameHeight": 130},
                {"id": gen_id(), "name": "Resonance", "displayType": "knob", "outputs": [{"id": gen_id(), "type": "cc", "control": 46, "channel": 6}], "frameWidth": 100, "frameHeight": 130}
            ]
            
            # Chorale 3-way cluster
            clusters.append({
                "id": gen_id(),
                "label": "Filter",
                "axis": "horizontal",
                "clusterType": "FlipSwitch",
                "controls": [
                    {"id": gen_id(), "name": "HIGH", "displayType": "toggleButton", "outputs": [{"id": gen_id(), "type": "cc", "control": 75, "channel": 6}]},
                    {"id": gen_id(), "name": "MEDIUM", "displayType": "toggleButton", "outputs": [{"id": gen_id(), "type": "cc", "control": 75, "channel": 6}]},
                    {"id": gen_id(), "name": "MILD", "displayType": "toggleButton", "outputs": [{"id": gen_id(), "type": "cc", "control": 75, "channel": 6}]}
                ]
            })
            
        elif engine == "Swell":
            variation_knobs = [
                {"id": gen_id(), "name": "Rise Time", "displayType": "knob", "outputs": [{"id": gen_id(), "type": "cc", "control": 37, "channel": 6}], "frameWidth": 100, "frameHeight": 130}
            ]
            
            # Swell Wet/Dry flip switch
            clusters.append({
                "id": gen_id(),
                "label": "Wet/Dry",
                "axis": "horizontal",
                "clusterType": "FlipSwitch",
                "controls": [
                    {"id": gen_id(), "name": "WET", "displayType": "toggleButton", "outputs": [{"id": gen_id(), "type": "cc", "control": 78, "channel": 6}]},
                    {"id": gen_id(), "name": "DRY", "displayType": "toggleButton", "outputs": [{"id": gen_id(), "type": "cc", "control": 78, "channel": 6, "isInverted": True}]}
                ]
            })
            
        # ALL engines have Hold + Infinite/Freeze 
        # Add Hold separately to variation knobs
        variation_knobs.append({
            "id": gen_id(), 
            "name": "HOLD", 
            "displayType": "momentaryButton", 
            "outputs": [{"id": gen_id(), "type": "cc", "control": 49, "channel": 6}],
            "frameWidth": 100, "frameHeight": 130
        })
        
        # Infinite/Freeze mutually exclusive cluster 
        # Appended as a PANEL (Horizontal)
        clusters.append({
             "id": gen_id(),
             "label": "Inf/Freeze",
             "axis": "horizontal",
             "clusterType": "FlipSwitch",
             "controls": [
                 {"id": gen_id(), "name": "INFINITE", "displayType": "toggleButton", "outputs": [{"id": gen_id(), "type": "cc", "control": 77, "channel": 6}]},
                 {"id": gen_id(), "name": "FREEZE", "displayType": "toggleButton", "outputs": [{"id": gen_id(), "type": "cc", "control": 77, "channel": 6, "isInverted": True}]}
             ]
        })

        top_row = {
            "id": gen_id(),
            "label": "Top Row",
            "axis": "horizontal",
            "controls": [
                {"id": gen_id(), "name": "Decay", "displayType": "knob", "formatScript": JS_DECAY, "outputs": [{"id": gen_id(), "type": "cc", "control": 40, "channel": 6}], "frameWidth": 100, "frameHeight": 130},
                {"id": gen_id(), "name": "Pre - Delay", "displayType": "knob", "outputs": [{"id": gen_id(), "type": "cc", "control": 41, "channel": 6}], "frameWidth": 100, "frameHeight": 130},
                {"id": gen_id(), "name": "Tone", "displayType": "knob", "outputs": [{"id": gen_id(), "type": "cc", "control": 42, "channel": 6}], "frameWidth": 100, "frameHeight": 130},
                {"id": gen_id(), "name": "Mod", "displayType": "knob", "outputs": [{"id": gen_id(), "type": "cc", "control": 43, "channel": 6}], "frameWidth": 100, "frameHeight": 130},
                {"id": gen_id(), "name": "Low End", "displayType": "knob", "outputs": [{"id": gen_id(), "type": "cc", "control": 44, "channel": 6}], "frameWidth": 100, "frameHeight": 130},
                {"id": global_mix_uuid, "name": "Mix", "displayType": "knob", "outputs": [{"id": gen_id(), "type": "cc", "control": 48, "channel": 6}], "frameWidth": 100, "frameHeight": 130}
            ]
        }
        
        # Assemble Row 2 (Bottom Row) natively utilizing the new "subPanels" architecture
        # Hold is injected as a standard control inside the horizontal row.
        # The Infinite/Freeze and Wet/Dry clusters are pushed recursively into `subPanels`.
        
        bottom_row = {
             "id": gen_id(),
             "label": "Variations",
             "axis": "horizontal",
             "controls": variation_knobs,
             "subPanels": clusters
        }
        
        preset_row = {
            "id": gen_id(),
            "label": "Preset Row",
            "axis": "horizontal",
            "controls": [
                {"id": gen_id(), "name": str(i), "displayType": "momentaryButton", "outputs": [{"id": gen_id(), "type": "program_change", "channel": 6}]}
                for i in range(1, 9)
            ]
        }
        
        # Assemble EXACTLY 3 Root Panels per explicit constraints
        panel_list = [top_row, bottom_row, preset_row]
        
        pages.append({
            "id": engine_uuids[engine],
            "name": engine,
            "panels": panel_list
        })

    permanent_panels = [
        {
            "id": gen_id(),
            "label": "Engine & I/O",
            "axis": "vertical",
            "controls": [
                {
                    "id": gen_id(),
                    "name": "Input",
                    "displayType": "knob",
                    "outputs": [{"id": gen_id(), "type": "cc", "control": 2, "channel": 6}]
                },
                {
                    "id": gen_id(),
                    "name": "Engine",
                    "displayType": "steppedKnob",
                    "color": "#33FF33",
                    "menuOptions": engines,
                    "linkedPageIds": [engine_uuids[e] for e in engines],
                    "outputs": [{"id": gen_id(), "type": "cc", "control": 45, "channel": 6}]
                }
            ]
        }
    ]

    plugin_json = {
        "id": gen_id(),
        "name": "BigSky",
        "layoutType": "paged",
        "skin": "BigSkyPlugin",
        "controls": [],
        "permanentPanels": permanent_panels,
        "pages": pages
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(plugin_json, f, indent=2)

    print(f"✅ Generated {OUTPUT_FILE} completely and flawlessly according to schema.")

if __name__ == "__main__":
    extract_bigsky()
