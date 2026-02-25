"""
com_reader.py

Đọc tín hiệu từ cổng COM để phát hiện cảm biến switch (ON/OFF)
Dùng serial port để nhận tín hiệu từ Arduino/PLC/sensor

Tín hiệu mong đợi:
- "1" hoặc "ON"  → Switch bật (thùng đã đặt vào)
- "0" hoặc "OFF" → Switch tắt (thùng được nhấc ra)
"""

import serial
import serial.tools.list_ports
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
            port: Tên cổng COM (vd: 'COM3'). Nếu None, sẽ tự detect
            baudrate: Tốc độ truyền (mặc định 9600)
            timeout: Thời gian chờ đọc (giây)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.last_state = SwitchState.OFF
        
    def auto_detect_port(self):
        """
        Tự động tìm cổng COM khả dụng
        
        Returns:
            str: Tên cổng COM hoặc None nếu không tìm thấy
        """
        ports = serial.tools.list_ports.comports()
        
        if not ports:
            return None
            
        # Ưu tiên cổng có mô tả Arduino/USB Serial
        for port in ports:
            desc = port.description.lower()
            if 'arduino' in desc or 'ch340' in desc or 'usb serial' in desc:
                return port.device
        
        # Nếu không tìm thấy, trả về cổng đầu tiên
        return ports[0].device
    
    def connect(self):
        """
        Kết nối tới cổng COM
        
        Returns:
            bool: True nếu kết nối thành công
        """
        try:
            # Auto detect nếu chưa có port
            if not self.port:
                self.port = self.auto_detect_port()
                
            if not self.port:
                print("[COM] Không tìm thấy cổng COM nào")
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
        start_time = time.time()
        
        print("[COM] Đang chờ switch ON...")
        
        while True:
            state = self.read_state()
            
            if state == SwitchState.ON:
                print("[COM] ✓ Switch ON")
                return True
            
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                print("[COM] ✗ Timeout chờ switch ON")
                return False
            
            time.sleep(0.1)  # Polling interval
    
    def wait_for_off(self, timeout=None):
        """
        Chờ cho đến khi switch tắt (OFF)
        
        Args:
            timeout: Thời gian chờ tối đa (giây), None = chờ vô hạn
            
        Returns:
            bool: True nếu switch đã OFF, False nếu timeout
        """
        start_time = time.time()
        
        print("[COM] Đang chờ switch OFF...")
        
        while True:
            state = self.read_state()
            
            if state == SwitchState.OFF:
                print("[COM] ✓ Switch OFF")
                return True
            
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                print("[COM] ✗ Timeout chờ switch OFF")
                return False
            
            time.sleep(0.1)


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
    
    # Tự động tìm cổng COM
    reader = COMReader()
    
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
