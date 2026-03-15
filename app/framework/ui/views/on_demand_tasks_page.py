import re
from functools import partial

from PySide6.QtCore import QEasingCurve, QParallelAnimationGroup, QPropertyAnimation, QPoint
from PySide6.QtWidgets import QFrame, QSizePolicy, QWidget, QVBoxLayout
from rapidfuzz import process
from qfluentwidgets import SpinBox, CheckBox, ComboBox, LineEdit, Slider, SwitchButton

from app.framework.infra.config.app_config import config
from app.framework.infra.events.signal_bus import signalBus
from app.framework.ui.shared.style_sheet import StyleSheet
from app.framework.ui.shared.widget_tree import get_all_children

from app.framework.ui.views.on_demand_tasks_view import OnDemandTasksView
from .periodic_base import BaseInterface
from app.framework.infra.logging.gui_logger import setup_ui_logger
from app.framework.ui.shared.log_startup_logo import insert_startup_logo
from app.framework.core.event_bus.global_task_bus import global_task_bus
from app.framework.application.modules import HostContext, get_on_demand_module_specs
from app.framework.application.periodic.on_demand_runner import OnDemandRunner
from app.framework.application.periodic.periodic_settings_usecase import PeriodicSettingsUseCase
from app.framework.core.task_engine.threads import ModuleTaskThread
from app.framework.i18n import _


class OnDemandTasksPage(QFrame, BaseInterface):
    """On-demand task host: a single-run specialization over periodic scheduling primitives."""

    def __init__(
        self,
        text: str,
        parent=None,
        *,
        shared_log_browser=None,
        module_thread_cls=ModuleTaskThread,
    ):
        super().__init__(parent)
        BaseInterface.__init__(self)
        self.ui = OnDemandTasksView(self)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self.ui)
        self.setObjectName(text.replace(' ', '-'))
        self.parent = parent
        self.task_coordinator = global_task_bus

        self.module_specs = get_on_demand_module_specs(include_passive=True)
        self.module_pages = {}
        self._task_metadata = {}
        self._page_name_to_task_id = {}
        self._mount_module_pages()
        self._build_task_metadata()
        self.module_thread_cls = module_thread_cls
        self._background_task_threads = {}


        # 鍏ㄥ眬浜掓枼浠诲姟璋冨害涓績鐘舵€?
        self.on_demand_runner = OnDemandRunner()

        # 鎵€鏈?additional 妯″潡缁熶竴鍏变韩鏃ュ織
        self._active_log_browser = shared_log_browser or self.ui.textBrowser_shared_log
        self._bind_shared_logger(self._active_log_browser)

        self._load_config()
        self._connect_to_slot()
        self.ui.sharedLogTitle.setText(_('Shared Log'))
        if self.stackedWidget.count() > 0:
            first_page = self.stackedWidget.widget(0)
            self.SegmentedWidget.setCurrentItem(first_page.objectName())
            self.stackedWidget.setCurrentWidget(first_page)
        StyleSheet.ON_DEMAND_TASKS_INTERFACE.apply(self)
        self._left_panel_animation_group = None

    def play_left_panel_animation(self):
        left_pane = getattr(self.ui, "leftPane", None)
        if left_pane is None or not left_pane.isVisible():
            return

        end_pos = left_pane.pos()
        start_pos = QPoint(end_pos.x(), end_pos.y() + 26)
        left_pane.move(start_pos)

        animation = QPropertyAnimation(left_pane, b"pos", self)
        animation.setDuration(220)
        animation.setStartValue(start_pos)
        animation.setEndValue(end_pos)
        animation.setEasingCurve(QEasingCurve.OutCubic)

        group = QParallelAnimationGroup(self)
        group.addAnimation(animation)
        self._left_panel_animation_group = group
        group.start(QParallelAnimationGroup.DeletionPolicy.DeleteWhenStopped)

    def _bind_shared_logger(self, log_browser):
        self._active_log_browser = log_browser or self.ui.textBrowser_shared_log
        insert_startup_logo(self._active_log_browser)
        self.shared_logger = setup_ui_logger(
            "logger_additional_shared",
            self._active_log_browser,
        )
        self.task_loggers = {
            spec.id: self.shared_logger for spec in self.module_specs
        }

    def set_shared_sidebar_cards(self, cards: list[QWidget], *, shared_log_browser=None):
        if cards:
            self.ui.show_external_sidebar_cards(cards)
            if shared_log_browser is not None:
                self._bind_shared_logger(shared_log_browser)
            return

        self.release_shared_sidebar_cards()

    def release_shared_sidebar_cards(self, *, shared_log_browser=None) -> list[QWidget]:
        cards = self.ui.take_external_sidebar_cards()
        self.ui.show_internal_sidebar()
        if shared_log_browser is not None:
            self._bind_shared_logger(shared_log_browser)
        else:
            self._bind_shared_logger(self.ui.textBrowser_shared_log)
        return cards

    def __getattr__(self, item):
        ui = self.__dict__.get('ui')
        if ui is not None and hasattr(ui, item):
            return getattr(ui, item)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")

    # ---------------- 缁熶竴浠诲姟璋冨害涓績 ----------------

    def _mount_module_pages(self):
        for spec in self.module_specs:
            page = spec.ui_factory(self, HostContext.ON_DEMAND)
            if hasattr(page, "bind_host_context"):
                page.bind_host_context(HostContext.ON_DEMAND)
            page_name = page.objectName()
            self.module_pages[spec.id] = page

            self.ui.add_page(
                page,
                page_name,
                spec.get_display_name(),
            )

            bindings = spec.ui_bindings
            if bindings is not None and bindings.page_attr:
                setattr(self, bindings.page_attr, page)

            # additional 缁熶竴鍏变韩鏃ュ織锛屾ā鍧楀唴鏃ュ織鍗＄墖涓嶅啀浣滀负鐙珛鏃ュ織鍑哄彛
            local_log_card = getattr(page, "SimpleCardWidget_log", None)
            if local_log_card is not None:
                local_log_card.setVisible(False)
            self._collapse_module_local_sidebar(page, local_log_card)

            if not spec.passive and spec.module_class is not None:
                self._page_name_to_task_id[page_name] = spec.id

    def _build_task_metadata(self):
        for spec in self.module_specs:
            if spec.passive or spec.module_class is None:
                continue
            bindings = spec.ui_bindings
            if bindings is None:
                continue
            page = getattr(self, bindings.page_attr, None)
            if page is None:
                continue

            self._task_metadata[spec.id] = {
                "module_class": spec.module_class,
                "name": spec.name,
                "name_msgid": spec.name_msgid,
                "page_attr": bindings.page_attr,
                "start_button_attr": bindings.start_button_attr,
                "card_widget_attr": bindings.card_widget_attr,
                "on_demand_execution": getattr(spec, "on_demand_execution", "exclusive"),
                "on_demand_background_keys": tuple(getattr(spec, "on_demand_background_keys", ()) or ()),
            }

    @staticmethod
    def _resolve_task_button(page: QWidget | None, task_id: str, configured_attr: str | None):
        if page is None:
            return None

        attr_candidates = [
            configured_attr,
            "PushButton_start",
            f"PushButton_start_{task_id}",
        ]
        for attr in attr_candidates:
            if not attr:
                continue
            button = getattr(page, attr, None)
            if button is not None and hasattr(button, "clicked"):
                return button

        object_name_candidates = [
            configured_attr,
            f"PushButton_start_{task_id}",
            "PushButton_start",
        ]
        for object_name in object_name_candidates:
            if not object_name:
                continue
            button = page.findChild(QWidget, object_name)
            if button is not None and hasattr(button, "clicked"):
                return button

        return None

    @staticmethod
    def _resolve_task_card(page: QWidget | None, task_id: str, configured_attr: str | None):
        if page is None:
            return None

        attr_candidates = [
            configured_attr,
            "SimpleCardWidget_option",
            f"SimpleCardWidget_{task_id}",
            "settings_container",
        ]
        for attr in attr_candidates:
            if not attr:
                continue
            card = getattr(page, attr, None)
            if isinstance(card, QWidget):
                return card

        object_name_candidates = [
            configured_attr,
            f"SimpleCardWidget_{task_id}",
            "SimpleCardWidget_option",
        ]
        for object_name in object_name_candidates:
            if not object_name:
                continue
            card = page.findChild(QWidget, object_name)
            if isinstance(card, QWidget):
                return card

        return None


    @staticmethod
    def _coerce_line_edit_text(value) -> str:
        if value is None:
            return ""
        if isinstance(value, (list, tuple, set)):
            return ", ".join(str(item) for item in value)
        return str(value)

    def _collapse_module_local_sidebar(self, page: QWidget, local_log_card: QWidget | None):
        if local_log_card is not None:
            local_log_card.setMinimumWidth(0)
            local_log_card.setMaximumWidth(0)
            local_log_card.setSizePolicy(
                QSizePolicy.Policy.Ignored,
                QSizePolicy.Policy.Ignored,
            )
            local_log_card.updateGeometry()

        right_layout = getattr(page, "right_layout", None)
        main_layout = getattr(page, "main_layout", None)
        left_layout = getattr(page, "left_layout", None)

        if right_layout is not None:
            while right_layout.count():
                right_item = right_layout.takeAt(0)
                right_widget = right_item.widget()
                if right_widget is not None:
                    right_widget.setParent(None)

        if main_layout is not None and right_layout is not None:
            right_layout_index = -1
            left_layout_index = -1
            for idx in range(main_layout.count()):
                item = main_layout.itemAt(idx)
                if item.layout() is right_layout:
                    right_layout_index = idx
                elif left_layout is not None and item.layout() is left_layout:
                    left_layout_index = idx

            if right_layout_index >= 0:
                main_layout.takeAt(right_layout_index)

            if left_layout_index >= 0:
                main_layout.setStretch(left_layout_index, 1)

        page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        page.updateGeometry()

    def _get_task_metadata(self):
        return self._task_metadata

    @staticmethod
    def _execution_policy(meta: dict) -> str:
        policy = str(meta.get("on_demand_execution", "exclusive") or "exclusive").strip().lower()
        return "background" if policy == "background" else "exclusive"

    def _build_module_thread(self, task_id: str, module_class: type, logger):
        meta = self._get_task_metadata().get(task_id, {})
        return self.module_thread_cls(
            module_class,
            logger_instance=logger,
            task_id=task_id,
            task_name=self._task_display_name(meta, task_id),
        )

    def _is_background_task_running(self, task_id: str) -> bool:
        thread = self._background_task_threads.get(task_id)
        if thread is None:
            return False
        try:
            running = bool(thread.isRunning())
        except Exception:
            running = False
        if not running:
            self._background_task_threads.pop(task_id, None)
        return running

    def _start_background_task(self, task_id: str):
        if self._is_background_task_running(task_id):
            return
        meta = self._get_task_metadata().get(task_id)
        if not meta:
            return

        module_class = meta.get("module_class")
        if module_class is None:
            return

        logger = self.task_loggers.get(task_id, self.logger)
        thread = self._build_module_thread(task_id, module_class, logger)
        thread.is_running.connect(
            lambda is_running, selected_task_id=task_id: self._on_background_thread_state_changed(
                selected_task_id,
                is_running,
            )
        )
        self._background_task_threads[task_id] = thread
        thread.start()
        self._refresh_task_ui()

    def _stop_background_task(self, task_id: str):
        thread = self._background_task_threads.get(task_id)
        if thread is None:
            return
        if thread.isRunning():
            thread.stop()
            return
        self._background_task_threads.pop(task_id, None)
        self._refresh_task_ui()

    def _task_id_for_widget(self, widget: QWidget | None) -> str | None:
        if widget is None:
            return None
        for task_id, meta in self._get_task_metadata().items():
            page = getattr(self, meta.get("page_attr", ""), None)
            if page is None:
                continue
            if widget is page or page.isAncestorOf(widget):
                return task_id
        return None

    def _background_should_run(self, task_id: str) -> bool:
        meta = self._get_task_metadata().get(task_id, {})
        module_class = meta.get("module_class")
        if module_class is None:
            return False

        predicate = getattr(module_class, "should_background_run", None)
        if callable(predicate):
            try:
                return bool(predicate(config))
            except TypeError:
                try:
                    return bool(predicate())
                except Exception:
                    return False
            except Exception:
                return False

        configured_keys = tuple(meta.get("on_demand_background_keys", ()) or ())
        if not configured_keys:
            return False

        for field_name in configured_keys:
            cfg_item = getattr(config, str(field_name), None)
            if cfg_item is None:
                continue
            if bool(getattr(cfg_item, "value", False)):
                return True
        return False

    def _sync_background_task(self, task_id: str):
        if self._background_should_run(task_id):
            self._start_background_task(task_id)
            return
        self._stop_background_task(task_id)

    def _toggle_background_task(self, task_id: str):
        if self._is_background_task_running(task_id):
            self._stop_background_task(task_id)
            return
        self._start_background_task(task_id)

    def _on_background_thread_state_changed(self, task_id: str, is_running: bool):
        if not is_running:
            self._background_task_threads.pop(task_id, None)
        self._refresh_task_ui()

    def _handle_universal_start_stop(self, clicked_task_id: str):
        meta = self._get_task_metadata().get(clicked_task_id, {})
        if self._execution_policy(meta) == "background":
            self._toggle_background_task(clicked_task_id)
            return

        self.on_demand_runner.toggle(
            clicked_task_id,
            is_global_running=getattr(self, "is_global_running", False),
            request_global_stop=self.task_coordinator.request_stop,
            get_module_class=lambda task_id: (
                self._get_task_metadata().get(task_id, {}).get("module_class")
            ),
            get_logger=lambda task_id: self.task_loggers.get(task_id, self.logger),
            build_thread=lambda task_id, module_class, logger: self._build_module_thread(
                task_id,
                module_class,
                logger,
            ),
            on_thread_state_changed=self._sync_all_ui_state,
        )

    def _refresh_task_ui(self):
        meta_dict = self._get_task_metadata()
        running_task_id = self.on_demand_runner.state.current_task_id
        external_running = bool(getattr(self, "is_global_running", False))
        external_name = getattr(self, "_external_running_name", "")
        external_name_msgid = getattr(self, "_external_running_name_msgid", "")

        for task_id, meta in meta_dict.items():
            page = getattr(self, meta["page_attr"], None)
            btn = self._resolve_task_button(page, task_id, meta["start_button_attr"])
            card = self._resolve_task_card(page, task_id, meta["card_widget_attr"])
            if not btn:
                continue

            policy = self._execution_policy(meta)
            if policy == "background":
                current_name = self._task_display_name(meta, task_id)
                if self._is_background_task_running(task_id):
                    btn.setText(_('Stop {var_0} (F8)').format(var_0=current_name))
                    if card is not None:
                        self.set_simple_card_enable(card, False)
                else:
                    btn.setText(_('Start {var_0}').format(var_0=current_name))
                    if card is not None:
                        self.set_simple_card_enable(card, True)
                continue

            if external_running:
                if str(external_name or "").strip():
                    stop_name = self._state_display_name(external_name, external_name_msgid, source="external")
                else:
                    stop_name = self._task_display_name(meta, task_id)
                btn.setText(_('Stop {stop_name} (F8)').format(stop_name=stop_name))
                if card is not None:
                    self.set_simple_card_enable(card, False)
                continue

            if running_task_id is not None:
                running_meta = meta_dict.get(running_task_id, {})
                running_name = self._task_display_name(running_meta, running_task_id)
                btn.setText(_('Stop {running_name} (F8)').format(running_name=running_name))
                if card is not None:
                    self.set_simple_card_enable(card, False)
                continue

            btn.setText(_('Start {var_0}').format(var_0=self._task_display_name(meta, task_id)))
            if card is not None:
                self.set_simple_card_enable(card, True)

    def _sync_all_ui_state(self, is_running: bool):
        meta_dict = self._get_task_metadata()
        running_task_id = self.on_demand_runner.state.current_task_id
        if is_running and running_task_id is not None:
            running_meta = meta_dict.get(running_task_id, {})
            name = self._task_display_name(running_meta, running_task_id)
            self.task_coordinator.publish_state(
                True,
                name,
                str(running_meta.get("name_msgid", "") or ""),
                "on_demand",
            )
        else:
            self.task_coordinator.publish_state(False, "", "", "on_demand")
            self.on_demand_runner.clear()

        self._refresh_task_ui()

    def start_current_visible_task(self):
        current_page = self.stackedWidget.currentWidget()
        if current_page is None:
            return

        current_page_name = current_page.objectName()
        task_id = self._page_name_to_task_id.get(current_page_name)
        meta = self._get_task_metadata().get(task_id)
        if not meta:
            return

        # Modules without a host-level start button (e.g. background toggles)
        # are controlled by their own switches, not by global start shortcuts.
        page = getattr(self, meta.get("page_attr", ""), None)
        button = self._resolve_task_button(page, task_id, meta.get("start_button_attr"))
        if button is None:
            return

        self._handle_universal_start_stop(task_id)

    def _on_global_state_changed(self, is_running: bool, task_name: str, task_name_msgid: str, source: str):
        if source in {"on_demand", "additional"}:
            return
        self.is_global_running = is_running
        self._external_running_name = task_name
        self._external_running_name_msgid = task_name_msgid
        self._refresh_task_ui()

    def _on_global_stop_request(self):
        if self.on_demand_runner.state.current_task_id is not None:
            self.on_demand_runner.stop_current()

    def _connect_to_slot(self):
        self.task_coordinator.state_changed.connect(self._on_global_state_changed)
        self.task_coordinator.stop_requested.connect(self._on_global_stop_request)
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)

        for task_id, meta in self._get_task_metadata().items():
            page = getattr(self, meta["page_attr"], None)
            if page is None:
                continue
            button = self._resolve_task_button(page, task_id, meta["start_button_attr"])
            if button is None:
                continue
            button.clicked.connect(
                lambda checked=False, selected_task_id=task_id: self._handle_universal_start_stop(selected_task_id)
            )

        self._connect_to_save_changed()

        if hasattr(self, "page_fishing"):
            self.page_fishing.LineEdit_fish_key.editingFinished.connect(
                lambda: self.update_fish_key(self.page_fishing.LineEdit_fish_key.text())
            )
            signalBus.updateFishKey.connect(self.update_fish_key)

        self._refresh_task_ui()

    def _load_config(self):
        self.settings_usecase = PeriodicSettingsUseCase()  # Ensure it exists
        self.settings_usecase.apply_config_to_widgets(self.findChildren(QWidget))
        
        for page in self.module_pages.values():
            if hasattr(page, 'update_label_color'):
                page.update_label_color()
            if hasattr(page, 'load_config'):
                page.load_config()

    def _connect_to_save_changed(self):
        from app.framework.application.periodic.periodic_ui_binding_usecase import PeriodicUiBindingUseCase
        self.settings_usecase = PeriodicSettingsUseCase()
        self.ui_binding_usecase = PeriodicUiBindingUseCase()

        # Connect main UI
        self.ui_binding_usecase.connect_config_bindings(
            root_widget=self.ui,
            on_widget_change=self.save_changed,
        )
        # Connect all module pages
        for task_id, page in self.module_pages.items():
            self.ui_binding_usecase.connect_config_bindings(
                root_widget=page,
                on_widget_change=self.save_changed,
            )

    def save_changed(self, widget, *args, **kwargs):
        # Use the robust unified persistence logic
        self.settings_usecase.persist_widget_change(widget)

        # Handle page-specific side effects
        if hasattr(widget, "objectName"):
            name = widget.objectName()
            if "water_bomb" in name and hasattr(self, "page_water_bomb") and hasattr(self.page_water_bomb, 'load_config'):
                self.page_water_bomb.load_config()

        # Sync background tasks if needed
        task_id = self._task_id_for_widget(widget)
        if task_id:
            meta = self._get_task_metadata().get(task_id, {})
            if self._execution_policy(meta) == "background":
                self._sync_background_task(task_id)
        
        # CRITICAL: Notify PeriodicTasksPage to snapshot these changes into the current preset
        signalBus.taskConfigChanged.emit()

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.SegmentedWidget.setCurrentItem(widget.objectName())

    def is_valid_format(self, input_string):
        pattern = r'^(\d+),(\d+),(\d+)$'
        match = re.match(pattern, input_string)
        if match:
            int_values = [int(match.group(1)), int(match.group(2)), int(match.group(3))]
            if all(0 <= value <= 255 for value in int_values):
                return True
        return False

    def update_fish_key(self, key):
        if not hasattr(self, "page_fishing"):
            return
        choices = ["ctrl", "space", "shift"]
        best_match = process.extractOne(key, choices)
        if best_match[1] > 60:
            key = best_match[0]
        self.page_fishing.LineEdit_fish_key.setText(key.lower())
        config.set(config.LineEdit_fish_key, key.lower())

    def set_simple_card_enable(self, simple_card, enable: bool):
        children = get_all_children(simple_card)
        for child in children:
            if isinstance(child, (CheckBox, SwitchButton, LineEdit, SpinBox, ComboBox)):
                if child.objectName() == 'LineEdit_fish_base' and enable:
                    continue
                child.setEnabled(enable)

    def showEvent(self, event):
        super().showEvent(event)
        self._load_config()

    def get_shared_log_browser(self):
        return self._active_log_browser
