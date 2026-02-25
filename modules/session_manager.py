"""
session_manager.py

Quản lý session cho workflow
- Giữ P1, Q1, Q2, Batch
- Kiểm tra rule nghiệp vụ
- Không phụ thuộc module khác
"""

class SessionManager:
    def __init__(self):
        self.reset()

    # -------------------------
    # Core state
    # -------------------------

    def reset(self):
        self.state = "IDLE"

        self.P = None
        self.Q1 = None
        self.Q2 = None
        self.B = None

    # -------------------------
    # Step handlers
    # -------------------------

    def handle_small_box_1(self, classified):
        """
        Bước 1: Thùng nhỏ số 1
        Yêu cầu: đúng 1 P, 1 Q
        """
        if self.state != "IDLE":
            return False, "Sai trạng thái, cần reset"

        P = classified.get("P", [])
        Q = classified.get("Q", [])
        B = classified.get("B", [])

        if B:
            return False, "Không được đọc Batch ở thùng nhỏ"

        if len(P) != 1 or len(Q) != 1:
            return False, "Thùng nhỏ 1 cần đúng 1 P và 1 Q"

        self.P = P[0]
        self.Q1 = Q[0]
        self.state = "SMALL_BOX_1_DONE"

        return True, "Đã lưu P1, Q1"

    def handle_small_box_2(self, classified):
        """
        Bước 2: Thùng nhỏ số 2
        Yêu cầu: P2 == P1, có Q2
        """
        if self.state != "SMALL_BOX_1_DONE":
            return False, "Chưa có dữ liệu thùng nhỏ 1"

        P = classified.get("P", [])
        Q = classified.get("Q", [])
        B = classified.get("B", [])

        if B:
            return False, "Không được đọc Batch ở thùng nhỏ"

        if len(P) != 1 or len(Q) != 1:
            return False, "Thùng nhỏ 2 cần đúng 1 P và 1 Q"

        if P[0] != self.P:
            return False, "Product Number thùng 2 không khớp thùng 1"

        self.Q2 = Q[0]
        self.state = "SMALL_BOX_2_DONE"

        return True, "Đã lưu Q2"

    def handle_big_box_batch(self, classified):
        """
        Bước 3: Thùng lớn chứa 2 thùng nhỏ
        Yêu cầu: chỉ có Batch
        """
        if self.state != "SMALL_BOX_2_DONE":
            return False, "Chưa đủ dữ liệu thùng nhỏ"

        P = classified.get("P", [])
        Q = classified.get("Q", [])
        B = classified.get("B", [])

        if P or Q:
            return False, "Thùng lớn chỉ được đọc Batch"

        if len(B) != 1:
            return False, "Cần đúng 1 Batch"

        self.B = B[0]
        self.state = "READY_TO_SEND"

        return True, "Đã sẵn sàng gửi dữ liệu"

    # -------------------------
    # BIG BOX (thùng TO)
    # -------------------------

    def handle_big_box_face_a(self, classified):
        """
        Thùng TO - Bước 1
        Chụp mặt A: P + Q
        """
        if self.state != "IDLE":
            return False, "Sai trạng thái, cần reset"

        P = classified.get("P", [])
        Q = classified.get("Q", [])
        B = classified.get("B", [])

        if B:
            return False, "Không được đọc Batch ở mặt A thùng TO"

        if len(P) != 1 or len(Q) != 1:
            return False, "Thùng TO mặt A cần đúng 1 P và 1 Q"

        self.P = P[0]
        self.Q1 = Q[0]   # dùng Q1 cho thống nhất
        self.state = "BIG_BOX_PQ_DONE"

        return True, "Đã lưu P và Q cho thùng TO"

    def handle_big_box_face_b(self, classified):
        """
        Thùng TO - Bước 2
        Chụp mặt B: Batch
        """
        if self.state != "BIG_BOX_PQ_DONE":
            return False, "Chưa scan mặt A thùng TO"

        P = classified.get("P", [])
        Q = classified.get("Q", [])
        B = classified.get("B", [])

        if P or Q:
            return False, "Mặt B thùng TO chỉ được đọc Batch"

        if len(B) != 1:
            return False, "Thùng TO cần đúng 1 Batch"

        self.B = B[0]
        self.state = "READY_TO_SEND"

        return True, "Thùng TO sẵn sàng gửi"

    # -------------------------
    # AUTO MODE (phân nhánh thông minh)
    # -------------------------

    def handle_auto_step_2_smart(self, classified):
        """
        AUTO MODE - Bước 2 (phân nhánh thông minh)
        
        Sau khi có P + Q từ step 1, step 2 có thể là:
          Case A: Scan được BATCH → Kết luận THÙNG TO → Chốt ngay
          Case B: Scan được P + Q  → Kết luận THÙNG NHỎ #2 → Đợi step 3
        
        Returns:
            (ok, msg, next_step)
            - ok: True/False
            - msg: Thông báo
            - next_step: "DONE" (chốt luôn) hoặc "WAIT_STEP_3" (cần step 3)
        """
        # Kiểm tra state hợp lệ (phải đã có dữ liệu từ step 1)
        if self.state not in ("SMALL_BOX_1_DONE", "BIG_BOX_PQ_DONE"):
            return False, "Chưa có dữ liệu step 1", None

        P = classified.get("P", [])
        Q = classified.get("Q", [])
        B = classified.get("B", [])

        # ===== CASE A: Có BATCH → THÙNG TO =====
        if B and len(B) == 1:
            # Không được có P hoặc Q kèm theo
            if P or Q:
                return False, "BATCH không được đi kèm P hoặc Q", None
            
            # Lưu Batch và chốt
            self.B = B[0]
            self.state = "READY_TO_SEND"
            
            return True, "✓ Phát hiện THÙNG TO → Đã lưu Batch → Sẵn sàng gửi", "DONE"

        # ===== CASE B: Có P + Q → THÙNG NHỎ #2 =====
        elif P and Q:
            if len(P) != 1 or len(Q) != 1:
                return False, "Thùng nhỏ #2 cần đúng 1 P và 1 Q", None
            
            # Kiểm tra P phải trùng với step 1
            if P[0] != self.P:
                return False, f"Product Number không khớp (step 1: {self.P}, step 2: {P[0]})", None
            
            # Lưu Q2
            self.Q2 = Q[0]
            self.state = "SMALL_BOX_2_DONE"
            
            return True, "✓ Phát hiện THÙNG NHỎ #2 → Đã lưu Q2 → Chờ Batch", "WAIT_STEP_3"

        # ===== Không khớp case nào =====
        else:
            return False, "Không phát hiện Batch hoặc P+Q hợp lệ", None

    # -------------------------
    # Output
    # -------------------------

    def get_result(self):
        """
        Trả dữ liệu cuối để gửi sang PC
        """
        if self.state != "READY_TO_SEND":
            return None

        return [
            self.P,
            self.Q1,
            self.Q2,
            self.B
        ]


# -------------------------
# Test nhanh
# -------------------------

def main():
    sm = SessionManager()

    print("\n--- STEP 1: Small box 1 ---")
    ok, msg = sm.handle_small_box_1({
        "P": ["P61897449"],
        "Q": ["Q00001000"],
        "B": []
    })
    print(ok, msg)

    print("\n--- STEP 2: Small box 2 ---")
    ok, msg = sm.handle_small_box_2({
        "P": ["P61897449"],
        "Q": ["Q00002000"],
        "B": []
    })
    print(ok, msg)

    print("\n--- STEP 3: Big box batch ---")
    ok, msg = sm.handle_big_box_batch({
        "P": [],
        "Q": [],
        "B": ["B12345678"]
    })
    print(ok, msg)

    print("\n--- RESULT ---")
    print(sm.get_result())


if __name__ == "__main__":
    main()
