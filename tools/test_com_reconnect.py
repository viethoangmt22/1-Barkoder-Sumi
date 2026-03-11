"""
test_com_reconnect.py

Test tính năng auto-reconnect của COM reader

Hướng dẫn test:
1. Kết nối Arduino/sensor vào cổng COM
2. Chạy script này
3. Trong lúc script đang chạy, thử:
   - Rút cáp USB ra rồi cắm lại
   - Reset Arduino
   - Ngắt kết nối bằng cách khác
4. Quan sát xem hệ thống có tự động reconnect không

Kết quả mong đợi:
- Khi mất kết nối, sẽ hiện thông báo "Phát hiện mất kết nối"
- Hệ thống tự động thử reconnect tối đa 3 lần
- Sau khi reconnect thành công, tiếp tục đọc dữ liệu bình thường
"""

import sys
import time
import json
from pathlib import Path

# Thêm thư mục cha vào path để import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.com_reader import COMReader, SwitchState


def load_com_config():
    """Đọc cấu hình COM từ config.json"""
    config_path = Path(__file__).parent.parent / "config.json"
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return {
            "com_port": data.get("com_port", "COM3"),
            "baudrate": int(data.get("baudrate", 9600)),
            "timeout": float(data.get("timeout", 1)),
        }
    except FileNotFoundError:
        print(f"⚠ Không tìm thấy {config_path}, dùng cấu hình mặc định")
        return {
            "com_port": "COM3",
            "baudrate": 9600,
            "timeout": 1,
        }
    except Exception as e:
        print(f"⚠ Lỗi đọc config: {e}, dùng cấu hình mặc định")
        return {
            "com_port": "COM3",
            "baudrate": 9600,
            "timeout": 1,
        }


def main():
    print("="*60)
    print("  TEST TÍNH NĂNG AUTO-RECONNECT COM")
    print("="*60)
    print("\nĐể test reconnect:")
    print("  1. Đợi script kết nối và bắt đầu đọc dữ liệu")
    print("  2. Rút cáp USB ra (hoặc reset Arduino)")
    print("  3. Quan sát thông báo reconnect")
    print("  4. Cắm lại cáp USB")
    print("  5. Kiểm tra xem có reconnect thành công không")
    print("\nNhấn Ctrl+C để thoát\n")
    
    # Đọc config
    config = load_com_config()
    print(f"Cấu hình COM: {config['com_port']} @ {config['baudrate']} baud\n")
    
    # Tạo COM reader với auto_reconnect=True
    reader = COMReader(
        port=config["com_port"],
        baudrate=config["baudrate"],
        timeout=config["timeout"],
        auto_reconnect=True,  # Bật auto-reconnect
        max_reconnect_attempts=3,
    )
    
    # Kết nối lần đầu
    print("Đang kết nối lần đầu...")
    if not reader.connect():
        print("\n❌ Không thể kết nối COM")
        print("Kiểm tra:")
        print("  - Cổng COM đã đúng chưa?")
        print("  - Driver COM đã cài chưa?")
        print("  - Sensor đã cắm USB chưa?")
        return
    
    print("\n✅ Kết nối thành công!")
    print("\n" + "="*60)
    print("  BẮT ĐẦU MONITOR (Thử rút cáp để test reconnect)")
    print("="*60 + "\n")
    
    read_count = 0
    error_count = 0
    reconnect_count = 0
    last_connected = True
    
    try:
        while True:
            # Kiểm tra trạng thái kết nối
            is_connected = reader.is_connected()
            
            # Phát hiện chuyển đổi trạng thái kết nối
            if is_connected != last_connected:
                if is_connected:
                    reconnect_count += 1
                    print(f"\n{'='*60}")
                    print(f"  ✅ RECONNECT THÀNH CÔNG (Lần {reconnect_count})")
                    print(f"{'='*60}\n")
                else:
                    print(f"\n{'='*60}")
                    print(f"  ⚠ MẤT KẾT NỐI - Đang thử reconnect...")
                    print(f"{'='*60}\n")
                
                last_connected = is_connected
            
            # Đọc trạng thái switch
            state = reader.read_state()
            read_count += 1
            
            # Hiển thị trạng thái (mỗi 10 lần đọc)
            if read_count % 10 == 0:
                status = "🟢 CONNECTED" if is_connected else "🔴 DISCONNECTED"
                print(f"[{read_count:05d}] {status} | Switch: {state.name}")
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("  KẾT QUẢ TEST")
        print("="*60)
        print(f"Tổng số lần đọc:      {read_count}")
        print(f"Số lần reconnect:     {reconnect_count}")
        print(f"Trạng thái cuối:      {'CONNECTED' if reader.is_connected() else 'DISCONNECTED'}")
        print("="*60)
        print("\n✅ Test hoàn thành!")
    
    finally:
        print("\nĐang đóng kết nối...")
        reader.disconnect()
        print("Đã ngắt kết nối COM")


if __name__ == "__main__":
    main()
