import cv2

# 1️⃣ Load ảnh test
frame = cv2.imread("/home/phuc/fist/image/2f.jpg")

if frame is None:
    print("❌ Không load được ảnh")
    exit()

# 2️⃣ Lấy chiều cao & chiều rộng ảnh
height, width = frame.shape[:2]
print("Kích thước gốc:", width, "x", height)

# 3️⃣ Resize nếu ảnh quá lớn
if width > 1280:
    scale = 1280 / width
    new_width = int(width * scale)
    new_height = int(height * scale)
    frame = cv2.resize(frame, (new_width, new_height))
    print("Đã resize:", new_width, "x", new_height)

# 4️⃣ Chuyển sang ảnh xám
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

# 5️⃣ Tạo CLAHE object
clahe = cv2.createCLAHE(
    clipLimit=3.0,
    tileGridSize=(10, 10)
)

# 6️⃣ Áp dụng CLAHE để tăng tương phản
enhanced = clahe.apply(gray)

# 7️⃣ Hiển thị kết quả
cv2.imshow("Original Frame", frame)
cv2.imshow("Gray Image", gray)
cv2.imshow("Enhanced (CLAHE)", enhanced)

cv2.waitKey(0)
cv2.destroyAllWindows()
