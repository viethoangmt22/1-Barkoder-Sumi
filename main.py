"""
main.py

Điều phối toàn bộ luồng xử lý barcode:
1. Khởi động app Barkoder trên điện thoại
2. Chạy AUTO mode bằng cảm biến COM
3. Tự động thu thập barcode liên tục
4. Phân loại → xử lý session → gửi kết quả
5. Lặp lại cho đến khi xong
"""

import sys
import time
import json
import atexit
import signal
import ctypes
import uiautomator2 as u2

# Import các module trong project
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
from modules.com_reader import COMReader, SwitchState


# ============================================================
# CONFIGURATION
# ============================================================

CONFIG_FILE = "config.json"

# ============================================================
# CLEANUP/EXIT HANDLER
# ============================================================

_cleanup_callbacks = []
_cleanup_done = False
_win_console_handler_ref = None


def register_cleanup(callback):
    """Đăng ký callback cleanup, sẽ chạy khi thoát app."""
    _cleanup_callbacks.append(callback)


def run_cleanup():
    """
    Chạy cleanup 1 lần duy nhất.
    Dùng cho cả Ctrl+C, lỗi runtime, và nhấn nút X trên cửa sổ console.
    """
    global _cleanup_done

    if _cleanup_done:
        return

    _cleanup_done = True

    # Chạy ngược thứ tự đăng ký: tài nguyên tạo sau sẽ đóng trước
    for callback in reversed(_cleanup_callbacks):
        try:
            callback()
        except Exception:
            pass


def _signal_handler(signum, frame):
    """Handle SIGINT/SIGTERM."""
    run_cleanup()

    # Tránh raise trong handler, thoát nhanh gọn
    raise SystemExit(0)


def install_exit_handlers():
    """
    Đăng ký handler thoát cho nhiều tình huống:
    - Ctrl+C (SIGINT)
    - SIGTERM
    - Đóng cửa sổ console bằng nút X (Windows)
    """
    global _win_console_handler_ref

    # Luôn chạy cleanup khi interpreter thoát bình thường
    atexit.register(run_cleanup)

    # Ctrl+C / SIGTERM
    signal.signal(signal.SIGINT, _signal_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _signal_handler)

    # Windows: bắt sự kiện đóng console bằng nút X
    if sys.platform.startswith("win"):
        HandlerRoutine = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_uint)

        def _win_console_handler(ctrl_type):
            # 2=CTRL_CLOSE_EVENT, 5=LOGOFF, 6=SHUTDOWN
            if ctrl_type in (0, 1, 2, 5, 6):
                run_cleanup()
            # False để Windows tiếp tục tiến trình đóng process
            return False

        _win_console_handler_ref = HandlerRoutine(_win_console_handler)
        ctypes.windll.kernel32.SetConsoleCtrlHandler(_win_console_handler_ref, True)


def load_config(config_path=CONFIG_FILE):
    """
    Đọc file config.json và validate bắt buộc com_port.

    Format tối thiểu:
    {
      "com_port": "COM3"
    }
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise RuntimeError(
            f"Không tìm thấy {config_path}. Vui lòng tạo file config với com_port"
        )
    except json.JSONDecodeError as e:
        raise RuntimeError(f"File {config_path} không đúng JSON: {e}")

    com_port = str(data.get("com_port", "")).strip()
    if not com_port:
        raise RuntimeError("Thiếu com_port trong config.json")

    baudrate = int(data.get("baudrate", 9600))
    timeout = float(data.get("timeout", 1))

    return {
        "com_port": com_port,
        "baudrate": baudrate,
        "timeout": timeout,
    }


# ============================================================
# CÁC HÀM HIỂN THỊ (UI trên terminal)
# ============================================================

def print_header():
    """In banner khi mở chương trình"""
    print("=" * 50)
    print("  HỆ THỐNG QUÉT BARCODE TỰ ĐỘNG")
    print("  Barkoder + Camera")
    print("=" * 50)


# ============================================================
# AUTO MODE (tự động phân loại bằng cảm biến COM)
# ============================================================

def auto_scan_until_step_ok(
    com,
    device,
    step_title,
    handler,
    timeout_seconds=120,
    poll_interval=0.3,
    initial_focus_delay=0.5,
):
    """
    Quét liên tục trong khi switch vẫn ON cho đến khi step hợp lệ.

    Returns:
        (ok, extra, reason)
        - ok=True  : step đã hợp lệ
        - ok=False : step thất bại
        - extra    : dữ liệu thêm của handler (vd: next_step ở step 2)
        - reason   : "ok" | "switch_off" | "timeout" | "invalid"
    """
    print(f"[AUTO] Đang thu thập barcode ({step_title})...")
    time.sleep(initial_focus_delay)

    started_at = time.time()

    while True:
        # Nếu thùng đã bị nhấc ra thì dừng step hiện tại
        if com.read_state() == SwitchState.OFF:
            print("[AUTO] ⚠ Switch đã OFF trước khi chốt dữ liệu step")
            return False, None, "switch_off"

        # Timeout để tránh loop vô hạn
        if time.time() - started_at > timeout_seconds:
            print(f"[AUTO] ⚠ Timeout {timeout_seconds}s, chưa chốt được dữ liệu step")
            return False, None, "timeout"

        barcodes = collect_barcodes(device)
        if not barcodes:
            time.sleep(poll_interval)
            continue

        print(f"[AUTO] Tìm thấy {len(barcodes)} barcode: {barcodes}")
        classified = classify_barcodes(barcodes)
        pretty_print(classified)

        # Handler có thể trả 2 tuple hoặc 3 tuple
        result = handler(classified)

        if len(result) == 3:
            ok, msg, extra = result
        else:
            ok, msg = result
            extra = None

        print(f"[AUTO] {msg}")

        if ok:
            return True, extra, "ok"

        # Chưa hợp lệ thì tiếp tục quét trong lúc switch vẫn ON
        print("[AUTO] Dữ liệu chưa hợp lệ, tiếp tục quét...")
        time.sleep(poll_interval)

def run_auto_mode(device, session, com_config):
    """
    AUTO MODE: Tự động phát hiện loại thùng bằng cảm biến switch
    
    Luồng:
    ┌─────────────────────────────────────┐
    │  Switch ON (lần 1)                  │
    │    → Scan P + Q → Lưu Step 1       │
    │  Switch OFF → Nhấc thùng ra        │
    │                                     │
    │  Switch ON (lần 2)                  │
    │    → Phân nhánh:                   │
    │       • Có Batch → THÙNG TO        │
    │       • Có P+Q → THÙNG NHỎ #2      │
    │                                     │
    │  (Nếu thùng nhỏ) Switch ON (lần 3) │
    │    → Scan Batch chung              │
    │                                     │
    │  Gửi dữ liệu → Reset → Lặp lại    │
    └─────────────────────────────────────┘
    """
    
    # Kết nối COM reader
    print("\n[AUTO] Đang kết nối cảm biến COM...")
    com = COMReader(
        port=com_config["com_port"],
        baudrate=com_config["baudrate"],
        timeout=com_config["timeout"],
    )
    
    if not com.connect():
        print("[AUTO] Không thể kết nối COM. Thoát chế độ auto.")
        return

    # Đảm bảo đóng COM cả khi người dùng tắt app đột ngột
    register_cleanup(com.disconnect)
    
    print("[AUTO] Chế độ AUTO đã sẵn sàng!")
    print("[AUTO] Đặt thùng lên băng chuyền để bắt đầu...\n")
    
    try:
        while True:
            # Reset session
            session.reset()
            
            # ===== STEP 1: Chờ switch ON → Scan P + Q =====
            print("\n" + "="*50)
            print("  STEP 1: Chờ thùng đầu tiên...")
            print("="*50)
            
            com.wait_for_on()
            start_industrial_1d_scan(device)
            ok, _, fail_reason = auto_scan_until_step_ok(
                com=com,
                device=device,
                step_title="P + Q",
                handler=session.handle_small_box_1,
                timeout_seconds=120,
            )

            if not ok:
                if fail_reason == "timeout":
                    print("[AUTO] ⚠ Step 1 timeout: xem như không có thùng, về HOME để chờ.")
                else:
                    print("[AUTO] ✗ Step 1 thất bại. Bỏ qua thùng này.")
                back_home_from_industrial_1d_scan(device)
                com.wait_for_off()
                continue
            
            print("[AUTO] ✓ Step 1 hoàn thành")
            com.send_signal("1")
            back_home_from_industrial_1d_scan(device)

            
            # Chờ thùng được nhấc ra
            com.wait_for_off()
            
            # ===== STEP 2: Chờ switch ON → Phân nhánh =====
            print("\n" + "="*50)
            print("  STEP 2: Chờ thùng tiếp theo (Batch hoặc Thùng #2)...")
            print("="*50)
            
            com.wait_for_on()
            start_industrial_1d_scan(device)
            ok, next_step, fail_reason = auto_scan_until_step_ok(
                com=com,
                device=device,
                step_title="Batch hoặc P + Q",
                handler=session.handle_auto_step_2_smart,
                timeout_seconds=120,
            )

            if not ok:
                if fail_reason == "timeout":
                    print("[AUTO] ⚠ Step 2 timeout: xem như không có thùng, về HOME để chờ.")
                else:
                    print("[AUTO] ✗ Step 2 thất bại. Reset session.")
                back_home_from_industrial_1d_scan(device)
                com.wait_for_off()
                continue
            
            back_home_from_industrial_1d_scan(device)
            com.send_signal("2")
            
            # Nếu đã xong (THÙNG TO) → gửi data
            if next_step == "DONE":
                print("\n[AUTO] ✓ Phát hiện THÙNG TO - Hoàn thành!")
                com.send_signal("3")
                com.wait_for_off()
                
                # Gửi dữ liệu
                result = session.get_result()
                if result:
                    barcodes_to_send = [code for code in result if code is not None]
                    print(f"\n[SEND] Đang gửi {len(barcodes_to_send)} barcode...")
                    send_barcodes(barcodes_to_send)
                    print("[SEND] Hoàn thành!")

                # Giữ app ở HOME để chờ thùng mới
                back_home_from_industrial_1d_scan(device)
                
                print("\n>>> Chờ thùng tiếp theo...\n")
                continue
            
            # Nếu chưa xong (THÙNG NHỎ) → chờ step 3
            com.wait_for_off()
            back_home_from_industrial_1d_scan(device)
            
            # ===== STEP 3: Chờ Batch chung =====
            print("\n" + "="*50)
            print("  STEP 3: Chờ Batch chung...")
            print("="*50)
            
            com.wait_for_on()
            start_industrial_1d_scan(device)
            ok, _, fail_reason = auto_scan_until_step_ok(
                com=com,
                device=device,
                step_title="Batch",
                handler=session.handle_big_box_batch,
                timeout_seconds=120,
            )

            if not ok:
                if fail_reason == "timeout":
                    print("[AUTO] ⚠ Step 3 timeout: xem như không có thùng, về HOME để chờ.")
                else:
                    print("[AUTO] ✗ Step 3 thất bại. Reset session.")
                back_home_from_industrial_1d_scan(device)
                com.wait_for_off()
                continue
            
            print("\n[AUTO] ✓ THÙNG NHỎ hoàn thành!")
            com.send_signal("3")
            back_home_from_industrial_1d_scan(device)
            com.wait_for_off()
            
            # Gửi dữ liệu
            result = session.get_result()
            if result:
                barcodes_to_send = [code for code in result if code is not None]
                print(f"\n[SEND] Đang gửi {len(barcodes_to_send)} barcode...")
                send_barcodes(barcodes_to_send)
                print("[SEND] Hoàn thành!")
            
            print("\n>>> Chờ thùng tiếp theo...\n")
    
    except KeyboardInterrupt:
        print("\n[AUTO] Dừng chế độ auto")
    
    finally:
        com.disconnect()
        close_app(device)


# ============================================================
# HÀM CHÍNH
# ============================================================

def main():
    """
    Entry point chính - Khởi động AUTO mode
    """

    print_header()
    install_exit_handlers()

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
    register_cleanup(lambda: close_app(device))
    print("[INIT] App sẵn sàng!\n")

    # Tạo session manager
    session = SessionManager()

    # Đọc config bắt buộc com_port
    try:
        config = load_config()
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        return

    print("\n" + "="*50)
    print("  CHẾ ĐỘ: AUTO (Cảm biến COM)")
    print("="*50)
    print(f"[CONFIG] COM Port: {config['com_port']}")
    run_auto_mode(device, session, config)


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
