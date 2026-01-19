import sqlite3
from datetime import datetime


class InventoryManager:
    """Class quan ly kho hang"""
    
    def __init__(self, db_name='inventory.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.init_database()
        self.check_and_migrate_database()
    
    def get_connection(self):
        """Lay ket noi database"""
        return sqlite3.connect(self.db_name)
    
    def check_and_migrate_database(self):
        """Kiem tra va cap nhat database neu can"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # ===== MIGRATE PRODUCTS =====
            cursor.execute("PRAGMA table_info(products)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'id' not in columns:
                print("Dang cap nhat database products...")
                
                # Tao bang moi voi cot id
                cursor.execute('''CREATE TABLE IF NOT EXISTS products_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    barcode TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    category TEXT,
                    quantity INTEGER DEFAULT 0,
                    min_stock INTEGER DEFAULT 10,
                    price REAL DEFAULT 0.0,
                    cost_price REAL DEFAULT 0.0,
                    description TEXT,
                    supplier TEXT,
                    last_updated TEXT,
                    created_at TEXT
                )''')
                
                # Sao chep du lieu tu bang cu sang bang moi
                cursor.execute('''INSERT INTO products_new 
                                (barcode, name, category, quantity, min_stock, price, 
                                 cost_price, supplier, description, last_updated, created_at)
                                SELECT barcode, name, category, quantity, min_stock, price, 
                                       cost_price, supplier, description, last_updated, created_at
                                FROM products''')
                
                # Xoa bang cu va doi ten bang moi
                cursor.execute('DROP TABLE products')
                cursor.execute('ALTER TABLE products_new RENAME TO products')
                
                conn.commit()
                print("Cap nhat database products thanh cong!")
            
            # ===== MIGRATE ORDER_ITEMS =====
            cursor.execute("PRAGMA table_info(order_items)")
            order_columns = [column[1] for column in cursor.fetchall()]
            
            if 'profit' not in order_columns:
                print("Them cot profit vao order_items...")
                cursor.execute("ALTER TABLE order_items ADD COLUMN profit REAL DEFAULT 0.0")
                cursor.execute("ALTER TABLE order_items ADD COLUMN cost_price REAL DEFAULT 0.0")
                conn.commit()
                print("Da them cot profit vao order_items!")
            
            # ✅ MIGRATE ORDERS - THÊM MỚI
            cursor.execute("PRAGMA table_info(orders)")
            orders_columns = [column[1] for column in cursor.fetchall()]
            
            if 'total_profit' not in orders_columns:
                print("Them cot total_profit vao orders...")
                cursor.execute("ALTER TABLE orders ADD COLUMN total_profit REAL DEFAULT 0.0")
                conn.commit()
                print("Da them cot total_profit vao orders!")
                
        except Exception as e:
            print(f"Loi cap nhat database: {e}")
        finally:
            conn.close()
    
    def init_database(self):
        """Khoi tao database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Bang san pham - CO COT ID
        cursor.execute('''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            quantity INTEGER DEFAULT 0,
            min_stock INTEGER DEFAULT 10,
            price REAL DEFAULT 0.0,
            cost_price REAL DEFAULT 0.0,
            description TEXT,
            supplier TEXT,
            last_updated TEXT,
            created_at TEXT
        )''')
        
        # Bang don hang
        cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT UNIQUE,
            customer_name TEXT,
            customer_phone TEXT,
            total_amount REAL,
            discount REAL DEFAULT 0.0,
            final_amount REAL,
            payment_method TEXT,
            status TEXT DEFAULT 'PENDING',
            created_by TEXT,
            created_at TEXT,
            completed_at TEXT,
            total_profit REAL DEFAULT 0.0
        )''')
        
        # Bang chi tiet don hang - THEM COT PROFIT
        cursor.execute('''CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            barcode TEXT,
            product_name TEXT,
            quantity INTEGER,
            unit_price REAL,
            cost_price REAL DEFAULT 0.0,
            subtotal REAL,
            profit REAL DEFAULT 0.0,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (barcode) REFERENCES products(barcode)
        )''')
        
        # Bang lich su xuat nhap
        cursor.execute('''CREATE TABLE IF NOT EXISTS inventory_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT,
            product_name TEXT,
            action TEXT,
            quantity INTEGER,
            note TEXT,
            user TEXT,
            timestamp TEXT,
            FOREIGN KEY (barcode) REFERENCES products(barcode)
        )''')
        
        # Bang canh bao
        cursor.execute('''CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT,
            alert_type TEXT,
            message TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY (barcode) REFERENCES products(barcode)
        )''')
        
        conn.commit()
        conn.close()
        print("Database initialized!")
    
    def check_product_status(self, barcode):
        """Kiem tra trang thai san pham"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM products WHERE barcode = ?", (barcode,))
        product = cursor.fetchone()
        conn.close()
        
        if product:
            (product_id, barcode, name, category, quantity, min_stock, price, cost_price,
             description, supplier, last_updated, created_at) = product
            
            if quantity == 0:
                status = "HET HANG"
            elif quantity <= min_stock:
                status = "TON KHO SAP HET"
            else:
                status = "CON HANG"
            
            return {
                'exists': True,
                'status': status,
                'data': {
                    'id': product_id,
                    'barcode': barcode,
                    'name': name,
                    'category': category,
                    'quantity': quantity,
                    'min_stock': min_stock,
                    'price': price,
                    'cost_price': cost_price,
                    'description': description,
                    'supplier': supplier,
                    'last_updated': last_updated,
                    'created_at': created_at
                }
            }
        else:
            return {'exists': False, 'status': 'SAN PHAM MOI', 'data': None}
    
    def get_product_by_barcode(self, barcode):
        """Lay thong tin san pham theo ma vach"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM products WHERE barcode = ?", (barcode,))
        product = cursor.fetchone()
        conn.close()
        
        return product
    
    def get_product_by_id(self, product_id):
        """Lay thong tin san pham theo ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        conn.close()
        
        return product
    
    def add_product(self, barcode, name, category='', quantity=0, 
                   min_stock=10, price=0.0, cost_price=0.0, supplier='', description=''):
        """Them san pham"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            cursor.execute('''INSERT INTO products 
                            (barcode, name, category, quantity, min_stock, price, cost_price,
                             description, supplier, last_updated, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (barcode, name, category, quantity, min_stock, price, cost_price,
                           description, supplier, now, now))
            
            cursor.execute('''INSERT INTO inventory_history 
                            (barcode, product_name, action, quantity, note, user, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                          (barcode, name, 'ADD_NEW', quantity, 'Them san pham moi', 'system', now))
            
            conn.commit()
            conn.close()
            return True, "Them san pham thanh cong!"
        except sqlite3.IntegrityError:
            conn.close()
            return False, "Ma vach da ton tai!"
        except Exception as e:
            conn.close()
            return False, f"Loi: {str(e)}"
    
    def update_product(self, barcode, name, category, quantity, min_stock, price, cost_price, supplier):
        """Cap nhat thong tin san pham"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            cursor.execute('''UPDATE products 
                            SET name = ?, category = ?, quantity = ?, min_stock = ?,
                                price = ?, cost_price = ?, supplier = ?, last_updated = ?
                            WHERE barcode = ?''',
                          (name, category, quantity, min_stock, price, cost_price, supplier, now, barcode))
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                return True, "Cap nhat san pham thanh cong!"
            else:
                conn.close()
                return False, "Khong tim thay san pham!"
                
        except Exception as e:
            conn.close()
            return False, f"Loi: {str(e)}"
    
    def delete_product(self, barcode):
        """Xoa san pham"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Kiem tra san pham co ton tai khong
            cursor.execute("SELECT name FROM products WHERE barcode = ?", (barcode,))
            product = cursor.fetchone()
            
            if not product:
                conn.close()
                return False, "Khong tim thay san pham!"
            
            product_name = product[0]
            
            # Xoa san pham
            cursor.execute("DELETE FROM products WHERE barcode = ?", (barcode,))
            
            # Luu lich su
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''INSERT INTO inventory_history 
                            (barcode, product_name, action, quantity, note, user, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?)''',
                          (barcode, product_name, 'DELETE', 0, 'Xoa san pham', 'system', now))
            
            conn.commit()
            conn.close()
            return True, "Xoa san pham thanh cong!"
            
        except Exception as e:
            conn.close()
            return False, f"Loi: {str(e)}"
    
    def quick_add_product(self, barcode, name="San pham moi", price=0.0):
        """Them nhanh san pham khi quet ma moi"""
        return self.add_product(
            barcode=barcode,
            name=name,
            category='Chua phan loai',
            quantity=0,
            min_stock=5,
            price=price,
            cost_price=0.0,
            supplier='',
            description='Tu dong them khi quet ma'
        )
    
    def update_quantity(self, barcode, quantity_change, action='UPDATE', note='', user='system'):
        """Cap nhat so luong"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("SELECT quantity, name FROM products WHERE barcode = ?", (barcode,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return False, "San pham khong ton tai!"
        
        current_qty, product_name = result
        new_qty = current_qty + quantity_change
        
        if new_qty < 0:
            conn.close()
            return False, f"Khong du hang! (Con: {current_qty})"
        
        cursor.execute('''UPDATE products 
                         SET quantity = ?, last_updated = ?
                         WHERE barcode = ?''', (new_qty, now, barcode))
        
        cursor.execute('''INSERT INTO inventory_history 
                         (barcode, product_name, action, quantity, note, user, timestamp)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                      (barcode, product_name, action, quantity_change, note, user, now))
        
        conn.commit()
        conn.close()
        return True, "Da cap nhat!"
    
    def import_stock(self, barcode, quantity, note='', user='system'):
        """Nhap kho"""
        return self.update_quantity(barcode, quantity, 'IMPORT', note, user)
    
    def export_stock(self, barcode, quantity, note='', user='system'):
        """Xuat kho"""
        return self.update_quantity(barcode, -quantity, 'EXPORT', note, user)
    
    def create_order(self, items, customer_name='', customer_phone='', 
                    discount=0.0, payment_method='CASH', user='system'):
        """
        Tao don hang - CO TINH LOI NHUAN
        items: [{'barcode': 'xxx', 'name': 'xxx', 'quantity': 1, 'price': 100, 'subtotal': 100}, ...]
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        order_code = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        try:
            # Tinh tong tien va loi nhuan
            total_amount = 0
            total_profit = 0
            order_details = []
            
            for item in items:
                barcode = item['barcode']
                quantity = item['quantity']
                
                cursor.execute("SELECT name, price, cost_price, quantity FROM products WHERE barcode = ?", (barcode,))
                product = cursor.fetchone()
                
                if not product:
                    # San pham da duoc them tu dong, lay thong tin tu item
                    name = item.get('name', f'SP_{barcode[:8]}')
                    price = item.get('price', 0)
                    cost_price = 0
                    stock = 999
                else:
                    name, price, cost_price, stock = product
                
                subtotal = price * quantity
                profit_per_item = (price - cost_price) * quantity
                
                total_amount += subtotal
                total_profit += profit_per_item
                
                order_details.append({
                    'barcode': barcode,
                    'name': name,
                    'quantity': quantity,
                    'price': price,
                    'cost_price': cost_price,
                    'subtotal': subtotal,
                    'profit': profit_per_item
                })
            
            final_amount = total_amount - discount
            
            # Tao don hang
            cursor.execute('''INSERT INTO orders 
                            (order_code, customer_name, customer_phone, total_amount, 
                             discount, final_amount, payment_method, status, created_by, created_at, total_profit)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (order_code, customer_name, customer_phone, total_amount,
                           discount, final_amount, payment_method, 'COMPLETED', user, now, total_profit))
            
            order_id = cursor.lastrowid
            
            # Them chi tiet don hang
            for detail in order_details:
                cursor.execute('''INSERT INTO order_items 
                                (order_id, barcode, product_name, quantity, unit_price, cost_price, subtotal, profit)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                              (order_id, detail['barcode'], detail['name'], 
                               detail['quantity'], detail['price'], detail['cost_price'], 
                               detail['subtotal'], detail['profit']))
                
                # Tru hang trong kho (neu co ton kho)
                cursor.execute('''UPDATE products 
                                 SET quantity = CASE 
                                     WHEN quantity >= ? THEN quantity - ?
                                     ELSE quantity
                                 END,
                                 last_updated = ?
                                 WHERE barcode = ?''', 
                              (detail['quantity'], detail['quantity'], now, detail['barcode']))
                
                # Luu lich su
                cursor.execute('''INSERT INTO inventory_history 
                                 (barcode, product_name, action, quantity, note, user, timestamp)
                                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
                              (detail['barcode'], detail['name'], 'SALE', -detail['quantity'],
                               f"Don hang {order_code}", user, now))
            
            # ✅ COMMIT - QUAN TRỌNG!
            conn.commit()
            conn.close()
            
            print(f"✅ Đã tạo đơn hàng {order_code} - Profit: {total_profit:,.0f}")
            
            return True, "Tao don hang thanh cong!", {
                'order_id': order_id,
                'order_code': order_code,
                'total': total_amount,
                'discount': discount,
                'final': final_amount,
                'profit': total_profit,
                'items': order_details
            }
            
        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"❌ Lỗi tạo đơn hàng: {e}")
            return False, f"Loi: {str(e)}", None
    
    def get_all_products(self):
        """Lay tat ca san pham"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''SELECT id, barcode, name, category, quantity, min_stock, 
                                price, cost_price, last_updated 
                         FROM products ORDER BY created_at DESC''')
        products = cursor.fetchall()
        conn.close()
        
        return products
    
    def get_low_stock_products(self):
        """Lay san pham ton kho thap"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''SELECT barcode, name, category, quantity, min_stock, 
                                price, last_updated, created_at 
                         FROM products 
                         WHERE quantity <= min_stock 
                         ORDER BY quantity ASC''')
        products = cursor.fetchall()
        conn.close()
        
        return products
    
    def get_inventory_history(self, limit=50):
        """Lay lich su xuat nhap"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''SELECT id, barcode, product_name, action, quantity, note, user, timestamp
                         FROM inventory_history
                         ORDER BY timestamp DESC LIMIT ?''', (limit,))
        history = cursor.fetchall()
        conn.close()
        
        return history
    
    def get_orders(self, limit=50):
        """Lay danh sach don hang - 11 cột"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''SELECT order_id, order_code, customer_name, customer_phone,
                                    total_amount, discount, final_amount, payment_method,
                                    status, created_at, total_profit
                             FROM orders
                             ORDER BY created_at DESC LIMIT ?''', (limit,))
            orders = cursor.fetchall()
            conn.close()
            
            print(f"✅ get_orders: Tìm thấy {len(orders)} đơn hàng")
            return orders
            
        except Exception as e:
            conn.close()
            print(f"❌ Lỗi get_orders: {e}")
            return []
    
    def get_order_details(self, order_id):
        """Lay chi tiet don hang"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''SELECT barcode, product_name, quantity, unit_price, cost_price, subtotal, profit
                         FROM order_items
                         WHERE order_id = ?''', (order_id,))
        items = cursor.fetchall()
        conn.close()
        
        return items
    
    def get_monthly_profit(self):
        """Thong ke loi nhuan theo thang"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                strftime('%Y-%m', created_at) as month,
                SUM(total_profit) as total_profit,
                SUM(final_amount) as total_revenue,
                COUNT(*) as order_count
            FROM orders
            WHERE status = 'COMPLETED'
            GROUP BY strftime('%Y-%m', created_at)
            ORDER BY month DESC
            LIMIT 12
        ''')
        
        monthly_data = cursor.fetchall()
        conn.close()
        
        return monthly_data
    
    # ✅ THÊM HÀM DEBUG
    def debug_database(self):
        """Debug database structure"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        print("\n=== DEBUG DATABASE ===")
        
        # Kiểm tra orders table
        cursor.execute("PRAGMA table_info(orders)")
        print("\n--- Cấu trúc bảng orders ---")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]})")
        
        # Đếm orders
        cursor.execute("SELECT COUNT(*) FROM orders")
        count = cursor.fetchone()[0]
        print(f"\n--- Tổng số đơn hàng: {count} ---")
        
        # Xem 3 đơn gần nhất
        if count > 0:
            cursor.execute("""
                SELECT order_id, order_code, customer_name, total_amount, 
                       final_amount, payment_method, created_at, total_profit
                FROM orders 
                ORDER BY created_at DESC 
                LIMIT 3
            """)
            print("\n--- 3 đơn hàng gần nhất ---")
            for row in cursor.fetchall():
                print(f"  {row}")
        
        conn.close()
