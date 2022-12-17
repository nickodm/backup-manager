from models import *
from keyboard import add_hotkey
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from threading import Thread
from time import sleep
import tkinter.filedialog as tkFd
import tkinter.messagebox as tkMsg
import sys
import typing as typ

__version__ = "0.4.0 (BETA)"
PROJECT_NAME = "Nicko's Backup Manager (BETA)"

class Listener:
    def __init__(self) -> None:
        self.interval: int | float = .08
        self.thread: Thread = Thread(daemon=True, target=self.run)
        self._funcs: set[typ.Callable] = set()
        self._stop = False
        self._paused = False
        
    @property
    def working(self) -> bool:
        "Whether the thread is active."
        return self.thread.is_alive()
    
    @property
    def paused(self) -> bool:
        "Whether the activity is paused or not."
        return self._paused
    
    def add(self, func: typ.Callable):
        "Add an object to be called periodically."
        self._funcs.add(func)
        return func
    
    def remove(self, func: typ.Callable):
        "Remove an object."
        self._funcs.remove(func)
        return func
    
    def start(self) -> typ.Self:
        "Start the activity and the thread."
        if not self.working:
            self.thread.start()
        return self
    
    def stop(self) -> typ.Self:
        "Stop the activity and join the thread."
        self._stop = True
        self.thread.join(self.interval * 2)
        return self
    
    def pause(self) -> typ.Self:
        "Pause the activity, but keep the thread alive."
        self._paused = True
        return self
    
    def resume(self) -> typ.Self:
        "Resume the activity."
        self._paused = False
        return self
    
    def run(self):
        "Call all the functions periodically."
        if self._stop:
            return

        for func in self._funcs:
            if self._stop:
                self._stop = False
                return

            while self._paused:
                sleep(self.interval)
            
            func()
            sleep(self.interval)
        sleep(self.interval)
        
        self.run()
            

class LogSpace(ScrolledText):
    def write(self, string: str, 
              index: str = tk.END, endline: str = "\n"):
        old_state = self['state']
        self['state'] = 'normal'
        self.insert(index, string + endline)
        self['state'] = old_state
        
        return len(string)
    
    def clear(self):
        old_state = self['state']
        self['state'] = 'normal'
        self.delete('0.0', tk.END)
        self['state'] = old_state
        return self
        
    def enable(self):
        self['state'] = tk.NORMAL
        return self
    
    def disable(self):
        self['state'] = tk.DISABLED
        return self
    
    def get(self, start: str = "0.0", end: str = tk.END) -> str:
        return super().get(start, end)


class Button(tk.Button):
    def __init__(self, master: tk.Misc, text: str = '', 
                 command: typ.Callable = None, 
                 state: typ.Literal['normal', 'disabled'] = 'normal', **kw):
        if command is None:
            command = lambda: print(f'BUTTON {text!r} PRESSED.')
        
        super().__init__(master, text=text, command=command, **kw)

        self.cursor = 'hand2' if state == 'normal' else 'arrow'

    @property
    def state(self) -> typ.Literal['active', 'normal', 'disabled']:
        return self['state']

    @state.setter
    def state(self, val):
        self['state'] = val
        
    @property
    def cursor(self):
        return self['cursor']
    
    @cursor.setter
    def cursor(self, val):
        self['cursor'] = val
        
    def enable(self):
        self.config(state='normal', cursor='hand2')
        return self
    
    def disable(self):
        self.config(state='disabled', cursor='arrow')
        return self


class ResourcesTable(ttk.Treeview):
    def __init__(self, master, *args, **kw):
        super().__init__(master, *args, **kw)
        
        self.column('#0', width=0, stretch=False)
        
        headings = {
            'ID': {
                'width': 50,
                'anchor': tk.CENTER
            },
            'Type': {
                'width': 60,
                'anchor': tk.CENTER
            },
            'Origin Path': {
                'width': 440,
                'anchor': tk.W
            },
            'Destiny Path': {
                'width': 440,
                'anchor': tk.W
            }
        }
        
        self['columns'] = list(headings.keys())
        for name, data in headings.items():
            self.column(name, stretch=False, **data)
            self.heading(name, text=name, anchor=data['anchor'])

        self._array: ResourcesArray | None = None
        
        self.scrollbar_x = ttk.Scrollbar(master, orient='horizontal',
                                         command=self.xview)
        self.scrollbar_x.grid(row=1, column=0, sticky='we')
        self.scrollbar_y = ttk.Scrollbar(master, command=self.yview)
        self.scrollbar_y.grid(row=0, column=1, sticky='ns')
        
        self.config(xscrollcommand=self.scrollbar_x.set,
                    yscrollcommand=self.scrollbar_y.set)
    
    @property
    def array(self) -> ResourcesArray | None:
        return self._array
    
    @array.setter
    def array(self, array: ResourcesArray):
        self._array = array
        for rsrc in array:
            self.insert(rsrc)
       
    def insert(self, meta: BackupMeta) -> BackupMeta:
        """Insert a resource in the view. JUST FOR RESOURCES IN THE ARRAY."""
        id = str(self.array.index(meta))
        super().insert('', 'end', iid=id, 
                       values=(id, 
                               meta.type.upper(), 
                               meta.origin, 
                               meta.destiny))
        return meta
        
    def reload(self) -> typ.Self:
        self.clear()
        self.array = self.array
        return self
    
    def clear(self) -> typ.Self:
        self.delete(*range(len(all_lists)))
        return self
        
    def add_file(self):
        origin = tkFd.askopenfilename(
            title= "Backup File",
            filetypes= (
                ("Any File", "*.*"), 
            )
        )

        if not origin:
            return

        origin = Path(origin).resolve(strict= True)

        destiny = Path(tkFd.asksaveasfilename(
            title= "Backup File Destiny",
            initialfile= "[BACKUP] " + origin.name,
            defaultextension= origin.suffix,
            filetypes= (("*" + origin.suffix, origin.suffix), 
            )
        ))

        if not destiny:
            return
        
        destiny = Path(destiny).resolve()
        
        new = BackupFile(origin, destiny)
        self.array.add(new)
        self.reload() #TODO: Optimize this
        
        return new

    def get_dir(*, zip_file:bool = False): #TODO
        origin = tkFd.askdirectory(
            title= "Backup Dir",
            mustexist= True
        )

        if not origin:
            return
        
        origin = Path(origin).resolve(strict= True)

        if zip_file:
            destiny = tkFd.asksaveasfilename(
                title= "Backup Dir Destiny",
                filetypes= (("Archivo ZIP", "*.zip"), ),
                defaultextension= "*.zip",
                initialfile= " [BACKUP] " + origin.name
            )
        else:
            destiny = tkFd.askdirectory(
                    title= "Backup Dir Destiny",
                    mustexist= False,
                    initialdir= " [BACKUP] " + origin.name
                )
            
        if not destiny:
            return
        
        destiny = Path(destiny).resolve()
        
    def button_delete(self):
        for i in self.selection():
            for j in self.array.pop(int(i)):
                pass
            self.delete(i)
            
    def select_all(self) -> typ.Self:
        self.selection_add([i for i in range(len(self.array))])
        return self
        

def main():
    def grid_sep(master: tk.Misc, *, row: int, column: int, 
                 orient: typ.Literal['horizontal', 'vertical']) -> None: 
        ttk.Separator(master, orient=orient).grid(row=row, 
                                                      column=column,
                                                      sticky='nswe', 
                                                      padx=6, pady=6)
        
    def export_log(): 
        path = tkFd.asksaveasfilename(
            title='Save Log',
            parent=root,
            confirmoverwrite=True,
            defaultextension='*.txt',
            filetypes=[
                ('Text File', '*.txt')
            ]
        )
        
        if not path:            
            return
        
        log_space.write("Exporting log...")
        with open(path, 'w', encoding='utf-8') as fp:
            fp.write(log_space.get())
            
        log_space.write('Log exported!')
        tkMsg.showinfo(PROJECT_NAME,
                       "Your log was exported!")
    
    def open_web_browser(url: str):
        if tkMsg.askokcancel(PROJECT_NAME,
                             'The web browser will open.'):        
            from webbrowser import open
            open(url)
            return True
        else:
            return False
        
    def use_command_prompt():
        from main import run
        if tkMsg.askokcancel(PROJECT_NAME,
                          "The graphic interface will close. Are you sure?"):
            listener.stop()
            root.destroy()
            run()
            
    
    root = tk.Tk()
    root.title(PROJECT_NAME)
    root.resizable(False, False)
    
    var_compress = tk.BooleanVar(root, True)
    
    listener = Listener()
    
    root.bind('<Map>', lambda x: listener.resume())
    root.bind('<Unmap>', lambda x: listener.pause())
    
    #****************
    #*     MENU
    #****************
    
    menu_main = tk.Menu(root)
    root.config(menu=menu_main)

    
    menu_options = tk.Menu(menu_main, tearoff=0)
    menu_main.add_cascade(menu=menu_options, label='Options')

    menu_options.add_command(label='Use Command Prompt',
                          command=use_command_prompt)

    menu_options.add_separator()

    menu_options.add_checkbutton(label='Compress Directories',
                                 variable=var_compress)
    
    menu_options.add_separator()
    
    menu_options.add_command(label='Save Lists and Resources',
                             command=lambda: (all_lists.save,
                                              log_space.write(
                                                  'Saved lists and resources!'
                                              )))
    
    menu_options.add_separator()

    menu_options.add_command(label='Exit',
                             command=sys.exit)
    
    menu_help = tk.Menu(menu_main, tearoff=0)
    menu_main.add_cascade(menu=menu_help, label='Help')

    menu_help.add_command(label='Open GitHub',
                          command= lambda: open_web_browser(
                              'https://github.com/nickodm/backup-manager'
                          ))
    
    menu_help.add_command(label='Report an Issue',
                          command= lambda: open_web_browser(
                              'https://github.com/nickodm/backup-manager/issues'
                          ))
    
    menu_help.add_command(
        label='View License',
        command= lambda: open_web_browser(
        "https://github.com/nickodm/backup-manager/blob/master/COPYING"
        ))
    
    menu_help.add_separator()
    
    menu_help.add_command(label='About',
                          command=lambda: tkMsg.showinfo(
                            PROJECT_NAME,
                            f"v{__version__}"))
    
    #****************
    #*    FRAMES
    #****************
    
    frame_buttons = tk.Frame(root, padx=10, pady=10)
    frame_buttons.grid(row=0, column=0, sticky='w')
    
    frame_lists = tk.Frame(root, padx=10, pady=10)
    frame_lists.grid(row=1, column=0)
    
    grid_sep(root, row=2, column=0, orient=tk.HORIZONTAL)
    
    frame_load_bar = tk.Frame(root, padx=10, pady=10)
    frame_load_bar.grid(row=3, column=0, sticky='we')
    
    frame_log = tk.Frame(root, padx=10, pady=10)
    frame_log.grid(row=4, column=0)
    
    frame_log_buttons = tk.Frame(root, padx=10, pady=10)
    frame_log_buttons.grid(row=5, column=0, sticky='we')
    
    #****************
    #*    BUTTONS
    #****************

    # Add File
    button_add_file = Button(frame_buttons, text='Add File')
    button_add_file.grid(row=0, column=0)

    # Add Dir
    button_add_dir = Button(frame_buttons, text='Add Dir')
    button_add_dir.grid(row=0, column=1)
    
    check_compress = ttk.Checkbutton(frame_buttons,
                                     variable=var_compress,
                                     text='Compress Dir',
                                     padding=10)
    check_compress.grid(row=0, column=2)
    
    grid_sep(frame_buttons, row=0, column=3, orient='vertical')
    
    # Edit Resource
    button_edit = Button(frame_buttons, text='Edit')
    button_edit.grid(row=0, column=4)

    # Delete Resource
    button_del = Button(frame_buttons, text='Delete')
    button_del.grid(row=0, column=5)
    
    grid_sep(frame_buttons, row=0, column=6, orient='vertical')
    
    # Backup
    button_backup = Button(frame_buttons, text='Backup')
    button_backup.grid(row=0, column=7)

    # Restore
    button_restore = Button(frame_buttons, text='Restore')
    button_restore.grid(row=0, column=8)

    button_copy = Button(frame_buttons, text='Copy')
    button_copy.grid(row=0, column=9)

    grid_sep(frame_buttons, row=0, column=10, orient='vertical')
    
    button_select_all = Button(frame_buttons, text='Select All')
    button_select_all.grid(row=0, column=11)

    grid_sep(frame_buttons, row=0, column=12, orient='vertical')
    
    select_list = ttk.Combobox(frame_buttons)
    select_list.config(values=[i.name for i in all_lists])
    select_list.grid(row=0, column=13)
    
    #****************
    #*    TABLE
    #****************
        
    table_resources = ResourcesTable(frame_lists)
    table_resources.array = all_lists[0]
    
    button_add_file.config(command=table_resources.add_file)
    button_del.config(command=table_resources.button_delete)
    button_select_all.config(command=table_resources.select_all)
    
    add_hotkey('ctrl+a', table_resources.select_all)
    
    @listener.add
    def activate_edit_delete_buttons():
        if table_resources.selection():
            button_edit.enable()
            button_del.enable()
        else:
            button_edit.disable()
            button_del.disable()
    
    table_resources.grid(row=0, column=0)
    
    #****************
    #*   LOAD BAR
    #****************

    pbar = ttk.Progressbar(frame_load_bar, length=910)
    pbar.grid(row=0, column=0)

    #****************
    #*    LOGS
    #****************
    
    log_space = LogSpace(frame_log, height=10, width=89).disable()
    log_space.write("Welcome to the software!")    
    log_space.grid(row=0, column=0)
    
    #* BUTTONS
    log_button_clear = Button(frame_log_buttons, text='Clear',
                                 command=log_space.clear)
    log_button_clear.grid(row=0, column=0)
    
    log_button_export = Button(frame_log_buttons, text='Export',
                               command=export_log)
    log_button_export.grid(row=0, column=1)
    
    listener.start()
    root.mainloop()

if __name__ == "__main__":
    all_lists.load()
    
    if sys.platform == "win32":
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1) # To avoid blurred windows
    
    try:
        main()
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        
        tkMsg.showerror(PROJECT_NAME,
                        f"An error has ocurred: {exc!r}.\n"
                         "The software will close now.")
        
        raise
        