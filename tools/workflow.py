"""
workflow.py

Xác định loại thùng:
- Thùng TO (BIG_BOX)
- Thùng NHỎ (SMALL_BOX)

Dựa trên barcode đã được classifier phân loại
"""

from typing import Dict, List


# -----------------------------
# Core workflow
# -----------------------------

def determine_box_type(classified: Dict[str, List[str]]) -> Dict:
    """
    Xác định thùng TO hay thùng NHỎ

    Input:
        classified = {
            "P": [...],
            "Q": [...],
            "B": [...],
            "UNKNOWN": [...]
        }

    Output:
        {
            "type": "BIG_BOX" | "SMALL_BOX" | "INVALID",
            "data": {...},
            "errors": [...]
        }
    """
    P = classified.get("P", [])
    Q = classified.get("Q", [])
    B = classified.get("B", [])
    UNKNOWN = classified.get("UNKNOWN", [])

    errors = []

    # Có barcode lạ → cảnh báo
    if UNKNOWN:
        errors.append(f"Có barcode không xác định: {UNKNOWN}")

    # -------------------------
    # Thùng TO
    # -------------------------
    if len(P) == 1 and len(Q) == 1 and len(B) == 1:
        return {
            "type": "BIG_BOX",
            "data": {
                "product_number": P[0],
                "quantity": Q[0],
                "batch": B[0]
            },
            "errors": errors
        }

    # -------------------------
    # Thùng NHỎ
    # -------------------------
    if len(P) == 1 and len(Q) == 2 and len(B) == 1:
        return {
            "type": "SMALL_BOX",
            "data": {
                "product_number": P[0],
                "quantity_1": Q[0],
                "quantity_2": Q[1],
                "batch": B[0]
            },
            "errors": errors
        }

    # -------------------------
    # Không hợp lệ
    # -------------------------
    errors.append(
        f"Tổ hợp barcode không hợp lệ: P={len(P)}, Q={len(Q)}, B={len(B)}"
    )

    return {
        "type": "INVALID",
        "data": {},
        "errors": errors
    }


# -----------------------------
# Test nhanh
# -----------------------------

def main():
    print("=== TEST WORKFLOW ===")

    # Test thùng TO
    classified_big = {
        "P": ["P61897449"],
        "Q": ["Q00001000"],
        "B": ["B12345678"],
        "UNKNOWN": []
    }

    print("\nTest BIG BOX:")
    print(determine_box_type(classified_big))

    # Test thùng NHỎ
    classified_small = {
        "P": ["P61897449"],
        "Q": ["Q00001000", "Q00002000"],
        "B": ["B12345678"],
        "UNKNOWN": []
    }

    print("\nTest SMALL BOX:")
    print(determine_box_type(classified_small))

    # Test lỗi
    classified_invalid = {
        "P": ["P61897449", "PXXXX"],
        "Q": ["Q00001000"],
        "B": [],
        "UNKNOWN": ["H8Y77MWA0985502X"]
    }

    print("\nTest INVALID:")
    print(determine_box_type(classified_invalid))


if __name__ == "__main__":
    main()
