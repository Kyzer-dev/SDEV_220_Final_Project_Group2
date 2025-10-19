"""
Group 2 Final Project: Restaraunt System
Riley, Nhan, Joey, Ashton, Harold, Jake

This program is an all-in-one point-of-sale system which has/can:
A GUI, load products from a text file, make customer orders,
save past orders to (a) file(s), update stock in the database file 
when orders are completed, etc.

Project started: 09/14/2025


Simple app launcher.

python main.py          # start the GUI
python main.py --cli    # quick console test mode
python main.py --tk     # use Tkinter version
python main.py --ctk    # use CustomTkinter version

"""
from restaraunt_system import InventoryHandler, defaultProductFile, defaultAddonFile # type: ignore
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


def gui_choice():
    """Ask user to choose to use Tkinter or CustomTkinter."""
    print("Restaurant Ordering System - GUI Version Selection")
    print("-"*50)
    print("\nWhich version would you like to use?")
    print("\n1. CustomTkinter (Modern)")
    print("2. Tkinter (Classic)\n")
    
    while True:
        choice = input("Enter 1 or 2 (or 'q' to quit): ").strip().lower()
        if choice == 'q':
            print("Exiting...")
            sys.exit(0)
        elif choice == '1':
            return 'ctk'
        elif choice == '2':
            return 'tk'
        else:
            print("Invalid choice. Please enter 1, 2, or 'q'.")

def run_tkinter_gui():
    """Launch the Tkinter GUI. If Tkinter is not available, print an error and exit."""
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
    return True
    
def run_customtkinter_gui():
    """Launch the CustomTkinter GUI. If CustomTkinter is not available, attempt to run the Tkinter GUI."""
    try:
        import tkinter as tk  # type: ignore
    except Exception as e:  # pragma: no cover - environment specific
        print("ERROR: Tkinter is not available. GUI cannot be started.")
        print(e)
        return
    
    try:
        import customtkinter as ctk  # type: ignore
    except Exception as e:  # pragma: no cover - environment specific
        print("\nCustomTkinter is not available.")
        print("Install it with: pip install customtkinter")
        return
    
    try:
        # import the main GUI class
        from gui.customtkinter_restaurant_app import RestaurantApp  # type: ignore
    except ModuleNotFoundError as e:
        print("ERROR: Could not import RestaurantApp. Make sure you run from the project root.")
        print("If you ran using an absolute path with spaces, quote the path or cd into the folder first.")
        return
    except Exception as e:  # unexpected import error
        print("Unexpected error importing GUI module:")
        traceback.print_exc()
        return

    root = ctk.CTk()
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
    return True

def run_gui():
    """Launch the GUI with the selected version."""
    # Check command-line arguments for which version to use
    if '--tk' in sys.argv:
        choice = 'tk'
        print("Force using Tkinter version (--tk flag)")
    elif '--ctk' in sys.argv:
        choice = 'ctk'
        print("Force using CustomTkinter version (--ctk flag)")
    else:
        choice = gui_choice()
    
    # Launch the chosen version
    if choice == 'ctk':
        result = run_customtkinter_gui()
        if result is None:
            print("\nAttempting to launch Tkinter version instead...\n\n")
            run_tkinter_gui()
        elif not result:
            print("\nFailed to launch CustomTkinter version.\n\n")
    elif choice == 'tk':
        result = run_tkinter_gui()
        if not result:
            print("\nFailed to launch Tkinter version.\n\n")


if __name__ == "__main__":
    if '--cli' in sys.argv:
        run_cli()
    else:
        run_gui()
