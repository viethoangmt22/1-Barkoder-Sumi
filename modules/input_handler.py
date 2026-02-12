"""
input_handler.py

Module nhận input từ bàn phím (sau này có thể mở rộng COM / Scanner)

Không phụ thuộc module khác
"""

# =========================
# Command constants
# =========================

CMD_SCAN = "SCAN"
CMD_START = "START"
CMD_HOME = "HOME"
CMD_BOX_BIG = "BOX_BIG"
CMD_BOX_SMALL = "BOX_SMALL"
CMD_EXIT = "EXIT"
CMD_UNKNOWN = "UNKNOWN"


# =========================
# Core function
# =========================

def get_command_from_keyboard() -> str:
    """
    Đọc 1 phím từ bàn phím và trả về command chuẩn hoá
    """
    key = input("Nhập lệnh [a=scan, s=bắt đầu, 1=thùng to, 2=thùng nhỏ, q=thoát]: ").strip()

    if key == "a":
        return CMD_SCAN
    elif key == "s":
        return CMD_START
    elif key == "1":
        return CMD_BOX_BIG
    elif key == "2":
        return CMD_BOX_SMALL
    elif key == "h":
        return CMD_HOME
    elif key == "q":
        return CMD_EXIT
    else:
        return CMD_UNKNOWN


# =========================
# Ví dụ mở rộng (stub)
# =========================

def get_command_from_com():
    """
    Placeholder cho COM / Serial sau này
    """
    raise NotImplementedError("COM input chưa được implement")


# =========================
# Test nhanh
# =========================

def main():
    print("=" * 50)
    print("TEST input_handler.py")
    print("=" * 50)

    while True:
        cmd = get_command_from_keyboard()
        print("→ Command nhận được:", cmd)

        if cmd == CMD_EXIT:
            print("Thoát chương trình test.")
            break


if __name__ == "__main__":
    main()
