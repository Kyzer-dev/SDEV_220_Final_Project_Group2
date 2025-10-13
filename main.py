"""Simple app launcher.

    python main.py        # start the GUI
    python main.py --cli  # quick console test mode
"""
from models import Inventory, Order, Product, Addon
import sys
import traceback


def run_cli():
    inv = Inventory(); inv.load()
    print(f"Loaded {len(inv.products)} products and {len(inv.addons)} addons.")
    if inv.products:
        first = inv.products[0]
        print("First product:", first.prodName, "Price:", first.prodPrice)
    order = Order()
    if inv.products:
        order.add_item(inv.products[0], 2)
    if inv.addons:
        order.add_item(inv.addons[0], 1)
    print(order.summary())


def run_gui():
    """Launch the GUI. If Tkinter is not available, print an error and exit."""
    try:
        import tkinter as tk  # type: ignore
    except Exception as e:  # pragma: no cover - environment specific
        print("ERROR: Tkinter is not available. GUI cannot be started.")
        print(e)
        return
    try:
        # Use package-qualified import so it works regardless of cwd.
        from gui.restaurant_app import RestaurantApp  # type: ignore
    except ModuleNotFoundError as e:
        print("ERROR: Could not import RestaurantApp. Make sure you run from the project root.")
        print("If you ran using an absolute path with spaces, quote the path or cd into the folder first.")
        print(e)
        return
    except Exception as e:  # unexpected import error
        print("Unexpected error importing GUI module:")
        traceback.print_exc()
        return

    inv = Inventory(); inv.load()
    root = tk.Tk()
    root.title("Restaurant Ordering System")
    try:
        _app = RestaurantApp(root, inv)
    except Exception:
        print("Unexpected error constructing RestaurantApp. Traceback below:")
        traceback.print_exc()
        root.destroy()
        return
    root.minsize(1050, 600)
    root.mainloop()


if __name__ == "__main__":
    if '--cli' in sys.argv:
        run_cli()
    else:
        run_gui()
