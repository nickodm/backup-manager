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
from ctypes import windll
from typing import Literal as _Literal
from models import *
import tkinter.filedialog as tkFd
import consoletools as ctools

__version__ = "0.2.0"

def exit():
    from sys import exit as sys_exit
    all_lists.save()
    sys_exit()
    
def check_index(num:str, allow_slice:bool = True, iter:_Literal['a', 's'] = 'a') -> int|slice:
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
        
        case "del":
            check_selected()
            index = check_index(enter[1])
            deleted = all_lists.selected.pop(index)
            print(f"The {deleted.type} \"{deleted.name}\" was deleted from the list.")
            logging.info(f"The {deleted.type} \"{deleted.name}\" was deleted from the list.")
        
        case "show":
            check_selected()
            print(all_lists.selected.report())
        
        case "backup":
            check_selected()
            index = check_index(enter[1], iter= 's') if enter[1] else ...
            print(f"Creating backups...")
            for result, meta in all_lists.selected.backup(index):
                if result:
                    print(f"\"{meta.name}\" was successfully copied.")
                    logging.info(f"\"{meta.name}\" was successfully copied.")
                else:
                    if not meta.are_different():
                        print(f'"{meta.name}" has no changes. It was not copied.')
                        logging.info(f'"{meta.name}" has no changes. It was not copied.')
                    else:
                        print(f"\"{meta.name}\" cannot be copied.")
                        logging.info(f"\"{meta.name}\" cannot be copied.")
                    
        case "restore":
            check_selected()
            print(f"Restoring {all_lists.selected.total_files} files...")
            for file_name, result, _ in all_lists.selected.restore_all():
                if result:
                    print(f"\"{file_name}\" was successfully copied.")
                    logging.info(f"\"{file_name}\" was successfully copied.")
                else:
                    print(f"\"{file_name}\" cannot be copied.")
                    logging.info(f"\"{file_name}\" cannot be copied.")
                    
        case "list":
            match enter[1]:
                case "show":
                    if not enter.get(2, None):
                        print(all_lists.mention())
                        return
                    
                    index = check_index(enter[2])
                    
                    print(all_lists[index].report())
                    
                case "select":
                    index = check_index(enter[2])

                    print("The \"%s\" list was selected."%all_lists.select(index).name)
                    
                case "create":
                    name = enter.get(2, "")

                    if name in ("exit", "cancel"):
                        print("The list was not created.")
                        return
                    
                    if name == "":
                        print("Please, choose a name for the list.")
                        return
                    
                    all_lists.add(ResourcesArray(name))
                    print(f"Created list \"{name}\".")
                    
                case "import":
                    path = tkFd.askopenfilename(
                        title= "Import List",
                        filetypes= (("JSON File", "*.json"), ),
                        defaultextension= "*.json"
                    )
                    
                    if path == "":
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
                    index = check_index(enter[2])

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
                    
                case "remove":
                    index = check_index(enter[2])

                    print(f"The list \"{all_lists.pop(index).name}\" was removed.")
                    
                case "rename":
                    index = check_index(enter[2])
                    
                    new_name = enter.get(3, "")
                    
                    if new_name == "":
                        print("Please, input a name.")
                        return
                    
                    if new_name in map(lambda x: x.name, all_lists):
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
    
    print(
"""Nicko's Backup Manager  Copyright (C) 2022  Nicolás Miranda
This program comes with ABSOLUTELY NO WARRANTY; for details type 'license'.
This is free software, and you are welcome to redistribute it
under certain conditions; type 'license' for details.
"""
    )
    print("Loading list...")
    all_lists.load()
    
    while True:
        try:
            main()
        except NextRoundAdvice:
            pass