import time

from app.framework.infra.automation.timer import Timer
from app.features.utils.ui import ui_text


def back_to_home(auto, logger, timeout_seconds=10):
    """Business navigation flow: return game UI to home screen."""
    timeout = Timer(timeout_seconds).start()
    while True:
        auto.take_screenshot()

        if auto.find_element(
            "基地",
            "text",
            crop=(1598 / 1920, 678 / 1080, 1661 / 1920, 736 / 1080),
        ) and auto.find_element(
            "任务",
            "text",
            crop=(1452 / 1920, 327 / 1080, 1529 / 1920, 376 / 1080),
        ):
            return True

        if auto.find_element(
            "app/features/assets/reward/home.png",
            "image",
            threshold=0.5,
            crop=(1580 / 1920, 18 / 1080, 1701 / 1920, 120 / 1080),
        ):
            auto.press_key("esc")
            time.sleep(0.5)
            continue

        if auto.click_element(
            "取消",
            "text",
            crop=(463 / 1920, 728 / 1080, 560 / 1920, 790 / 1080),
        ):
            time.sleep(0.3)
            continue

        auto.press_key("esc")
        time.sleep(0.5)

        if timeout.reached():
            logger.error(ui_text("返回主页面超时", "Timeout returning to home page"))
            return False
