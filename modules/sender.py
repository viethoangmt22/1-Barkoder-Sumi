"""
sender.py

Giả lập scanner barcode truyền thống bằng cách:
- Gõ text
- Nhấn Enter

Dùng cho hệ thống camera barcode
"""

import time
import keyboard


def send_barcodes(barcodes, delay=0.2):
    """
    barcodes: list[str]
    delay: thời gian nghỉ giữa mỗi barcode (giây)
    """

    if not barcodes:
        print("[SENDER] Không có barcode để gửi")
        return

    print("[SENDER] Bắt đầu gửi barcode...")

    for code in barcodes:
        code = code.strip()
        print(f"[SENDER] Gửi: {code}")
        keyboard.write(code)
        keyboard.press_and_release("enter")
        time.sleep(delay)

    print("[SENDER] Hoàn thành gửi barcode")


# -----------------------------
# Test nhanh
# -----------------------------
def main():
    print("⚠️ Click vào ô nhập liệu trước khi test (Notepad, Excel, ERP...)")
    time.sleep(5)

    test_data = [
        "P61897449",
        "Q00001000",
        "Q00002000",
        "B12345678"
    ]

    send_barcodes(test_data)


if __name__ == "__main__":
    main()
