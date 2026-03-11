import win32api
import win32con
import win32gui


def is_fullscreen(hwnd):
    window_rect = win32gui.GetWindowRect(hwnd)
    window_width = window_rect[2] - window_rect[0]
    window_height = window_rect[3] - window_rect[1]

    screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

    return window_width == screen_width and window_height == screen_height


def enumerate_child_windows(parent_hwnd):
    def callback(handle, windows):
        windows.append(handle)
        return True

    child_windows = []
    win32gui.EnumChildWindows(parent_hwnd, callback, child_windows)
    return child_windows


def get_hwnd(window_title, window_class):
    """
    更稳健地获取窗口句柄：
    1. 遍历所有顶层窗口，寻找标题匹配的窗口
    2. 在匹配标题的窗口及其子窗口中寻找匹配类名的窗口
    3. 严格选择可见、有尺寸且非最小化的窗口
    """
    def is_valid_game_window(h):
        if not win32gui.IsWindow(h) or not win32gui.IsWindowVisible(h):
            return False
        # 排除最小化窗口（最小化窗口在某些系统下 rect 为 0）
        if win32gui.IsIconic(h):
            return False
        rect = win32gui.GetWindowRect(h)
        if rect[2] - rect[0] <= 0 or rect[3] - rect[1] <= 0:
            return False
        return True

    def callback(hwnd, results):
        if win32gui.GetWindowText(hwnd) == window_title:
            results.append(hwnd)
        return True

    top_hwnds = []
    win32gui.EnumWindows(callback, top_hwnds)

    # 第一轮：寻找符合条件的顶级窗口
    for top_hwnd in top_hwnds:
        if win32gui.GetClassName(top_hwnd) == window_class:
            if is_valid_game_window(top_hwnd):
                return top_hwnd

    # 第二轮：如果顶级窗口没找到，再找子窗口（针对某些特殊启动器结构）
    for top_hwnd in top_hwnds:
        child_hwnds = enumerate_child_windows(top_hwnd)
        for ch in child_hwnds:
            if win32gui.GetClassName(ch) == window_class:
                if is_valid_game_window(ch):
                    return ch

    # 第三轮：如果还是没找到（可能窗口被最小化了），返回一个可见的但可能尺寸有问题的句柄
    for top_hwnd in top_hwnds:
        if win32gui.GetClassName(top_hwnd) == window_class:
            if win32gui.IsWindowVisible(top_hwnd):
                return top_hwnd
        child_hwnds = enumerate_child_windows(top_hwnd)
        for ch in child_hwnds:
            if win32gui.GetClassName(ch) == window_class:
                if win32gui.IsWindowVisible(ch):
                    return ch
                
    return None

