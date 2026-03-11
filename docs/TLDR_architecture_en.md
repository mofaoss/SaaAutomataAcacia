# SaaAssistantAca Architecture (Framework-Driven)

## 1. Core Philosophy: Framework vs. Features
The project has transitioned from a traditional layered application to a **Framework-Feature** model.
- **The Framework (`app/framework`)**: Provides the "rules of the game" (rendering, execution, observability, i18n). It is feature-agnostic.
- **The Features (`app/features`)**: Contains vertical business logic (modules). Features "hook" into the framework using decorators and standardized metadata.

---

## 2. Structural Layering

### 📂 `app/framework/` (The Kernel)
- **`core/`**: The brain of the system.
  - `module_system/`: Handles module discovery, `@periodic_module` / `@on_demand_module` decorators, and `config_schema` generation.
  - `task_engine/`: Manages thread lifecycles, schedulers, and `BaseTask` execution.
  - `event_bus/`: Decouples components via pub/sub (e.g., UI logging, task state updates).
- **`application/`**: Business-level orchestration.
  - `modules/`: Standardizes how the UI consumes module specifications (`ModuleSpec`).
  - `periodic/` & `startup/`: Defines the state machine to run the task and interface loading plans.
- **`ui/`**: The Rendering Engine.
  - `auto_page/`: Uses `AutoPageFactory` to dynamically build Qt pages from module metadata.
  - `widgets/` & `themes/`: Shared UI components and visual styles.
- **`infra/`**: Technical adapters.
  - `automation/`: Window control, input simulation.
  - `vision/`: OCR and image recognition services.
- **`i18n/`**: Advanced internationalization supporting dynamic templates and per-module scopes.

### 📂 `app/features/` (The Business)
- **`modules/`**: Vertical slices of functionality (e.g., `fishing`, `chasm`).
  - Structure: Each module is a package containing logic (usecases).
  - Integration: Modules define their configuration via Python Type Hints and `Field()` metadata.

---

## 3. Key Mechanisms

### ⚙️ AutoPage UI Generation (The "No-UI-Code" Flow)
1. **Declaration**: A feature module uses `@periodic_module` and defines variables (e.g., `count: int = Field(default=5)`).
2. **Metadata**: The framework's `ModuleMeta` extracts these types and constraints.
3. **Rendering**: `AutoPageFactory` instantiates a page. `AutoPageBase` iterates over the `config_schema` and maps:
   - `bool` -> `QCheckBox`
   - `int` -> `QSpinBox`
   - `str` -> `QLineEdit` / `QComboBox`
4. **Binding**: `AutoPageActionsMixin` automatically binds UI 'Run' buttons to the module's `runner` method.

### 🧵 Task Execution Model
- **Thread Isolation**: All automation logic runs in a dedicated `TaskThread` to prevent UI freezing.
- **State Tracking**: `RuntimeSession` maintains the global state of the current execution.
- **Communication**: Modules communicate with the UI via `EventBus` signals rather than direct references.

---

## 4. Internationalization (i18n)
The system uses a unique **Runtime Translation** flow:
- **Keys**: Developers use English keys/labels in decorators.
- **Resolution**: `AutoPageI18nMixin` translates these keys on-the-fly using `i18n/runtime.py`.
- **Injection**: Supports dynamic variables in translations using `TemplateRenderer`.

---

## 5. Directory cleanup (Legacy Removal)
The following legacy paths are **fully removed** and must not be used:
- `app/presentation` (replaced by `app/framework/ui`)
- `app/view` & `app/repackage` (obsolete)
- `app/core` (at root, moved to `app/framework/core`)
- `app/modules` (moved to `app/features/modules`)

---

## 6. Development Rules
- **No Direct UI Coding**: Do not write custom Qt layouts for feature modules; use the `AutoPage` system.
- **Type Safety**: Always provide explicit type hints and `Field` descriptions for configuration variables.
- **Decoupling**: Features must never import from `app/framework/ui`. They only provide data/logic; the framework handles the display.
- **Runtime Pathing**: Always use the standardized `runtime/appdata`, `runtime/log`, and `runtime/temp` directories.
