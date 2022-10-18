"""
Nicko's Backup Manager - A python program to control backups
Copyright (C) 2022  Nicolás Miranda

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from pathlib import Path
import logging
from typing import Literal
from models import *
import tkinter.filedialog as tkFd
import consoletools as ctools

__version__ = "0.3.2"

class NextRoundAdvice(Exception):
    """
    Exception to jump to the next round of the mainloop.
    """
    pass

def exit():
    from sys import exit as sys_exit
    all_lists.save()
    sys_exit()
    
def check_index(num:str, allow_slice:bool = True, iter:Literal['a', 's'] = 'a') -> int|slice:
    assert iter in ('a', 's')
    iter_ = all_lists if iter == 'a' else all_lists.selected

    if allow_slice and ctools.is_slice(num):
        index = ctools.convert_slice(num)
        if index.start < 0 or index.stop > len(iter_):
            print("The index is out of range.")
            raise NextRoundAdvice()
            
        return index
    
    if not num.isdigit():
        print("You must input a real index.")
        raise NextRoundAdvice()
    
    index = int(num)
    
    if index >= len(iter_):
        print("The index is out of range.")
        raise NextRoundAdvice()
        
    return index

def check_selected() -> None:
    if all_lists.selected == None:
        print("First, you must select a list.")
        raise NextRoundAdvice()

def get_file() -> tuple[Path, Path]:
    origin = tkFd.askopenfilename(
        title= "Backup File",
        filetypes= (
            ("Any File", "*.*"), 
        )
    )
    
    if not origin:
        print("The file was not added.")
        raise NextRoundAdvice()
    origin = Path(origin).resolve(strict= True)

    destiny = Path(tkFd.asksaveasfilename(
        title= "Backup File Destiny",
        initialfile= "[BACKUP] " + origin.name,
        defaultextension= origin.suffix,
        filetypes= (("*" + origin.suffix, origin.suffix), 
        )
    ))
    
    if not destiny:
        print("The file was not added.")
        raise NextRoundAdvice()    
    destiny = Path(destiny).resolve()

    return (origin, destiny)

def get_dir(*, zip_file:bool = False) -> tuple[Path, Path]:
    origin = tkFd.askdirectory(
        title= "Backup Dir",
        mustexist= True
    )
    
    if not origin:
        print("The dir was not added.")
        raise NextRoundAdvice()
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
        print("The dir was not added.")
        raise NextRoundAdvice()    
    destiny = Path(destiny).resolve()

    return (origin, destiny)

def main():
    enter = ctools.prompt(f"[{all_lists.selected_index}] >> ")
    
    match enter[0]:
        case "exit":
            print("Saving list...")
            print("Exiting...")
            exit()
        
        case "add":
            check_selected()
            match enter[1]:
                case "file":
                    new_file = BackupFile(*get_file())
                    
                    all_lists.selected.add(new_file)
                    print(f"The file \"{new_file.origin.name}\" was added to the list.")
                    logging.info(f"The file \"{new_file.origin.name}\" was added to the list.")
                    
                case "dir":
                    compress = enter[2] in ("--compress", "-c")
                    
                    new_dir = BackupDir(*get_dir(zip_file= compress), compress= compress)
                    
                    all_lists.selected.add(new_dir)
                    print(f"The dir \"{new_dir.origin.name}\" was added to the list.")
                    logging.info(f"The dir \"{new_dir.origin.name}\" was added to the list.")            
                    
                case _:
                    print("You must add \"file\" or \"dir\".")
        
        case "pop":
            check_selected()
            index = check_index(enter[1], iter= 's')
            for meta in all_lists.selected.pop(index):
                print(f"The {meta.type} \"{meta.name}\" was deleted from the list.")
                logging.info(f"The {meta.type} \"{meta.name}\" was deleted from the list.")
        
        case "show":
            check_selected()
            print(all_lists.selected.report())
        
        case "backup":
            check_selected()
            index = check_index(enter[1], iter= 's') if enter[1] else ...
            print("Creating backups...")
            for result, meta in all_lists.selected.backup(index):
                if result:
                    print(f"\"{meta.name}\" was successfully copied.")
                elif not meta.are_different():
                    print(f'"{meta.name}" has no changes. It was not copied.')
                else:
                    print(f"\"{meta.name}\" cannot be copied.")
                    
        case "restore":
            check_selected()
            index = check_index(enter[1], iter= 's') if enter[1] else ...
            print("Restoring...")
            for result, meta in all_lists.selected.restore(index):
                if result:
                    print(f"\"{meta.name}\" was successfully copied.")
                elif not meta.are_different():
                    print(f'"{meta.name}" has no changes. It was not copied.')
                else:
                    print(f"\"{meta.name}\" cannot be copied.")
                    
        case "list":
            match enter[1]:
                case "show":
                    if not enter.get(2, None):
                        print()
                        print(all_lists.mention())
                        print()
                        return
                    
                    print(all_lists[check_index(enter[2], False)].report())
                    
                case "select":
                    if not enter[2]:
                        print(f'The current list is "{all_lists.selected.name}" ({all_lists.selected_index}).')
                        return
                    
                    index = check_index(enter[2], False)
                    print("The list \"%s\" was selected."%all_lists.select(index).name)
                    
                case "create"|"new":
                    name = enter.get(2, None)

                    if name in ("exit", "cancel"):
                        print("The list was not created.")
                        return
                    
                    if not name:
                        print("Please, choose a name for the list.")
                        return
                    
                    if name in all_lists.names():
                        print("There is already a list with that name.")
                        return
                    
                    all_lists.add(ResourcesArray(name))
                    print(f"Created list \"{name}\".")
                    
                case "import":
                    path = tkFd.askopenfilename(
                        title= "Import List",
                        filetypes= (("JSON File", "*.json"), ),
                        defaultextension= "*.json"
                    )
                    
                    if not path:
                        print("The list was not imported.")
                        return
                    
                    importing = ResourcesArray.from_import(path)
                    
                    if importing in all_lists:
                        print(f"There is already a list named \"{importing.name}\".")
                        return

                    if not ("-d" in enter or "--direct" in enter):
                        print(f"Is \"{importing.name}\" the list?", end= " ")
                        if not ctools.confirm(cancel= True):
                            print("The list was not imported.")
                            return
                                
                    all_lists.add(importing)
                    print(f"The list \"{importing.name}\" was imported.")
                    
                case "export":
                    index = check_index(enter[2], allow_slice= False)

                    path = tkFd.asksaveasfilename(
                        title= "Export List",
                        filetypes= (("JSON File", "*.json"), ),
                        defaultextension= "*.json",
                        initialfile= "%s - Backup List.json"%all_lists[index].name
                    )
                    
                    if path == "":
                        print("The list was not exported.")
                        return
                    
                    all_lists[index].export(path)
                    print(f"The list was exported to \"{Path(path).resolve()}\".")
                    
                case "pop":
                    index = check_index(enter[2])
                    if isinstance(index, int):
                        index = slice(index, index + 1)
                    
                    for rarray in all_lists[index]:
                        all_lists.remove(rarray)
                        print(f"The list \"{rarray.name}\" was deleted.")
                    
                case "rename":
                    index = check_index(enter[2], False)
                    new_name = enter.get(3, "")
                    
                    if not new_name:
                        print("Please, input a name.")
                        return
                    
                    if new_name in all_lists.names():
                        print(f"There is already a list named \"{new_name}\".")
                        return
                    
                    print(f'The list "{all_lists[index].name}" will be renamed to "{new_name}".')
                    print("Are you sure?", end= " ")
                    if ctools.confirm(cancel= True):
                        all_lists[index].name = new_name
                        print("The list was renamed.")
                    else: 
                        print("The list was not renamed.")
                    return
                
                case "diff":
                    check_selected()
                    index = check_index(enter[2])
                    if isinstance(index, int):
                        index = slice(index, index + 1)
                    target = all_lists.selected
                    
                    for rarray in all_lists[index]:
                        if rarray is target:
                            print("Cannot show differences between the selected list and itself. Continuing...")
                            continue
                        
                        print(f'Showing differences between "{target.name}" and "{rarray.name}":')
                        for rsrc in target.diff(rarray):
                            print(rsrc.report())
                    
                    print("Diff finished.")

                case "merge":
                    check_selected()
                    index = check_index(enter[2]) 
                    if isinstance(index, int):
                        index = slice(index, index + 1)

                    target = all_lists.selected
                    
                    for rarray in all_lists[index]:
                        if rarray is target:
                            print(f"Cannot merge the target list into itself. Continuing...")
                            continue
                        
                        print(f'Merging "{rarray.name}" into "{target.name}"...')
                        target.extend(rarray)
                    print("Merge finished.")

                case "clone":
                    index = check_index(enter[2])
                    if isinstance(index, int):
                        index = slice(index, index + 1)
                    
                    for rarray in all_lists[index]:
                        rarray_cp = rarray.copy(f"Copy {all_lists.count_copies(rarray)} of {rarray.name}")

                        all_lists.add(rarray_cp)
                        print(f'"{rarray.name}" has been cloned.')
                
                case ""|None:
                    print("You must use a subcommand also.")
                
                case _:
                    print("Unknown command")
                    
        case "license":
            print(
"""
Nicko's Backup Manager - A python program to control backups
Copyright (C) 2022  Nicolás Miranda

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
""")
        case "cls"|"clear":
            ctools.shell.clear()

        case "version"|"ver":
            print(f"Nicko's Backup Manager - v{__version__}")
        
        case "":
            pass
        
        case _:
            print("Unknown command")

if __name__ == "__main__":
    from colorama import init
    init()
    del init
    
    try:
        from sys import platform
        if platform == "win32":    
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1) # To avoid blurred windows

        if not PROJECT_DIR.exists():
            PROJECT_DIR.mkdir()
            PROJECT_DIR.joinpath("logs").mkdir()
            
        with PROJECT_DIR.joinpath("logs/Last Log.log") as log_path:
            if log_path.exists():
                from os import remove
                remove(log_path)
                
            logging.basicConfig(filename= log_path, level= logging.INFO, 
                                format= "[%(asctime)s] %(levelname)s: %(message)s", datefmt= "%b %d, %Y %H:%M:%S")
        
        logging.info("Starting...")
        logging.info(f"Working in {platform!r}. \n"
                     f"Project Dir: '{PROJECT_DIR}'\n"
                     f"App Version: {__version__}")
        
        print(
"""Nicko's Backup Manager  Copyright (C) 2022  Nicolás Miranda
This program comes with ABSOLUTELY NO WARRANTY; for details type 'license'.
This is free software, and you are welcome to redistribute it
under certain conditions; type 'license' for details.
"""
        )
        print("Loading list...")
        all_lists.load()
        if all_lists.selected is not None:
            print(f'List "{all_lists.selected.name}" is selected.')
        else:
            print("There are not a selected list.")
        
        while True:
            try:
                main()
            except NextRoundAdvice:
                pass
        
    except BaseException as exc:
        if isinstance(exc, SystemExit):
            raise
        logging.exception(exc)
        print(f'An error has ocurred: {exc!r}.\nPlease report it on "github.com/nickodm/backup-manager".')