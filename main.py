"""
main.py

Điều phối toàn bộ luồng xử lý barcode:
1. Khởi động app Barkoder trên điện thoại
2. Hiện menu → user chọn loại thùng (to / nhỏ)
3. User nhấn 's' → khởi động camera scan
4. Tự động thu thập barcode liên tục
5. Phân loại → xử lý session → gửi kết quả
6. Lặp lại cho đến khi xong

Luồng phím:
    1/2  = chọn thùng to / nhỏ
    s    = bắt đầu scan (khởi động camera)
    h    = quay lại menu chọn thùng
    q    = thoát chương trình
"""

import sys
import time
import uiautomator2 as u2

# Import các module trong project
from modules.input_handler import (
    get_command_from_keyboard,
    CMD_START,      # s = bắt đầu
    CMD_HOME,       # h = quay lại
    CMD_BOX_BIG,    # 1 = thùng to
    CMD_BOX_SMALL,  # 2 = thùng nhỏ
    CMD_EXIT,       # q = thoát
)
from modules.barkoder_reader import (
    close_app,
    start_barkoder_app,
    start_industrial_1d_scan,
    collect_barcodes,
    back_home_from_industrial_1d_scan,
)
from modules.classifier import classify_barcodes, pretty_print
from modules.session_manager import SessionManager
from modules.sender import send_barcodes


# ============================================================
# CÁC HÀM HIỂN THỊ (UI trên terminal)
# ============================================================

def print_header():
    """In banner khi mở chương trình"""
    print("=" * 50)
    print("  HỆ THỐNG QUÉT BARCODE TỰ ĐỘNG")
    print("  Barkoder + Camera")
    print("=" * 50)


def print_home_menu():
    """In menu chọn loại thùng"""
    print("\n" + "-" * 40)
    print("  CHỌN LOẠI THÙNG")
    print("-" * 40)
    print("  1 = Thùng TO  (1P, 1Q, 1B)")
    print("  2 = Thùng NHỎ (P chung, Q1, Q2, B chung)")
    print("  q = Thoát chương trình")
    print("-" * 40)


# ============================================================
# HÀM CHỌN LOẠI THÙNG
# ============================================================

def choose_box_type():
    """
    Hiện menu, đợi user nhấn 1 hoặc 2.

    Returns:
        "BIG"   nếu chọn thùng to
        "SMALL" nếu chọn thùng nhỏ
        None    nếu user thoát (đã gọi sys.exit)
    """
    print_home_menu()

    while True:
        cmd = get_command_from_keyboard()

        if cmd == CMD_BOX_BIG:
            print("\n>>> Đã chọn: THÙNG TO")
            return "BIG"

        elif cmd == CMD_BOX_SMALL:
            print("\n>>> Đã chọn: THÙNG NHỎ")
            return "SMALL"

        elif cmd == CMD_EXIT:
            close_app()
            print("\n[EXIT] Thoát chương trình. Tạm biệt!")
            sys.exit(0)

        else:
            print("  Vui lòng nhấn 1, 2 hoặc q")


# ============================================================
# HÀM SCAN 1 SESSION (nhiều bước)
# ============================================================

def run_scan_session(device, steps):
    """
    Chạy qua tất cả các bước scan tuần tự.

    Mỗi bước:
        1. Đợi user nhấn 'a' → collect_barcodes
        2. Phân loại → gọi handler tương ứng
        3. Nếu OK → chuyển bước tiếp
        4. Nếu FAIL → cho phép thử lại (nhấn 'a' lần nữa)

    Params:
        device: đối tượng uiautomator2
        steps: list of (mô_tả, handler_function)
            Ví dụ: [
                ("Bước 1/2: Mặt A - P + Q", session.handle_big_box_face_a),
                ("Bước 2/2: Mặt B - Batch", session.handle_big_box_face_b),
            ]

    Returns:
        True  = hoàn thành tất cả bước
        False = user nhấn 'h' (quay lại home)
    """

    # --------------------------------------------------
    # Bước 0: Đợi user nhấn 's' để khởi động camera
    # --------------------------------------------------
    print("\n  Nhấn 's' để bắt đầu quét")
    print("  Nhấn 'h' để quay lại chọn thùng")

    while True:
        cmd = get_command_from_keyboard()

        if cmd == CMD_START:
            print("\n[SCAN] Đang khởi động camera...")
            start_industrial_1d_scan(device)
            print("[SCAN] Camera sẵn sàng!")
            break

        elif cmd == CMD_HOME:
            return False

        elif cmd == CMD_EXIT:
            close_app(device)
            print("\n[EXIT] Thoát chương trình. Tạm biệt!")
            sys.exit(0)

        else:
            print("  Nhấn 's' để bắt đầu")

    # --------------------------------------------------
    # Lặp qua từng bước scan
    # --------------------------------------------------
    for i, (description, handler) in enumerate(steps):
        print(f"\n{'=' * 40}")
        print(f"  {description}")
        print(f"{'=' * 40}")
        print("  Đặt thùng trước camera, chương trình sẽ tự quét")
        print("  Nhấn Ctrl+C để dừng khẩn cấp")

        # Vòng lặp tự động quét cho phép thử lại nếu scan thất bại
        step_done = False
        step_start = time.time()
        timeout_seconds = 120
        poll_interval = 0.5

        while not step_done:
            if time.time() - step_start > timeout_seconds:
                print("\n[TIMEOUT] Quá thời gian chờ scan, quay lại menu")
                back_home_from_industrial_1d_scan(device)
                return False

            print("\n[SCAN] Đang thu thập barcode...")
            barcodes = collect_barcodes(device)

            if not barcodes:
                time.sleep(poll_interval)
                continue

            print(f"[SCAN] Tìm thấy {len(barcodes)} barcode: {barcodes}")

            # Phân loại barcode (P, Q, B, UNKNOWN)
            classified = classify_barcodes(barcodes)
            pretty_print(classified)

            # Gọi handler của session để xử lý bước này
            ok, msg = handler(classified)
            print(f"\n[SESSION] {msg}")

            if ok:
                # Quay lại màn hình chính của scan (reset dữ liệu trên app)
                back_home_from_industrial_1d_scan(device)
                # Bước này thành công!
                # Nếu còn bước tiếp → khởi động lại camera
                if i < len(steps) - 1:
                    print("[SCAN] Chuẩn bị bước tiếp...")
                    start_industrial_1d_scan(device)
                step_done = True
            else:
                # Scan thất bại → cho phép thử lại
                print("\n  !!! Scan thất bại, vui lòng đặt lại thùng !!!")
                

    # Tất cả bước đã hoàn thành
    return True


# ============================================================
# FLOW THÙNG TO
# ============================================================

def run_big_box_flow(device, session):
    """
    Flow thùng TO gồm 2 bước:
        Bước 1: Chụp mặt A → Product Number (P) + Quantity (Q)
        Bước 2: Xoay thùng, chụp mặt B → Batch (B)

    Returns:
        True nếu hoàn thành, False nếu user huỷ
    """
    steps = [
        ("Bước 1/2: Chụp mặt A — Product (P) + Quantity (Q)",
         session.handle_big_box_face_a),

        ("Bước 2/2: Xoay thùng, chụp mặt B — Batch (B)",
         session.handle_big_box_face_b),
    ]

    return run_scan_session(device, steps)


# ============================================================
# FLOW THÙNG NHỎ
# ============================================================

def run_small_box_flow(device, session):
    """
    Flow thùng NHỎ gồm 3 bước:
        Bước 1: Thùng nhỏ 1 → P + Q1
        Bước 2: Thùng nhỏ 2 → P (phải trùng) + Q2
        Bước 3: Batch chung → B

    Returns:
        True nếu hoàn thành, False nếu user huỷ
    """
    steps = [
        ("Bước 1/3: Thùng nhỏ 1 — Product (P) + Quantity 1 (Q1)",
         session.handle_small_box_1),

        ("Bước 2/3: Thùng nhỏ 2 — Product (P) + Quantity 2 (Q2)",
         session.handle_small_box_2),

        ("Bước 3/3: Batch chung (B)",
         session.handle_big_box_batch),
    ]

    return run_scan_session(device, steps)


# ============================================================
# HÀM CHÍNH
# ============================================================

def main():
    """
    Luồng chính của chương trình:

    ┌─────────────────────────────────────┐
    │  Khởi động app Barkoder             │
    │            ↓                        │
    │  Chọn loại thùng (1 hoặc 2)        │  ← vòng lặp chính
    │            ↓                        │
    │  Nhấn 's' → khởi động camera       │
    │            ↓                        │
    │  Tự quét → xử lý                 │  ← lặp từng bước
    │            ↓                        │
    │  Gửi kết quả (sender)              │
    │            ↓                        │
    │  Quay lại chọn thùng               │
    └─────────────────────────────────────┘
    """

    print_header()

    # --------------------------------------------------
    # Bước 0: Kết nối điện thoại & khởi động app
    # --------------------------------------------------
    print("\n[INIT] Đang kết nối thiết bị Android...")

    try:
        device = u2.connect()
        print("[INIT] Kết nối thành công!")
    except Exception as e:
        print(f"[ERROR] Không thể kết nối thiết bị: {e}")
        print("  → Kiểm tra USB / ADB đã bật chưa")
        return

    print("[INIT] Đang khởi động app Barkoder...")
    start_barkoder_app(device)
    print("[INIT] App sẵn sàng!\n")

    # Tạo session manager để quản lý state
    session = SessionManager()

    # --------------------------------------------------
    # Vòng lặp chính: chọn thùng → scan → gửi → lặp lại
    # --------------------------------------------------
    while True:
        # Reset session về trạng thái ban đầu
        session.reset()

        # Bước 1: Chọn loại thùng
        box_type = choose_box_type()

        # Bước 2: Chạy flow tương ứng
        if box_type == "BIG":
            success = run_big_box_flow(device, session)
        else:
            success = run_small_box_flow(device, session)

        # Bước 3: Gửi kết quả nếu hoàn thành
        if success:
            result = session.get_result()

            if result:
                # Lọc bỏ None (VD: Q2 = None cho thùng to)
                barcodes_to_send = [code for code in result if code is not None]

                print(f"\n[SEND] Đang gửi {len(barcodes_to_send)} barcode...")
                send_barcodes(barcodes_to_send)
                print("[SEND] Hoàn thành!")
            else:
                print("\n[ERROR] Không có dữ liệu để gửi")

            print("\n>>> Quay lại menu chọn thùng...")
        else:
            # User nhấn 'h' → quay lại chọn thùng (không cần thông báo thêm)
            print("\n>>> Quay lại menu chọn thùng...")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[EXIT] Đã dừng chương trình (Ctrl+C)")
    except SystemExit:
        pass
    except Exception as e:
        print(f"\n[ERROR] Lỗi không mong đợi: {e}")
        print("  → Vui lòng kiểm tra kết nối thiết bị và thử lại")
