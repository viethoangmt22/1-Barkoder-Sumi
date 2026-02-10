import uiautomator2 as u2

d = u2.connect()

# Tìm tất cả phần tử có thuộc tính clickable là True
buttons = d.xpath('//*[@clickable="true"]').all()

print(f"--- Tìm thấy {len(buttons)} phần tử có thể bấm được ---")

for btn in buttons:
    # Lấy thông tin cơ bản để nhận diện
    text = btn.text or "Không có chữ"
    res_id = btn.info.get('resourceName') or "Không có ID"
    class_name = btn.info.get('className')
    
    print(f"ID: {res_id} | Text: {text} | Loại: {class_name}")