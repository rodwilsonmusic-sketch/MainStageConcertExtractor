# Agent Directives & Sandbox Rules

1. **The Ultimate Goal**: Assist the user in building concerts, needed screens, and JS scripts for the Midi Assistant.
2. **The Sandbox Environment**: The folder `/Users/rodney_wilson/Desktop/BackStage/BS Learning` is the designated playground.
3. **Strict Read-Only Mandate for BackStage**:
   - MUST **NOT** write, overwrite, modify, or delete *any* file inside the live `/Users/rodney_wilson/Desktop/BackStage` directory or its subfolders.
   - Allowed to **read** from the live `BackStage` folder to learn from ongoing changes, structure, and code.
   - Allowed to **copy** files from `BackStage` into the `BS Learning` folder for testing.
4. **Separation of Tasks & Data Growth**:
   - **Heavy Data Lifting & Extraction**: All large-scale XML/Plist parsing, deep extraction, and learning from libraries must be done exclusively here in the `ConcertExtractorUtility` workspace. 
   - **Midi Assistant UI/Configuration**: The `BS Learning` folder is used strictly for replicating the BackStage environment and testing configurations (like config.json).
   - **No Big Data Growth in Sandbox**: Do not store massive extracted datasets or cause big data growth in the `BS Learning` directory. Keep heavy data parsing constrained to `ConcertExtractorUtility`.
