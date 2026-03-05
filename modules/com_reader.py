"""
com_reader.py

Đọc tín hiệu từ cổng COM để phát hiện cảm biến switch (ON/OFF)
Dùng serial port để nhận tín hiệu từ Arduino/PLC/sensor

Tín hiệu mong đợi:
- "1" hoặc "ON"  → Switch bật (thùng đã đặt vào)
- "0" hoặc "OFF" → Switch tắt (thùng được nhấc ra)
"""

import serial
import time
from enum import Enum


class SwitchState(Enum):
    """Trạng thái của switch"""
    OFF = 0
    ON = 1


class COMReader:
    def __init__(self, port=None, baudrate=9600, timeout=1):
        """
        Khởi tạo COM reader
        
        Args:
            port: Tên cổng COM (vd: 'COM3'). Bắt buộc phải truyền
            baudrate: Tốc độ truyền (mặc định 9600)
            timeout: Thời gian chờ đọc (giây)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.last_state = SwitchState.OFF
    
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

    def send_signal(self, value: str, with_newline: bool = True) -> bool:
        """
        Gửi tín hiệu ra cổng COM (ví dụ: "1", "2", "3").

        Returns:
            bool: True nếu gửi thành công, False nếu lỗi
        """
        if not self.serial or not self.serial.is_open:
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
        except Exception as e:
            print(f"[COM] Lỗi gửi tín hiệu '{value}': {e}")
            return False
    
    def read_state(self):
        """
        Đọc trạng thái hiện tại của switch
        
        Returns:
            SwitchState: ON hoặc OFF
        """
        if not self.serial or not self.serial.is_open:
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
            
        except Exception as e:
            print(f"[COM] Lỗi đọc dữ liệu: {e}")
            return SwitchState.OFF
    
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
