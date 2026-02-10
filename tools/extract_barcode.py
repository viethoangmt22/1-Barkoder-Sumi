import uiautomator2 as u2

d = u2.connect()

# 1. Lấy tổng số lượng đã quét (Scanned Counter)
counter = d(resourceId="com.barkoder.demoscanner:id/scannedCounter").get_text()
print(f"--- Tổng số lượng đã quét: {counter} ---\n")

# 2. Tìm tất cả các kết quả barcode trên màn hình
# Chúng ta sẽ dùng xpath để lấy danh sách các kết quả
results = d.xpath('//*[@resource-id="com.barkoder.demoscanner:id/txtBarcodeResult"]').all()
types = d.xpath('//*[@resource-id="com.barkoder.demoscanner:id/txtBarcodeType"]').all()

print(f"Tìm thấy {len(results)} kết quả đang hiển thị:")
print("-" * 30)

# 3. Duyệt và in ra
for i in range(len(results)):
    barcode_text = results[i].text
    barcode_type = types[i].text if i < len(types) else "Unknown"
    
    print(f"[{i+1}] Loại: {barcode_type}")
    print(f"    Giá trị: {barcode_text}")
    print("-" * 30)