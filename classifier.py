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
    Phân loại barcode theo prefix kèm dãy số.

    Input:
        barcodes: iterable các string barcode

    Output:
        {
            "P": [list product numbers],
            "Q": [list quantities],
            "B": [list batches],
            "UNKNOWN": [list barcode không hợp lệ]
        }
    """
    result = {
        "P": [],
        "Q": [],
        "B": [],
        "UNKNOWN": []
    }

    for raw in barcodes:
        if not raw:
            continue

        value = raw.strip()

        if value.startswith("P") and value[1:].isdigit():
            result["P"].append(value)
        elif value.startswith("Q") and value[1:].isdigit():
            result["Q"].append(value)
        elif value.startswith("B") and value[1:].isdigit():
            result["B"].append(value)
        else:
            result["UNKNOWN"].append(value)

    return result


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
