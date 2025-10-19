"""RestaurantApp GUI.

Heads-up:
- Products expose prodID/prodName/prodPrice/prodStock (aliases: id/price/stock).
- Inventory.load() pulls products + addons, but we only list products for now.
- Order items could be a Product or an Addon; UI sticks to products until we expand it.

Category buttons are just filler (no category field yet). 'All' just reloads everything.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Any
from restaraunt_system import InventoryHandler, defaultProductFile, defaultAddonFile, errorPopup
import customtkinter as ctk

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# -------------- Connect to Backend --------------
class BackendAdapter:
    def __init__(self) -> None:
        self.handler = InventoryHandler()
        # Load product data
        self.handler.loadDataFile(defaultProductFile, "Product")
        self.handler.loadDataFile(defaultAddonFile, "Addon")

    @property
    def products(self):
        return self.handler.productList

    @property
    def addons(self):
        return self.handler.addonList

    def load(self) -> None:
        self.handler.loadDataFile(defaultProductFile, "Product")
        self.handler.loadDataFile(defaultAddonFile, "Addon")

    def get_product(self, pid: int, val: str = 'prodID', searchFor: str = 'UNSET'):
        for p in self.handler.productList:
            if getattr(p, val, None) == pid:
                if searchFor != 'UNSET':
                    return getattr(p, searchFor)
                return p
        return None
    
    def get_addon(self, aid: int, val: str = 'addonID'):
        for a in self.handler.addonList:
            if getattr(a, val, None) == aid:
                return a
        return None

    def reduce_stock(self, pid: int, qty: int) -> bool:
        # Negative reduces stock; InventoryHandler enforces bounds
        return self.handler.updateStock(pid, -qty)
    
    def reduce_addon_stock(self, aid: int, qty: int) -> bool:
        # Mirror reduce_stock for addons list (since InventoryHandler tracks both)
        for addon in self.handler.addonList:
            if getattr(addon, 'addonID', None) == aid:
                new_stock = getattr(addon, 'addonStock', 0) - qty
                if new_stock < 0:
                    return False
                addon.addonStock = new_stock
                return True
        return False

    def save_products(self) -> bool:
        ids = [str(p.prodID) for p in self.handler.productList]
        return self.handler.commitMultipleStock(ids)
    
    def save_addons(self) -> bool:
        """Save addon stock changes to file."""
        try:
            with open(self.handler.addonFilePath, "r") as f:
                lines = f.readlines()

            # Build a dict of addonID -> new stock
            stock_map = {addon.addonID: addon.addonStock for addon in self.handler.addonList}
            
            in_addon = None
            for i, line in enumerate(lines):
                if line.startswith("addonID="):
                    addon_id = int(line.split("=")[1].strip())
                    in_addon = addon_id if addon_id in stock_map else None
                elif in_addon is not None and line.startswith("addonStock="):
                    lines[i] = f"addonStock={stock_map[in_addon]}\n"

            with open(self.handler.addonFilePath, "w") as f:
                f.writelines(lines)

            print(f"Addon stock committed for addons: {', '.join(map(str, stock_map.keys()))}")
            return True
        except Exception as e:
            print("Error committing addon stock:", e)
            return False


# -------------- Lightweight order local to GUI --------------
class AppOrder:
    def __init__(self) -> None:
        self.items: list[tuple[Any, int]] = []

    def add_item(self, item: Any, qty: int = 1, itemType = 'Product') -> None:
        if itemType == 'Product':
            self.items.append((item, qty))
        elif itemType == 'Addon':
            '''This is here because I wanted to add a way to make addons stick out better versus normal items.
            However, it seems to be changing the actual backend class info or something because it just keeps adding the '  +' for each entry.
            If someone wants to figure it out, please do.'''
            #newItem = item
            #newName = "  +" + newItem.addonName
            #newItem.addonName = newName
            #self.items.append((newItem, qty))
            self.items.append((item, qty))
        # Check for if the item comes with addons by default, and if so, we need to add them.
        

    def remove_last_item(self) -> None:
        if self.items:
            self.items.pop()

    # This is the function for removing stuff from the center pane. Couldn't get it working properly so if someone else wants to do it, go ahead
    '''
    def remove_sel_item(self, itemToRemove: Any) -> None:
        self.items.remove(itemToRemove)
    '''

    def total(self) -> float:
        return sum(getattr(i, 'prodPrice', getattr(i, 'addonPrice', 0.0)) * q for i, q in self.items)

    def summary(self) -> str:
        lines = ["Receipt Summary:"]
        for i, q in self.items:
            name = getattr(i, 'prodName', getattr(i, 'addonName', 'Item'))
            price = getattr(i, 'prodPrice', getattr(i, 'addonPrice', 0.0))
            lines.append(f"{name} x{q} @ ${price:.2f} = ${price * q:.2f}")
        lines.append("-" * 28)
        lines.append(f"Subtotal: ${self.total():.2f}")
        return "\n".join(lines)
    
    def save_to_file(self, filename: str, tax: float = 0.0, tip: float = 0.0) -> None:
        """Save the order details to a orders.txt with tax and tip included."""
        from datetime import datetime
        import os
        order_number = 1
        if os.path.exists(filename):
            #count orders 
            with open(filename, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("Order #"):
                        order_number += 1

        subtotal = self.total()
        total = subtotal + tax + tip

        with open(filename, 'a', encoding='utf-8') as f:
            f.write(f"Order #{order_number} — Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            for i, q in self.items:
                name = getattr(i, 'prodName', getattr(i, 'addonName', 'Item'))
                price = getattr(i, 'prodPrice', getattr(i, 'addonPrice', 0.0))
                f.write(f"{name} x{q} @ ${price:.2f} = ${price * q:.2f}\n")
            f.write(f"Subtotal: ${subtotal:.2f}\n")
            f.write(f"Tax: ${tax:.2f}\n")
            f.write(f"Tip: ${tip:.2f}\n")
            f.write(f"Total: ${total:.2f}\n\n")

class RestaurantApp:
    TAX_RATE = 0.07

    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("Restaurant Ordering System")
        # Add backend adapter
        self.backend = BackendAdapter()
        self.order = AppOrder()
        self.current_category: Optional[str] = None

        # Declare widget attributes for type checking
        self.menu_tree = None
        self.order_tree = None
        self.stock_tree = None
        self.quantity_entry = None
        self.hold_list = None
        self.activeTree = None
        self.selected_tree = None  # Track which tree has selection for removal
        self.selected_item = None  # Track selected item for removal
        self.held_orders = []  # Held orders storage
        self.hold_seq = 1
        self.order_sent_to_kitchen = False

        # Keep parent open state
        self.tree_index_map: dict[str, dict[str, int | bool]] = {}
        self.open_parent_indices: set[int] = set()

        self.subtotal_var = tk.StringVar(value="Subtotal: $0.00")
        self.tax_var = tk.StringVar(value="Tax: $0.00")
        self.total_var = tk.StringVar(value="Total: $0.00")

        self.build_layout()
        self.refresh_products()
        self.refresh_stock_display()
        self.update_order_summary()

    # ---------------- Layout ----------------
    def build_layout(self):
        top_frame = ctk.CTkFrame(self.root)
        top_frame.pack(fill='x', pady=8, padx=8)
        ctk.CTkLabel(top_frame, text="Restaurant Ordering System", font=("Segoe UI", 18, "bold")).pack(pady=8)

        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill='both', expand=True, padx=8, pady=8)

        left_frame = ctk.CTkFrame(main_frame)
        left_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        center_frame = ctk.CTkFrame(main_frame)
        center_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.grid(row=0, column=2, sticky='nsew', padx=5, pady=5)

        main_frame.columnconfigure(0, weight=2)
        main_frame.columnconfigure(1, weight=3)
        main_frame.columnconfigure(2, weight=2)
        main_frame.rowconfigure(0, weight=1)

        # Left: categories and menu list
        cat_frame = ctk.CTkFrame(left_frame)
        cat_frame.pack(fill='x', pady=(5, 10), padx=5)
        ctk.CTkLabel(cat_frame, text="Categories:").pack(anchor='w', padx=5)
        # Category buttons are placeholders; product records currently have no category metadata.
        for cat in ["All"]:
            ctk.CTkButton(cat_frame, text=cat, width=10, command=lambda c=cat: self.filter_category(c)).pack(side='left', padx=5, pady=5)

        menu_frame = ctk.CTkFrame(left_frame)
        menu_frame.pack(fill='both', expand=True, padx=5, pady=5)
        ctk.CTkLabel(menu_frame, text="Products", font=("Segoe UI", 14, "bold")).pack(pady=2)
        self.menu_tree = ttk.Treeview(menu_frame, columns=("id", "name", "price", "stock"), show='headings', height=12)
        for col, text, w in [("id", "ID", 40), ("name", "Name", 140), ("price", "Price", 70), ("stock", "Stock", 60)]:
            self.menu_tree.heading(col, text=text)
            self.menu_tree.column(col, width=w, anchor='center')
        self.menu_tree.pack(side='left', fill='both', expand=True)
        menu_scroll = ttk.Scrollbar(menu_frame, orient='vertical')
        menu_scroll.config(command=self.menu_tree.yview)  # type: ignore[arg-type]
        self.menu_tree.configure(yscrollcommand=menu_scroll.set)
        menu_scroll.pack(side='right', fill='y')
        
        # Quantity and Add button directly under Products (same row)
        qty_frame = ctk.CTkFrame(left_frame)
        qty_frame.pack(fill='x', pady=5)
        ctk.CTkLabel(qty_frame, text="Qty:").pack(side='left')
        self.quantity_entry = ctk.CTkEntry(qty_frame, width=50)
        self.quantity_entry.insert(0, "1")
        self.quantity_entry.pack(side='left', padx=4)
        ctk.CTkButton(qty_frame, text="Add to Dine-In", command=self.add_to_order, width=16).pack(side='left', padx=8)
        ctk.CTkButton(qty_frame, text="Add to Carry-Out", command=self.hold_order, width=16).pack(side='left', padx=8)
        
        self.menu_tree.bind("<<TreeviewSelect>>", self.tree_selected)
        
        # Addons menu, left side, basically the same as the product one above
        addon_menu_frame = ctk.CTkFrame(left_frame)
        addon_menu_frame.pack(fill='both', expand=True, padx=5, pady=5)
        ctk.CTkLabel(addon_menu_frame, text="Addons / Mods", font=("Segoe UI", 14, "bold")).pack(pady=2)
        self.addon_menu_tree = ttk.Treeview(addon_menu_frame, columns=("id", "name", "price", "stock"), show='headings', height=12)
        for col, text, w in [("id", "ID", 40), ("name", "Name", 140), ("price", "Price", 70), ("stock", "Stock", 60)]:
            self.addon_menu_tree.heading(col, text=text)
            self.addon_menu_tree.column(col, width=w, anchor='center')
        self.addon_menu_tree.pack(side='left', fill='both', expand=True)
        addon_menu_scroll = ttk.Scrollbar(addon_menu_frame, orient='vertical')
        addon_menu_scroll.config(command=self.addon_menu_tree.yview)  # type: ignore[arg-type]
        self.addon_menu_tree.configure(yscrollcommand=addon_menu_scroll.set)
        addon_menu_scroll.pack(side='right', fill='y')

        
        self.addon_menu_tree.bind("<<TreeviewSelect>>", self.tree_selected)
        
        # Add Mod button
        mod_btn_frame = ctk.CTkFrame(left_frame)
        mod_btn_frame.pack(fill='x', pady=5)
        ctk.CTkButton(mod_btn_frame, text="Add Mod", command=self.add_mod, width=16).pack(side='bottom', padx=8)

        # Center: order tree, buttons and totals
        ctk.CTkLabel(center_frame, text="Dine-In Order", font=("Segoe UI", 14, "bold")).pack(anchor='w', padx=5, pady=5)
        order_tree_frame = ctk.CTkFrame(center_frame)
        order_tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        # Initialize hierarchical order tree
        self.order_tree = ttk.Treeview(order_tree_frame, columns=("qty", "price", "subtotal"), show='tree headings', height=14)
        self.order_tree.heading("#0", text="Item")
        self.order_tree.heading("qty", text="Qty")
        self.order_tree.heading("price", text="Price")
        self.order_tree.heading("subtotal", text="Subtotal")
        self.order_tree.column("#0", width=160)
        self.order_tree.column("qty", width=40, anchor='center')
        self.order_tree.column("price", width=70, anchor='e')
        self.order_tree.column("subtotal", width=90, anchor='e')
        self.order_tree.pack(side='left', fill='both', expand=True)
        order_scroll = ttk.Scrollbar(order_tree_frame, orient='vertical')
        order_scroll.config(command=self.order_tree.yview)  # type: ignore[arg-type]
        self.order_tree.configure(yscrollcommand=order_scroll.set)
        order_scroll.pack(side='right', fill='y')

        # Small screen for Carry-Out orders (bold label)
        hold_frame = tk.LabelFrame(center_frame, text="Carry-Out Orders", padx=6, pady=6, font=("Segoe UI", 14, "bold"))
        hold_frame.pack(fill='x', pady=(8, 0))
        # Switch to tree-only view to show products as children under each carry-out order
        self.hold_list = ttk.Treeview(hold_frame, show='tree', height=4)
        self.hold_list.pack(fill='x')
        self.hold_list.column("#0", anchor='center')
        self.hold_list.insert('', 'end', text="No carry-out orders yet")

        # Buttons and totals (aligned with upstream layout)
        btn_frame = ctk.CTkFrame(center_frame)
        btn_frame.pack(fill='x', pady=5, padx=5)
        ctk.CTkButton(btn_frame, text="Remove Sel.", command=self.remove_sel_item).pack(side='left') 
        ctk.CTkButton(btn_frame, text="Remove Last", command=self.remove_last_item).pack(side='left', padx=5)
        ctk.CTkButton(btn_frame, text="Print Receipt", command=self.print_receipt).pack(side='right')
        ctk.CTkButton(btn_frame, text="Checkout", command=self.checkout_popup).pack(side='right', padx=5)
        
        # This might be useful for removing an item from the center order list. There is a function defined for this bind some ways below
        # Bind selection events for remove
        self.order_tree.bind("<<TreeviewSelect>>", self.centerpane_selected)
        self.hold_list.bind("<<TreeviewSelect>>", self.centerpane_selected)

        totals_frame = ctk.CTkFrame(center_frame)
        totals_frame.pack(fill='x', pady=5, padx=5)
        ctk.CTkLabel(totals_frame, textvariable=self.subtotal_var).pack(anchor='e', padx=5)
        ctk.CTkLabel(totals_frame, textvariable=self.tax_var).pack(anchor='e', padx=5)
        ctk.CTkLabel(totals_frame, textvariable=self.total_var, font=("Segoe UI", 12, "bold")).pack(anchor='e', padx=5)

        # Right: stock levels and actions
        ctk.CTkLabel(right_frame, text="Stock Levels", font=("Segoe UI", 14, "bold")).pack(anchor='w', padx=5, pady=5)
        stock_frame = ctk.CTkFrame(right_frame)
        stock_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.stock_tree = ttk.Treeview(stock_frame, columns=("id", "name", "stock"), show='headings', height=12)
        self.stock_tree.heading("id", text="ID")
        self.stock_tree.heading("name", text="Name")
        self.stock_tree.heading("stock", text="Stock")
        self.stock_tree.column("id", width=40, anchor='center')
        self.stock_tree.column("name", width=140)
        self.stock_tree.column("stock", width=60, anchor='center')
        self.stock_tree.pack(side='left', fill='both', expand=True)
        stock_scroll = ttk.Scrollbar(stock_frame, orient='vertical')
        stock_scroll.config(command=self.stock_tree.yview)  # type: ignore[arg-type]
        self.stock_tree.configure(yscrollcommand=stock_scroll.set)
        stock_scroll.pack(side='right', fill='y')

        self.stock_tree.tag_configure('low', background='#ffcccc')
        self.stock_tree.tag_configure('ok', background='#ccffcc')

        right_btns = ctk.CTkFrame(right_frame)
        right_btns.pack(fill='x', pady=5, padx=5)
        ctk.CTkButton(right_btns, text="Send to Kitchen", command=self.send_to_kitchen).pack(fill='x', pady=2)
        ctk.CTkButton(right_btns, text="Cancel Order", command=self.cancel_order).pack(fill='x', pady=2)
        ctk.CTkButton(right_btns, text="Load Menu", command=self.reload_menu).pack(fill='x', pady=2)
        ctk.CTkButton(right_btns, text="Update Stock", command=self.update_stock).pack(fill='x', pady=2)

    # --------------- Product / Stock ---------------
    def refresh_products(self):
        if not self.backend.products or not self.backend.addons:
            self.backend.load()
        if not self.menu_tree or not self.addon_menu_tree:
            return
        for row in self.menu_tree.get_children():
            self.menu_tree.delete(row)
        for row in self.addon_menu_tree.get_children():
            self.addon_menu_tree.delete(row)
        for p in self.backend.products:
            # Category filtering skipped (no category field). Could be extended later.
            self.menu_tree.insert('', 'end', values=(getattr(p, 'prodID', getattr(p, 'id', '?')),
                                                     getattr(p, 'prodName', 'Unknown'),
                                                     f"${getattr(p, 'prodPrice', 0.0):.2f}",
                                                     getattr(p, 'prodStock', 0)))
        for a in self.backend.addons:
            self.addon_menu_tree.insert('', 'end', values=(getattr(a, 'addonID', getattr(a, 'id', '?')),
                                                           getattr(a, 'addonName', 'Unknown'),
                                                           f"${getattr(a, 'addonPrice', 0.0):.2f}",
                                                           getattr(a, 'addonStock', 0)))

    def refresh_stock_display(self):
        if not self.stock_tree:
            return
        for row in self.stock_tree.get_children():
            self.stock_tree.delete(row)
        for p in self.backend.products:
            stock_val = getattr(p, 'prodStock', 0)
            tag = 'low' if stock_val <= 5 else 'ok'
            self.stock_tree.insert('', 'end', values=(getattr(p, 'prodID', getattr(p, 'id', '?')),
                                                      getattr(p, 'prodName', 'Unknown'),
                                                      stock_val), tags=(tag,))

    def filter_category(self, category: str):
        self.current_category = None if category == 'All' else category
        self.refresh_products()
        
    def tree_selected(self, event):
        self.activeTree = event.widget
        
    def centerpane_selected(self, event):
        """Track which tree and item is selected for removal."""
        self.selected_tree = event.widget
        self.selected_item = self.selected_tree.selection()

    # --------------- Order Logic ---------------
    def add_to_order(self):
        if not self.activeTree:
            return
        selection = self.activeTree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a menu item first.")
            return
        item_vals = self.activeTree.item(selection[0], 'values')
        iid = int(item_vals[0])
        if self.activeTree == self.menu_tree:
            try:
                assert self.quantity_entry is not None, "Quantity entry not initialized"
                qty = int(self.quantity_entry.get())
                if qty <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Bad Quantity", "Enter a positive whole number for quantity.")
                return
            item = self.backend.get_product(iid)
            if not item:
                messagebox.showerror("Error", "Product not found.")
                return
            current_stock = getattr(item, 'prodStock', 0)
            if current_stock < qty:
                messagebox.showinfo("Out of Stock", f"Only {current_stock} left in stock.")
                return

            # Reused code from below for manually adding addons, could probably be done nicer with an external function
            presetAddons = self.backend.get_product(item.prodID, 'prodID', 'prodPresetAddons')
            if presetAddons == 'None' or presetAddons == '': # If there's no prodPresetAddons, we just add it
                self.commit_add_to_cart(item, qty)
            else:
                storedItem = item
                presetAddons = presetAddons.split(',')
                for i in range(qty):
                    for a in presetAddons:
                        try:
                            a = int(a)
                        except:
                            errorPopup(1, RestaurantApp, "gui/restaraunt_app.py > def add_to_order > adding preset addons", "Someone didn't put in an integer for that menu item's prodPresetAddons. Get it fixed!")
                            return
                        item = self.backend.get_addon(a)
                        if not item:
                            messagebox.showerror("Error", "Product not found.")
                            return
                        current_stock = getattr(item, 'addonStock', 0)
                        if current_stock < qty:
                            messagebox.showinfo("Out of Stock", f"Only {current_stock} left in stock.")
                            return
                    # If we didn't return, we're good to add it to the cart.
                    self.commit_add_to_cart(storedItem, 1)
                    for a in presetAddons:
                        a = int(a) # We would've errored out (returned) in the previous check to see if we had stock, so we can just do it here.
                        item = self.backend.get_addon(a)
                        self.commit_add_to_cart(item, 1, 'Addon')
            # Reset qty field after adding
            try:
                if self.quantity_entry is not None:
                    self.quantity_entry.delete(1, 'end')
            except Exception:
                pass
                    
        else:
            self.add_mod()
            return
        
    def commit_add_to_cart(self, item, qty = 1, itemType = 'Product'):
        self.order.add_item(item, qty, itemType)
        self.update_order_tree()
        self.update_order_summary()
        
    def add_mod(self):
        """Add the selected addon/mod dine-in order."""
        if not hasattr(self, 'addon_menu_tree') or self.addon_menu_tree is None:
            return
        selection = self.addon_menu_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an addon/mod first.")
            return
        item_vals = self.addon_menu_tree.item(selection[0], 'values')
        try:
            aid = int(item_vals[0])
        except Exception:
            messagebox.showerror("Error", "Could not read addon ID.")
            return
        addon = self.backend.get_addon(aid)
        if not addon:
            messagebox.showerror("Error", "Addon not found.")
            return
        current_stock = getattr(addon, 'addonStock', 0)
        if current_stock < 1:
            messagebox.showinfo("Out of Stock", f"No stock left for {getattr(addon, 'addonName', 'Addon')}")
            return
        self.commit_add_to_cart(addon, 1, 'Addon')

    def update_order_tree(self):
        if not self.order_tree:
            return
        # Preserve open parents
        prev_open_ids: set[int] = set()
        try:
            for iid in self.order_tree.get_children(''):
                if self.order_tree.item(iid, 'open'):
                    info = self.tree_index_map.get(iid)
                    if info and not info.get('is_addon', False):
                        idx = info.get('index')
                        if isinstance(idx, int) and 0 <= idx < len(self.order.items):
                            obj = self.order.items[idx][0]
                            prev_open_ids.add(id(obj))
        except Exception:
            pass

        # Rebuild
        for row in self.order_tree.get_children():
            self.order_tree.delete(row)
        self.tree_index_map = {}
        parent_id: Optional[str] = None
        parent_index: Optional[int] = None
        for idx, (item, q) in enumerate(self.order.items):
            is_addon = hasattr(item, 'addonPrice')
            price_val = getattr(item, 'prodPrice', getattr(item, 'addonPrice', 0.0))
            name_val = getattr(item, 'prodName', getattr(item, 'addonName', 'Item'))
            subtotal = price_val * q
            if not is_addon:
                parent_id = self.order_tree.insert('', 'end', text=name_val, values=(q, f"${price_val:.2f}", f"${subtotal:.2f}"))
                parent_index = idx
                # map parent
                self.tree_index_map[parent_id] = {'index': idx, 'is_addon': False}
                # Restore open state
                try:
                    if id(item) in prev_open_ids:
                        self.order_tree.item(parent_id, open=True)
                except Exception:
                    pass
            else:
                # Indent addons under the last product (if present)
                parent = parent_id if parent_id else ''
                child_id = self.order_tree.insert(parent, 'end', text=f"+ {name_val}", values=(q, f"${price_val:.2f}", f"${subtotal:.2f}"))
                self.tree_index_map[child_id] = {'index': idx, 'is_addon': True}

    def remove_last_item(self):
        self.order.remove_last_item()
        self.update_order_tree()
        self.update_order_summary()
        
    # Someone do this please, there's a commented out centerpanes_selected, as well as a .bind for centerpane, and a func in Order (may or may not be useful)
    def remove_sel_item(self):
        """Remove the selected item from dine-in order or carry-out orders."""
        if self.order_tree is not None and self.order_tree.selection():
            self._remove_from_dine_in()
        elif self.hold_list is not None and self.hold_list.selection():
            self._remove_from_carry_out()
        else:
            if not hasattr(self, 'selected_item') or not self.selected_item:
                messagebox.showwarning("No Selection", "Please select an item to remove first.")
                return
            if self.selected_tree == self.order_tree:
                self._remove_from_dine_in()
            elif self.selected_tree == self.hold_list:
                self._remove_from_carry_out()
            else:
                messagebox.showwarning("No Selection", "Please select an item to remove first.")
                return
            
        self.update_order_tree()
        self.update_order_summary()

    def _remove_from_dine_in(self):
        """Remove selected item from the dine-in order."""
        if not self.order.items:
            return
            
        selected_id = None
        try:
            if self.order_tree is not None:
                sel = self.order_tree.selection()
                if sel:
                    selected_id = sel[0]
                else:
                    focus = self.order_tree.focus()
                    if focus:
                        selected_id = focus
        except Exception:
            pass

        if not selected_id and self.selected_item:
            selected_id = self.selected_item[0]
        if not selected_id:
            return
        # Use index map to find link to order index
        info = self.tree_index_map.get(selected_id)
        if not info or 'index' not in info:
            messagebox.showerror("Error", "Could not map selected item to order.")
            return

        idx = info.get('index')
        is_addon = info.get('is_addon', False)
        if not isinstance(idx, int):
            return

        # If a parent (product) is selected, remove it and children (addons)
        if not is_addon:
            # Remove the product at idx
            if idx < len(self.order.items):
                removed_product = self.order.items.pop(idx)
                # Remove addons that belong to this product
                while idx < len(self.order.items):
                    next_item, _ = self.order.items[idx]
                    if hasattr(next_item, 'addonPrice'):
                        self.order.items.pop(idx)
                    else:
                        break
                messagebox.showinfo(
                    "Removed",
                    f"Removed {getattr(removed_product[0], 'prodName', 'Item')} and its addons."
                )
        else:
            # Remove only the selected addon
            removed_addon = self.order.items.pop(idx)
            messagebox.showinfo(
                "Removed",
                f"Removed {getattr(removed_addon[0], 'addonName', getattr(removed_addon[0], 'prodName', 'Item'))}."
            )
        

    def _remove_from_carry_out(self):
        """Remove selected item or order from carry-out orders."""
        selected_id = self.selected_item[0]
        
        # Check if it's a parent (order) or child (item)
        parent = self.hold_list.parent(selected_id)
        
        if not parent:  # It's a parent (entire carry-out order)
            # Get all children of this order
            all_orders = self.hold_list.get_children('')
            try:
                order_index = all_orders.index(selected_id)
                if order_index < len(self.held_orders):
                    self.held_orders.pop(order_index)
                    self.hold_list.delete(selected_id)
                    messagebox.showinfo("Removed", "Removed carry-out order.")
                    
                    # If no more orders, show placeholder
                    if not self.held_orders:
                        self.hold_list.insert('', 'end', text="No carry-out orders yet")
            except (ValueError, IndexError):
                messagebox.showerror("Error", "Could not remove selected order.")
        else:
            # Child item - remove specific item from carry-out
            try:
                # Link order to child
                all_orders = self.hold_list.get_children('')
                order_index = all_orders.index(parent)
                # Find child index
                children = self.hold_list.get_children(parent)
                child_index = children.index(selected_id)
                # Update data and UI
                if 0 <= order_index < len(self.held_orders):
                    order_items = self.held_orders[order_index]
                    if 0 <= child_index < len(order_items):
                        removed = order_items.pop(child_index)
                        self.hold_list.delete(selected_id)
                        messagebox.showinfo(
                            "Removed",
                            f"Removed {getattr(removed[0], 'prodName', getattr(removed[0], 'addonName', 'Item'))} from carry-out order."
                        )
                        # If order empty, remove parent too
                        if not order_items:
                            self.held_orders.pop(order_index)
                            self.hold_list.delete(parent)
                            if not self.held_orders:
                                self.hold_list.insert('', 'end', text="No carry-out orders yet")
            except Exception:
                messagebox.showerror("Error", "Could not remove selected item from carry-out order.")
                
    def update_order_summary(self):
        subtotal = self.order.total()
        tax = subtotal * self.TAX_RATE
        total = subtotal + tax
        self.subtotal_var.set(f"Subtotal: ${subtotal:.2f}")
        self.tax_var.set(f"Tax: ${tax:.2f}")
        self.total_var.set(f"Total: ${total:.2f}")

    # --------------- Checkout & Receipt ---------------
    def checkout_popup(self):
        if not self.order.items:
            messagebox.showinfo("Empty", "No items in order.")
            return
        if not getattr(self, 'order_sent_to_kitchen', False):
            messagebox.showinfo("Kitchen", "Send the order to the kitchen before checkout.")
            return
        subtotal = self.order.total()
        tax = subtotal * self.TAX_RATE
        total = subtotal + tax
        win = ctk.CTkToplevel(self.root)
        win.title("Checkout Confirmation")
        ctk.CTkLabel(win, text=f"Subtotal: ${subtotal:.2f}").pack(anchor='w', padx=5)
        ctk.CTkLabel(win, text=f"Tax: ${tax:.2f}").pack(anchor='w', padx=5)
        ctk.CTkLabel(win, text=f"Total: ${total:.2f}", font=("Arial", 12, 'bold')).pack(anchor='w', padx=5, pady=(0,5))
        ctk.CTkLabel(win, text="Confirm checkout? This will reduce stock.").pack(anchor='w', padx=5)

        def confirm():
            # Calculate subtotal and tax
            subtotal = self.order.total()
            tax = subtotal * self.TAX_RATE

            # Ask user for tip
            import tkinter.simpledialog as simpledialog
            tip_str = simpledialog.askstring("Tip", "Enter tip amount ($):", initialvalue="0")
            try:
                tip = float(tip_str)
                if tip < 0:
                    tip = 0.0
            except Exception:
                tip = 0.0

            total = subtotal + tax + tip

            try:
                self.order.save_to_file("DatabaseFiles/orders.txt", tax=tax, tip=tip)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save order: {e}")
            
            self.refresh_products()
            self.refresh_stock_display()
            messagebox.showinfo("Done", "Order checked out.")
            self.order = AppOrder()
            self.order_sent_to_kitchen = False
            self.update_order_tree()
            self.update_order_summary()
            win.destroy()

        btns = ctk.CTkFrame(win)
        btns.pack(pady=10)
        confirm_btn = ctk.CTkButton(btns, text="Confirm", command=confirm, takefocus=0, default='disabled')
        confirm_btn.pack(side='left', padx=5)
        cancel_btn = ctk.CTkButton(btns, text="Cancel", command=win.destroy)
        cancel_btn.pack(side='left', padx=5)
        # Move focus after window is rendered so Confirm doesn't show focus ring
        win.after(0, cancel_btn.focus_set)

    def print_receipt(self):
        if not self.order.items:
            messagebox.showinfo("Empty", "No items to print.")
            return
        subtotal = self.order.total()
        tax = subtotal * self.TAX_RATE
        total = subtotal + tax
        win = ctk.CTkToplevel(self.root)
        win.title("Receipt Preview")
        text = tk.Text(win, width=40, height=20)
        text.pack(fill='both', expand=True)
        text.insert('end', self.order.summary())
        text.insert('end', f"\nTax: ${tax:.2f}\n")
        text.insert('end', f"Total: ${total:.2f}\n")
        text.insert('end', "\nThank you! (Printing receipt...)\n")
        text.config(state='disabled')

    # --------------- Right Buttons ---------------
    def send_to_kitchen(self):
        if not self.order.items:
            messagebox.showinfo("Kitchen", "No order to send to kitchen.")
            return

        # Reduce stock for all items (both products and addons)
        for item, qty in self.order.items:
            is_addon = hasattr(item, 'addonPrice')
            
            if is_addon:
                # It's an addon
                aid = getattr(item, 'addonID', None)
                if aid is not None:
                    success = self.backend.reduce_addon_stock(aid, qty)
                    if not success:
                        messagebox.showerror("Stock Error", 
                            f"Not enough stock for addon: {getattr(item, 'addonName', 'Unknown')}")
                        return
            else:
                # It's a product
                pid = getattr(item, 'prodID', None)
                if pid is not None:
                    success = self.backend.reduce_stock(pid, qty)
                    if not success:
                        messagebox.showerror("Stock Error", 
                            f"Not enough stock for product: {getattr(item, 'prodName', 'Unknown')}")
                        return

        # Save all changes to files
        self.backend.save_products()
        self.backend.save_addons()
        
        # Refresh displays
        self.refresh_products()
        self.refresh_stock_display()
        
        self.order_sent_to_kitchen = True
        self.update_order_tree()
        self.update_order_summary()
        messagebox.showinfo("Kitchen", "Order sent to kitchen! Stock updated. Proceed to checkout.")

    def hold_order(self):
        if self.order.items:
            messagebox.showinfo("Carry-Out", "Finish or clear Dine-In before adding to Carry-Out.")
            return

        # Require a selected product
        if not self.menu_tree:
            return
        sel = self.menu_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a product to add to Carry-Out.")
            return
        vals = self.menu_tree.item(sel[0], 'values')
        try:
            pid = int(vals[0])
        except Exception:
            messagebox.showerror("Error", "Could not read product ID.")
            return
        prod = self.backend.get_product(pid)
        if not prod:
            messagebox.showerror("Error", "Product not found.")
            return
        try:
            qty = int(self.quantity_entry.get()) if self.quantity_entry else 1
            if qty <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Bad Quantity", "Enter a positive whole number for quantity.")
            return
        stock = getattr(prod, 'prodStock', 0)
        if stock < qty:
            messagebox.showinfo("Out of Stock", f"Only {stock} left in stock.")
            return
        
        try:
            if self.hold_list is not None:
                children = self.hold_list.get_children()
                if children:
                    if self.hold_list.item(children[0], 'text') == "No carry-out orders yet":
                        self.hold_list.delete(children[0])
        except Exception:
            pass
        # Create carry-out order
        price_val = getattr(prod, 'prodPrice', 0.0)
        subtotal = price_val * qty
        note = f"Carry-Out Order #{self.hold_seq}: 1 items, ${subtotal:.2f}"
        parent = None
        if self.hold_list is not None:
            parent = self.hold_list.insert('', 'end', text=note)
            name_val = getattr(prod, 'prodName', 'Item')
            self.hold_list.insert(parent, 'end', text=f"{name_val} x{qty} @ ${price_val:.2f}")
        self.held_orders.append([(prod, qty)])
        self.hold_seq += 1
        messagebox.showinfo("Carry-Out", "Added to carry-out queue.")

    def cancel_order(self):
        if not self.order.items:
            messagebox.showinfo("Nothing", "No order to cancel.")
            return
        if messagebox.askyesno("Cancel", "Clear current order?"):
            self.order = AppOrder()
            self.update_order_tree()
            self.update_order_summary()

    def reload_menu(self):
        self.backend.load()
        self.refresh_products()
        self.refresh_stock_display()
        messagebox.showinfo("Reloaded", "Menu reloaded.")

    def update_stock(self):
        """Update stock for the selected product from the Stock Levels table."""
        if not self.stock_tree:
            return
        sel = self.stock_tree.selection()
        if not sel:
            messagebox.showinfo("Update Stock", "Select a product in the Stock Levels list first.")
            return
        item_vals = self.stock_tree.item(sel[0], 'values')
        try:
            pid = int(item_vals[0])
        except Exception:
            messagebox.showerror("Error", "Could not read product ID.")
            return
        product = self.backend.get_product(pid)
        if not product:
            messagebox.showerror("Error", "Product not found in inventory.")
            return

        # Tiny prompt window
        win = ctk.CTkToplevel(self.root)
        win.title("Update Stock")
        ctk.CTkLabel(win, text=f"Set new stock for: {getattr(product, 'prodName', 'Item')} (ID {pid})").pack(anchor='w', padx=8, pady=(8, 4))
        row = ctk.CTkFrame(win)
        row.pack(fill='x', padx=8)
        ctk.CTkLabel(row, text="New stock:").pack(side='left')
        qty_var = tk.StringVar(value=str(getattr(product, 'prodStock', 0)))
        qty_entry = ctk.CTkEntry(row, width=10, textvariable=qty_var)
        qty_entry.pack(side='left', padx=6)

        def apply_update():
            try:
                new_stock = int(qty_var.get())
                if new_stock < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid", "Enter a non-negative whole number for stock.")
                return
            # Update in memory
            setattr(product, 'prodStock', new_stock)
            # Persist to file via backend adapter
            self.backend.save_products()
            # Refresh UI
            self.refresh_products()
            self.refresh_stock_display()
            messagebox.showinfo("Updated", f"Stock set to {new_stock} for {getattr(product, 'prodName', 'Item')}.")
            win.destroy()

        btns = ctk.CTkFrame(win)
        btns.pack(pady=8)
        ctk.CTkButton(btns, text="Apply", command=apply_update).pack(side='left', padx=6)
        ctk.CTkButton(btns, text="Cancel", command=win.destroy).pack(side='left', padx=6)
        qty_entry.focus_set()
