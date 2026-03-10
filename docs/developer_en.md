# SAA Developer Guide (Current Architecture)

> The Chinese document `docs/developer.md` takes precedence in representing the current state of the code.

## 0. First Step (One-Shot, Lowest Barrier to Entry)

If you just want to "get a module done as quickly as possible," this section is all you need.
Directly use AI_develop_guidance.md and follow these 3 steps:

1. Fill out the "User Input Section" (try to use natural language; you can leave items blank).
2. Select the entire page (`Ctrl+A`) and copy it to your AI/Agent.
3. Let the AI apply the file changes from the output directly, then run:
   - `python -m compileall app`
   - `python scripts/smoke_modules.py`

If you are using a web-based Chat (where the AI cannot directly manipulate local files), follow this manual process:

1. Ask the AI to first output a "file list" in a format that must include:
   - New files (full path)
   - Modified files (full path)
   - Deleted files (if any)
2. Create the directories and files locally according to the list:
   - Module code usually goes in `app/features/modules/<module_english_name>/usecase/<module_english_name>_usecase.py`
   - Module UI usually goes in `app/features/modules/<module_english_name>/ui/<module_english_name>_interface.py`
   - Module assets (image templates/features for recognition) usually go in `app/features/assets/<module_english_name>/`
   - Naming convention: Please use lowercase English snake_case for directory and file names (e.g., `collect_supplies`). Do not use Chinese, spaces, or special characters.
3. Ask the AI to output the "paste-ready" full content for each file (don't just provide snippets).
4. Save each file after pasting, and finally, run the compilation and smoke checks all at once.
5. If the AI provides "move/rename" instructions, perform the same operations in your local file manager or IDE.

By this point, you should have a runnable module.
The following "Code Development Chapters" are advanced content for those with the capacity to do deep customization, debugging, or optimization.

---

## 1. Understanding the Architecture in One Sentence

Imagine the project as a "chassis + plugins":

- `app/framework`: The chassis (general capabilities, scheduling, threads, UI shell).
- `app/features`: The plugins (Snowbreak business modules, assets, composition root).
- Modules are registered via a declarative `@module(...)`.

The current top-level directory has only two main structures:

- `app/framework`
- `app/features`

---

## 2. Periodic vs. On-Demand Tasks

### Periodic

- Schedulable, can be executed serially in a queue.
- Typical examples: Login, Supplies, Shop, Stamina, Rewards, Exit.
- The UI page is more of a "configuration panel" and usually doesn't require a "Start Button" within the module.

### On-Demand

- Manually triggered to run once, common for scenario-based features.
- Typical examples: Fishing, Water Bomb, Maze, Capture Pals.
- The UI page usually includes a "Start Button".

### Passive

- Still hosted on the on-demand page but does not follow the normal single-task execution flow.
- Typical examples: Trigger-like helper functionalities.

---

## 3. Current Module Protocol (Must Be Followed)

### 3.1 Minimal Declaration

Write this directly in the `usecase` file:

```python
from app.framework.core.module_system import module

@module(
    id="task_example",
    name="Example Task",
    host="periodic",  # or on_demand
)
class ExampleTask:
    def __init__(self, auto, logger):
        self.auto = auto
        self.logger = logger

    def run(self):
        ...
```

### 3.2 Current Implementation

1. Modules are declared with `@module(...)` directly on the `usecase` class.
2. Module information is aggregated and automatically discovered by the `module_system`.
3. The unified entry point for execution is the class's `run(self)` method.

### 3.3 Auto-Discovery

Modules will be discovered automatically, but there are constraints on file paths:

- Must be in `app/features/modules/<module>/usecase/`
- The filename must be `*_usecase.py`

The discovery logic is in:

- discovery.py

---

## 4. Developing a New Module (Implementation Steps)

## 4.1 Create Directories

The recommended minimal structure is:

```text
app/features/modules/<module_name>/
  ├─ usecase/<module_name>_usecase.py
  └─ ui/<module_name>_interface.py   # Create only if UI is needed
```

Place resources in:

- `app/features/assets/<module_name>/`

## 4.2 Write the Usecase (Core)

Must satisfy:

1. `__init__(self, auto, logger)`
2. `run(self)` as the entry point
3. Loops must have a `Timer` for timeouts
4. Logging must use the injected `logger`

## 4.3 Write the UI (As Needed)

It is recommended to inherit from `ModulePageBase` (which automatically adapts to periodic/on-demand hosts):

- periodic_base.py

## 4.4 Page Integration and Sorting (Current Single Entry Point)

Currently, UI mapping, default order, and periodic metadata are centrally maintained by the framework in:

- decorators.py

When adding a new module, you usually need to add to:

1. `_DEFAULT_ORDER`: For module display and execution sorting.
2. `_FRAMEWORK_DEFAULTS`: For page class paths, `ui_bindings`, and periodic default policies.

This is the "single source of truth" in the current codebase.

---

## 5. auto / Config / Logs (Must-Read for Development)

## 5.1 `auto` Common Capabilities

The entry point for capabilities is in:

- automation.py

Recommended calling order:

1. `auto.take_screenshot()`
2. `auto.find_element(...)` to determine the state
3. `auto.move_click(...)` / `auto.press_key(...)` to perform an action
4. `Timer` for timeout fallback

## 5.2 Click Limitation (Very Important)

In the current Snowbreak environment, all mouse clicks must use:

- `auto.move_click(...)`

Do not rely on `auto.click_element(...)` as the final click action.

## 5.3 Config Reading

Read uniformly from:

- `config.xxx.value`

Do not read UI control values directly for business logic within a module.

## 5.4 Logs

Use the injected `logger` uniformly; do not use `print`.

---

## 6. Resolution and Coordinate Rules

The current default baseline is 16:9.
`BaseTask` will check the ratio and set scaling parameters, see:

- base_task.py

Recommendations:

1. Use ratio-based crop (0-1) instead of absolute pixels whenever possible.
2. Scale click coordinates according to the current window size before calling `move_click`.
3. For non-16:9 scenarios, explicitly log the risks.

---

## 7. Startup and Composition Root

The entry point for business injection is:

- main_window_wiring.py

It is responsible for:

1. Triggering module discovery `discover_modules(...)`
2. Creating the periodic / on-demand page hosts
3. Injecting OCR, navigation, and business usecase dependencies

---

## 8. Pre-Commit Checks (Minimum Standard)

Run at least:

```bash
python -m compileall app
python scripts/smoke_modules.py
python scripts/smoke_release.py
```

Must satisfy:

1. no `ModuleNotFoundError / ImportError / NameError`
2. no UI construction failure in smoke checks
3. startup smoke should not crash early

## 6.3 PR workflow (recommended)

1. Sync `main`, create a feature branch (recommended prefix: `codex/`).
2. Commit in small logical chunks.
3. PR description should include:
   - why this change exists
   - architectural impact (layers/files touched)
   - verification commands and outputs
   - risk and rollback notes
4. Include screenshots/videos for UI changes.

## 6.4 Auto-reject conditions

1. Business logic leaked back into framework generic layer.
2. Hardcoded page/module assembly bypassing registry.
3. Resource path refactor without runtime path fix (`Cannot open file ...` errors).
4. Thread lifecycle leaks (`QThread: Destroyed while thread is still running`).
5. Missing verification evidence.

---

## 7. Troubleshooting

## 7.1 Module not visible

Check:

1. host registration in `module_specs.py`
2. `ui_factory` returns page with valid object name
3. `ui_bindings.page_attr` is unique and accessible

## 7.2 Periodic task never runs

Check:

1. task id exists in `periodic_task_wiring.py`
2. `default_activation_config` schema is valid
3. runtime config has `use_periodic/execution_config` enabled

## 7.3 On-demand log/state mismatch

Check:

1. `OnDemandRunner` state clear path
2. injected `module_thread_cls`
3. module trying to bypass shared log behavior

## 7.4 Tray icon missing

Check:

1. icon files under root `resources/icons` and `resources/logo`
2. `resources/resource.qrc` includes them and `resource_qrc.py` is up to date

---

## 8. Fastest Path for New Contributors

1. Read sections 1, 2, 4, 6 first.
2. Run:
   - `python -m compileall app`
   - `python scripts/smoke_modules.py`
3. Copy `_template`, create a minimal module, register it in `module_specs.py`.
4. Ensure it mounts and starts cleanly.
5. Then add real business logic and config binding.

Once you can finish that loop, you can independently deliver production-grade module PRs in this repo.
