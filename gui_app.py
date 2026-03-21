import tkinter as tk
from tkinter import ttk, messagebox
import json

class MainStageBatchEditor:
    def __init__(self, root, mappings_file):
        self.root = root
        self.root.title("MainStage Concert Batch Editor")
        self.root.geometry("900x500")
        
        self.mappings_file = mappings_file
        self.mappings = []
        
        self.load_data()
        self.build_ui()
        self.populate_grid()

    def load_data(self):
        try:
            with open(self.mappings_file, 'r') as f:
                data = json.load(f)
                self.mappings = data.get("concertMappings", [])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load clean schema: {e}")

    def build_ui(self):
        # Top Frame for Actions
        top_frame = tk.Frame(self.root, padx=10, pady=10)
        top_frame.pack(fill=tk.X)
        
        tk.Label(top_frame, text="Filter by Port:").pack(side=tk.LEFT)
        self.filter_entry = tk.Entry(top_frame)
        self.filter_entry.pack(side=tk.LEFT, padx=5)
        self.filter_entry.bind("<KeyRelease>", self.filter_grid)
        
        tk.Button(top_frame, text="Batch Change Channel", command=self.batch_channel).pack(side=tk.RIGHT, padx=5)
        tk.Button(top_frame, text="Batch Change Port", command=self.batch_port).pack(side=tk.RIGHT, padx=5)
        
        # Grid/Treeview
        columns = ("Patch", "Control Name", "Port", "Channel", "CC ID", "Type")
        self.tree = ttk.Treeview(self.root, columns=columns, show='headings', selectmode='extended')
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
            
        self.tree.column("Patch", width=250)
        self.tree.column("Control Name", width=180)
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def populate_grid(self, filter_text=""):
        # Clear existing
        for raw in self.tree.get_children():
            self.tree.delete(raw)
            
        for i, item in enumerate(self.mappings):
            if filter_text.lower() in item.get("portName", "").lower() or filter_text.lower() in item.get("controlName", "").lower():
                self.tree.insert("", tk.END, iid=i, values=(
                    item["sourcePatch"],
                    item["controlName"],
                    item["portName"],
                    item["channel"],
                    item["controllerID"],
                    item["controlType"]
                ))
                
    def filter_grid(self, event):
        self.populate_grid(self.filter_entry.get())

    def batch_channel(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select items to edit.")
            return
            
        # In a real app we would open a popup to ask for the channel.
        # This is a prototype skeleton.
        messagebox.showinfo("Batch Edit", f"Imagine a popup here asking for a new Channel for {len(selected)} items. \n\nAfter editing the UI model, we'd trigger the deep 'repacker' utility to write back to the .concert binary!")

    def batch_port(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select items to edit.")
            return
        messagebox.showinfo("Batch Edit", f"Replacing port for {len(selected)} items!")

if __name__ == "__main__":
    root = tk.Tk()
    app = MainStageBatchEditor(root, "./extracted_data/midi_assistant_schema.json")
    root.mainloop()
