from tkinter.filedialog import askopenfilename

fname = askopenfilename(filetypes=( ("Text file", "*.txt*"),("HTML files", "*.html;*.htm")))
print(fname)
