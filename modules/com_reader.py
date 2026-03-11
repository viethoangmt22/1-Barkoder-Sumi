"""
com_reader.py

Đọc tín hiệu từ cổng COM để phát hiện cảm biến switch (ON/OFF)
Dùng serial port để nhận tín hiệu từ Arduino/PLC/sensor

Tín hiệu mong đợi:
- "1" hoặc "ON"  → Switch bật (thùng đã đặt vào)
- "0" hoặc "OFF" → Switch tắt (thùng được nhấc ra)

Tính năng:
- Auto-reconnect: Tự động kết nối lại khi phát hiện mất kết nối
- Retry mechanism: Thử kết nối lại với exponential backoff
- Connection monitoring: Kiểm tra trạng thái kết nối liên tục
"""

import serial
import time
from enum import Enum


class SwitchState(Enum):
    """Trạng thái của switch"""
    OFF = 0
    ON = 1


class COMReader:
    def __init__(self, port=None, baudrate=9600, timeout=1, auto_reconnect=True, max_reconnect_attempts=3):
        """
        Khởi tạo COM reader
        
        Args:
            port: Tên cổng COM (vd: 'COM3'). Bắt buộc phải truyền
            baudrate: Tốc độ truyền (mặc định 9600)
            timeout: Thời gian chờ đọc (giây)
            auto_reconnect: Tự động reconnect khi mất kết nối (mặc định True)
            max_reconnect_attempts: Số lần thử reconnect tối đa (mặc định 3)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.last_state = SwitchState.OFF
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        self._reconnect_count = 0
    
    def connect(self):
        """
        Kết nối tới cổng COM
        
        Returns:
            bool: True nếu kết nối thành công
        """
        try:
            if not self.port:
                print("[COM] Thiếu cổng COM. Vui lòng cấu hình com_port trong config.json")
                return False
            
            # Mở kết nối serial
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            # Chờ Arduino reset (nếu có)
            time.sleep(2)
            
            # Clear buffer
            self.serial.reset_input_buffer()
            
            print(f"[COM] Kết nối thành công: {self.port} @ {self.baudrate} baud")
            return True
            
        except serial.SerialException as e:
            print(f"[COM] Lỗi kết nối: {e}")
            return False
    
    def disconnect(self):
        """Ngắt kết nối COM"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("[COM] Đã ngắt kết nối")
    
    def is_connected(self):
        """
        Kiểm tra trạng thái kết nối COM
        
        Returns:
            bool: True nếu đang kết nối, False nếu mất kết nối
        """
        try:
            if not self.serial:
                return False
            
            if not self.serial.is_open:
                return False
            
            # Thử đọc trạng thái để kiểm tra kết nối thực sự
            # Nếu cổng COM bị rút ra hoặc lỗi phần cứng, sẽ raise exception
            _ = self.serial.in_waiting
            return True
            
        except (serial.SerialException, OSError, AttributeError):
            return False
    
    def reconnect(self, max_attempts=None):
        """
        Thử kết nối lại COM với số lần thử tối đa
        
        Args:
            max_attempts: Số lần thử tối đa (None = dùng giá trị mặc định)
            
        Returns:
            bool: True nếu reconnect thành công
        """
        if max_attempts is None:
            max_attempts = self.max_reconnect_attempts
        
        print(f"[COM] Đang thử reconnect... (tối đa {max_attempts} lần)")
        
        # Đóng kết nối cũ nếu còn tồn tại
        try:
            if self.serial and self.serial.is_open:
                self.serial.close()
        except:
            pass
        
        # Thử kết nối lại với retry
        for attempt in range(1, max_attempts + 1):
            print(f"[COM] Lần thử {attempt}/{max_attempts}...")
            
            if self.connect():
                self._reconnect_count = 0
                print(f"[COM] ✓ Reconnect thành công!")
                return True
            
            if attempt < max_attempts:
                wait_time = min(2 ** attempt, 10)  # Exponential backoff, max 10s
                print(f"[COM] Chờ {wait_time}s trước khi thử lại...")
                time.sleep(wait_time)
        
        print(f"[COM] ✗ Reconnect thất bại sau {max_attempts} lần thử")
        return False

    def send_signal(self, value: str, with_newline: bool = True) -> bool:
        """
        Gửi tín hiệu ra cổng COM (ví dụ: "1", "2", "3").
        Tự động reconnect nếu phát hiện mất kết nối (khi auto_reconnect=True)

        Returns:
            bool: True nếu gửi thành công, False nếu lỗi
        """
        # Kiểm tra kết nối trước khi gửi
        if not self.is_connected():
            if self.auto_reconnect:
                print("[COM] ⚠ Phát hiện mất kết nối, đang thử reconnect trước khi gửi...")
                if not self.reconnect():
                    print("[COM] Không thể gửi tín hiệu: Reconnect thất bại")
                    return False
            else:
                print("[COM] Không thể gửi tín hiệu: COM chưa kết nối")
                return False

        try:
            payload = value.strip()
            if with_newline:
                payload += "\n"

            self.serial.write(payload.encode("utf-8"))
            self.serial.flush()
            print(f"[COM] → Đã gửi tín hiệu: {value}")
            return True
        except (serial.SerialException, OSError) as e:
            print(f"[COM] Lỗi gửi tín hiệu '{value}': {e}")
            
            # Thử reconnect và gửi lại
            if self.auto_reconnect:
                print("[COM] Đang thử reconnect sau lỗi gửi...")
                if self.reconnect():
                    try:
                        payload = value.strip()
                        if with_newline:
                            payload += "\n"
                        self.serial.write(payload.encode("utf-8"))
                        self.serial.flush()
                        print(f"[COM] → Đã gửi tín hiệu (sau reconnect): {value}")
                        return True
                    except:
                        pass
            
            return False
        except Exception as e:
            print(f"[COM] Lỗi không xác định khi gửi '{value}': {e}")
            return False
    
    def read_state(self):
        """
        Đọc trạng thái hiện tại của switch
        Tự động reconnect nếu phát hiện mất kết nối (khi auto_reconnect=True)
        
        Returns:
            SwitchState: ON hoặc OFF
        """
        # Kiểm tra kết nối trước khi đọc
        if not self.is_connected():
            if self.auto_reconnect:
                print("[COM] ⚠ Phát hiện mất kết nối, đang thử reconnect...")
                if self.reconnect():
                    print("[COM] Reconnect thành công, tiếp tục đọc dữ liệu")
                else:
                    print("[COM] Không thể reconnect, trả về trạng thái OFF")
                    return SwitchState.OFF
            else:
                return SwitchState.OFF
        
        try:
            # Đọc dữ liệu từ serial
            if self.serial.in_waiting > 0:
                raw_data = self.serial.readline().decode('utf-8').strip()
                
                # Parse tín hiệu
                if raw_data in ('1', 'ON', 'on', 'HIGH'):
                    self.last_state = SwitchState.ON
                elif raw_data in ('0', 'OFF', 'off', 'LOW'):
                    self.last_state = SwitchState.OFF
                    
            return self.last_state
            
        except (serial.SerialException, OSError) as e:
            print(f"[COM] Lỗi đọc dữ liệu: {e}")
            
            # Nếu auto_reconnect, thử kết nối lại
            if self.auto_reconnect:
                print("[COM] Đang thử reconnect sau lỗi...")
                if self.reconnect():
                    # Thử đọc lại sau khi reconnect
                    try:
                        if self.serial.in_waiting > 0:
                            raw_data = self.serial.readline().decode('utf-8').strip()
                            if raw_data in ('1', 'ON', 'on', 'HIGH'):
                                self.last_state = SwitchState.ON
                            elif raw_data in ('0', 'OFF', 'off', 'LOW'):
                                self.last_state = SwitchState.OFF
                    except:
                        pass
            
            return self.last_state
        except Exception as e:
            print(f"[COM] Lỗi không xác định: {e}")
            return self.last_state
    
    def wait_for_on(self, timeout=None):
        """
        Chờ cho đến khi switch bật (ON)
        
        Args:
            timeout: Thời gian chờ tối đa (giây), None = chờ vô hạn
            
        Returns:
            bool: True nếu switch đã ON, False nếu timeout
        """
        return self._wait_for_state_stable(
            target_state=SwitchState.ON,
            timeout=timeout,
            stable_seconds=0.3,
            poll_interval=0.05,
            waiting_message="[COM] Đang chờ switch ON...",
            success_message="[COM] ✓ Switch ON (ổn định)",
            timeout_message="[COM] ✗ Timeout chờ switch ON",
        )
    
    def wait_for_off(self, timeout=None):
        """
        Chờ cho đến khi switch tắt (OFF)
        
        Args:
            timeout: Thời gian chờ tối đa (giây), None = chờ vô hạn
            
        Returns:
            bool: True nếu switch đã OFF, False nếu timeout
        """
        return self._wait_for_state_stable(
            target_state=SwitchState.OFF,
            timeout=timeout,
            stable_seconds=0.3,
            poll_interval=0.05,
            waiting_message="[COM] Đang chờ switch OFF...",
            success_message="[COM] ✓ Switch OFF (ổn định)",
            timeout_message="[COM] ✗ Timeout chờ switch OFF",
        )

    def _wait_for_state_stable(
        self,
        target_state,
        timeout,
        stable_seconds,
        poll_interval,
        waiting_message,
        success_message,
        timeout_message,
    ):
        """
        Chờ đến khi target_state giữ ổn định liên tục trong stable_seconds.
        Đây là debounce phần mềm để lọc nhiễu bấm/nhả nhanh.
        """
        start_time = time.time()
        stable_start = None

        print(waiting_message)

        while True:
            state = self.read_state()

            if state == target_state:
                if stable_start is None:
                    stable_start = time.time()

                if (time.time() - stable_start) >= stable_seconds:
                    print(success_message)
                    return True
            else:
                stable_start = None

            if timeout and (time.time() - start_time) > timeout:
                print(timeout_message)
                return False

            time.sleep(poll_interval)


# ============================================================
# Test nhanh
# ============================================================

def main():
    """
    Test module COM reader
    Yêu cầu:
    - Kết nối Arduino/sensor tới cổng COM
    - Arduino gửi "1" hoặc "0" qua Serial
    """
    
    # Test nhanh bằng cổng COM cấu hình sẵn
    reader = COMReader(port="COM3")
    
    if not reader.connect():
        print("Không thể kết nối. Kiểm tra:")
        print("  - Sensor đã cắm USB chưa?")
        print("  - Driver COM đã cài chưa?")
        return
    
    print("\n" + "="*50)
    print("TEST COM READER")
    print("="*50)
    print("\nĐọc trạng thái liên tục. Nhấn Ctrl+C để thoát.\n")
    
    try:
        while True:
            state = reader.read_state()
            print(f"Switch: {state.name}")
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n\nDừng test")
    
    finally:
        reader.disconnect()


if __name__ == "__main__":
    main()
