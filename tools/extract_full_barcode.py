import uiautomator2 as u2
import time

d = u2.connect()
all_barcodes = set() # Dùng set để không bao giờ bị trùng
last_count = -1

print("Đang bắt đầu thu thập dữ liệu...")

while len(all_barcodes) != last_count:
    last_count = len(all_barcodes)
    
    # 1. Lấy tất cả barcode đang hiện trên màn hình
    elements = d.xpath('//*[@resource-id="com.barkoder.demoscanner:id/txtBarcodeResult"]').all()
    for el in elements:
        all_barcodes.add(el.text)
    
    # 2. Vuốt xuống để hiện các phần tử mới
    # d.swipe_ext("up", scale=0.5) # Vuốt lên để danh sách trôi xuống
    d(scrollable=True).scroll.forward() 
    
    time.sleep(0.1) # Đợi một chút để app load dữ liệu mới

print(f"Hoàn thành! Tổng số barcode thu thập được: {len(all_barcodes)}")
print(all_barcodes)