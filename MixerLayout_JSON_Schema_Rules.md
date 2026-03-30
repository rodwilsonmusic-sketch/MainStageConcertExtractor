# MixerLayout JSON Schema Rules for Autonomous Agents

This document STRICTLY defines how autonomous agents must format SwiftUI `.json` payloads when generating UI Subs-screens for the Midi Assistant App.
DO NOT hallucinate keys like `parameterTarget`, `layout`, or arbitrary dictionary wrappers. 

## 1. SubScreen Architecture
A valid Mixer Sub-Screen is always an Object inside the `subScreens` array.
For dynamic UI generation, `layoutType` MUST be `"dynamic"`, and it uses `panels` to build grids.

```json
{
  "id": "UUID-HERE",
  "name": "Screen Name",
  "layoutType": "dynamic",
  "controls": [],
  "panels": [
    // This array holds the top-level Column/Row containers
  ]
}
```

## 2. Panels and Axis Wrapping
`SubScreenPanel` objects contain `axis` ("vertical" or "horizontal"), `controls`, and recursive `subPanels`.
**CRITICAL:** If you want multiple rows stacked vertically on top of each other, you MUST wrap them in a master `vertical` panel inside the `panels` array.

```json
{
  "id": "UUID-MASTER",
  "axis": "vertical",
  "subPanels": [
    {
      "id": "UUID-ROW-1",
      "axis": "horizontal",
      "controls": [ /* ControlDefs go here */ ]
    },
    {
      "id": "UUID-ROW-2",
      "axis": "horizontal",
      "controls": [ /* ControlDefs go here */ ]
    }
  ],
  "controls": []
}
```

## 3. ControlDef (The UI Elements)
A `ControlDef` defines an individual knob, button, or fader.
**CRITICAL RULE:** DO NOT use `parameterTarget`. Parameter routing logic is handled natively via the strict `namespace` key.

*   `id`: String UUID
*   `name`: Display Label
*   `displayType`: One of: `fader`, `horizontalFader`, `toggleButton`, `momentaryButton`, `knob`, `steppedKnob`, `pickerMenu`
*   `namespace`: The strict routing binder string (e.g. `"Worship Pads Omnishere > Omnispher > 3 Level"`). It must perfectly match the internal channel/plugin map.
*   `outputs`: Always include an empty array `[]` as a fallback.
*   `frameWidth` / `frameHeight`: (Optional) Explicit pixel bounds. If omitted, the SwiftUI engine applies perfect geometric defaults.

### Example Fader Object:
```json
{
  "id": "UUID-FADER-1",
  "name": "Platinum Shiny Strings",
  "displayType": "horizontalFader",
  "namespace": "Worship Pads Omnishere > Omnispher > 1 Level",
  "outputs": []
}
```

## 4. Execution Protocol
If the User asks you to construct a JSON screen payload for iOS/Mac:
1. Parse the requested Channel/Names from XML.
2. Build the precise nested Array structure exactly as outlined above.
3. Supply ONLY string UUIDs using a standard v4 generator.
4. Output the raw text block perfectly formatted so the User or backend Agent can inject it.
