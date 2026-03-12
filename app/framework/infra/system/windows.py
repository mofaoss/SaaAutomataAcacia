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
    """Mirror main-branch lookup order to avoid resolving a wrong window handle."""

    def is_valid_game_window(hwnd):
        if not hwnd or not win32gui.IsWindow(hwnd):
            return False
        if win32gui.IsIconic(hwnd):
            return False
        rect = win32gui.GetWindowRect(hwnd)
        return (rect[2] - rect[0]) > 0 and (rect[3] - rect[1]) > 0

    def find_class_from_root(root_hwnd, require_valid=True):
        handle_list = [root_hwnd]
        handle_list.extend(enumerate_child_windows(root_hwnd))
        for handle in handle_list:
            if win32gui.GetClassName(handle) != window_class:
                continue
            if not require_valid or is_valid_game_window(handle):
                return handle
        return None

    # Keep compatibility with main branch: start from title root, then inspect descendants.
    root_hwnd = win32gui.FindWindow(None, window_title)
    if root_hwnd:
        matched = find_class_from_root(root_hwnd, require_valid=True)
        if matched:
            return matched
        matched = find_class_from_root(root_hwnd, require_valid=False)
        if matched:
            return matched

    # Fallback for environments where FindWindow may resolve a stale instance.
    def callback(hwnd, results):
        if win32gui.GetWindowText(hwnd) == window_title:
            results.append(hwnd)
        return True

    top_hwnds = []
    win32gui.EnumWindows(callback, top_hwnds)

    for top_hwnd in top_hwnds:
        matched = find_class_from_root(top_hwnd, require_valid=True)
        if matched:
            return matched

    for top_hwnd in top_hwnds:
        matched = find_class_from_root(top_hwnd, require_valid=False)
        if matched:
            return matched

    return None
