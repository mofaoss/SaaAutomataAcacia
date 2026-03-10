# AI Develop Guidance (One-Shot Version)

This document is formatted for "one-shot" input to an AI.
The user only needs to fill out the [User Input Section] below, then select all (Ctrl+A) and copy the entire page to the AI/Agent.

```text
==================== Complete Instruction Packet for AI (Ready to Execute) ====================

You are developing a PC script module for the game "Snowbreak: Containment Zone" for the SAA project. Strictly follow the instructions in this packet. Do not invent additional protocols.

【Hard Constraints (Must be followed)】
1) Mouse clicks are only allowed using: auto.move_click(...)
   - Do not use auto.click_element(...) for the final click action.
2) Modules use a declarative protocol: the @module(...) decorator directly on the class.
   - Wrappers are not allowed: def run_task_xxx(...): return Xxx(...).run()
3) Module entry point is fixed:
   - class XxxTask:
   - __init__(self, auto, logger)
   - run(self)
4) Every loop must have a timeout (Timer) and an exit condition. Infinite loops are forbidden.
5) Configuration must be read from config.xxx.value, not passed as business values directly from the UI.

【Project Architecture Summary】
1) app/framework: General capabilities (core/application/infra/ui)
2) app/features: Business-specific capabilities (modules/assets/bootstrap/utils)
3) Module Discovery: framework/core/module_system/discovery.py scans app.features.modules.*.usecase.*_usecase

-------------------- User Input Section (User only fills this part) --------------------

Filling Rules (Quick Version):
- Use [y] for checked, [ ] for unchecked.
- Besides "Module Type/Entry Point", prefer writing directly in natural language; no extra checkboxes needed.
- If any field is left blank, the AI must fill it with the default value and proceed.

1) Basic Information
- Module Name (Chinese):
- Module Name (English, optional):
- Objective (one sentence):

2) Module Type (select one, required)
- [ ] periodic (scheduled task, can be queued)
- [ ] on_demand (manually triggered task)
- [ ] Unsure (let AI decide)

3) Page Entry Point (can select multiple)
- [ ] Mount on periodic page
- [ ] Mount on on_demand page
- [ ] Passive toggle (persistent helper)

4) Resolution Confirmation (required)
- Current game resolution (e.g., 1920x1080):
- Is the current aspect ratio 16:9?:
  - [ ] Yes
  - [ ] No
  - [ ] Unsure

5) Prerequisites
- Needs to return to home screen first:
  - [ ] Yes
  - [ ] No
- Needs to enter a specific screen first (write screen name, optional):

6) Process Steps (Default is 3 steps, add Step4/Step5 if needed)
- Step1
  - Recognition Method (write directly, optional):
    - Example: OCR text / Image match / Color block / Unsure
  - Recognition Target (write naturally, AI will auto-detect text/image):
    - Example: Start Battle
    - Example: start_btn.png (usually requires adding this image to resources)
  - Region (optional):
    - Blank / unchecked / wrong format => defaults to full screen
    - If specified, write: x1,y1,x2,y2
  - Threshold (default 0.7, optional):
  - Action (write a natural language sentence, no checkbox needed):
    - Example: Press key F
    - Example: Hold key A for 5 seconds
    - Example: Click 960,540
    - Example: Wait 1.2 seconds
    - Example: Swipe down 300 pixels
- Step2
  - Recognition Method (write directly, optional):
  - Recognition Target (write naturally, AI will auto-detect text/image):
    - Example: Confirm
    - Example: confirm_btn.png (usually requires adding this image to resources)
  - Region (optional):
    - Blank / unchecked / wrong format => defaults to full screen
    - If specified, write: x1,y1,x2,y2
  - Threshold (default 0.7, optional):
  - Action (write a natural language sentence, no checkbox needed):
- Step3
  - Recognition Method (write directly, optional):
  - Recognition Target (write naturally, AI will auto-detect text/image):
    - Example: Complete
    - Example: finish_flag.png (usually requires adding this image to resources)
  - Region (optional):
    - Blank / unchecked / wrong format => defaults to full screen
    - If specified, write: x1,y1,x2,y2
  - Threshold (default 0.7, optional):
  - Action (write a natural language sentence, no checkbox needed):

7) Retries and Timeout
- Max retries per step (default 3):
- Overall timeout in seconds (default 30):
- On failure (default: log error and exit):

8) UI Requirements (AI will infer if not filled)
- [ ] Needs a master CheckBox
- [ ] Needs a mode ComboBox (list options):
- [ ] Needs a count SpinBox (specify range):
- [ ] Needs a text input LineEdit (describe purpose):
- [ ] Needs a threshold Slider (specify range):
- [ ] Needs a start button (usually for on_demand)

9) Resources
- [ ] Need to add new image resources
- Resource directory (default app/features/assets/<module_name>/):
- Note: If a step includes "Image=xxx.png", you should check "Need to add new image resources" here and provide the filename/source.

10) Acceptance Criteria
- Minimum acceptable result:
- Forbidden behaviors (e.g., getting stuck, infinite loops):

11) Optional: Recorded Script Paste Area (for direct conversion)
- Recording source (optional): AHK / AutoHotkey / Python / Other
- Original recorded script (paste multi-line script here):
<<<SCRIPT_START>>>
(Paste recorded script here)
<<<SCRIPT_END>>>
- Conversion requirements (optional):
  - Example: Convert all clicks to move_click, and add recognition and timeouts

-------------------- AI Execution Section (User should not modify) --------------------

You must translate each item from the "User Input Section" into project code without omission. Follow the mappings below:

[A. User Options -> Code Implementation]
1) Module Type
- periodic => @module(host="periodic")
- on_demand => @module(host="on_demand")
- Unsure => Auto-determine:
  - Contains "scheduled/daily/auto-execute" => periodic
  - Contains "manual start/pre-position" => on_demand

2) Entry Point Selection
- periodic checked => Generate/mount periodic UI
- on_demand checked => Generate/mount on_demand UI
- Passive toggle checked => on_demand passive mode (trigger style)

3) Prerequisites
- Return to home=Yes => Call back_to_home(self.auto, self.logger) at the start of run()
- Enter screen => Use as the initial state of the state machine

4) Recognition Method
- OCR => auto.find_element(target, "text", ...)
- Image => auto.find_element("app/features/assets/<module>/<img>", "image", ...)
- Color block => get_crop_form_first_screenshot + color check
- Unsure => Try OCR first, then image match on failure; explain the reasoning in a comment
- If recognition method is blank: auto-infer from "Recognition Target"
  - Looks like plain text => OCR
  - Looks like a filename (.png/.jpg/.jpeg) => Image match
  - Looks like HSV/RGB/color threshold => Color block

5) Action Translation
- Mouse click => Must be auto.move_click(...)
- Key press => auto.press_key / key_down / key_up
- Wait => time.sleep
- Swipe => Use existing automation swipe capabilities
- If action is written in natural language (e.g., "Hold key A for 5 seconds"): you must automatically parse and convert it to code, without requiring the user to select an action type.

6) Region and Threshold
- Region is blank, unchecked, or has wrong format => Default to full screen (do not pass crop)
- Region is valid (x1,y1,x2,y2) => Write to crop
- Threshold is blank => Default to 0.7

[B. Resolution Scaling (Must be implemented)]
1) Read the current window size, with a base design resolution of 1920x1080.
2) Any "pixel coordinate click" must be scaled:
   - scale_x = current_w / 1920
   - scale_y = current_h / 1080
   - click_x = int(base_x * scale_x)
   - click_y = int(base_y * scale_y)
   - auto.move_click(click_x, click_y)
3) Any crop should prioritize storing ratios (0~1) instead of absolute pixels:
   - crop=(x1/1920, y1/1080, x2/1920, y2/1080)
4) If user confirms non-16:9:
   - Prioritize using ratio-based crop + text OCR
   - Reduce strong dependency on template images
   - Log a clear warning that "non-16:9 may affect template matching"
5) If user resolution is uncertain:
   - Generate based on a 1920x1080 design baseline
   - Execute all actions using the scaling formula

[C. auto Key Function Usage Standards]
1) auto.take_screenshot()
   - Call at the beginning of each loop to refresh the current frame.
2) auto.find_element(target, mode, ...)
   - Only responsible for recognition, not the final click.
3) auto.move_click(x, y, ...)
   - The only allowed click action for Snowbreak.
4) auto.press_key(...)
   - For keyboard-triggered actions.
5) auto.get_crop_form_first_screenshot(crop=...)
   - Use for color block detection.

[D. UI Auto-Inference Rules]
1) User didn't specify UI => Generate a minimal UI:
   - CheckBox_enable
   - SpinBox_times
   - ComboBox_mode (if there are branches)
   - Default to a start button under on_demand
2) When user mentions threshold/delay/count/mode/key:
   - Threshold -> Slider/SpinBox
   - Delay -> SpinBox
   - Count -> SpinBox
   - Mode -> ComboBox
   - Key -> LineEdit

[E. Output Order (Must follow this order)]
1) Directory Changes (new/modified files)
2) Usecase core code (class with declarative @module decorator)
3) UI code (if needed)
4) Integration instructions (if auto-mounted, state "no extra registration needed")
5) Test commands and results
6) "Requirement -> Implementation" mapping table
7) If user provided a recorded script, append a "Recorded Statement -> SAA Code" mapping table

[E-1. File Output Format (Must be followed)]
1) Must output one file per code block, do not provide only snippets.
2) Each code block must be preceded by the clear target path (full path or project-relative path).
3) Each code block must be the complete file content, ready to be pasted and overwritten.
4) Code blocks need a language tag (e.g., ```python).
5) If modifying a file, still provide the "full file after modification," not just a diff.

[F. Verification Commands (at least)]
- python -m compileall app
- python scripts/smoke_modules.py

=====================================================================
```
