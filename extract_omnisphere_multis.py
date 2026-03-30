import os
import json
import re

# --- 1. CONFIGURATION ---
STEAM_MULTI_DIR = os.path.expanduser("~/Library/Omnisphere/STEAM/Omnisphere/Settings Library/Multis/User")
PROJECT_ROOT = "/Volumes/Music1/GeminiProjects/ConcertExtractorUtility"
OUTPUT_JSON = os.path.join(PROJECT_ROOT, "omnisphere_multis_extracted.json")

def extract_multi_data(file_path):
    extracted_info = {
        "multiName": "Unknown",
        "liveSlots": [None] * 8  # 8 Live slots, default to None/Empty
    }
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
            
            # Extract Multi Name
            name_match = re.search(r'ENTRYDESCR\s+name="([^"]+)"', text)
            if name_match: 
                extracted_info["multiName"] = name_match.group(1).strip()
            
            # Extract out the PATCH NAMES sequentially as they appear in the file.
            # In Omnisphere .mlt_omn format, origPatchName denotes the loaded sound.
            patches = re.findall(r'origPatchName="([^"]+)"', text)
            
            # Populate our 8 slots. If the file has fewer loaded slots, the loop naturally stops.
            for i in range(8):
                if i < len(patches):
                    extracted_info["liveSlots"][i] = patches[i].strip()
                    
    except Exception as error: 
        print(f"Error reading {file_path}: {error}")
        
    return extracted_info

def main():
    print(f"Starting Deep Extractor on: {STEAM_MULTI_DIR}")
    
    if not os.path.exists(STEAM_MULTI_DIR):
        print(f"[!] Error: The directory {STEAM_MULTI_DIR} does not exist.")
        return

    all_multis = []
    
    # Process all subfolders in User category
    for folder_name in os.listdir(STEAM_MULTI_DIR):
        folder_path = os.path.join(STEAM_MULTI_DIR, folder_name)
        
        if os.path.isdir(folder_path):
            print(f"Scanning folder: {folder_name}...")
            
            for file_name in os.listdir(folder_path):
                if file_name.endswith(".mlt_omn"):
                    file_path = os.path.join(folder_path, file_name)
                    
                    data = extract_multi_data(file_path)
                    
                    data["categoryFolder"] = folder_name
                    data["fileName"] = file_name
                    
                    all_multis.append(data)

    # Sort results
    all_multis_sorted = sorted(all_multis, key=lambda x: (x.get("categoryFolder", ""), x.get("multiName", "")))

    with open(OUTPUT_JSON, "w", encoding="utf-8") as out:
        json.dump(all_multis_sorted, out, indent=4)
        
    print(f"\n✅ Deep Extraction Complete! {len(all_multis_sorted)} Multis fully mapped (Slots 1-8).")
    print(f"✅ Saved to: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
