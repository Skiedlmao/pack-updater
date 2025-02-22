#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os, shutil, json, zipfile, tempfile

TARGET_PACK_FORMAT = 46

def update_pack_mcmeta(mcmeta_path):
    with open(mcmeta_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if "pack" in data and isinstance(data["pack"], dict):
        data["pack"]["pack_format"] = TARGET_PACK_FORMAT
    else:
        raise ValueError(mcmeta_path + " does not contain a valid 'pack' object.")
    with open(mcmeta_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def rename_texture_dirs(root_path):
    for dirpath, _, _ in os.walk(root_path):
        if os.path.basename(dirpath) == "textures":
            for old, new in (("blocks", "block"), ("items", "item")):
                old_dir = os.path.join(dirpath, old)
                new_dir = os.path.join(dirpath, new)
                if os.path.isdir(old_dir) and not os.path.exists(new_dir):
                    os.rename(old_dir, new_dir)

def process_pack(root_path):
    mcmeta_path = os.path.join(root_path, "pack.mcmeta")
    if not os.path.isfile(mcmeta_path):
        raise FileNotFoundError("pack.mcmeta not found in " + root_path)
    update_pack_mcmeta(mcmeta_path)
    rename_texture_dirs(root_path)

def process_zip(input_zip, output_zip=None):
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(input_zip, 'r') as zf:
            zf.extractall(tmpdir)
        process_pack(tmpdir)
        if output_zip is None:
            base, _ = os.path.splitext(input_zip)
            output_zip = base + "_upgraded.zip"
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zf_out:
            for folder, _, files in os.walk(tmpdir):
                for file in files:
                    filepath = os.path.join(folder, file)
                    relpath = os.path.relpath(filepath, tmpdir)
                    zf_out.write(filepath, relpath)
    return output_zip

def process_directory(input_dir, output_dir=None):
    if output_dir is None:
        output_dir = input_dir + "_upgraded"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    shutil.copytree(input_dir, output_dir)
    process_pack(output_dir)
    return output_dir

class UpgradeGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Resource Pack Upgrader")
        self.geometry("600x500")
        self.path_var = tk.StringVar()
        self.create_widgets()
    def create_widgets(self):
        frame = tk.Frame(self)
        frame.pack(pady=10)
        tk.Label(frame, text="Resource Pack Path:").pack(side=tk.LEFT, padx=5)
        self.path_entry = tk.Entry(frame, width=50, textvariable=self.path_var)
        self.path_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Browse File", command=self.browse_file).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Browse Folder", command=self.browse_folder).pack(side=tk.LEFT, padx=5)
        tk.Button(self, text="Process", command=self.process_input).pack(pady=10)
        self.log_text = scrolledtext.ScrolledText(self, width=70, height=20)
        self.log_text.pack(padx=10, pady=10)
    def log(self, msg):
        self.log_text.insert(tk.END, msg+"\n")
        self.log_text.see(tk.END)
    def browse_file(self):
        path = filedialog.askopenfilename(title="Select Resource Pack ZIP", filetypes=[("ZIP Files", "*.zip"), ("All Files", "*.*")])
        if path:
            self.path_var.set(path)
    def browse_folder(self):
        path = filedialog.askdirectory(title="Select Resource Pack Folder")
        if path:
            self.path_var.set(path)
    def process_input(self):
        path = self.path_var.get()
        if not path:
            messagebox.showerror("Error", "No path provided")
            return
        try:
            if os.path.isfile(path):
                if zipfile.is_zipfile(path):
                    output = process_zip(path)
                    self.log("Upgraded ZIP created: " + output)
                    messagebox.showinfo("Success", "Upgraded ZIP created:\n" + output)
                else:
                    raise ValueError("Selected file is not a valid ZIP")
            elif os.path.isdir(path):
                output = process_directory(path)
                self.log("Upgraded folder created: " + output)
                messagebox.showinfo("Success", "Upgraded folder created:\n" + output)
            else:
                raise ValueError("Invalid path")
        except Exception as e:
            self.log("Error: " + str(e))
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = UpgradeGUI()
    app.mainloop()
