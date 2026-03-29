# 🌙 Session Hand-Off & Assessment: Omnisphere Extractor

**Date/Time:** 2026-03-28 (Night Session)
**Agent Role:** Specialized Python Data Mining & Parsing Agent (Sandbox Compliant)

---

## 🔍 Assessment of Discoveries

During this session, we targeted Spectrasonics Omnisphere `.mlt_omn` files. Our investigation successfully revealed several critical breakthroughs concerning how Omnisphere securely structures its proprietary files:

### 1. File Structure Architecture
*   **The Big Reveal:** Omnisphere `.mlt_omn` files are NOT fully obfuscated binaries. They are fundamentally composed of extremely long-line, single-string XML payloads. 
*   **Impact:** This dramatically improves our ability to parse the files reliably using robust Regex or text mapping without needing reverse-engineering tools. We can confidently extract exact relationships.

### 2. The Part 1 / Live 1 Program Relationship
*   You correctly guided the exploration toward isolating the "Multi Name" and pairing it with its underlying "Part 1" (Live 1) Patch Name.
*   **Discovery:** The patch loaded into any given Part inside Omnisphere is denoted under the XML text attribute: `origPatchName="..."`.
*   **Proof:** Inside your `Strings Pad 4Multi.mlt_omn` file, we discovered the following structure:
    *   **Multi Name:** `Strings Pad 4Multi` (Found at `ENTRYDESCR name="..."`)
    *   **Part 1 Program:** `Platinum Shiny Strings` (Found as the first sequence of `origPatchName="..."`)
    *   **Part 2+ Programs:** Including *Fingerbells*, *Atmosphere Strings - Close a*, and *Cathedral String Orchestra* loaded into subsequent layers.
*   **Next Steps:** The Python extractor script is now structured to map this exact relationship, prioritizing and returning `"Platinum Shiny Strings"` as the foundational Part 1 anchor for your MainStage mappings.

### 3. Deep MIDI CC Mappings
*   Even though you noted that the MainStage channel assignments are handled elsewhere, it is deeply valuable to note that the Omnisphere Multi file *does* embed internal MIDI Learn data.
*   We found parameters mapped via the `MidiLearnIDnum0` attribute.
*   **Example from "Strings Pad 4Multi":** We observed `pPan0` through `pPan7` globally mapped to **CC 10** inside the plugin, and `pLevel0` through `pLevel7` strictly designated to **CCs 17 through 24**. We will capture these values strictly for documentation and troubleshooting.

---

## 🛠️ Drafted Python Payload for Next Session
*This script adheres 100% to the Non-Destructive Prime Directive and Sandbox Mandate. We will execute it to extract the User Multis JSON payload right when we resume.*

```python
import os
import shutil
import json
import re

# --- 1. CONFIGURATION ---
STEAM_MULTI_DIR = os.path.expanduser("~/Library/Omnisphere/STEAM/Omnisphere/Settings Library/Multis/User")
PROJECT_ROOT = "/Volumes/Music1/GeminiProjects/ConcertExtractorUtility"
SANDBOX_DIR = os.path.join(PROJECT_ROOT, "extraction_sandbox")
OUTPUT_JSON = os.path.join(PROJECT_ROOT, "omnisphere_multis_extracted.json")

def extract_multi_data(file_path):
    extracted_info = {"multiName": "Unknown", "part1_ProgramName": "None"}
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
            # Extract Multi Name
            name_match = re.search(r'ENTRYDESCR\s+name="([^"]+)"', text)
            if name_match: extracted_info["multiName"] = name_match.group(1).strip()
            
            # Extract Part 1 Program matched to Multi
            programs = re.findall(r'origPatchName="([^"]+)"', text)
            if programs: extracted_info["part1_ProgramName"] = programs[0]
                
    except Exception as error: pass
    return extracted_info

# Full Execution Logic awaiting next session...
```

---

## 📌 Directives For Next Session
1. **Run the Sandbox Extractor:** We will execute this script over the `User` Multi limits and generate `omnisphere_multis_extracted.json`.
2. **Review the JSON Output:** You will review the Part 1/Program Name pairings to verify their structure.
3. **Bridge to MainStage:** You will provide the routing guidance and connections on how these Omnisphere User Multis tie back to your MainStage channel data.

*Have a great night! I've committed this assessment and our findings to the repository. Ready to resume whenever you are.*
