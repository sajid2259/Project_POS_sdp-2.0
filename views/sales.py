import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
import db, sales
from views.theme import (
    CARD_BG, INPUT_BG, TEXT_PRIMARY, TEXT_MUTED, ACCENT, ACCENT_HOVER,
    SUCCESS, SUCCESS_HOVER, BORDER, CORNER_RADIUS, setup_treeview_style, section_title
)

class SalesView(ctk.CTkFrame):
    def __init__(self, master, reload_callback=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.reload_callback = reload_callback
        self.cart = []
        
        # Title
        section_title(self, "Sales").pack(pady=(18, 10), padx=20, anchor="w")
        tree_style = setup_treeview_style()
        
        # Form frame
        form_frame = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=CORNER_RADIUS, border_width=1, border_color=BORDER)
        form_frame.pack(fill="x", padx=20, pady=8)
        
        # Product
        ctk.CTkLabel(form_frame, text="Product / Barcode:", text_color=TEXT_MUTED).pack(side="left", padx=(14, 5), pady=14)
        
        # We use a frame to hold the entry to allow absolute positioning of a suggestion listbox if needed,
        # but a simple Combobox is much better for autocomplete!
        self.products_list = [p[0] for p in db.con().execute("SELECT name FROM products").fetchall()]
        
        self.pr_e = ctk.CTkComboBox(
            form_frame, width=220, values=self.products_list, command=self.on_pr_key,
            fg_color=INPUT_BG, border_color=BORDER, text_color=TEXT_PRIMARY, button_color=ACCENT, button_hover_color=ACCENT_HOVER
        )
        self.pr_e.set("") # empty initially
        self.pr_e.pack(side="left", padx=5)
        self.pr_e.bind("<KeyRelease>", self.on_pr_key)
        
        # Quantity
        ctk.CTkLabel(form_frame, text="Quantity:", text_color=TEXT_MUTED).pack(side="left", padx=(15, 5))
        self.qt_e = ctk.CTkEntry(form_frame, width=110, fg_color=INPUT_BG, border_color=BORDER, text_color=TEXT_PRIMARY)
        self.qt_e.pack(side="left", padx=5)
        self.qt_e.bind("<Return>", lambda e: self.add_to_cart())
        self.qt_e.bind("<KeyRelease>", self.on_pr_key)
        self.pr_e.bind("<Return>", lambda e: self.add_to_cart())
        
        # Unit Hint
        self.unit_hint = ctk.StringVar(value="")
        tk.Label(form_frame, textvariable=self.unit_hint, bg=CARD_BG, fg="#8FBEFF", font=("Segoe UI", 9, "italic")).pack(side="left", padx=8)
        
        # Cart bar
        cart_bar = ctk.CTkFrame(self, fg_color="transparent")
        cart_bar.pack(fill="x", padx=20, pady=(2, 8))
        ctk.CTkButton(
            cart_bar, text="Add to Cart", fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color="white", command=self.add_to_cart, width=120
        ).pack(side="left")
        self.cart_var = ctk.StringVar(value="Cart: 0 items (0.00 ৳)")
        tk.Label(cart_bar, textvariable=self.cart_var, bg="#0F1A30",
                 fg=TEXT_PRIMARY, font=("Segoe UI", 10)).pack(side="left", padx=10)
        ctk.CTkButton(
            cart_bar, text="Checkout + Print", fg_color=SUCCESS, hover_color=SUCCESS_HOVER,
            text_color="white", command=self.checkout_cart, width=140
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            cart_bar, text="Clear Cart", fg_color="#1A2A47", hover_color="#223861",
            text_color="white", command=self.clear_cart, width=100,
            border_width=1, border_color=BORDER
        ).pack(side="left")
        
        # Treeview mapping properties
        cols = ["ID", "Product", "Qty", "Total ৳", "Timestamp"]
        widths = [55, 260, 100, 100, 150]
        
        # Treeview Frame
        tree_frame = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=CORNER_RADIUS, border_width=1, border_color=BORDER)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(8, 10))
        
        self.stree = ttk.Treeview(tree_frame, columns=list(range(1, len(cols)+1)), show="headings", height=10, style=tree_style)
        for i, (col, w) in enumerate(zip(cols, widths), 1):
            self.stree.heading(i, text=col)
            self.stree.column(i, width=w, anchor="center")
            
        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.stree.yview)
        self.stree.configure(yscrollcommand=sb.set)
        self.stree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        
        self.refresh()

    def on_pr_key(self, choice=None):
        pr_val = str(choice) if isinstance(choice, str) else self.pr_e.get()
        p = db.find(pr_val.strip())
        qt_str = self.qt_e.get().strip()
        if p:
            try:
                qty = float(qt_str) if qt_str else 0
            except ValueError:
                qty = 0
            total = qty * p['sell_price']
            self.unit_hint.set(f"({p['unit']} | ৳{p['sell_price']})  =>  {p['sell_price']} × {qty} = {total:.2f} ৳")
        else:
            self.unit_hint.set("")

    def _update_cart_label(self):
        total = sum(i["amount"] for i in self.cart)
        self.cart_var.set(f"Cart: {len(self.cart)} items ({total:.2f} ৳)")

    def add_to_cart(self):
        pr = self.pr_e.get().strip()
        qt = self.qt_e.get().strip()
        if not pr or not qt:
            return messagebox.showwarning("Input", "Product & Qty required.")

        p = db.find(pr)
        if not p:
            return messagebox.showerror("Error", "Product not found.")
        try:
            qty = float(qt)
        except ValueError:
            return messagebox.showerror("Error", "Invalid quantity.")
        if p["stock"] < qty:
            return messagebox.showerror("Error", f"Insufficient stock. Only {p['stock']} {p['unit']} left.")

        self.cart.append({
            "product": p["name"],
            "qty": qty,
            "amount": qty * p["sell_price"],
        })
        self._update_cart_label()
        self.pr_e.set("")
        self.qt_e.delete(0, "end")
        self.unit_hint.set("")

    def clear_cart(self):
        self.cart = []
        self._update_cart_label()

    def checkout_cart(self):
        if not self.cart:
            return messagebox.showinfo("Empty Cart", "No items in the cart to checkout.")

        payload = [{"product": i["product"], "qty": i["qty"]} for i in self.cart]
        err, result = sales.checkout(payload, tree=self.stree)
        if err:
            return messagebox.showerror("Error", err)

        self.after(0, self._refresh_after_checkout)
        filename = None
        try:
            import invoice
            filename = invoice.generate_cart_receipt(result["items"], result["total"])
        except Exception as e:
            messagebox.showerror("Error", f"Checkout complete, but receipt failed: {e}")

        msg = f"Checked out {len(result['items'])} item(s).\nTotal: {result['total']:.2f} ৳"
        if filename:
            msg += f"\nReceipt: {filename}"
        messagebox.showinfo("Checkout Complete", msg)
        self.clear_cart()

    def _refresh_after_checkout(self):
        self.refresh()
        if self.reload_callback:
            self.reload_callback()

    def refresh(self):
        sales.load(self.stree)
        self.products_list = [p[0] for p in db.con().execute("SELECT name FROM products").fetchall()]
        self.pr_e.configure(values=self.products_list)
