"""
classifier.py

Phân loại barcode theo quy ước kho:
- Product Number: bắt đầu bằng 'P' + dãy số
- Quantity: bắt đầu bằng 'Q' + dãy số
- Batch: bắt đầu bằng 'B' + dãy số

Không phụ thuộc module khác
Có test nhanh bằng main()
"""

from typing import Iterable, Dict, List


# -----------------------------
# Core logic
# -----------------------------

def classify_barcodes(barcodes: Iterable[str]) -> Dict[str, List[str]]:
    """
    Phân loại barcode, chỉ giữ lại P và Q lớn nhất, Batch giữ nguyên danh sách.
    """
    # Khởi tạo giá trị mặc định là None cho P và Q để dễ so sánh
    max_p = None
    max_q = None
    batches = []
    unknowns = []

    for raw in barcodes:
        if not raw:
            continue
        
        value = raw.strip()
        prefix = value[0] if value else ""
        content = value[1:]

        # Kiểm tra định dạng: Bắt đầu bằng P/Q/B và phần còn lại là số
        if prefix in ("P", "Q", "B") and content.isdigit():
            num_val = int(content) # Chuyển sang số để so sánh chính xác (ví dụ 1000 > 2)

            if prefix == "P":
                # Nếu chưa có P nào hoặc P hiện tại lớn hơn P cũ thì cập nhật
                if max_p is None or num_val > int(max_p[1:]):
                    max_p = value
            
            elif prefix == "Q":
                # Tương tự cho Q
                if max_q is None or num_val > int(max_q[1:]):
                    max_q = value
            
            elif prefix == "B":
                # Batch thì vẫn lấy tất cả theo yêu cầu cũ
                batches.append(value)
        else:
            # Không khớp định dạng thì cho vào UNKNOWN
            unknowns.append(value)

    # Tổng hợp kết quả trả về (ép P và Q vào List để đúng format yêu cầu)
    return {
        "P": [max_p] if max_p else [],
        "Q": [max_q] if max_q else [],
        "B": batches,
        "UNKNOWN": unknowns
    }


# -----------------------------
# Helper (tuỳ chọn)
# -----------------------------

def pretty_print(result: Dict[str, List[str]]):
    """In kết quả phân loại dễ nhìn"""
    print("\nKẾT QUẢ PHÂN LOẠI")
    print("-" * 40)

    for k, values in result.items():
        print(f"{k} ({len(values)}):")
        for v in values:
            print(f"  - {v}")


# -----------------------------
# Test nhanh
# -----------------------------

def main():
    """
    Test thủ công module classifier
    Chạy:
        python classifier.py
    """

    sample_input = {
        "P61897449  ",
        "Q00001000",
        "Q000GL000",
        "B12345678",
        "H8Y77MWA0985502X",
        "C61897449  PAV0WC"
    }

    print("INPUT:")
    for v in sample_input:
        print(" ", v)

    result = classify_barcodes(sample_input)
    pretty_print(result)


if __name__ == "__main__":
    main()
