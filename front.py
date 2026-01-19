import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
from PIL import Image, ImageTk
import cv2
import numpy as np
from datetime import datetime
from dulieu import InventoryManager
from scan import RealtimeBarcodeScanner
from pyzbar.pyzbar import decode
import threading
import os


class InventoryApp:
    """Ung dung quan ly kho hang"""

    def __init__(self, root):
        self.root = root
        self.root.title("He Thong Quan Ly Kho Hang")
        self.root.geometry("1600x900")
        self.root.configure(bg='#f0f0f0')

        self.manager = InventoryManager()

        try:
            self.camera_scanner = RealtimeBarcodeScanner(callback=self.on_camera_scanned)
            self.camera_available = True
        except Exception as e:
            self.camera_scanner = None
            self.camera_available = False
            print(f"Canh bao: Khong tim thay camera - {e}")

        self.current_image = None
        self.camera_running = False
        self.update_camera_job = None
        self.cart_items = []
        self.last_scanned_product = None
        self.current_tab_mode = None
        self.last_order_data = None

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TNotebook.Tab', padding=[20, 10], font=('Arial', 10, 'bold'))
        self.style.configure('TButton', font=('Arial', 10), padding=10)

        self.create_widgets()
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)

    def create_widgets(self):
        """Tao giao dien chinh"""

        header_frame = tk.Frame(self.root, bg='#007bff', height=80)
        header_frame.pack(fill='x', side='top')

        tk.Label(
            header_frame,
            text="HE THONG QUAN LY KHO HANG",
            font=('Arial', 24, 'bold'),
            bg='#007bff',
            fg='white'
        ).pack(pady=20)

        self.status_bar = tk.Label(
            self.root,
            text="San sang",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=('Arial', 9),
            bg='#e0e0e0'
        )
        self.status_bar.pack(side='bottom', fill='x')

        main_container = tk.Frame(self.root, bg='#f0f0f0')
        main_container.pack(fill='both', expand=True, padx=10, pady=10)

        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill='both', expand=True)

        self.tab_sell = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.tab_sell, text='Ban Hang')
        self.create_sell_tab()

        self.tab_products = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.tab_products, text='San Pham')
        self.create_products_tab()

        self.tab_inventory = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.tab_inventory, text='Xuat Nhap')
        self.create_inventory_tab_new()

        self.tab_orders = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.tab_orders, text='Don Hang')
        self.create_orders_tab()

        self.tab_alerts = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.tab_alerts, text='Canh Bao')
        self.create_alerts_tab()

        self.tab_reports = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.tab_reports, text='Bao Cao')
        self.create_reports_tab()

        camera_status = "Co camera" if self.camera_available else "Khong co camera - Chi dung nhap thu cong"
        self.update_status(f"San sang - {camera_status}")

    def on_tab_changed(self, event):
        """Xu ly khi chuyen tab"""
        if not self.camera_available:
            return

        current_tab = event.widget.tab('current')['text']

        if 'Ban Hang' in current_tab:
            self.current_tab_mode = 'sell'
            if not self.camera_running:
                self.start_camera_auto()
        else:
            if self.camera_running:
                self.stop_camera_auto()

    # ================= TAB BAN HANG =================
    def create_sell_tab(self):
        """Tab ban hang"""
        
        main = tk.Frame(self.tab_sell, bg='#f5f7fa')
        main.pack(fill='both', expand=True)

        # HEADER
        header = tk.Frame(main, bg='#2c3e50', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)

        header_content = tk.Frame(header, bg='#2c3e50')
        header_content.pack(fill='both', expand=True, padx=20, pady=10)

        tk.Label(
            header_content,
            text="BAN HANG",
            font=('Segoe UI', 18, 'bold'),
            bg='#2c3e50',
            fg='white'
        ).pack(side='left')

        info_right = tk.Frame(header_content, bg='#2c3e50')
        info_right.pack(side='right')

        tk.Label(
            info_right,
            text="TONG:",
            font=('Segoe UI', 11),
            bg='#2c3e50',
            fg='#bdc3c7'
        ).pack(side='left', padx=(0, 5))

        self.header_total = tk.Label(
            info_right,
            text="0 VND",
            font=('Segoe UI', 16, 'bold'),
            bg='#2c3e50',
            fg='#2ecc71'
        )
        self.header_total.pack(side='left')

        # BODY - 2 COT
        body = tk.Frame(main, bg='#f5f7fa')
        body.pack(fill='both', expand=True, padx=10, pady=10)

        # COT TRAI
        left_col = tk.Frame(body, bg='#f5f7fa', width=550)
        left_col.pack(side='left', fill='y', padx=(0, 5))
        left_col.pack_propagate(False)

        # CARD TIM KIEM
        search_card = tk.Frame(left_col, bg='white', relief=tk.SOLID, borderwidth=1)
        search_card.pack(fill='x', pady=(0, 8))

        search_header = tk.Frame(search_card, bg='#3498db', height=35)
        search_header.pack(fill='x')
        search_header.pack_propagate(False)

        tk.Label(
            search_header,
            text="TIM KIEM SAN PHAM",
            font=('Segoe UI', 11, 'bold'),
            bg='#3498db',
            fg='white'
        ).pack(side='left', padx=15, pady=8)

        search_body = tk.Frame(search_card, bg='white')
        search_body.pack(fill='x', padx=15, pady=12)

        search_input_frame = tk.Frame(search_body, bg='white')
        search_input_frame.pack(fill='x')

        self.sell_barcode_entry = tk.Entry(
            search_input_frame,
            font=('Segoe UI', 12),
            relief=tk.SOLID,
            borderwidth=1,
            bg='#f8f9fa'
        )
        self.sell_barcode_entry.pack(side='left', fill='x', expand=True, ipady=6)
        self.sell_barcode_entry.bind('<Return>', lambda e: self.add_to_cart_manual())

        tk.Button(
            search_input_frame,
            text="THEM",
            command=self.add_to_cart_manual,
            bg='#27ae60',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            width=10,
            cursor='hand2',
            relief=tk.FLAT,
            activebackground='#229954'
        ).pack(side='left', padx=(8, 0), ipady=6)

        self.sell_barcode_entry.insert(0, "Nhap ma hoac ten san pham...")
        self.sell_barcode_entry.config(fg='gray')

        def on_focus_in(e):
            if self.sell_barcode_entry.get() == "Nhap ma hoac ten san pham...":
                self.sell_barcode_entry.delete(0, tk.END)
                self.sell_barcode_entry.config(fg='black')

        def on_focus_out(e):
            if not self.sell_barcode_entry.get():
                self.sell_barcode_entry.insert(0, "Nhap ma hoac ten san pham...")
                self.sell_barcode_entry.config(fg='gray')

        self.sell_barcode_entry.bind('<FocusIn>', on_focus_in)
        self.sell_barcode_entry.bind('<FocusOut>', on_focus_out)

        # CARD CAMERA
        if self.camera_available:
            camera_card = tk.Frame(left_col, bg='white', relief=tk.SOLID, borderwidth=1, height=180)
            camera_card.pack(fill='x', pady=(0, 8))
            camera_card.pack_propagate(False)

            camera_header = tk.Frame(camera_card, bg='#e74c3c', height=32)
            camera_header.pack(fill='x')
            camera_header.pack_propagate(False)

            tk.Label(
                camera_header,
                text="QUET MA VACH",
                font=('Segoe UI', 10, 'bold'),
                bg='#e74c3c',
                fg='white'
            ).pack(side='left', padx=15, pady=6)

            camera_body = tk.Frame(camera_card, bg='white')
            camera_body.pack(fill='both', expand=True, padx=10, pady=8)

            self.sell_camera_canvas = tk.Canvas(
                camera_body,
                bg='#34495e',
                highlightthickness=0
            )
            self.sell_camera_canvas.pack(fill='both', expand=True)

            self.sell_camera_canvas.create_text(
                150, 65,
                text="Camera dang khoi dong...",
                font=('Segoe UI', 10),
                fill='white',
                tags='placeholder'
            )

        # CARD THONG TIN SAN PHAM
        info_card = tk.Frame(left_col, bg='white', relief=tk.SOLID, borderwidth=1)
        info_card.pack(fill='both', expand=True)

        info_header = tk.Frame(info_card, bg='#95a5a6', height=32)
        info_header.pack(fill='x')
        info_header.pack_propagate(False)

        tk.Label(
            info_header,
            text="SAN PHAM VUA THEM",
            font=('Segoe UI', 10, 'bold'),
            bg='#95a5a6',
            fg='white'
        ).pack(side='left', padx=15, pady=6)

        self.product_info_text = scrolledtext.ScrolledText(
            info_card,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg='#ecf0f1',
            relief=tk.FLAT,
            borderwidth=0,
            height=8
        )
        self.product_info_text.pack(fill='both', expand=True, padx=10, pady=10)
        self.product_info_text.insert(tk.END, "Chua co san pham nao...")

        # COT PHAI: HOA DON
        right_col = tk.Frame(body, bg='white', relief=tk.SOLID, borderwidth=1)
        right_col.pack(side='right', fill='both', expand=True, padx=(5, 0))

        invoice_header = tk.Frame(right_col, bg='#16a085', height=45)
        invoice_header.pack(fill='x')
        invoice_header.pack_propagate(False)

        tk.Label(
            invoice_header,
            text="HOA DON BAN HANG",
            font=('Segoe UI', 14, 'bold'),
            bg='#16a085',
            fg='white'
        ).pack(expand=True)

        canvas_container = tk.Frame(right_col, bg='white')
        canvas_container.pack(fill='both', expand=True)

        canvas = tk.Canvas(canvas_container, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_container, orient='vertical', command=canvas.yview)
        
        scrollable_frame = tk.Frame(canvas, bg='white')
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        def on_canvas_configure(event):
            canvas.itemconfig('all', width=event.width)
        canvas.bind('<Configure>', on_canvas_configure)

        invoice_body = scrollable_frame

        tk.Label(
            invoice_body,
            text="San pham trong gio:",
            font=('Segoe UI', 10, 'bold'),
            bg='white',
            fg='#2c3e50',
            anchor='w'
        ).pack(fill='x', padx=15, pady=(10, 5))

        tree_frame = tk.Frame(invoice_body, bg='white')
        tree_frame.pack(fill='both', expand=True, padx=15)

        scroll_y = ttk.Scrollbar(tree_frame, orient='vertical')

        style = ttk.Style()
        style.configure("Treeview", font=('Segoe UI', 9), rowheight=30)
        style.configure("Treeview.Heading", font=('Segoe UI', 9, 'bold'))

        self.cart_tree = ttk.Treeview(
            tree_frame,
            columns=('Ten', 'SL', 'Gia', 'Tong'),
            show='headings',
            yscrollcommand=scroll_y.set,
            height=6
        )

        scroll_y.config(command=self.cart_tree.yview)

        self.cart_tree.heading('Ten', text='Ten san pham')
        self.cart_tree.heading('SL', text='SL')
        self.cart_tree.heading('Gia', text='Don gia')
        self.cart_tree.heading('Tong', text='Thanh tien')

        self.cart_tree.column('Ten', width=200, anchor='w')
        self.cart_tree.column('SL', width=50, anchor='center')
        self.cart_tree.column('Gia', width=100, anchor='e')
        self.cart_tree.column('Tong', width=100, anchor='e')

        self.cart_tree.pack(side='left', fill='both', expand=True)
        scroll_y.pack(side='right', fill='y')

        self.cart_tree.bind('<Double-1>', lambda e: self.edit_cart_quantity())

        edit_frame = tk.Frame(invoice_body, bg='white')
        edit_frame.pack(fill='x', padx=15, pady=8)

        btn_style = {'font': ('Segoe UI', 9, 'bold'), 'cursor': 'hand2', 'relief': tk.FLAT, 'width': 7, 'height': 1}

        tk.Button(edit_frame, text="Giam", command=lambda: self.change_cart_qty(-1), 
                  bg='#f39c12', fg='white', activebackground='#e67e22', **btn_style).pack(side='left', padx=2)
        
        tk.Button(edit_frame, text="Tang", command=lambda: self.change_cart_qty(1),
                  bg='#27ae60', fg='white', activebackground='#229954', **btn_style).pack(side='left', padx=2)
        
        tk.Button(edit_frame, text="Sua SL", command=self.edit_cart_quantity,
                  bg='#3498db', fg='white', activebackground='#2980b9', **btn_style).pack(side='left', padx=2)
        
        tk.Button(edit_frame, text="Xoa", command=self.remove_from_cart,
                  bg='#e74c3c', fg='white', activebackground='#c0392b', **btn_style).pack(side='left', padx=2)

        ttk.Separator(invoice_body, orient='horizontal').pack(fill='x', padx=15, pady=8)

        customer_section = tk.LabelFrame(
            invoice_body,
            text="Thong tin khach hang",
            font=('Segoe UI', 9, 'bold'),
            bg='white',
            fg='#34495e'
        )
        customer_section.pack(fill='x', padx=15, pady=(0, 8))

        cust_grid = tk.Frame(customer_section, bg='white')
        cust_grid.pack(fill='x', padx=10, pady=8)

        tk.Label(cust_grid, text="Ten:", bg='white', font=('Segoe UI', 9), width=10, anchor='w').grid(row=0, column=0, pady=3)
        self.customer_name_entry = tk.Entry(cust_grid, font=('Segoe UI', 9), relief=tk.SOLID, borderwidth=1)
        self.customer_name_entry.grid(row=0, column=1, sticky='ew', pady=3, padx=(5, 0))

        tk.Label(cust_grid, text="So dien thoai:", bg='white', font=('Segoe UI', 9), width=10, anchor='w').grid(row=1, column=0, pady=3)
        self.customer_phone_entry = tk.Entry(cust_grid, font=('Segoe UI', 9), relief=tk.SOLID, borderwidth=1)
        self.customer_phone_entry.grid(row=1, column=1, sticky='ew', pady=3, padx=(5, 0))

        cust_grid.columnconfigure(1, weight=1)

        payment_section = tk.LabelFrame(
            invoice_body,
            text="Thanh toan",
            font=('Segoe UI', 9, 'bold'),
            bg='#f8f9fa',
            fg='#2c3e50',
            relief=tk.RIDGE,
            borderwidth=1
        )
        payment_section.pack(fill='x', padx=15, pady=(0, 8))

        pay_container = tk.Frame(payment_section, bg='#f8f9fa')
        pay_container.pack(fill='x', padx=10, pady=8)

        row1 = tk.Frame(pay_container, bg='#f8f9fa')
        row1.pack(fill='x', pady=2)

        tk.Label(row1, text="Giam gia:", bg='#f8f9fa', font=('Segoe UI', 9, 'bold'), 
                 fg='#e67e22', width=11, anchor='w').pack(side='left')
        
        self.discount_entry = tk.Entry(row1, font=('Segoe UI', 9), width=12, relief=tk.SOLID, borderwidth=1)
        self.discount_entry.pack(side='left', ipady=2)
        self.discount_entry.insert(0, "0")
        self.discount_entry.bind('<KeyRelease>', lambda e: self.refresh_cart_display())
        
        tk.Label(row1, text="VND", bg='#f8f9fa', font=('Segoe UI', 9), fg='#7f8c8d').pack(side='left', padx=(3, 0))

        row2 = tk.Frame(pay_container, bg='#f8f9fa')
        row2.pack(fill='x', pady=2)

        tk.Label(row2, text="Phuong thuc:", bg='#f8f9fa', font=('Segoe UI', 9, 'bold'),
                 fg='#3498db', width=11, anchor='w').pack(side='left')
        
        self.payment_method = ttk.Combobox(row2, values=['Tien mat', 'The', 'Chuyen khoan'],
                                           state='readonly', font=('Segoe UI', 9), width=16)
        self.payment_method.pack(side='left', ipady=2)
        self.payment_method.set('Tien mat')

        row3 = tk.Frame(pay_container, bg='#27ae60', relief=tk.RAISED, borderwidth=1)
        row3.pack(fill='x', pady=(6, 0), ipady=6)

        tk.Label(row3, text="TONG THANH TOAN:", bg='#27ae60', font=('Segoe UI', 10, 'bold'), fg='white').pack(side='left', padx=10)
        
        self.total_label = tk.Label(row3, text="0 VND", bg='#27ae60', font=('Segoe UI', 13, 'bold'), fg='white')
        self.total_label.pack(side='right', padx=10)

        action_section = tk.Frame(invoice_body, bg='white')
        action_section.pack(fill='x', padx=15, pady=(5, 15))

        self.btn_payment = tk.Button(
            action_section,
            text="THANH TOAN",
            command=self.complete_payment,
            font=('Segoe UI', 13, 'bold'),
            bg='#28a745',
            fg='white',
            height=2,
            cursor='hand2',
            relief=tk.FLAT,
            activebackground='#218838'
        )
        self.btn_payment.pack(fill='x', pady=(0, 5))

        bottom_buttons = tk.Frame(action_section, bg='white')
        bottom_buttons.pack(fill='x', pady=(0, 5))

        self.btn_cancel_payment = tk.Button(
            bottom_buttons,
            text="HUY THANH TOAN",
            command=self.cancel_payment,
            font=('Segoe UI', 11, 'bold'),
            bg='#ffc107',
            fg='#000',
            height=2,
            cursor='hand2',
            relief=tk.FLAT,
            activebackground='#e0a800',
            state=tk.DISABLED
        )
        self.btn_cancel_payment.pack(side='left', fill='both', expand=True, padx=(0, 3))

        self.btn_export_bill = tk.Button(
            bottom_buttons,
            text="XUAT HOA DON",
            command=self.export_bill,
            font=('Segoe UI', 11, 'bold'),
            bg='#007bff',
            fg='white',
            height=2,
            cursor='hand2',
            relief=tk.FLAT,
            activebackground='#0056b3',
            state=tk.DISABLED
        )
        self.btn_export_bill.pack(side='right', fill='both', expand=True, padx=(3, 0))

        tk.Button(
            action_section,
            text="XOA GIO HANG",
            command=self.clear_cart,
            font=('Segoe UI', 9),
            bg='#dc3545',
            fg='white',
            height=1,
            cursor='hand2',
            relief=tk.FLAT,
            activebackground='#c82333'
        ).pack(fill='x')

    # GIO HANG / THANH TOAN

    def add_to_cart(self, barcode):
        """Them san pham vao gio hang theo ma vach"""
        result = self.manager.check_product_status(barcode)
        if not result['exists']:
            self.manager.quick_add_product(barcode, f"SP{barcode[-8:]}", 0.0)
            result = self.manager.check_product_status(barcode)

        data = result['data']
        for item in self.cart_items:
            if item['barcode'] == barcode:
                item['quantity'] += 1
                item['subtotal'] = item['quantity'] * item['price']
                self.refresh_cart_display()
                self.update_product_info(data, item['quantity'])
                self.update_status(f"Tang so luong {data['name']} SL {item['quantity']}")
                return

        self.cart_items.append({
            'barcode': barcode,
            'name': data['name'],
            'quantity': 1,
            'price': data['price'],
            'subtotal': data['price']
        })
        self.refresh_cart_display()
        self.update_product_info(data, 1)
        self.update_status(f"Da them {data['name']}")

    def add_to_cart_manual(self):
        """Them san pham bang tay"""
        barcode = self.sell_barcode_entry.get().strip()
        if barcode and barcode != "Nhap ma hoac ten san pham...":
            self.add_to_cart(barcode)
            self.sell_barcode_entry.delete(0, tk.END)

    def update_product_info(self, data, quantity_in_cart):
        """Cap nhat thong tin san pham vua them"""
        self.product_info_text.delete(1.0, tk.END)
        info = (
            "SAN PHAM VUA THEM\n"
            "----------------------------------------\n"
            f"Ten: {data['name']}\n"
            f"Ma: {data.get('barcode', 'NA')}\n"
            f"Gia: {data['price']:,.0f} VND\n"
            f"Ton kho: {data['quantity']}\n"
            f"So luong trong gio: {quantity_in_cart}\n"
            f"Thanh tien: {data['price'] * quantity_in_cart:,.0f} VND\n"
        )
        self.product_info_text.insert(tk.END, info)

    def refresh_cart_display(self):
        """Refresh gio hang + cap nhat tong"""
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)

        total = 0
        for item in self.cart_items:
            self.cart_tree.insert(
                '',
                'end',
                values=(
                    item['name'],
                    item['quantity'],
                    f"{item['price']:,.0f}",
                    f"{item['subtotal']:,.0f}"
                )
            )
            total += item['subtotal']

        try:
            discount = float(self.discount_entry.get() or 0)
        except:
            discount = 0

        final = total - discount
        if final < 0:
            final = 0

        self.total_label.config(text=f"{final:,.0f} VND")
        if hasattr(self, 'header_total'):
            self.header_total.config(text=f"{final:,.0f} VND")

    def change_cart_qty(self, delta):
        """Tang/giam so luong"""
        selected = self.cart_tree.selection()
        if not selected:
            messagebox.showwarning("Canh bao", "Chon san pham truoc!")
            return
        values = self.cart_tree.item(selected[0])['values']
        name = values[0]
        for item in self.cart_items:
            if item['name'] == name:
                item['quantity'] += delta
                if item['quantity'] <= 0:
                    self.cart_items.remove(item)
                else:
                    item['subtotal'] = item['quantity'] * item['price']
                break
        self.refresh_cart_display()

    def edit_cart_quantity(self):
        """Chinh sua so luong bang dialog"""
        selected = self.cart_tree.selection()
        if not selected:
            messagebox.showwarning("Canh bao", "Chon san pham truoc!")
            return
        values = self.cart_tree.item(selected[0])['values']
        name = values[0]
        current_qty = int(values[1])

        new_qty = simpledialog.askinteger(
            "Sua so luong",
            f"So luong moi cho '{name}':",
            initialvalue=current_qty,
            minvalue=0
        )
        if new_qty is None:
            return

        for item in self.cart_items:
            if item['name'] == name:
                if new_qty <= 0:
                    self.cart_items.remove(item)
                else:
                    item['quantity'] = new_qty
                    item['subtotal'] = new_qty * item['price']
                break
        self.refresh_cart_display()

    def remove_from_cart(self):
        """Xoa san pham khoi gio"""
        selected = self.cart_tree.selection()
        if not selected:
            messagebox.showwarning("Canh bao", "Chon san pham truoc!")
            return
        values = self.cart_tree.item(selected[0])['values']
        name = values[0]
        self.cart_items = [item for item in self.cart_items if item['name'] != name]
        self.refresh_cart_display()

    def clear_cart(self):
        """Xoa gio / huy don (truoc khi xuat bill)"""
        if not self.cart_items and not self.last_order_data:
            return

        if not messagebox.askyesno("Xac nhan", "Xoa toan bo gio hang / huy don hien tai?"):
            return

        self.cart_items = []
        self.last_order_data = None
        self.refresh_cart_display()
        self.product_info_text.delete(1.0, tk.END)
        self.product_info_text.insert(tk.END, "Chua co san pham...")

        self.customer_name_entry.delete(0, tk.END)
        self.customer_phone_entry.delete(0, tk.END)
        self.discount_entry.delete(0, tk.END)
        self.discount_entry.insert(0, "0")

        self.btn_payment.config(state=tk.NORMAL, bg="#28a745")
        self.btn_cancel_payment.config(state=tk.DISABLED, bg="#6c757d")
        self.btn_export_bill.config(state=tk.DISABLED, bg="#6c757d")

        self.update_status("Da xoa gio hang / huy don hien tai")

    def complete_payment(self):
        """THANH TOAN (khong in bill)"""
        if not self.cart_items:
            messagebox.showwarning("Gio trong", "Them san pham truoc!")
            return

        try:
            discount = float(self.discount_entry.get() or 0)
        except:
            discount = 0

        customer_name = self.customer_name_entry.get().strip()
        customer_phone = self.customer_phone_entry.get().strip()
        payment_text = self.payment_method.get()

        if 'Tien mat' in payment_text:
            payment_method = 'CASH'
        elif 'The' in payment_text:
            payment_method = 'CARD'
        else:
            payment_method = 'TRANSFER'

        success, msg, order_data = self.manager.create_order(
            items=self.cart_items,
            customer_name=customer_name,
            customer_phone=customer_phone,
            discount=discount,
            payment_method=payment_method,
            user='admin'
        )

        if success:
            self.last_order_data = {
                'orderdata': order_data,
                'customername': customer_name,
                'customerphone': customer_phone,
                'paymentmethod': payment_method,
                'discount': discount
            }

            messagebox.showinfo(
                "THANH TOAN THANH CONG",
                f"Ma don: {order_data['order_code']}\n\n"
                f"Tong: {order_data['final']:,.0f} VND\n"
                f"Loi nhuan: {order_data['profit']:,.0f} VND\n\n"
                f"Bam nut 'HUY THANH TOAN' de huy hoac 'XUAT HOA DON' de in bill"
            )

            self.btn_payment.config(state=tk.DISABLED, bg="#6c757d")
            self.btn_cancel_payment.config(state=tk.NORMAL, bg="#ffc107")
            self.btn_export_bill.config(state=tk.NORMAL, bg="#007bff")

            # TU DONG CAP NHAT BANG DON HANG
            try:
                self.refresh_orders()
                print("Da cap nhat tab Don Hang!")
            except Exception as e:
                print(f"Loi refresh_orders: {e}")
            
            self.refresh_reports()
            self.refresh_products_list()
        else:
            messagebox.showerror("LOI", msg)

    def cancel_payment(self):
        """HUY THANH TOAN da thuc hien (chua xuat bill)"""
        if not self.last_order_data:
            messagebox.showwarning("Canh bao", "Khong co thanh toan nao de huy!")
            return

        if not messagebox.askyesno(
            "Xac nhan huy thanh toan", 
            f"Ban co chac muon huy thanh toan?\n\n"
            f"Ma don: {self.last_order_data['orderdata']['order_code']}\n"
            f"So tien: {self.last_order_data['orderdata']['final']:,.0f} VND\n\n"
            f"Luu y: Hanh dong nay se hoan tra so luong san pham ve kho!"
        ):
            return

        orderdata = self.last_order_data['orderdata']
        for item in orderdata['items']:
            barcode = item['barcode']
            quantity = item['quantity']
            self.manager.import_stock(
                barcode, 
                quantity, 
                f"Hoan tra tu don huy {orderdata['order_code']}", 
                'admin'
            )

        messagebox.showinfo(
            "Da huy thanh toan", 
            f"Da huy thanh toan don {orderdata['order_code']}\n"
            f"San pham da duoc hoan tra vao kho!"
        )

        self.last_order_data = None
        
        self.btn_payment.config(state=tk.NORMAL, bg="#28a745")
        self.btn_cancel_payment.config(state=tk.DISABLED, bg="#6c757d")
        self.btn_export_bill.config(state=tk.DISABLED, bg="#6c757d")

        self.refresh_orders()
        self.refresh_reports()
        self.refresh_products_list()
        self.update_status("Da huy thanh toan thanh cong")

    def export_bill(self):
        """XUAT HOA DON sau khi da thanh toan"""
        if not self.last_order_data:
            messagebox.showwarning("Canh bao", "Chua thanh toan!")
            return

        orderdata = self.last_order_data['orderdata']
        customername = self.last_order_data['customername']
        customerphone = self.last_order_data['customerphone']
        paymentmethod = self.last_order_data['paymentmethod']
        discount = self.last_order_data['discount']

        invoice = self.generate_invoice(orderdata, customername, customerphone, paymentmethod, discount)
        self.save_invoice_to_file(invoice, orderdata['order_code'])

        messagebox.showinfo("Thanh cong", f"Da xuat hoa don {orderdata['order_code']}")

        # Reset sau khi da xuat bill
        self.cart_items = []
        self.last_order_data = None
        self.refresh_cart_display()
        self.customer_name_entry.delete(0, tk.END)
        self.customer_phone_entry.delete(0, tk.END)
        self.discount_entry.delete(0, tk.END)
        self.discount_entry.insert(0, "0")
        self.product_info_text.delete(1.0, tk.END)
        self.product_info_text.insert(tk.END, "Chua co san pham...")

        self.btn_payment.config(state=tk.NORMAL, bg="#28a745")
        self.btn_cancel_payment.config(state=tk.DISABLED, bg="#6c757d")
        self.btn_export_bill.config(state=tk.DISABLED, bg="#6c757d")

        # TU DONG CAP NHAT BANG DON HANG
        print("Dang cap nhat tab Don Hang sau xuat bill...")
        try:
            self.refresh_orders()
            print("Da cap nhat tab Don Hang thanh cong!")
        except Exception as e:
            print(f"Loi refresh_orders: {e}")
            import traceback
            traceback.print_exc()
        
        self.refresh_reports()
        self.refresh_products_list()
        self.update_status("Da xuat hoa don va cap nhat don hang")

    # HOA DON

    def generate_invoice(self, orderdata, customername, customerphone, paymentmethod, discount):
        """Tao noi dung hoa don text"""
        invoice = ""
        invoice += " " * 20 + "HOA DON BAN HANG\n"
        invoice += "-" * 50 + "\n"
        invoice += f"Ma don hang: {orderdata['order_code']}\n"
        invoice += f"Khach hang: {customername or 'Khach le'}\n"
        invoice += f"So dien thoai: {customerphone or 'N/A'}\n"
        invoice += f"Thoi gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        invoice += "-" * 50 + "\n"
        invoice += "DANH SACH SAN PHAM\n"
        invoice += "-" * 50 + "\n"
        for item in orderdata['items']:
            name = item['name']
            qty = item['quantity']
            price = item['price']
            subtotal = item['subtotal']
            invoice += f"{name}\n"
            invoice += f"  {qty} x {price:,.0f} = {subtotal:,.0f} VND\n"
        invoice += "-" * 50 + "\n"
        invoice += f"Tong cong: {orderdata['total']:,.0f} VND\n"
        if discount > 0:
            invoice += f"Giam gia: {discount:,.0f} VND\n"
        invoice += f"THANH TOAN: {orderdata['final']:,.0f} VND\n"
        invoice += f"Phuong thuc: {paymentmethod}\n"
        invoice += "-" * 50 + "\n"
        invoice += "CAM ON QUY KHACH!\n"
        invoice += "-" * 50 + "\n"
        return invoice

    def save_invoice_to_file(self, invoice_content, order_code):
        """Luu hoa don ra file txt"""
        try:
            invoice_dir = "invoices"
            if not os.path.exists(invoice_dir):
                os.makedirs(invoice_dir)
            filename = os.path.join(invoice_dir, f"HOADON_{order_code}.txt")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(invoice_content)
            self.update_status(f"Da luu {filename}")
            if messagebox.askyesno("Mo hoa don?", "Ban co muon mo file hoa don?"):
                try:
                    import subprocess
                    subprocess.call(["xdg-open", filename])
                except:
                    print(f"Khong mo duoc {filename}")
        except Exception as e:
            messagebox.showerror("Loi", f"Loi luu file: {e}")

    # CAMERA

    def start_camera_auto(self):
        """Bat camera"""
        if self.camera_running or not self.camera_available:
            return
        self.update_status("Dang khoi dong camera...")

        def startthread():
            try:
                success = self.camera_scanner.start(camera_id=0)
                if success:
                    self.camera_running = True
                    self.root.after(0, lambda: self.update_status("Camera hoat dong"))
                    self.root.after(0, self.update_camera_view)
                else:
                    self.root.after(0, lambda: self.update_status("Khong the bat camera"))
            except Exception as e:
                print("Loi camera", e)
                self.root.after(0, lambda: self.update_status("Loi camera"))

        threading.Thread(target=startthread, daemon=True).start()

    def stop_camera_auto(self):
        """Tat camera"""
        if not self.camera_running:
            return
        self.camera_running = False
        if self.camera_scanner:
            self.camera_scanner.stop()
        if self.update_camera_job:
            self.root.after_cancel(self.update_camera_job)
            self.update_camera_job = None
        if hasattr(self, 'sell_camera_canvas'):
            self.sell_camera_canvas.delete("all")
            self.sell_camera_canvas.create_text(
                150, 75,
                text="Camera da tam dung",
                font=('Arial', 14),
                fill='white'
            )
        self.update_status("Camera da tat")

    def update_camera_view(self):
        """Cap nhat khung camera"""
        if not self.camera_running:
            return
        try:
            frame = self.camera_scanner.get_frame()
            if frame is not None:
                self.display_camera_image(frame)
        except:
            pass
        self.update_camera_job = self.root.after(33, self.update_camera_view)

    def display_camera_image(self, cvimage):
        """Hien thi anh camera"""
        try:
            rgbimage = cv2.cvtColor(cvimage, cv2.COLOR_BGR2RGB)
            canvas_width = self.sell_camera_canvas.winfo_width()
            canvas_height = self.sell_camera_canvas.winfo_height()
            if canvas_width <= 1 and canvas_height <= 1:
                return
            h, w, _ = rgbimage.shape
            scale = min(canvas_width / w, canvas_height / h) * 0.95
            new_w, new_h = int(w * scale), int(h * scale)
            resized = cv2.resize(rgbimage, (new_w, new_h))
            pilimage = Image.fromarray(resized)
            photo = ImageTk.PhotoImage(pilimage)
            self.sell_camera_canvas.delete("all")
            self.sell_camera_canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=photo,
                anchor='center'
            )
            self.sell_camera_canvas.image = photo
        except Exception as e:
            print("Loi hien thi", e)

    def on_camera_scanned(self, result):
        """Callback khi quet duoc ma vach"""
        code_data = result['data']
        try:
            current_tab_id = self.notebook.select()
            current_tab_name = self.notebook.tab(current_tab_id, "text")
            if "Ban Hang" in current_tab_name:
                self.root.after(0, lambda c=code_data: self.add_to_cart(c))
        except Exception as e:
            print("Loi callback", e)

    # ================= TAB DON HANG (SUA LAI HOAN CHINH) =================

    def create_orders_tab(self):
        """Tab don hang - CO DAY DU CHUC NANG"""
        
        # HEADER
        header = tk.Frame(self.tab_orders, bg='#2c3e50', height=70)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="LICH SU DON HANG",
            font=('Segoe UI', 18, 'bold'),
            bg='#2c3e50',
            fg='white'
        ).pack(pady=20)
        
        # BUTTONS
        btn_frame = tk.Frame(self.tab_orders, bg='white')
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        btn_style = {
            'font': ('Segoe UI', 10, 'bold'),
            'cursor': 'hand2',
            'relief': tk.FLAT,
            'width': 12,
            'height': 2
        }
        
        tk.Button(
            btn_frame,
            text="LAM MOI",
            command=self.refresh_orders,
            bg='#17a2b8',
            fg='white',
            activebackground='#138496',
            **btn_style
        ).pack(side='left', padx=5)
        
        tk.Button(
            btn_frame,
            text="THEM DON",
            command=self.add_order_manual,
            bg='#28a745',
            fg='white',
            activebackground='#218838',
            **btn_style
        ).pack(side='left', padx=5)
        
        tk.Button(
            btn_frame,
            text="SUA DON",
            command=self.edit_order,
            bg='#ffc107',
            fg='#000',
            activebackground='#e0a800',
            **btn_style
        ).pack(side='left', padx=5)
        
        tk.Button(
            btn_frame,
            text="XOA DON",
            command=self.delete_order,
            bg='#dc3545',
            fg='white',
            activebackground='#c82333',
            **btn_style
        ).pack(side='left', padx=5)
        
        tk.Button(
            btn_frame,
            text="XEM CHI TIET",
            command=lambda: self.view_order_details(None),
            bg='#6c757d',
            fg='white',
            activebackground='#5a6268',
            **btn_style
        ).pack(side='left', padx=5)
        
        # SEARCH BAR
        search_frame = tk.Frame(self.tab_orders, bg='white')
        search_frame.pack(fill='x', padx=10, pady=(0, 5))
        
        tk.Label(
            search_frame,
            text="Tim kiem:",
            font=('Segoe UI', 10),
            bg='white'
        ).pack(side='left', padx=5)
        
        self.order_search_entry = tk.Entry(
            search_frame,
            font=('Segoe UI', 10),
            width=30
        )
        self.order_search_entry.pack(side='left', padx=5)
        self.order_search_entry.bind('<KeyRelease>', lambda e: self.search_orders())
        
        tk.Button(
            search_frame,
            text="Tim",
            command=self.search_orders,
            bg='#007bff',
            fg='white',
            font=('Segoe UI', 9, 'bold'),
            width=8,
            cursor='hand2',
            relief=tk.FLAT
        ).pack(side='left', padx=5)
        
        # TABLE
        tree_frame = tk.Frame(self.tab_orders, bg='white')
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        scroll_y = ttk.Scrollbar(tree_frame, orient='vertical')
        scroll_x = ttk.Scrollbar(tree_frame, orient='horizontal')
        
        self.orders_tree = ttk.Treeview(
            tree_frame,
            columns=('ID', 'Ma DH', 'Khach hang', 'SDT', 'Tong tien', 'Giam gia', 'Thanh toan', 'Loi nhuan', 'PT', 'Ngay'),
            show='headings',
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
            height=20
        )
        
        scroll_y.config(command=self.orders_tree.yview)
        scroll_x.config(command=self.orders_tree.xview)
        
        columns = {
            'ID': 50,
            'Ma DH': 120,
            'Khach hang': 150,
            'SDT': 100,
            'Tong tien': 110,
            'Giam gia': 90,
            'Thanh toan': 110,
            'Loi nhuan': 110,
            'PT': 80,
            'Ngay': 140
        }
        
        for col, width in columns.items():
            self.orders_tree.heading(col, text=col)
            self.orders_tree.column(col, width=width, anchor='center')
        
        self.orders_tree.pack(side='top', fill='both', expand=True)
        scroll_y.pack(side='right', fill='y')
        scroll_x.pack(side='bottom', fill='x')
        
        self.orders_tree.bind('<Double-1>', self.view_order_details)
        
        # STATUS BAR
        self.orders_status = tk.Label(
            self.tab_orders,
            text="San sang",
            bg='#e9ecef',
            anchor='w',
            font=('Segoe UI', 9),
            padx=10,
            pady=5
        )
        self.orders_status.pack(side='bottom', fill='x')
        
        self.refresh_orders()

    def refresh_orders(self):
        """SUA: Refresh danh sach don hang"""
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)
        
        try:
            orders = self.manager.get_orders()
            
            print(f"DEBUG: Tim thay {len(orders)} don hang")
            
            if len(orders) == 0:
                self.orders_status.config(text="Chua co don hang nao")
                return
            
            for o in orders:
                try:
                    order_id = o[0]
                    code = o[1]
                    customer = o[2] or 'Khach le'
                    phone = o[3] or ''
                    total = float(o[4]) if o[4] else 0.0      # ← SỬA
                    discount = float(o[5]) if o[5] else 0.0   # ← SỬA
                    final = float(o[6]) if o[6] else 0.0      # ← SỬA
                    method = o[7]
                    status = o[8]
                    created = o[9]
                    profit = float(o[10]) if o[10] else 0.0   # ← SỬA

                    
                    self.orders_tree.insert(
                        '',
                        'end',
                        values=(
                            order_id,
                            code,
                            customer,
                            phone,
                            f"{total:,.0f}",
                            f"{discount:,.0f}",
                            f"{final:,.0f}",
                            f"{profit:,.0f}",
                            method,
                            created
                        )
                    )
                    
                except (IndexError, ValueError, TypeError) as e:
                    print(f"Loi load don {o}: {e}")
                    continue
            
            self.orders_status.config(text=f"Co {len(orders)} don hang")
            print(f"Da load {len(orders)} don hang vao table")
            
        except Exception as e:
            print(f"Loi refresh_orders: {e}")
            import traceback
            traceback.print_exc()
            self.orders_status.config(text=f"Loi: {e}")

    def search_orders(self):
        """Tim kiem don hang"""
        keyword = self.order_search_entry.get().strip().lower()
        
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)
        
        orders = self.manager.get_orders(limit=200)
        count = 0
        
        for o in orders:
            try:
                order_id = o[0]
                code = o[1]
                customer = o[2] or 'Khach le'
                phone = o[3] or ''
                
                if (keyword in code.lower() or 
                    keyword in customer.lower() or 
                    keyword in phone.lower()):
                    
                    total = float(o[4]) if o[4] else 0.0
                    discount = float(o[5]) if o[5] else 0.0
                    final = float(o[6]) if o[6] else 0.0

                    method = o[7]
                    status = o[8]
                    created = o[9]
                    profit = float(o[10]) if o[10] else 0.0

                    
                    self.orders_tree.insert(
                        '',
                        'end',
                        values=(
                            order_id,
                            code,
                            customer,
                            phone,
                            f"{total:,.0f}",
                            f"{discount:,.0f}",
                            f"{final:,.0f}",
                            f"{profit:,.0f}",
                            method,
                            created
                        )
                    )
                    count += 1
            except:
                continue
        
        self.orders_status.config(text=f"Tim thay {count} don hang")

    def view_order_details(self, event):
        """Xem chi tiet don hang"""
        selected = self.orders_tree.selection()
        if not selected:
            messagebox.showwarning("Canh bao", "Chon don hang truoc!")
            return
        
        values = self.orders_tree.item(selected[0])['values']
        order_id = values[0]
        code = values[1]
        
        items = self.manager.get_order_details(order_id)
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Don hang {code}")
        dialog.geometry("900x600")
        dialog.transient(self.root)
        
        # Header
        header = tk.Frame(dialog, bg='#007bff', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=f"DON HANG {code}",
            font=('Segoe UI', 16, 'bold'),
            bg='#007bff',
            fg='white'
        ).pack(pady=15)
        
        # Info
        info_frame = tk.Frame(dialog, bg='#f8f9fa')
        info_frame.pack(fill='x', padx=15, pady=10)
        
        info_text = f"Khach hang: {values[2]}  |  SDT: {values[3]}  |  Ngay: {values[9]}"
        tk.Label(
            info_frame,
            text=info_text,
            font=('Segoe UI', 10),
            bg='#f8f9fa'
        ).pack(pady=5)
        
        # Table
        tree_frame = tk.Frame(dialog)
        tree_frame.pack(fill='both', expand=True, padx=15, pady=5)
        
        tree = ttk.Treeview(
            tree_frame,
            columns=('Ma', 'Ten', 'SL', 'Gia', 'Gia von', 'Tong', 'Loi nhuan'),
            show='headings',
            height=15
        )
        
        tree.heading('Ma', text='Ma')
        tree.heading('Ten', text='Ten san pham')
        tree.heading('SL', text='SL')
        tree.heading('Gia', text='Don gia')
        tree.heading('Gia von', text='Gia von')
        tree.heading('Tong', text='Thanh tien')
        tree.heading('Loi nhuan', text='Loi nhuan')
        
        tree.column('Ma', width=100)
        tree.column('Ten', width=200)
        tree.column('SL', width=50, anchor='center')
        tree.column('Gia', width=100, anchor='e')
        tree.column('Gia von', width=100, anchor='e')
        tree.column('Tong', width=120, anchor='e')
        tree.column('Loi nhuan', width=120, anchor='e')
        
        for item in items:
            barcode, name, qty, price, cost, subtotal, profit = item
            tree.insert(
                '',
                'end',
                values=(
                    barcode,
                    name,
                    qty,
                    f"{price:,.0f}",
                    f"{cost:,.0f}",
                    f"{subtotal:,.0f}",
                    f"{profit:,.0f}"
                )
            )
        
        tree.pack(fill='both', expand=True)
        
        # Summary
        summary_frame = tk.Frame(dialog, bg='#e9ecef')
        summary_frame.pack(fill='x', padx=15, pady=10)
        
        tk.Label(
            summary_frame,
            text=f"Tong: {values[4]}  |  Giam gia: {values[5]}  |  Thanh toan: {values[6]}  |  Loi nhuan: {values[7]}",
            font=('Segoe UI', 11, 'bold'),
            bg='#e9ecef'
        ).pack(pady=10)
        
        ttk.Button(
            dialog,
            text="Dong",
            command=dialog.destroy
        ).pack(pady=10)

    def add_order_manual(self):
        """Them don hang thu cong"""
        messagebox.showinfo(
            "Thong bao",
            "Vui long su dung tab 'Ban Hang' de tao don hang moi!"
        )

    def edit_order(self):
        """Sua don hang"""
        selected = self.orders_tree.selection()
        if not selected:
            messagebox.showwarning("Canh bao", "Chon don hang truoc!")
            return
        
        values = self.orders_tree.item(selected[0])['values']
        order_id = values[0]
        code = values[1]
        current_customer = values[2]
        current_phone = values[3]
        
        # Lay chi tiet don hang
        items = self.manager.get_order_details(order_id)
        
        # Tao dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Sua don hang {code}")
        dialog.geometry("1000x700")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header = tk.Frame(dialog, bg='#ffc107', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=f"SUA DON HANG {code}",
            font=('Segoe UI', 16, 'bold'),
            bg='#ffc107',
            fg='#000'
        ).pack(pady=15)
        
        # Thong tin khach hang
        info_frame = tk.LabelFrame(
            dialog,
            text="Thong tin khach hang",
            font=('Segoe UI', 10, 'bold'),
            bg='white',
            fg='#2c3e50'
        )
        info_frame.pack(fill='x', padx=15, pady=10)
        
        form = tk.Frame(info_frame, bg='white')
        form.pack(fill='x', padx=10, pady=10)
        
        tk.Label(form, text="Ten:", bg='white', font=('Segoe UI', 10), width=12, anchor='w').grid(row=0, column=0, pady=5)
        customer_entry = tk.Entry(form, font=('Segoe UI', 10), width=30)
        customer_entry.grid(row=0, column=1, sticky='ew', pady=5, padx=5)
        customer_entry.insert(0, current_customer)
        
        tk.Label(form, text="So dien thoai:", bg='white', font=('Segoe UI', 10), width=12, anchor='w').grid(row=1, column=0, pady=5)
        phone_entry = tk.Entry(form, font=('Segoe UI', 10), width=30)
        phone_entry.grid(row=1, column=1, sticky='ew', pady=5, padx=5)
        phone_entry.insert(0, current_phone)
        
        form.columnconfigure(1, weight=1)
        
        # Danh sach san pham
        product_frame = tk.LabelFrame(
            dialog,
            text="San pham trong don hang",
            font=('Segoe UI', 10, 'bold'),
            bg='white',
            fg='#2c3e50'
        )
        product_frame.pack(fill='both', expand=True, padx=15, pady=10)
        
        tree_container = tk.Frame(product_frame, bg='white')
        tree_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        scroll_y = ttk.Scrollbar(tree_container, orient='vertical')
        
        product_tree = ttk.Treeview(
            tree_container,
            columns=('Ma', 'Ten', 'SL', 'Gia', 'Tong'),
            show='headings',
            yscrollcommand=scroll_y.set,
            height=10
        )
        
        scroll_y.config(command=product_tree.yview)
        
        product_tree.heading('Ma', text='Ma vach')
        product_tree.heading('Ten', text='Ten san pham')
        product_tree.heading('SL', text='So luong')
        product_tree.heading('Gia', text='Don gia')
        product_tree.heading('Tong', text='Thanh tien')
        
        product_tree.column('Ma', width=100)
        product_tree.column('Ten', width=250)
        product_tree.column('SL', width=80, anchor='center')
        product_tree.column('Gia', width=100, anchor='e')
        product_tree.column('Tong', width=120, anchor='e')
        
        # Load san pham
        for item in items:
            barcode, name, qty, price, cost, subtotal, profit = item
            product_tree.insert(
                '',
                'end',
                values=(
                    barcode,
                    name,
                    qty,
                    f"{price:,.0f}",
                    f"{subtotal:,.0f}"
                )
            )
        
        product_tree.pack(side='left', fill='both', expand=True)
        scroll_y.pack(side='right', fill='y')
        
        # Nut chinh sua san pham
        btn_frame = tk.Frame(product_frame, bg='white')
        btn_frame.pack(fill='x', padx=10, pady=5)
        
        def edit_quantity():
            selected_item = product_tree.selection()
            if not selected_item:
                messagebox.showwarning("Canh bao", "Chon san pham truoc!")
                return
            
            values_item = product_tree.item(selected_item[0])['values']
            barcode = values_item[0]
            name = values_item[1]
            current_qty = int(values_item[2])
            
            new_qty = simpledialog.askinteger(
                "Sua so luong",
                f"So luong moi cho '{name}':",
                initialvalue=current_qty,
                minvalue=0
            )
            
            if new_qty is None:
                return
            
            # Cap nhat trong tree
            price_str = values_item[3].replace(',', '')
            price = float(price_str)
            new_total = new_qty * price
            
            product_tree.item(
                selected_item[0],
                values=(
                    barcode,
                    name,
                    new_qty,
                    f"{price:,.0f}",
                    f"{new_total:,.0f}"
                )
            )
        
        def remove_product():
            selected_item = product_tree.selection()
            if not selected_item:
                messagebox.showwarning("Canh bao", "Chon san pham truoc!")
                return
            
            if messagebox.askyesno("Xac nhan", "Xoa san pham khoi don hang?"):
                product_tree.delete(selected_item[0])
        
        tk.Button(
            btn_frame,
            text="Sua so luong",
            command=edit_quantity,
            bg='#3498db',
            fg='white',
            font=('Segoe UI', 9, 'bold'),
            width=12,
            cursor='hand2',
            relief=tk.FLAT
        ).pack(side='left', padx=5)
        
        tk.Button(
            btn_frame,
            text="Xoa san pham",
            command=remove_product,
            bg='#e74c3c',
            fg='white',
            font=('Segoe UI', 9, 'bold'),
            width=12,
            cursor='hand2',
            relief=tk.FLAT
        ).pack(side='left', padx=5)
        
        # Nut luu/huy
        action_frame = tk.Frame(dialog, bg='white')
        action_frame.pack(fill='x', padx=15, pady=15)
        
        def save_changes():
            new_customer = customer_entry.get().strip()
            new_phone = phone_entry.get().strip()
            
            # Lay danh sach san pham moi
            new_items = []
            for item_id in product_tree.get_children():
                values_item = product_tree.item(item_id)['values']
                barcode = values_item[0]
                qty = int(values_item[2])
                if qty > 0:
                    new_items.append({
                        'barcode': barcode,
                        'quantity': qty
                    })
            
            if not new_items:
                messagebox.showwarning("Canh bao", "Don hang phai co it nhat 1 san pham!")
                return
            
            if not messagebox.askyesno(
                "Xac nhan luu",
                f"Luu thay doi cho don hang {code}?"
            ):
                return
            
            try:
                conn = self.manager.get_connection()
                cursor = conn.cursor()
                
                # 1. Hoan tra hang cu ve kho
                old_items = self.manager.get_order_details(order_id)
                for item in old_items:
                    old_barcode = item[0]
                    old_qty = item[2]
                    self.manager.import_stock(
                        old_barcode,
                        old_qty,
                        f"Hoan tra tu don sua {code}",
                        'admin'
                    )
                
                # 2. Cap nhat thong tin don hang
                cursor.execute("""
                    UPDATE orders 
                    SET customer_name = ?, customer_phone = ?
                    WHERE order_id = ?
                """, (new_customer, new_phone, order_id))
                
                # 3. Xoa san pham cu
                cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
                
                # 4. Them san pham moi va tinh lai
                total = 0
                total_profit = 0
                
                for item in new_items:
                    barcode = item['barcode']
                    qty = item['quantity']
                    
                    # Lay thong tin san pham
                    cursor.execute("""
                        SELECT name, price, cost_price 
                        FROM products 
                        WHERE barcode = ?
                    """, (barcode,))
                    
                    product = cursor.fetchone()
                    if not product:
                        continue
                    
                    name, price, cost = product
                    price = float(price)
                    cost = float(cost)
                    
                    subtotal = price * qty
                    profit = (price - cost) * qty
                    
                    total += subtotal
                    total_profit += profit
                    
                    # Them vao order_items
                    cursor.execute("""
                        INSERT INTO order_items 
                        (order_id, barcode, name, quantity, price, cost_price, subtotal, profit)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (order_id, barcode, name, qty, price, cost, subtotal, profit))
                    
                    # Xuat kho
                    self.manager.export_stock(
                        barcode,
                        qty,
                        f"Xuat lai tu don sua {code}",
                        'admin'
                    )
                
                # 5. Cap nhat tong tien
                cursor.execute("""
                    UPDATE orders 
                    SET total = ?, final = ?, profit = ?
                    WHERE order_id = ?
                """, (total, total, total_profit, order_id))
                
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Thanh cong", f"Da cap nhat don hang {code}")
                dialog.destroy()
                self.refresh_orders()
                self.refresh_reports()
                self.refresh_products_list()
                
            except Exception as e:
                messagebox.showerror("Loi", f"Loi khi sua don: {e}")
                import traceback
                traceback.print_exc()
        
        tk.Button(
            action_frame,
            text="LUU THAY DOI",
            command=save_changes,
            bg='#28a745',
            fg='white',
            font=('Segoe UI', 12, 'bold'),
            width=15,
            height=2,
            cursor='hand2',
            relief=tk.FLAT
        ).pack(side='left', padx=5)
        
        tk.Button(
            action_frame,
            text="HUY",
            command=dialog.destroy,
            bg='#6c757d',
            fg='white',
            font=('Segoe UI', 12, 'bold'),
            width=15,
            height=2,
            cursor='hand2',
            relief=tk.FLAT
        ).pack(side='left', padx=5)


    def delete_order(self):
        """Xoa don hang"""
        selected = self.orders_tree.selection()
        if not selected:
            messagebox.showwarning("Canh bao", "Chon don hang truoc!")
            return
        
        values = self.orders_tree.item(selected[0])['values']
        order_id = values[0]
        code = values[1]
        
        if not messagebox.askyesno(
            "Xac nhan xoa",
            f"Ban co chac muon xoa don hang {code}?\n\n"
            "Luu y: San pham se duoc hoan tra vao kho!"
        ):
            return
        
        # Lay chi tiet don hang
        items = self.manager.get_order_details(order_id)
        
        # Hoan tra san pham
        for item in items:
            barcode = item[0]
            quantity = item[2]
            self.manager.import_stock(
                barcode,
                quantity,
                f"Hoan tra tu don xoa {code}",
                'admin'
            )
        
        # Xoa don hang
        conn = self.manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
        cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Thanh cong", f"Da xoa don hang {code}")
        self.refresh_orders()
        self.refresh_reports()
        self.refresh_products_list()


    def create_inventory_tab_new(self):
        """Tab xuat nhap"""

        main = tk.Frame(self.tab_inventory, bg='white')
        main.pack(fill='both', expand=True, padx=10, pady=10)

        header = tk.Frame(main, bg='#17a2b8', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(
            header,
            text="XUAT NHAP KHO",
            font=('Arial', 20, 'bold'),
            bg='#17a2b8',
            fg='white'
        ).pack(expand=True)

        content = tk.Frame(main, bg='white')
        content.pack(fill='both', expand=True, pady=10)

        # BEN TRAI: NHAP KHO
        left = tk.LabelFrame(
            content,
            text="NHAP KHO",
            font=('Arial', 14, 'bold'),
            bg='white',
            fg='#28a745'
        )
        left.pack(side='left', fill='both', expand=True, padx=5)

        tk.Label(
            left,
            text="Ma vach hoac Ten san pham:",
            bg='white',
            font=('Arial', 10, 'bold')
        ).pack(anchor='w', padx=10, pady=(10, 5))

        search_frame = tk.Frame(left, bg='white')
        search_frame.pack(fill='x', padx=10, pady=5)

        self.import_search_entry = tk.Entry(search_frame, font=('Arial', 12))
        self.import_search_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.import_search_entry.bind('<KeyRelease>', lambda e: self.search_product_realtime('import'))
        self.import_search_entry.bind('<Return>', lambda e: self.select_first_product('import'))

        tk.Button(
            search_frame,
            text="Tim",
            command=lambda: self.search_product_realtime('import'),
            bg='#17a2b8',
            fg='white',
            font=('Arial', 10, 'bold')
        ).pack(side='left')

        self.import_search_listbox = tk.Listbox(left, height=6, font=('Arial', 10))
        self.import_search_listbox.pack(fill='x', padx=10, pady=5)
        self.import_search_listbox.bind('<<ListboxSelect>>', lambda e: self.on_select_product('import'))

        info_frame = tk.LabelFrame(left, text="Thong tin san pham", bg='#f8f9fa', font=('Arial', 10, 'bold'))
        info_frame.pack(fill='x', padx=10, pady=10)

        self.import_product_info = tk.Text(info_frame, height=5, font=('Consolas', 9), bg='#f8f9fa', state='disabled')
        self.import_product_info.pack(fill='x', padx=5, pady=5)

        tk.Label(left, text="So luong nhap:", bg='white', font=('Arial', 10, 'bold')).pack(anchor='w', padx=10, pady=5)
        self.import_qty = tk.Entry(left, font=('Arial', 14), width=20)
        self.import_qty.pack(fill='x', padx=10, pady=5)

        tk.Label(left, text="Ghi chu:", bg='white', font=('Arial', 10, 'bold')).pack(anchor='w', padx=10, pady=5)
        self.import_note = tk.Text(left, height=4, font=('Arial', 10))
        self.import_note.pack(fill='x', padx=10, pady=5)

        tk.Button(
            left,
            text="NHAP KHO",
            command=self.do_import_stock,
            bg='#28a745',
            fg='white',
            font=('Arial', 12, 'bold'),
            height=2,
            cursor='hand2'
        ).pack(fill='x', padx=10, pady=10)

        # BEN PHAI: XUAT KHO
        right = tk.LabelFrame(
            content,
            text="XUAT KHO",
            font=('Arial', 14, 'bold'),
            bg='white',
            fg='#dc3545'
        )
        right.pack(side='right', fill='both', expand=True, padx=5)

        tk.Label(
            right,
            text="Ma vach hoac Ten san pham:",
            bg='white',
            font=('Arial', 10, 'bold')
        ).pack(anchor='w', padx=10, pady=(10, 5))

        search_frame2 = tk.Frame(right, bg='white')
        search_frame2.pack(fill='x', padx=10, pady=5)

        self.export_search_entry = tk.Entry(search_frame2, font=('Arial', 12))
        self.export_search_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.export_search_entry.bind('<KeyRelease>', lambda e: self.search_product_realtime('export'))
        self.export_search_entry.bind('<Return>', lambda e: self.select_first_product('export'))

        tk.Button(
            search_frame2,
            text="Tim",
            command=lambda: self.search_product_realtime('export'),
            bg='#17a2b8',
            fg='white',
            font=('Arial', 10, 'bold')
        ).pack(side='left')

        self.export_search_listbox = tk.Listbox(right, height=6, font=('Arial', 10))
        self.export_search_listbox.pack(fill='x', padx=10, pady=5)
        self.export_search_listbox.bind('<<ListboxSelect>>', lambda e: self.on_select_product('export'))

        info_frame2 = tk.LabelFrame(right, text="Thong tin san pham", bg='#f8f9fa', font=('Arial', 10, 'bold'))
        info_frame2.pack(fill='x', padx=10, pady=10)

        self.export_product_info = tk.Text(info_frame2, height=5, font=('Consolas', 9), bg='#f8f9fa', state='disabled')
        self.export_product_info.pack(fill='x', padx=5, pady=5)

        tk.Label(right, text="So luong xuat:", bg='white', font=('Arial', 10, 'bold')).pack(anchor='w', padx=10, pady=5)
        self.export_qty = tk.Entry(right, font=('Arial', 14), width=20)
        self.export_qty.pack(fill='x', padx=10, pady=5)

        tk.Label(right, text="Ghi chu:", bg='white', font=('Arial', 10, 'bold')).pack(anchor='w', padx=10, pady=5)
        self.export_note = tk.Text(right, height=4, font=('Arial', 10))
        self.export_note.pack(fill='x', padx=10, pady=5)

        tk.Button(
            right,
            text="XUAT KHO",
            command=self.do_export_stock,
            bg='#dc3545',
            fg='white',
            font=('Arial', 12, 'bold'),
            height=2,
            cursor='hand2'
        ).pack(fill='x', padx=10, pady=10)

        self.selected_import_barcode = None
        self.selected_export_barcode = None

    def search_product_realtime(self, mode):
        """Tim kiem realtime"""
        if mode == 'import':
            keyword = self.import_search_entry.get().strip().lower()
            listbox = self.import_search_listbox
        else:
            keyword = self.export_search_entry.get().strip().lower()
            listbox = self.export_search_listbox

        listbox.delete(0, tk.END)
        if len(keyword) < 1:
            return

        products = self.manager.get_all_products()
        matching = []
        for p in products:
            product_id, barcode, name, category, quantity, min_stock, price, cost_price, last_updated = p
            if keyword in barcode.lower() or keyword in name.lower():
                matching.append((barcode, name, quantity, price))

        for barcode, name, qty, price in matching[:10]:
            display_text = f"{barcode} - {name} (Ton: {qty}, Gia: {price:,.0f})"
            listbox.insert(tk.END, display_text)

    def on_select_product(self, mode):
        """Chon san pham"""
        if mode == 'import':
            listbox = self.import_search_listbox
            info_widget = self.import_product_info
        else:
            listbox = self.export_search_listbox
            info_widget = self.export_product_info

        selection = listbox.curselection()
        if not selection:
            return

        selected_text = listbox.get(selection[0])
        barcode = selected_text.split(' - ')[0]

        if mode == 'import':
            self.selected_import_barcode = barcode
        else:
            self.selected_export_barcode = barcode

        product = self.manager.get_product_by_barcode(barcode)

        if product:
            info_widget.config(state='normal')
            info_widget.delete(1.0, tk.END)
            info_text = (
                f"Ma: {product[1]}\n"
                f"Ten: {product[2]}\n"
                f"Danh muc: {product[3] or 'N/A'}\n"
                f"Ton kho: {product[4]}\n"
                f"Gia ban: {product[6]:,.0f} VND\n"
                f"Gia von: {product[7]:,.0f} VND\n"
                f"NCC: {product[9] or 'N/A'}"
            )
            info_widget.insert(1.0, info_text)
            info_widget.config(state='disabled')

    def select_first_product(self, mode):
        """Chon san pham dau tien"""
        if mode == 'import':
            listbox = self.import_search_listbox
        else:
            listbox = self.export_search_listbox

        if listbox.size() > 0:
            listbox.selection_set(0)
            self.on_select_product(mode)

    def do_import_stock(self):
        """Nhap kho"""
        if not self.selected_import_barcode:
            messagebox.showwarning("Canh bao", "Vui long chon san pham!")
            return
        try:
            qty = int(self.import_qty.get())
        except:
            messagebox.showerror("Loi", "So luong khong hop le!")
            return

        note = self.import_note.get(1.0, tk.END).strip()
        if qty <= 0:
            messagebox.showwarning("Canh bao", "So luong phai lon hon 0!")
            return

        success, msg = self.manager.import_stock(self.selected_import_barcode, qty, note, 'admin')
        if success:
            messagebox.showinfo("Thanh cong", f"Da nhap {qty} san pham")
            self.import_search_entry.delete(0, tk.END)
            self.import_qty.delete(0, tk.END)
            self.import_note.delete(1.0, tk.END)
            self.import_search_listbox.delete(0, tk.END)
            self.import_product_info.config(state='normal')
            self.import_product_info.delete(1.0, tk.END)
            self.import_product_info.config(state='disabled')
            self.selected_import_barcode = None
            self.refresh_products_list()
        else:
            messagebox.showerror("Loi", msg)

    def do_export_stock(self):
        """Xuat kho"""
        if not self.selected_export_barcode:
            messagebox.showwarning("Canh bao", "Vui long chon san pham!")
            return
        try:
            qty = int(self.export_qty.get())
        except:
            messagebox.showerror("Loi", "So luong khong hop le!")
            return

        note = self.export_note.get(1.0, tk.END).strip()
        if qty <= 0:
            messagebox.showwarning("Canh bao", "So luong phai lon hon 0!")
            return

        success, msg = self.manager.export_stock(self.selected_export_barcode, qty, note, 'admin')
        if success:
            messagebox.showinfo("Thanh cong", f"Da xuat {qty} san pham")
            self.export_search_entry.delete(0, tk.END)
            self.export_qty.delete(0, tk.END)
            self.export_note.delete(1.0, tk.END)
            self.export_search_listbox.delete(0, tk.END)
            self.export_product_info.config(state='normal')
            self.export_product_info.delete(1.0, tk.END)
            self.export_product_info.config(state='disabled')
            self.selected_export_barcode = None
            self.refresh_products_list()
        else:
            messagebox.showerror("Loi", msg)

    # ================== TAB SAN PHAM ==================

    def create_products_tab(self):
        """Tab san pham"""

        header = tk.Frame(self.tab_products, bg='white')
        header.pack(fill='x', padx=10, pady=10)

        tk.Label(
            header,
            text="DANH SACH SAN PHAM",
            font=('Arial', 16, 'bold'),
            bg='white',
            fg='#007bff'
        ).pack(side='left')

        btn_container = tk.Frame(header, bg='white')
        btn_container.pack(side='right')

        ttk.Button(btn_container, text="Them", command=self.show_add_product_dialog).pack(side='left', padx=2)
        ttk.Button(btn_container, text="Sua", command=self.show_edit_product_dialog).pack(side='left', padx=2)
        ttk.Button(btn_container, text="Xoa", command=self.delete_selected_product).pack(side='left', padx=2)
        ttk.Button(btn_container, text="Lam moi", command=self.refresh_products_list).pack(side='left', padx=2)

        search_frame = tk.Frame(self.tab_products, bg='white')
        search_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(search_frame, text="Tim kiem:", bg='white').pack(side='left', padx=5)
        self.search_entry = tk.Entry(search_frame, font=('Arial', 11), width=40)
        self.search_entry.pack(side='left', padx=5)
        self.search_entry.bind('<KeyRelease>', lambda e: self.search_products())

        tree_frame = tk.Frame(self.tab_products, bg='white')
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        tree_scroll_y = ttk.Scrollbar(tree_frame, orient='vertical')
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient='horizontal')

        self.products_tree = ttk.Treeview(
            tree_frame,
            columns=('ID', 'Ma', 'Ten', 'Danh muc', 'So luong', 'Ton TT', 'Gia', 'Cap nhat'),
            show='headings',
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
            height=20
        )

        tree_scroll_y.config(command=self.products_tree.yview)
        tree_scroll_x.config(command=self.products_tree.xview)

        columns_config = {
            'ID': 50,
            'Ma': 130,
            'Ten': 250,
            'Danh muc': 120,
            'So luong': 100,
            'Ton TT': 100,
            'Gia': 120,
            'Cap nhat': 150
        }

        for col, width in columns_config.items():
            self.products_tree.heading(col, text=col, anchor='w')
            self.products_tree.column(col, width=width, anchor='w')

        self.products_tree.pack(side='left', fill='both', expand=True)
        tree_scroll_y.pack(side='right', fill='y')
        tree_scroll_x.pack(side='bottom', fill='x')

        self.products_tree.bind('<Double-1>', lambda e: self.show_edit_product_dialog())

        self.refresh_products_list()

    def refresh_products_list(self):
        """Refresh danh sach san pham"""
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)

        products = self.manager.get_all_products()
        for product in products:
            pid, barcode, name, category, quantity, min_stock, price, cost_price, last_updated = product
            self.products_tree.insert(
                '',
                'end',
                values=(
                    pid,
                    barcode,
                    name,
                    category,
                    quantity,
                    min_stock,
                    f"{price:,.0f}",
                    last_updated
                )
            )

    def search_products(self):
        """Tim kiem san pham theo tu khoa"""
        keyword = self.search_entry.get().strip().lower()
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)

        products = self.manager.get_all_products()
        for product in products:
            pid, barcode, name, category, quantity, min_stock, price, cost_price, last_updated = product
            if (
                keyword in barcode.lower()
                or keyword in (name or '').lower()
                or keyword in (category or '').lower()
            ):
                self.products_tree.insert(
                    '',
                    'end',
                    values=(
                        pid,
                        barcode,
                        name,
                        category,
                        quantity,
                        min_stock,
                        f"{price:,.0f}",
                        last_updated
                    )
                )

    def show_add_product_dialog(self):
        """Dialog them san pham"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Them san pham moi")
        dialog.geometry("550x650")
        dialog.transient(self.root)
        x = dialog.winfo_screenwidth() // 2 - 275
        y = dialog.winfo_screenheight() // 2 - 325
        dialog.geometry(f"+{x}+{y}")
        dialog.update_idletasks()
        dialog.grab_set()

        tk.Label(dialog, text="THEM SAN PHAM MOI", font=('Arial', 14, 'bold')).pack(pady=15)

        formframe = tk.Frame(dialog)
        formframe.pack(fill='both', expand=True, padx=20, pady=10)

        fields = [
            ("Ma vach", "barcode"),
            ("Ten", "name"),
            ("Danh muc", "category"),
            ("So luong", "quantity"),
            ("Ton TT", "minstock"),
            ("Gia ban", "price"),
            ("Gia von", "costprice"),
            ("NCC", "supplier"),
        ]
        entries = {}
        for i, (label, field) in enumerate(fields):
            tk.Label(formframe, text=label, anchor='w').grid(row=i, column=0, sticky='w', pady=8, padx=5)
            entry = tk.Entry(formframe, font=('Arial', 10), width=35)
            entry.grid(row=i, column=1, sticky='ew', pady=8, padx=5)
            entries[field] = entry
        formframe.columnconfigure(1, weight=1)

        def save():
            try:
                barcode = entries['barcode'].get().strip()
                name = entries['name'].get().strip()
                category = entries['category'].get().strip()
                quantity = int(entries['quantity'].get() or 0)
                minstock = int(entries['minstock'].get() or 10)
                price = float(entries['price'].get() or 0)
                costprice = float(entries['costprice'].get() or 0)
                supplier = entries['supplier'].get().strip()

                if not barcode or not name:
                    messagebox.showwarning("Canh bao", "Ma va ten khong duoc trong!")
                    return

                success, msg = self.manager.add_product(
                    barcode,
                    name,
                    category,
                    quantity,
                    minstock,
                    price,
                    costprice,
                    supplier
                )
                if success:
                    messagebox.showinfo("OK", msg)
                    dialog.destroy()
                    self.refresh_products_list()
                else:
                    messagebox.showerror("Loi", msg)
            except ValueError as e:
                messagebox.showerror("Loi", f"Du lieu sai! {e}")

        btnframe = tk.Frame(dialog)
        btnframe.pack(pady=15)
        ttk.Button(btnframe, text="Luu", command=save, width=15).pack(side='left', padx=5)
        ttk.Button(btnframe, text="Huy", command=dialog.destroy, width=15).pack(side='left', padx=5)

    def show_edit_product_dialog(self):
        """Dialog sua san pham"""
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("Canh bao", "Chon san pham!")
            return

        values = self.products_tree.item(selected[0])['values']
        product_id = values[0]
        product = self.manager.get_product_by_id(product_id)
        if not product:
            messagebox.showerror("Loi", "Khong tim thay!")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Sua {product[2]}")
        dialog.geometry("550x650")
        dialog.transient(self.root)
        x = dialog.winfo_screenwidth() // 2 - 275
        y = dialog.winfo_screenheight() // 2 - 325
        dialog.geometry(f"+{x}+{y}")
        dialog.update_idletasks()
        dialog.grab_set()

        tk.Label(dialog, text="SUA SAN PHAM", font=('Arial', 14, 'bold')).pack(pady=15)

        formframe = tk.Frame(dialog)
        formframe.pack(fill='both', expand=True, padx=20, pady=10)

        fields = [
            ("Ma", "barcode", product[1]),
            ("Ten", "name", product[2]),
            ("Danh muc", "category", product[3] or ""),
            ("So luong", "quantity", product[4]),
            ("Ton TT", "minstock", product[5]),
            ("Gia ban", "price", product[6]),
            ("Gia von", "costprice", product[7]),
            ("NCC", "supplier", product[9] or ""),
        ]
        entries = {}
        for i, (label, field, value) in enumerate(fields):
            tk.Label(formframe, text=label, anchor='w').grid(row=i, column=0, sticky='w', pady=8, padx=5)
            entry = tk.Entry(formframe, font=('Arial', 10), width=35)
            entry.grid(row=i, column=1, sticky='ew', pady=8, padx=5)
            entry.insert(0, str(value))
            if field == 'barcode':
                entry.config(state='readonly')
            entries[field] = entry
        formframe.columnconfigure(1, weight=1)

        def update():
            try:
                barcode = entries['barcode'].get().strip()
                name = entries['name'].get().strip()
                category = entries['category'].get().strip()
                quantity = int(entries['quantity'].get() or 0)
                minstock = int(entries['minstock'].get() or 10)
                price = float(entries['price'].get() or 0)
                costprice = float(entries['costprice'].get() or 0)
                supplier = entries['supplier'].get().strip()

                if not name:
                    messagebox.showwarning("Canh bao", "Ten khong duoc trong!")
                    return

                success, msg = self.manager.update_product(
                    barcode,
                    name,
                    category,
                    quantity,
                    minstock,
                    price,
                    costprice,
                    supplier
                )
                if success:
                    messagebox.showinfo("OK", msg)
                    dialog.destroy()
                    self.refresh_products_list()
                else:
                    messagebox.showerror("Loi", msg)
            except ValueError as e:
                messagebox.showerror("Loi", f"Du lieu sai! {e}")

        btnframe = tk.Frame(dialog)
        btnframe.pack(pady=15)
        ttk.Button(btnframe, text="Cap nhat", command=update, width=15).pack(side='left', padx=5)
        ttk.Button(btnframe, text="Huy", command=dialog.destroy, width=15).pack(side='left', padx=5)

    def delete_selected_product(self):
        """Xoa san pham"""
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("Canh bao", "Chon san pham!")
            return

        values = self.products_tree.item(selected[0])['values']
        barcode = values[1]
        name = values[2]

        if not messagebox.askyesno("Xac nhan", f"Xoa san pham {name} ({barcode})?"):
            return

        success, msg = self.manager.delete_product(barcode)
        if success:
            messagebox.showinfo("OK", msg)
            self.refresh_products_list()
        else:
            messagebox.showerror("Loi", msg)

    # ================== TAB DON HANG ==================



    # ================== TAB CANH BAO ==================

    def create_alerts_tab(self):
        """Tab canh bao"""

        tk.Label(
            self.tab_alerts,
            text="CANH BAO TON KHO THAP",
            font=('Arial', 16, 'bold'),
            bg='white',
            fg='#dc3545'
        ).pack(pady=20)

        tree_frame = tk.Frame(self.tab_alerts, bg='white')
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        tree_scroll = ttk.Scrollbar(tree_frame, orient='vertical')

        self.alerts_tree = ttk.Treeview(
            tree_frame,
            columns=('Ma', 'Ten', 'So luong', 'Ton TT', 'Trang thai'),
            show='headings',
            yscrollcommand=tree_scroll.set,
            height=20
        )

        tree_scroll.config(command=self.alerts_tree.yview)

        columns = {
            'Ma': 150,
            'Ten': 300,
            'So luong': 120,
            'Ton TT': 120,
            'Trang thai': 150
        }

        for col, width in columns.items():
            self.alerts_tree.heading(col, text=col)
            self.alerts_tree.column(col, width=width)

        self.alerts_tree.pack(side='left', fill='both', expand=True)
        tree_scroll.pack(side='right', fill='y')

        ttk.Button(self.tab_alerts, text="Lam moi", command=self.refresh_alerts).pack(pady=10)

        self.refresh_alerts()

    def refresh_alerts(self):
        """Refresh canh bao ton kho thap"""
        for item in self.alerts_tree.get_children():
            self.alerts_tree.delete(item)

        low = self.manager.get_low_stock_products()
        for p in low:
            barcode, name, cat, qty, minstock, price, last, created = p
            status = "HET" if qty == 0 else "SAP HET"
            tag = "out" if qty == 0 else "low"
            self.alerts_tree.insert(
                '',
                'end',
                values=(barcode, name, qty, minstock, status),
                tags=(tag,)
            )
        self.alerts_tree.tag_configure("out", background='#f8d7da')
        self.alerts_tree.tag_configure("low", background='#fff3cd')

        self.update_status(f"Co {len(low)} canh bao")

    # ================== TAB BAO CAO ==================

    def create_reports_tab(self):
        """Tab bao cao"""

        tk.Label(
            self.tab_reports,
            text="BAO CAO LOI NHUAN THEO THANG",
            font=('Arial', 16, 'bold'),
            bg='white',
            fg='#007bff'
        ).pack(pady=20)

        btnframe = tk.Frame(self.tab_reports, bg='white')
        btnframe.pack(fill='x', padx=10, pady=5)

        ttk.Button(btnframe, text="Lam moi", command=self.refresh_reports).pack(side='left', padx=5)

        tree_frame = tk.Frame(self.tab_reports, bg='white')
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        scrolly = ttk.Scrollbar(tree_frame, orient='vertical')

        self.reports_tree = ttk.Treeview(
            tree_frame,
            columns=('Thang', 'Doanh thu', 'Loi nhuan', 'Ty le LN', 'So don'),
            show='headings',
            yscrollcommand=scrolly.set,
            height=20
        )

        scrolly.config(command=self.reports_tree.yview)

        columns = {
            'Thang': 150,
            'Doanh thu': 200,
            'Loi nhuan': 200,
            'Ty le LN': 150,
            'So don': 100
        }

        for col, width in columns.items():
            self.reports_tree.heading(col, text=col)
            self.reports_tree.column(col, width=width)

        self.reports_tree.pack(side='left', fill='both', expand=True)
        scrolly.pack(side='right', fill='y')

        self.refresh_reports()

    def refresh_reports(self):
        """Refresh bao cao thang"""
        for item in self.reports_tree.get_children():
            self.reports_tree.delete(item)

        monthly = self.manager.get_monthly_profit()
        for monthdata in monthly:
            month, profit, revenue, count = monthdata
            if revenue != 0:
                margin = profit / revenue * 100
            else:
                margin = 0
            self.reports_tree.insert(
                '',
                'end',
                values=(
                    month,
                    f"{revenue:,.0f} VND",
                    f"{profit:,.0f} VND",
                    f"{margin:.1f} %",
                    count
                )
            )

    # ================== TIỆN ÍCH CHUNG ==================

    def update_status(self, msg):
        """Cap nhat status bar"""
        if hasattr(self, 'status_bar'):
            self.status_bar.config(text=msg)
            self.root.update_idletasks()

    def on_closing(self):
        """Dong app"""
        if self.camera_running:
            self.stop_camera_auto()
        try:
            cv2.destroyAllWindows()
        except:
            pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = InventoryApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
