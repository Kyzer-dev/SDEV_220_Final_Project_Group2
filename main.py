"""Simple app launcher.

    python main.py        # start the GUI
    python main.py --cli  # quick console test mode
"""
from restaraunt_system import InventoryHandler, defaultProductFile, defaultAddonFile  # type: ignore
import sys
import traceback


def run_cli():
    """Use to verify data loads from text database files."""
    handler = InventoryHandler()
    handler.loadDataFile(defaultProductFile, "Product")
    handler.loadDataFile(defaultAddonFile, "Addon")
    print(f"Loaded {len(handler.productList)} products and {len(handler.addonList)} addons.")
    if handler.productList:
        first = handler.productList[0]
        print("First product:", getattr(first, 'prodName', '?'), "Price:", getattr(first, 'prodPrice', 0.0))


def run_gui():
    """Launch the GUI. If Tkinter is not available, print an error and exit."""
    try:
        import tkinter as tk  # type: ignore
    except Exception as e:  # pragma: no cover - environment specific
        print("ERROR: Tkinter is not available. GUI cannot be started.")
        print(e)
        return
    try:
        # import the main GUI class
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

    root = tk.Tk()
    root.title("Restaurant Ordering System")
    try:
        _app = RestaurantApp(root)
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
