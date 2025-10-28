import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, Scrollbar
import subprocess
import sys
import re
import os

def check_and_install_dependencies():
    required_packages = ["pygments"]
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

check_and_install_dependencies()

from pygments import lex
from pygments.lexers import get_lexer_by_name, guess_lexer_for_filename
from pygments.token import Token

file_path = None
text_changed = False
current_lexer = None
current_language = "None"

themes = {
    "light": {
        "bg": "#FFFFFF",  # Background
        "fg": "#000000",  # Text
        "colon_fg": "#0000FF",  # Text before ':'
        "variable_fg": "#FF0000",  # Variables between %%
        "quote_fg": "#1E1E1E",  # Text in commas
        "comment_fg": "#208d02"  # Commentary text
    },
    "dark": {
        "bg": "#1E1E1E",
        "fg": "#FFFFFF",
        "colon_fg": "#87CEEB",  # Text before ':'
        "variable_fg": "#FF6347",  # Variables between %%
        "quote_fg": "#1E1E1E",  # Text in commas
        "comment_fg": "#208d02"  # Commentary text
    }
}
current_theme = "light"

available_fonts = [
    "Arial",
    "Arial Black",
    "Arial Narrow",
    "Book Antiqua",
    "Bookman Old Style",
    "Calibri",
    "Cambria",
    "Century Gothic",
    "Comic Sans MS",
    "Consolas",
    "Constantia",
    "Courier",
    "Courier New",
    "Garamond",
    "Georgia",
    "Helvetica",
    "Impact",
    "Lucida Console",
    "Lucida Sans Unicode",
    "Microsoft Sans Serif",
    "Monaco",
    "Palatino",
    "Roboto",
    "Segoe UI",
    "Tahoma",
    "Times New Roman",
    "Trebuchet MS",
    "Verdana"
]

def set_window_size(width, height):
    root.geometry(f"{width}x{height}")

def setup_window():
    set_window_size(1000, 600)

def open_file(initial_file_path=None):
    global file_path, text_changed

    if text_changed:
        if confirm_discard_changes():
            return

    if initial_file_path:
        file_path = initial_file_path
    else:
        file_path = filedialog.askopenfilename(defaultextension=".txt",
                                               filetypes=[("All Files", "*.*")])

    if file_path:
        try:
            with open(file_path, "r") as file:
                content = file.read()
                text.delete(1.0, tk.END)
                text.insert(tk.END, content)
                text.edit_modified(False)
                text_changed = False

            set_language_by_filename(file_path)
            update_line_numbers()

        except Exception as e:
            tk.messagebox.showerror("Error", f"File could not be opened: {str(e)}")

def save_file(event=None):
    global file_path, text_changed
    if not file_path:
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("All Files", "*.*")])
    if file_path:
        with open(file_path, "w") as file:
            file.write(text.get(1.0, tk.END))
        text_changed = False
        text.edit_modified(False)

def change_font(font_name):
    text.config(font=(font_name, 12))

def new_file(event=None):
    global file_path, text_changed
    if text_changed:
        response = confirm_discard_changes()
        if response is None:
            return
        elif response:
            save_file()
    file_path = None
    text.delete(1.0, tk.END)
    text_changed = False
    set_language("None")
    update_line_numbers()

def new_file_dialog():
    def create_new_file():
        filename = filename_entry.get()
        language = language_var.get()

        if not filename.strip():
            messagebox.showerror("Error", "Please enter a valid filename.")
            return

        if language == "Python":
            extension = ".py"
        elif language == "YAML":
            extension = ".yml"
        elif language == "Batch":
            extension = ".bat"
        else:
            extension = ".txt"

        filename_with_extension = filename + extension

        messagebox.showinfo("Success", f"New file '{filename_with_extension}' created with language '{language}'.")
        saved_file_path = save_new_file(filename_with_extension)
        if saved_file_path:
            open_created_file(saved_file_path, filename)
            dialog.destroy()
            update_line_numbers()

    def save_new_file(filename):
        content = f"# File: {filename}\n# Language: {current_language}\n\n# Add your code here"
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Python", "*.py"),
                                                            ("YAML", "*.yml"),
                                                            ("Batch", "*.bat"),
                                                            ("Text files", "*.txt"),
                                                            ("All files", "*.*")],
                                                 initialfile=filename)
        if file_path:
            try:
                with open(file_path, "w") as file:
                    file.write(content)
                messagebox.showinfo("File Saved", f"File '{filename}' saved successfully.")
                return file_path
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")

    def open_created_file(file_path, filename):
        open_file(file_path)

    dialog = tk.Toplevel()
    dialog.title("New File Configuration")

    filename_label = tk.Label(dialog, text="Filename:")
    filename_label.grid(row=0, column=0, padx=10, pady=5)
    filename_entry = tk.Entry(dialog, width=30)
    filename_entry.grid(row=0, column=1, padx=10, pady=5)

    language_label = tk.Label(dialog, text="Language:")
    language_label.grid(row=1, column=0, padx=10, pady=5)
    languages = ["Batch", "Python", "YAML", "None"]
    language_var = tk.StringVar(dialog)
    language_var.set(languages[0])
    language_menu = tk.OptionMenu(dialog, language_var, *languages)
    language_menu.grid(row=1, column=1, padx=10, pady=5)

    create_button = tk.Button(dialog, text="Create File", command=create_new_file)
    create_button.grid(row=2, columnspan=2, padx=10, pady=10)
    root.destroy

def on_text_change(event=None):
    global text_changed
    text_changed = True
    highlight_syntax()

def confirm_discard_changes():
    return messagebox.askyesnocancel("Confirm", "Do you want to save your changes before continuing?")

def on_scroll(*args):
    text.yview(*args)
    y_scrollbar.set(*args)
    update_line_numbers_view()

def update_line_numbers():
    lines = text.get("1.0", "end").splitlines()
    line_numbers.config(state="normal")
    line_numbers.delete(1.0, tk.END)
    for i, line in enumerate(lines, start=1):
        line_numbers.insert(tk.END, f"{i}\n")
    line_numbers.config(state="disabled")

def update_line_numbers_view():
    yview = text.yview()[0]
    line_numbers.yview_moveto(yview)

def sync_line_numbers(*args):
    line_numbers.yview_moveto(args[0])
    text.yview_moveto(args[0])

def on_closing():
    if text_changed:
        response = confirm_discard_changes()
        if response is None:
            return
        elif response:
            save_file()
            root.destroy()
        else:
            root.destroy()
    else:
        root.destroy()

def insert_text(text_to_insert):
    current_pos = text.index(tk.INSERT)
    text.insert(current_pos, text_to_insert)

def set_language(language):
    global current_language
    current_language = language
    if language == "None":
        lexer = get_lexer_by_name("text")
    else:
        lexer = get_lexer_by_name(language.lower())
    update_language_menu(language)
    highlight_syntax()

def update_language_menu(selected_language=None):
    if selected_language is None:
        selected_language = current_language
    for index, (lang_name) in enumerate(languages):
        language_menu.entryconfig(index, label=lang_name)
    language_menu.entryconfig(language_to_menu_index[selected_language], label=f"{selected_language.capitalize()} ✔️")

def set_language_by_filename(filename):
    ext = filename.split('.')[-1]
    if ext == 'py':
        set_language('Python')
    elif ext == 'yaml' or ext == 'yml':
        set_language('YAML')
    elif ext == 'bat':
        set_language('Batch')
    else:
        set_language('None')

def change_theme(theme_name):
    global current_theme
    current_theme = theme_name
    apply_theme()

def apply_theme():
    theme = themes[current_theme]
    text.config(bg=theme["bg"], fg=theme["fg"])
    highlight_syntax()

def highlight_syntax():
    theme = themes[current_theme]
    text.tag_remove("colon_word", "1.0", tk.END)
    text.tag_remove("variable", "1.0", tk.END)
    text.tag_remove("quote", "1.0", tk.END)
    text.tag_remove("comment", "1.0", tk.END)
    
    if current_language == "YAML":
        colon_fg = theme["colon_fg"]
        variable_fg = theme["variable_fg"]
        quote_fg = theme["quote_fg"]
        comment_fg = theme["comment_fg"]

        content = text.get("1.0", tk.END)
        lines = content.split("\n")
        
        for line_num, line in enumerate(lines, start=1):
            if "#" in line:
                start = line.index("#")
                end = len(line)
                text.tag_add("comment", f"{line_num}.{start}", f"{line_num}.{end}")
                text.tag_config("comment", foreground=comment_fg)
                line = line[:start]

            for match in re.finditer(r"%[^%]*%", line):
                start, end = match.span()
                text.tag_add("variable", f"{line_num}.{start}", f"{line_num}.{end}")
                text.tag_config("variable", foreground=variable_fg)
            
            if ":" in line:
                parts = line.split(":", 1)
                prefix = parts[0]
                text.tag_add("colon_word", f"{line_num}.0", f"{line_num}.{len(prefix)}")
                text.tag_config("colon_word", foreground=colon_fg)
            
            for match in re.finditer(r'"[^"]*"', line):
                start, end = match.span()
                text.tag_add("quote", f"{line_num}.{start}", f"{line_num}.{end}")
                text.tag_config("quote", foreground=quote_fg)

def y_scroll(*args):
    text.yview(*args)

def x_scroll(*args):
    text.xview(*args)

def cut(event=None):
    if text.tag_ranges(tk.SEL):
        text.event_generate("<<Cut>>")

def copy(event=None):
    if text.tag_ranges(tk.SEL):
        text.event_generate("<<Copy>>")

def paste(event=None):
    text.event_generate("<<Paste>>")

def select_all(event=None):
    text.tag_add("sel", "1.0", "end")
    return "break"

def delete(event=None):
    if text.tag_ranges(tk.SEL):
        text.event_generate("<<Clear>>")

def delete_word(event=None):
    current_pos = text.index(tk.INSERT)
    line_start = f"{current_pos.split('.')[0]}.0"
    line_end = f"{current_pos.split('.')[0]}.end"
    line_text = text.get(line_start, line_end)

    pos = int(current_pos.split('.')[1])
    start = pos
    end = pos

    while start > 0 and line_text[start-1].isalnum():
        start -= 1

    while end < len(line_text) and line_text[end].isalnum():
        end += 1

    text.delete(f"{current_pos.split('.')[0]}.{start}", f"{current_pos.split('.')[0]}.{end}")

def batch_insert_base(event=None):
    text.insert(tk.INSERT, """@echo off
    
rem Código

pause""")

def batch_insert_if_equals(event=None):
    text.insert(tk.INSERT, """if "%variable%" equ "valor" (
    rem Action if true
)""")

def batch_insert_if_greater(event=None):
    text.insert(tk.INSERT, """if "%variable%" gtr "valor" (
    rem Action if true
)""")

def batch_insert_if_less(event=None):
    text.insert(tk.INSERT, """if "%variable%" lss "valor" (
    rem Action if true
)""")

def batch_insert_if_greater_equals(event=None):
    text.insert(tk.INSERT, """if "%variable%" geq "valor" (
    rem Action if true
)""")

def batch_insert_if_less_equals(event=None):
    text.insert(tk.INSERT, """if "%variable%" leq "valor" (
    rem Action if true
)""")

def batch_insert_for_loop(event=None):
    text.insert(tk.INSERT, """for /L %%A IN (1,1,10) DO (
    rem Action for each iteration
    for loop
    )""")

def python_insert_base(event=None):
    text.insert(tk.INSERT, """import os

os.system('cls')

# Code""")
    
def python_insert_if_equals(event=None):
    text.insert(tk.INSERT, """if variable == 'valor':
    # Action if true
""")

def python_insert_if_greater(event=None):
    text.insert(tk.INSERT, """if variable > 'valor':
    # Action if true
""")

def python_insert_if_less(event=None):
    text.insert(tk.INSERT, """if variable < 'valor':
    # Action if true
""")

def python_insert_if_greater_equals(event=None):
    text.insert(tk.INSERT, """if variable >= 'valor':
    # Action if true
""")

def python_insert_if_less_equals(event=None):
    text.insert(tk.INSERT, """if variable <= 'valor':
    # Action if true
""")

def python_insert_for_loop(event=None):
    text.insert(tk.INSERT, """for i in range(10):
    # Action for each iteration
""")
    
def python_insert_while_loop(event=None):
    text.insert(tk.INSERT, """while condition:
    # Code inside the while loop
    pass
""")

root = tk.Tk()
root.title("HNotepad")

text_frame = tk.Frame(root)
text_frame.pack(fill="both", expand=True)

text = tk.Text(text_frame, wrap="word", undo=True)
text.pack(side="right", fill="both", expand=True)

def undo(event=None):
    try:
        text.edit_undo()
    except tk.TclError:
        pass

def redo(event=None):
    try:
        text.edit_redo()
    except tk.TclError:
        pass

y_scrollbar = Scrollbar(text_frame, orient=tk.VERTICAL)
y_scrollbar.pack(side="left", fill="y")
y_scrollbar.config(command=on_scroll)

x_scrollbar = Scrollbar(text, orient=tk.HORIZONTAL)
x_scrollbar.pack(side="bottom", fill="x")
x_scrollbar.config(command=text.xview)

text.config(yscrollcommand=y_scrollbar.set)
text.config(xscrollcommand=x_scrollbar.set)

line_number_font = ("Courier", 9)

line_numbers = tk.Text(text_frame, width=4, padx=5, pady=5, wrap="none", font=line_number_font, state="disabled")
line_numbers.pack(side="left", fill="y")

text['yscrollcommand'] = sync_line_numbers
text['xscrollcommand'] = sync_line_numbers

menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="New                       Ctrl + N", command=new_file)
file_menu.add_command(label="New as         Ctrl + Alt + N", command=new_file_dialog)
file_menu.add_separator()
file_menu.add_command(label="Open                     Ctrl + O", command=open_file)
file_menu.add_command(label="Save                       Ctrl + S", command=save_file)
file_menu.add_separator()
file_menu.add_command(label="Exit                        Alt + F4", command=on_closing)

edit_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Edit", menu=edit_menu)
theme_menu = tk.Menu(edit_menu, tearoff=0)
edit_menu.add_command(label="Undo                                                                Ctrl + Z", command=undo)
edit_menu.add_command(label="Redo                                                                 Ctrl + Y", command=redo)
edit_menu.add_separator()
edit_menu.add_command(label="Cut                                                                   Ctrl + X", command=cut)
edit_menu.add_command(label="Copy                                                                Ctrl + C", command=copy)
edit_menu.add_command(label="Paste                                                                Ctrl + V", command=paste)
edit_menu.add_command(label="Delete                                                                     DEL", command=delete)
edit_menu.add_command(label="Delete word                                                Ctrl + DEL", command=delete_word)
edit_menu.add_command(label="Select all                                                          Ctrl + A", command=select_all)

format_view_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Format", menu=format_view_menu)
insert_menu = tk.Menu(format_view_menu, tearoff=0)

format_view_menu.add_cascade(label="Insert", menu=insert_menu)
batch_menu = tk.Menu(insert_menu, tearoff=0)
python_menu = tk.Menu(insert_menu, tearoff=0)

insert_menu.add_cascade(label="Batch", menu=batch_menu)
batch_menu.add_command(label="Base                                  Ctrl + Alt + a", command=batch_insert_base)
batch_menu.add_command(label="if (EQUALS)                      Ctrl + Alt + q", command=batch_insert_if_equals)
batch_menu.add_command(label="if (MAJOR)                      Ctrl + Alt + l", command=batch_insert_if_greater)
batch_menu.add_command(label="if (MINOR)                      Ctrl + Alt + p", command=batch_insert_if_less)
batch_menu.add_command(label="if (MAJOR EQUAL)          Ctrl + Alt + v", command=batch_insert_if_greater_equals)
batch_menu.add_command(label="if (MINOR EQUAL)          Ctrl + Alt + m", command=batch_insert_if_less_equals)
batch_menu.add_command(label="for                                     Ctrl + Alt + u", command=batch_insert_for_loop)

insert_menu.add_cascade(label="Python", menu=python_menu)
python_menu.add_command(label="Base                                  Ctrl + Alt + w", command=python_insert_base)
python_menu.add_command(label="if (EQUALS)                      Ctrl + Alt + z", command=python_insert_if_equals)
python_menu.add_command(label="if (MAJOR)                      Ctrl + Alt + x", command=python_insert_if_greater)
python_menu.add_command(label="if (MINOR)                      Ctrl + Alt + s", command=python_insert_if_less)
python_menu.add_command(label="if (MAJOR EQUAL)          Ctrl + Alt + e", command=python_insert_if_greater_equals)
python_menu.add_command(label="if (MINOR EQUAL)          Ctrl + Alt + d", command=python_insert_if_less_equals)
python_menu.add_command(label="for                                     Ctrl + Alt + c", command=python_insert_for_loop)
python_menu.add_command(label="while                                 Ctrl + Alt + r", command=python_insert_while_loop)

view_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="View", menu=view_menu)
theme_menu = tk.Menu(view_menu, tearoff=0)
view_menu.add_cascade(label="Theme", menu=theme_menu)

theme_menu.add_radiobutton(label="Light", command=lambda: change_theme("light"))
theme_menu.add_radiobutton(label="Dark", command=lambda: change_theme("dark"))

source_menu = tk.Menu(view_menu, tearoff=0)
view_menu.add_cascade(label="Font", menu=source_menu)

for font_name in available_fonts:
    source_menu.add_radiobutton(label=font_name, command=lambda font=font_name: change_font(font))

languages = ["Python", "YAML", "Batch", "None"]
language_to_menu_index = {
    "Python": 0,
    "YAML": 1,
    "Batch": 2,
    "None": 3
}

language_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Language", menu=language_menu)
for lang_name in languages:
    language_menu.add_command(label=lang_name, command=lambda lang=lang_name: set_language(lang))

current_language_label = tk.Label(root, text="Actual: None", bd=1, relief=tk.SUNKEN, anchor=tk.W)
current_language_label.pack(side=tk.BOTTOM, fill=tk.X)

setup_window()
apply_theme()
highlight_syntax()

text.bind("<Control-n>", new_file)
text.bind("<Control-o>", open_file)
text.bind("<Control-s>", save_file)
text.bind("<Control-z>", undo)
text.bind("<Control-y>", redo)
text.bind("<Control-x>", cut)
text.bind("<BackSpace>", delete)
text.bind("<Control-BackSpace>", delete_word)
text.bind("<Control-Alt-a>", batch_insert_base)
text.bind("<Control-Alt-q>", batch_insert_if_equals)
text.bind("<Control-Alt-l>", batch_insert_if_greater)
text.bind("<Control-Alt-p>", batch_insert_if_less)
text.bind("<Control-Alt-v>", batch_insert_if_greater_equals)
text.bind("<Control-Alt-m>", batch_insert_if_less_equals)
text.bind("<Control-Alt-u>", batch_insert_for_loop)
text.bind("<Control-Alt-w>", python_insert_base)
text.bind("<Control-Alt-z>", python_insert_if_equals)
text.bind("<Control-Alt-x>", python_insert_if_greater)
text.bind("<Control-Alt-s>", python_insert_if_less)
text.bind("<Control-Alt-e>", python_insert_if_greater_equals)
text.bind("<Control-Alt-d>", python_insert_if_less_equals)
text.bind("<Control-Alt-c>", python_insert_for_loop)
text.bind("<Control-Alt-r>", python_insert_while_loop)
text.bind("<KeyRelease>", on_text_change)

root.protocol("WM_DELETE_WINDOW", on_closing)

update_line_numbers()

root.mainloop()
