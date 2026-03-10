# SAA 开发者手册（当前架构版）

> English 文档仍可参考 `docs/developer_en.md`，但本文件优先代表当前代码现状。

## 0. 第一步（一步到位，最低门槛）

如果你只想“最快把模块做出来”，只做这一节就够了。
直接使用 [AI_develop_guidance.md](E:/workspace/SaaAssistantAca/docs/AI_develop_guidance.md)，按下面 3 步走：

1. 填“用户填写区”（尽量用自然语言，空白项可以不填）。
2. 整页 `Ctrl+A` 复制给 AI/Agent。
3. 让 AI 按输出给出的文件改动直接落地，然后运行：
   - `python -m compileall app`
   - `python scripts/smoke_modules.py`

如果你用的是网页 Chat（AI 不能直接操作本地文件），按这个方法手工落地：

1. 让 AI 先输出“文件清单”，格式必须包含：
   - 新增文件（完整路径）
   - 修改文件（完整路径）
   - 删除文件（如有）
2. 在本地按清单创建目录和文件：
   - 模块代码通常放 `app/features/modules/<模块英文名>/usecase/<模块英文名>_usecase.py`
   - 模块 UI 通常放 `app/features/modules/<模块英文名>/ui/<模块英文名>_interface.py`
   - 模块资源（用于识别的图片模板/特征图）通常放 `app/features/assets/<模块英文名>/`
   - 命名规范：目录名和文件名请使用英文小写蛇形（例如 `collect_supplies`），不要用中文、空格或特殊字符。
3. 让 AI 分文件输出“可直接粘贴”的完整内容（不要只给片段）。
4. 每粘贴完一个文件就保存，最后统一运行编译和 smoke 检查。
5. 如果 AI 给了“移动/重命名”，你在本地文件管理器或 IDE 里执行同名操作即可。

做到这里，通常已经能完成一个可运行模块。
后面的“代码开发章节”是给有余力、要做深度定制/排错/优化的人准备的进阶内容。

---

## 1. 一句话理解架构

把项目想象成“底盘 + 插件”：

- `app/framework`：底盘（通用能力、调度、线程、UI壳子）。
- `app/features`：插件（尘白业务模块、资源、组合根）。
- 模块通过声明式 `@module(...)` 注册。

当前顶层目录只有两层主结构：

- `app/framework`
- `app/features`

---

## 2. 周期任务 vs 非周期任务

### Periodic（周期任务）

- 可排班、可队列串行执行。
- 典型：登录、福利、商店、体力、奖励、退出。
- 页面偏“配置面板”，通常不需要模块内“开始按钮”。

### On-Demand（非周期任务）

- 手动点一次跑一次，常见于场景型功能。
- 典型：钓鱼、水弹、迷宫、抓帕鲁。
- 页面通常带“开始按钮”。

### Passive（被动辅助）

- 仍挂在 on-demand，但不走普通单任务执行流程。
- 典型：trigger 类开关辅助功能。

---

## 3. 当前模块协议（必须遵守）

### 3.1 最小声明

在 `usecase` 文件里直接写：

```python
from app.framework.core.module_system import module

@module(
    id="task_example",
    name="示例任务",
    host="periodic",  # 或 on_demand
)
class ExampleTask:
    def __init__(self, auto, logger):
        self.auto = auto
        self.logger = logger

    def run(self):
        ...
```

### 3.2 当前实现形态

1. 模块以 `@module(...)` 直接声明在 `usecase` 类上。
2. 模块信息由 `module_system` 汇总并自动发现。
3. 运行入口统一是类的 `run(self)`。

### 3.3 自动发现

模块会被自动发现，但文件路径有约束：

- 必须在 `app/features/modules/<module>/usecase/`
- 文件名必须是 `*_usecase.py`

发现逻辑在：

- [discovery.py](E:/workspace/SaaAssistantAca/app/framework/core/module_system/discovery.py)

---

## 4. 开发一个新模块（落地步骤）

## 4.1 建目录

建议最小结构：

```text
app/features/modules/<module_name>/
  ├─ usecase/<module_name>_usecase.py
  └─ ui/<module_name>_interface.py   # 有UI需求时再建
```

资源放到：

- `app/features/assets/<module_name>/`

## 4.2 写 usecase（核心）

必须满足：

1. `__init__(self, auto, logger)`
2. `run(self)` 为入口
3. 循环必须有 `Timer` 超时
4. 日志必须用注入的 `logger`

## 4.3 写 UI（按需）

推荐继承 `ModulePageBase`（自动适配 periodic/on_demand host）：

- [periodic_base.py](E:/workspace/SaaAssistantAca/app/framework/ui/views/periodic_base.py)

## 4.4 接入页面与排序（当前版本单一入口）

当前 UI 映射、默认顺序、periodic 元数据由 framework 统一维护在：

- [decorators.py](E:/workspace/SaaAssistantAca/app/framework/core/module_system/decorators.py)

新增模块时，通常需要补充：

1. `_DEFAULT_ORDER`：模块展示与执行排序。
2. `_FRAMEWORK_DEFAULTS`：页面类路径、`ui_bindings`、periodic 默认策略。

这是当前代码现状下的“单一事实来源”。

---

## 5. auto / 配置 / 日志（开发必读）

## 5.1 auto 常用能力

入口能力在：

- [automation.py](E:/workspace/SaaAssistantAca/app/framework/infra/automation/automation.py)

常用调用顺序（推荐）：

1. `auto.take_screenshot()`
2. `auto.find_element(...)` 判定状态
3. `auto.move_click(...)` / `auto.press_key(...)` 执行动作
4. `Timer` 超时兜底

## 5.2 点击限制（非常重要）

在尘白当前环境，鼠标点击统一使用：

- `auto.move_click(...)`

不要把 `auto.click_element(...)` 当最终点击动作依赖。

## 5.3 配置读取

统一从：

- `config.xxx.value`

不要在模块里直接读 UI 控件值做业务逻辑。

## 5.4 日志

统一使用注入 `logger`，不要 `print`。

---

## 6. 分辨率与坐标规则

当前默认基准是 16:9。
`BaseTask` 会检查比例并设置缩放参数，见：

- [base_task.py](E:/workspace/SaaAssistantAca/app/framework/core/task_engine/base_task.py)

建议：

1. 尽量用比例 crop（0~1）而非绝对像素。
2. 点击坐标按当前窗口尺寸缩放后再 `move_click`。
3. 非 16:9 场景要在日志明确提示风险。

---

## 7. 启动与组合根

业务注入入口在：

- [main_window_wiring.py](E:/workspace/SaaAssistantAca/app/features/bootstrap/main_window_wiring.py)

它负责：

1. 触发模块发现 `discover_modules(...)`
2. 创建 periodic / on-demand 页面宿主
3. 注入 OCR、导航、业务 usecase 依赖

---

## 8. 提交前检查（最低标准）

至少跑：

```bash
python -m compileall app
python scripts/smoke_modules.py
python scripts/smoke_release.py
```

PR 描述建议包含：

1. 改动目的
2. 架构影响（改了哪层）
3. 验证命令与结果
4. 风险与回滚方式

---

## 9. 常见坑（高频）

1. 模块文件名不符合 `*_usecase.py`，导致 discovery 不加载。
2. 忘记在 `decorators.py` 补默认映射，页面挂载失败。
3. 死循环无超时，导致线程无法回收。
4. 路径写旧目录，启动时报 `Cannot open file ...`。
5. 点击未走 `move_click`，实际游戏内动作失效。

---

## 10. 最短上手路径（新同学）

1. 先看并使用 [AI_develop_guidance.md](E:/workspace/SaaAssistantAca/docs/AI_develop_guidance.md)。
2. 复制一个最接近的模块（例如 `collect_supplies` 或 `operation_action`）做最小改造。
3. 保证先“可编译 + 可启动 + 不死循环”，再逐步提精度。
