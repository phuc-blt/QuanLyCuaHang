import cv2
import numpy as np
from pyzbar.pyzbar import decode
from datetime import datetime


class RealtimeBarcodeScanner:
    def __init__(self):
        """Scanner thời gian thực từ camera"""
        self.barcode_types = {
            'QRCODE': 'Mã QR',
            'EAN13': 'EAN-13',
            'EAN8': 'EAN-8',
            'CODE128': 'Code 128',
            'CODE39': 'Code 39',
            'CODE93': 'Code 93',
            'UPC_A': 'UPC-A',
            'UPC_E': 'UPC-E',
        }
        self.qr_detector = cv2.QRCodeDetector()
        self.scanned_codes = {}
        self.scan_cooldown = 2
    
    def preprocess_frame(self, frame):
        """Tiền xử lý frame"""
        height, width = frame.shape[:2]
        if width > 1280:
            scale = 1280 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height))
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        return frame, enhanced
    
    def decode_barcode(self, frame, enhanced):
        """Decode barcode"""
        results = []
        
        detected = decode(frame)
        for obj in detected:
            results.append({
                'data': obj.data.decode('utf-8'),
                'type': obj.type,
                'type_vn': self.barcode_types.get(obj.type, obj.type),
                'rect': obj.rect,
                'polygon': obj.polygon,
                'quality': obj.quality
            })
        
        if not results:
            detected = decode(enhanced)
            for obj in detected:
                results.append({
                    'data': obj.data.decode('utf-8'),
                    'type': obj.type,
                    'type_vn': self.barcode_types.get(obj.type, obj.type),
                    'rect': obj.rect,
                    'polygon': obj.polygon,
                    'quality': obj.quality
                })
        
        if not results:
            try:
                data, bbox, _ = self.qr_detector.detectAndDecode(frame)
                if data and bbox is not None:
                    results.append({
                        'data': data,
                        'type': 'QRCODE',
                        'type_vn': 'Mã QR',
                        'rect': None,
                        'polygon': bbox,
                        'quality': 100
                    })
            except:
                pass
        
        return results
    
    def draw_barcode(self, frame, result):
        """Vẽ khung và thông tin lên barcode"""
        try:
            if result['polygon'] is not None:
                points = result['polygon']
                
                if isinstance(points, (list, tuple)):
                    points_array = []
                    for point in points:
                        if hasattr(point, 'x') and hasattr(point, 'y'):
                            points_array.append([int(point.x), int(point.y)])
                        elif isinstance(point, (list, tuple)) and len(point) >= 2:
                            points_array.append([int(point[0]), int(point[1])])
                    
                    if len(points_array) > 0:
                        points_array = np.array(points_array, dtype=np.int32)
                        cv2.polylines(frame, [points_array], True, (0, 255, 0), 3)
            
            if result['rect'] is not None:
                x = result['rect'].left
                y = result['rect'].top
                w = result['rect'].width
                h = result['rect'].height
                
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                text = f"{result['type_vn']}: {result['data']}"
                (text_w, text_h), baseline = cv2.getTextSize(
                    text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                
                bg_y1 = max(0, y - text_h - 10)
                bg_y2 = max(text_h + 10, y)
                
                cv2.rectangle(frame, (x, bg_y1), (x + text_w, bg_y2), 
                            (0, 255, 0), -1)
                
                cv2.putText(frame, text, (x, y - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        except Exception as e:
            text = f"{result['type_vn']}: {result['data']}"
            cv2.putText(frame, text, (10, 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        return frame
    
    def is_new_scan(self, barcode_data):
        """Kiểm tra mã mới (cooldown)"""
        current_time = datetime.now()
        
        if barcode_data in self.scanned_codes:
            last_scan_time = self.scanned_codes[barcode_data]
            time_diff = (current_time - last_scan_time).total_seconds()
            
            if time_diff < self.scan_cooldown:
                return False
        
        self.scanned_codes[barcode_data] = current_time
        return True
    
    def run(self, camera_id=0, show_fps=True):
        """Chạy scanner real-time"""
        cap = cv2.VideoCapture(camera_id)
        
        if not cap.isOpened():
            print("❌ Không thể mở camera!")
            return
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        
        
        frame_count = 0
        start_time = datetime.now()
        scan_count = 0
        fps = 0
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            frame_count += 1
            
            processed_frame, enhanced = self.preprocess_frame(frame)
            results = self.decode_barcode(processed_frame, enhanced)
            
            for result in results:
                processed_frame = self.draw_barcode(processed_frame, result)
                
                if self.is_new_scan(result['data']):
                    scan_count += 1
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {result['type_vn']}: {result['data']}")
            
            # UI
            cv2.putText(processed_frame, f"Quet: {scan_count}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            if show_fps:
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > 0:
                    fps = frame_count / elapsed
                
                cv2.putText(processed_frame, f"FPS: {fps:.1f}", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            cv2.putText(processed_frame, "q: Thoat | c: Xoa | s: Luu", 
                       (10, processed_frame.shape[0] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('Barcode Scanner', processed_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('c'):
                self.scanned_codes.clear()
                scan_count = 0
                print("Đã xóa lịch sử\n")
            elif key == ord('s'):
                filename = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                cv2.imwrite(filename, processed_frame)
                print(f"Đã lưu: {filename}\n")
        
        cap.release()
        cv2.destroyAllWindows()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n Thống kê: {scan_count} mã | {fps:.1f} FPS | {elapsed:.1f}s")


if __name__ == "__main__":
    scanner = RealtimeBarcodeScanner()
    scanner.run(camera_id=0, show_fps=True)
