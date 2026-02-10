import uiautomator2 as u2

d = u2.connect()

# Lấy tất cả các object trên màn hình bằng xpath
all_elements = d.xpath('//*').all()

# Dùng set để lưu các ID không trùng nhau
ids = set()

for el in all_elements:
    res_id = el.info.get('resourceName') # resourceName thường là ID đầy đủ
    if res_id:
        ids.add(res_id)

print(f"--- Tìm thấy {len(ids)} ID duy nhất ---")
for i in sorted(ids):
    print(i)