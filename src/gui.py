from models import *
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkMsg
import sys
import typing as typ

__version__ = "0.4.0 (BETA)"
PROJECT_NAME = "Nicko's Backup Manager (BETA)"

class ResourcesTable(ttk.Treeview):
    def __init__(self, master, *args, **kw):
        super().__init__(master, *args, **kw)
        self['columns'] = ('ID', 'Origin Path', 'Destiny Path',
                           'Type')
        
        self.column('#0', width=0, stretch=tk.NO)
        self.column('ID', width=50, anchor=tk.CENTER)
        self.column('Origin Path', width=400, anchor=tk.W)
        self.column('Destiny Path', width=400, anchor=tk.W)
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
                           values=(id, 
                                   rsrc.origin, 
                                   rsrc.destiny, 
                                   rsrc.type.upper()))
    
        self._array = array    

def main():
    root = tk.Tk()
    root.title(PROJECT_NAME)
    
    #****************
    #*     MENU
    #****************
    
    menu_main = tk.Menu(root)

    
    menu_main.add_command(label='About',
                          command=lambda: tkMsg.showinfo(
                            PROJECT_NAME,
                            f"v{__version__}"))

    
    root.config(menu=menu_main)
    
    #****************
    #*    FRAMES
    #****************
    
    frame_buttons = tk.Frame(root, padx=10, pady=10)
    frame_buttons.grid(row=0, column=0, sticky='w')

    
    frame_lists = tk.Frame(root, padx=10, pady=10)
    frame_lists.grid(row=1, column=0)
    
    #****************
    #*    BUTTONS
    #****************
    def grid_sep(*, row: int, column: int) -> None: 
        ttk.Separator(frame_buttons, orient='vertical') \
        .grid(row=row, column=column,
        sticky='nswe',padx=6, pady=6)

    # Add File
    button_add_file = tk.Button(frame_buttons, text='Add File',
                                command=lambda: print('Add File'))
    button_add_file.grid(row=0, column=0)

    # Add Dir
    button_add_dir = tk.Button(frame_buttons, text='Add Dir',
                               command=lambda: print('Add Dir'))
    button_add_dir.grid(row=0, column=1)
    
    grid_sep(row=0, column=2)
    
    # Edit Resource
    button_edit_resource = tk.Button(frame_buttons, text='Edit',
                                     command= lambda: print('Edit Resource'))
    button_edit_resource.grid(row=0, column=3)

    # Delete Resource
    button_del = tk.Button(frame_buttons, text='Delete',
                           command=lambda: print('Delete Resource'))
    button_del.grid(row=0, column=5)
    
    grid_sep(row=0, column=6)
    
    button_backup = tk.Button(frame_buttons, text='Backup')
    button_backup.grid(row=0, column=7)

    button_restore = tk.Button(frame_buttons, text='Restore')
    button_restore.grid(row=0, column=8)

    button_restore = tk.Button(frame_buttons, text='Copy')
    button_restore.grid(row=0, column=9)

    grid_sep(row=0, column=10)
    
    button_select_all = tk.Button(frame_buttons, text='Select All')
    button_select_all.grid(row=0, column=11)

    grid_sep(row=0, column=12)
    
    select_list = ttk.Combobox(frame_buttons)
    select_list.config(values=[i.name for i in all_lists])
    select_list.grid(row=0, column=13)
    
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
    table_resources.array = all_lists[0]
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
    all_lists.load()
    
    if sys.platform == "win32":
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1) # To avoid blurred windows
    
    try:
        main()
    except BaseException as exc:
        tkMsg.showerror(PROJECT_NAME,
                        f"An error has ocurred: {exc!r}.\n"
                         "The software will close now.")
        
        raise
        