# barkoder_reader.py
import uiautomator2 as u2
import time


DEFAULT_BARCODE_XPATH = '//*[@resource-id="com.barkoder.demoscanner:id/txtBarcodeResult"]'


def collect_barcodes(
    device=None,
    barcode_xpath=DEFAULT_BARCODE_XPATH,
    expand_res_id="com.barkoder.demoscanner:id/layoutExpandBtn",
    click_expand=False,
    expand_delay=0.2,
):
    """
    Lấy barcode đang hiển thị.
    Tuỳ chọn click các nút expand hiện có trên màn hình.
    """
    d = device or u2.connect()
    barcodes = set()

    # 1) Thu barcode đang hiển thị
    for el in d.xpath(barcode_xpath).all():
        text = (el.text or "").strip()
        if text:
            barcodes.add(text)

    # 2) Nếu cần thì click expand (không phụ thuộc vào el.elem.xpath)
    if click_expand:
        btn_xpath = f'//*[@resource-id="{expand_res_id}"]'
        for btn in d.xpath(btn_xpath).all():
            btn.click()
            time.sleep(expand_delay)

    return barcodes

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
