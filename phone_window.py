import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from utils import validate_phone_number

class PhoneNumberWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Emergency Contacts")
        self.window.geometry("400x500")
        self.window.configure(bg="#f0f2f5")
        
        self.phone_numbers = []
        self._create_widgets()
        self.load_phone_numbers()
    
    def _create_widgets(self):
        # Main container
        self.main_frame = tk.Frame(self.window, bg="#f0f2f5")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        self.title_label = ttk.Label(self.main_frame, text="Emergency Contacts", style="Header.TLabel")
        self.title_label.pack(pady=(0, 20))
        
        # Phone number entry
        self._create_entry_section()
        
        # Phone numbers list
        self._create_list_section()
        
        # Delete button
        self.delete_btn = ttk.Button(self.main_frame, text="Delete Selected",
                                   command=self.delete_phone_number, style="Stop.TButton")
        self.delete_btn.pack(pady=10)
    
    def _create_entry_section(self):
        self.entry_frame = tk.Frame(self.main_frame, bg="#f0f2f5")
        self.entry_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.phone_entry = ttk.Entry(self.entry_frame, font=('Helvetica', 12), width=20)
        self.phone_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        self.add_btn = ttk.Button(self.entry_frame, text="Add Contact",
                                command=self.add_phone_number, style="Contacts.TButton")
        self.add_btn.pack(side=tk.LEFT)
    
    def _create_list_section(self):
        self.list_frame = tk.Frame(self.main_frame, bg="#ffffff")
        self.list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.phone_list = tk.Listbox(self.list_frame, font=('Helvetica', 12),
                                   bg="#ffffff", relief=tk.FLAT,
                                   highlightthickness=1, highlightbackground="#e0e0e0")
        self.phone_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def add_phone_number(self):
        number = self.phone_entry.get().strip()
        if not number:
            messagebox.showerror("Error", "Please enter a phone number")
            return
            
        if not validate_phone_number(number):
            messagebox.showerror("Error", "Please enter a valid Indian phone number (10 digits starting with 6-9)")
            return
            
        name = simpledialog.askstring("Contact Name", "Enter the name for this contact:", parent=self.window)
        if not name or not name.strip():
            messagebox.showerror("Error", "Please enter a name for the contact")
            return
            
        name = name.strip()
        if any(num == number for _, num in self.phone_numbers):
            messagebox.showerror("Error", "This number is already in the list")
            return
            
        self.phone_numbers.append((name, number))
        self.phone_list.insert(tk.END, f"{name} - {number}")
        self.phone_entry.delete(0, tk.END)
        self.save_phone_numbers()
    
    def delete_phone_number(self):
        try:
            selection = self.phone_list.curselection()
            if selection:
                index = selection[0]
                self.phone_numbers.pop(index)
                self.phone_list.delete(index)
                self.save_phone_numbers()
        except Exception as e:
            messagebox.showerror("Error", "Please select a number to delete")
    
    def save_phone_numbers(self):
        with open("emergency_contacts.txt", "w") as f:
            for name, number in self.phone_numbers:
                f.write(f"{name}|{number}\n")
    
    def load_phone_numbers(self):
        try:
            with open("emergency_contacts.txt", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and '|' in line:
                        name, number = line.split('|', 1)
                        if validate_phone_number(number):
                            self.phone_numbers.append((name, number))
                            self.phone_list.insert(tk.END, f"{name} - {number}")
        except FileNotFoundError:
            pass 