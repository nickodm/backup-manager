from models import *
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkMsg
import sys
import typing as typ

__version__ = "0.4.0"

class ResourcesTable(ttk.Treeview):
    def __init__(self, master, *args, **kw):
        super().__init__(master, *args, **kw)
        self['columns'] = ('ID', 'Origin Path', 'Destiny Path',
                           'Type')
        
        self.column('#0', width=0, stretch=tk.NO)
        self.column('ID', width=50, anchor=tk.CENTER)
        self.column('Origin Path', width=200, anchor=tk.CENTER)
        self.column('Destiny Path', width=200, anchor=tk.CENTER)
        self.column('Type', width=60, anchor=tk.CENTER)
        # self.column('Compress', width=80, anchor=tk.CENTER)
        
        for column in self['columns']:
            self.heading(column, text=column, anchor=tk.CENTER)

        self._array: ResourcesArray | None = None
    
    @property
    def array(self) -> ResourcesArray | None:
        return self._array
    
    @array.setter
    def array(self, array: ResourcesArray):
        for rsrc in array:
            id = str(array.index(rsrc))
            super().insert(parent='',
                           index='end',
                           iid=id,
                           values=(id, rsrc.origin, rsrc.destiny, rsrc.type))
    
        self._array = array    

def main():
    root = tk.Tk()
    root.title("Nicko's Backup Manager")
    
    #****************
    #*     MENU
    #****************
    
    menu_main = tk.Menu(root)

    
    menu_main.add_command(label='About',
                          command=lambda: tkMsg.showinfo(
                            "Nicko's Backup Manager",
                            f"v{__version__}"))

    
    root.config(menu=menu_main)
    
    #****************
    #*    FRAMES
    #****************
    
    frame_buttons = tk.Frame(root, padx=40, pady=40)
    frame_buttons.grid(row=0, column=0)

    
    frame_lists = tk.Frame(root, padx=40, pady=40)
    frame_lists.grid(row=0, column=1)
    
    #****************
    #*    BUTTONS
    #****************

    button_add_file = tk.Button(frame_buttons, text='Add File',
                                command=lambda: print('Add File'))
    button_add_file.grid(row=1, column=0)


    button_add_dir = tk.Button(frame_buttons, text='Add Dir',
                               command=lambda: print('Add Dir'))
    button_add_dir.grid(row=1, column=1)
    
    #****************
    #*    TABLE
    #****************
    
    #* Scrollbars
    # table_resources_x_scroll = tk.Scrollbar(frame_lists)
    # table_resources_x_scroll.grid(row=0, column=1)
    
    # table_resources_y_scroll = tk.Scrollbar(frame_lists, orient='horizontal')
    # table_resources_y_scroll.grid(row=1, column=0)
    
    table_resources = ResourcesTable(frame_lists)
    # table_resources['columns'] = ('ID', 'Origin Path', 'Destiny Path',
    #                               'Type', 'Compress')
    
    # table_resources.column('#0', width=0, stretch=tk.NO)
    # table_resources.column('ID', width=50, anchor=tk.CENTER)
    # table_resources.column('Origin Path', width=200, anchor=tk.CENTER)
    # table_resources.column('Destiny Path', width=200, anchor=tk.CENTER)
    # table_resources.column('Type', width=60, anchor=tk.CENTER)
    # table_resources.column('Compress', width=80, anchor=tk.CENTER)
    
    # for column in table_resources['columns']:
    #     table_resources.heading(column, text=column, anchor=tk.CENTER)
    
    # for i in range(4):
    #     table_resources.insert('', 'end', values=(str(i), 'a', 'b', 'FILE', 'Yes'),
    #                        iid=str(i))
    
    table_resources.grid(row=0, column=0)
    
    
    button_add_file.config(command=lambda: print(table_resources.selection()))
    
    ttk.Combobox # Lista desplegable
    
    root.mainloop()

if __name__ == "__main__":
    if sys.platform == "win32":
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1) # To avoid blurred windows
    
    try:
        main()
    except BaseException as exc:
        tkMsg.showerror("Nicko's Backup Manager",
                        f"An error has ocurred: {exc!r}.\n"
                         "The software will close now.")
        
        raise
        