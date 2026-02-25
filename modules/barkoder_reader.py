# barkoder_reader.py
import uiautomator2 as u2
import time


DEFAULT_BARCODE_XPATH = '//*[@resource-id="com.barkoder.demoscanner:id/txtBarcodeResult"]'


def collect_barcodes(
    device=None,
    xpath=DEFAULT_BARCODE_XPATH,
    scroll_delay=0.1,
    max_idle_rounds=1
):
    """
    Thu thập toàn bộ barcode đang hiển thị trong Barkoder app.

    Returns:
        set[str]: tập barcode không trùng
    """
    d = device or u2.connect()

    all_barcodes = set()
    last_count = -1
    idle_rounds = 0

    while True:
        last_count = len(all_barcodes)

        elements = d.xpath(xpath).all()
        for el in elements:
            if el.text:
                all_barcodes.add(el.text.strip())

        if not d(scrollable=True).exists:
            break

        d(scrollable=True).scroll.forward()
        time.sleep(scroll_delay)

        if len(all_barcodes) == last_count:
            idle_rounds += 1
            if idle_rounds >= max_idle_rounds:
                break
        else:
            idle_rounds = 0

    return all_barcodes


def back_home_from_industrial_1d_scan(device=None):
    """
    Quay về màn hình chính của app Barkoder để reset dữ liệu.
    Dùng cách đóng/mở app thay vì nhấn back để đảm bảo luôn về đúng home screen.
    """
    d = device or u2.connect()

    # Đóng và mở lại app để đảm bảo về đúng trang chủ
    d.app_stop("com.barkoder.demoscanner")
    time.sleep(0.3)  # Chờ app đóng hoàn toàn
    d.app_start("com.barkoder.demoscanner")
    time.sleep(0.5)  # Chờ app khởi động xong

def back_to_main_screen(device=None):
    """
    Quay lại màn hình chính của app Barkoder Demo Scanner.

    Không phụ thuộc nút Back: đóng và mở lại app.
    """
    d = device or u2.connect()
    # Đảm bảo về đúng trang chủ bằng cách khởi động lại app.
    d.app_stop("com.barkoder.demoscanner")
    d.app_start("com.barkoder.demoscanner")

def close_app(device=None):
    d = device or u2.connect()
    # Đảm bảo về đúng trang chủ bằng cách khởi động lại app.
    d.app_stop("com.barkoder.demoscanner")

def start_industrial_1d_scan(device=None):
    """
    Khởi động phần đọc barcode 1D Industrial.
    """
    d = device or u2.connect()
    # Click vào thẻ 1D Industrial để vào màn hình quét.
    d(resourceId="com.barkoder.demoscanner:id/cardBarcodesIndustrial1D").click()

def start_barkoder_app(device=None):
    """
    Khởi động app Barkoder Demo Scanner.
    """
    d = device or u2.connect()
    d.app_start("com.barkoder.demoscanner")

if __name__ == "__main__":
    back_home_from_industrial_1d_scan()
