'''
Group 2 Final Project: Restaraunt System
Riley, Nhan, Joey, Ashton, Harold, Jake

This program is an all-in-one point-of-sale system which has/can:
A GUI, load products from a text file, make customer orders,
save past orders to (a) file(s), update stock in the database file 
when orders are completed, etc.

Project started: 09/14/2025
First release: ...
'''

# Imports
from tkinter import messagebox
import tkinter as tk
import re
# from PIL import ImageTK, Image, ImageOps
# The above is commented out because it's not needed yet. We will probably need it in the future though.
# Python image library (PIL) used to require a slightly older version of Python -- it may still -- so if and when we need it,
# Just set your interpreter to the version compatible (VSCode should be able to install the right version)

# General Global Vars
defaultProductFile = "DatabaseFiles/default.txt" # Do not change this! If we want to change files, use the InventoryHandler's functions!
defaultAddonFile = "DatabaseFiles/default_addons.txt" # Do not change this! See above.
errorSeverity=["Debug Only Error", "Critical Error", "Error", "Invalid Input"] # We use this to pass errors severity to the errorPopup function.

# Classes
class Product:
    # Addon class refers to things slightly differently! Be careful!
    def __init__(self, id, name, desc, price, stock, sales, basedOn, presetAddons, validAddons, imgPath, imgSmallPath):
        self.prodID = int(id)
        self.prodName = str(name)
        self.prodDesc = str(desc)
        self.prodPrice = float(price)
        self.prodStock = int(stock)
        self.prodSales = int(sales)
        self.prodPresetAddons = str(presetAddons) # FRONT END TEAM: It's up to you when building the frontend systems if you want to nest products, allow preset addons to be removed, or build presets by button presses and just use a base item instead.
        self.prodValidAddons = str(validAddons)
        self.prodImg = str(imgPath)
        self.prodSmall = str(imgSmallPath)
        try:
            self.prodBasedOn = int(basedOn) # Int type is optimal!
        except:
            self.prodBasedOn = basedOn # Just set it to an empty string instead if it cant set it to an int.

class Addon:
    # We refer to things in here the same as Product, but instead of prod-, it's addon-!
    def __init__(self, id, name, desc, price, stock, sales, imgPath, imgSmallPath):
        self.addonID = int(id)
        self.addonName = str(name)
        self.addonDesc = str(desc)
        self.addonPrice = float(price)
        self.addonStock = int(stock)
        self.addonSales = int(sales)
        self.addonImg = str(imgPath)
        self.addonImgSmall = str(imgSmallPath)

class InventoryHandler:
    def __init__(self):
        self.productFilePath = defaultProductFile # Initialize to the default products file; this is just done for reference.
        self.addonFilePath = defaultAddonFile # Initiatilize to the default addons file; this is just done for reference.
        self.productList = []
        self.addonList = []

    def loadProductFile(self, newFilePath, mode):
        productCount = int(0)
        tempDict = {}
        try:
            with open(newFilePath, "r") as newFile: # Attempt to open the file.
                print("Ok! Building products/addons into memory and clearing old products/addons list.")
                if mode == "Product":
                    self.productFilePath = newFilePath # Set the InventoryHandler's productFilePath to the new, valid database file.
                    self.productList.clear()
                elif mode == "Addon":
                    self.addonFilePath = newFilePath # Same as above but for the addonFilePath instead.
                    self.addonList.clear()

                for index, line in enumerate(newFile, start=1):
                    if line.startswith("//") or line.startswith("\n"): # Ignore the comment lines/empty lines and just move on (pass)
                        continue
                    elif line.startswith("prodID=000"): # If it's the first entry, we increment this counter only
                        productCount += 1
                    elif line.startswith("prodID=") and tempDict != {}: # We're detecting if another product comes up. If we do, build the existing product/addon.
                        productCount += 1
                        self.makeNewProduct(tempDict, mode)
                        print(tempDict)
                        tempDict.clear()
                    elif line.startswith("end_of_file"): # There's probably a better way to do this but it works for now
                        self.makeNewProduct(tempDict, mode)
                        print(tempDict)
                        tempDict.clear()
                        break                    
                    tempLine = line.split("=") # Split at the delimiter of '='
                    tempLine[1] = tempLine[1].rstrip() # Remove the trailing \n because it detects a new line in the file
                    tempDict[tempLine[0]] = tempLine[1] # Make a new key and set it to the previously made tempLine's 0 and 1 indices.
                        
                if productCount == 0: # If our database file has no products (no lines start with 'prodID='), throw an error
                    errorPopup(2, InvHandler, "InvHandler.loadProductFile()", "Database file was found, but there are no products in it (no lines start with 'prodID=000')")
                print(productCount, mode + "s detected.") # Debug purposes

        except FileNotFoundError: # If we don't find the file specified and/or invalid
            errorPopup(1, InvHandler, "InvHandler.loadProductFile()", "Database file not found in the provided path or is invalid. If you didn't specify a path, that means the 'default.txt' database file in the 'DatabaseFiles' folder is missing.")

    def makeNewProduct(self, passedDict, mode):
        # We make a new Product class object
        if mode == "Product":
            newProduct = Product(passedDict['prodID'], passedDict['prodName'], passedDict['prodDesc'], passedDict['prodPrice'], passedDict['prodStock'], passedDict['prodSales'], passedDict['prodBasedOn'], passedDict['prodPresetAddons'], passedDict['prodValidAddons'], passedDict['prodImg'], passedDict['prodImgSmall'])
            self.productList.append(newProduct)
        elif mode == "Addon":
            newAddon = Addon(passedDict['prodID'], passedDict['prodName'], passedDict['prodDesc'], passedDict['prodPrice'], passedDict['prodStock'], passedDict['prodSales'], passedDict['prodImg'], passedDict['prodImgSmall'])
            self.addonList.append(newAddon)

    def learningHelper(self, mode): # This is here to help anyone who needs it with how to find data in the InventoryHandler's self.productList and self.addonList lists. This isn't a tutorial! The best method to use is up to the application and what you are trying to get out of each item in the list.
        if mode == "Product":
            for index, product in enumerate(self.productList):
                if product.prodID == "000": # You can replace prodID with prodName and change 000 to Burger and it works the same.
                    print("Found a", product.prodName, "at", index) # We reference the product's name here.
                    print(product.prodImg)
                    print("A Burger can have the following addons:")
                    tempList = product.prodValidAddons.split(",") # NOTE: 
                    for item in range(len(tempList)):
                        for entry in self.addonList:
                            if entry.addonID == tempList[item]:
                                print(entry.addonName)
                elif product.prodName == "Cheeseburger": # What was mentioned in the previous 'if' statement's comment is here.
                    print("Found a", product.prodName, "at", index)
        elif mode == "Addon":
            for index, addon in enumerate(self.addonList):
                if addon.addonID == "000": 
                    print("Found a", addon.addonName, "at", index)
                elif addon.addonName == "Mustard":
                    print("Found a", addon.addonName, "at", index)

# Non-Class Functions (defs)
def errorPopup(severity=0, perpetrator="Unspecified Perpetrator", perpetrator_where="?", message="?"):
    # You don't technically require anything to use this function, but please do proper error handling.
    # See class InventoryHandler > def loadProductFile > try & except for an example of how to use this.
    newMessage = str(str(perpetrator) + "\nProblem at function: " + perpetrator_where + "\nMessage: " + message)
    messagebox.showerror(errorSeverity[severity], newMessage) 

if __name__ == "__main__":
    InvHandler = InventoryHandler()
    InvHandler.loadProductFile(defaultProductFile, "Product")
    InvHandler.loadProductFile(defaultAddonFile, "Addon")
    InvHandler.learningHelper("Product")
    InvHandler.learningHelper("Addon")