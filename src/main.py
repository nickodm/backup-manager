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
from models import *
import tkinter.filedialog as tkFd
import consoletools as ctools

__version__ = "0.2.0"

def exit():
    from sys import exit as sys_exit
    all_lists.save()
    sys_exit()
    
def check_index(num:str) -> int:
    if not num.isdigit():
        print("You must input a real index.")
        raise NextRoundAdvice
    
    index = int(num)
    
    if all_lists.get(index, None) == None:
        print("The index is out of range.")
        raise NextRoundAdvice
        
    return index

def check_selected() -> None:
    if all_lists.selected == None:
        print("First, you must select a list.")
        raise NextRoundAdvice()

def get_file_destiny(origin_path:Path):
    path = tkFd.asksaveasfilename(
        title= "Backup File Destiny",
        initialfile= "[BACKUP] " + origin_path.name,
        defaultextension= origin_path.suffix,
        filetypes= (("*" + origin_path.suffix, origin_path.suffix), 
        )
    )

    return Path(path)
    
def get_file_origin():
    path = tkFd.askopenfilename(
        title= "Backup File",
        filetypes= (
            ("Cualquier Archivo", "*.*"), 
        )
    )

    return Path(path)

def get_dir_origin():
    path = tkFd.askdirectory(
        title= "Backup Dir",
        mustexist= True
    )
    
    return Path(path)

def get_dir_destiny(*, zip_file:bool = False, file_name:str = ""):
    if zip_file:
        path = tkFd.asksaveasfilename(
            title= "Backup Dir Destiny",
            filetypes= (("Archivo ZIP", "*.zip"), ),
            defaultextension= "*.zip",
            initialfile= " [BACKUP] " + file_name
        )
    else:
        path = tkFd.askdirectory(
                title= "Backup Dir Destiny",
                mustexist= False,
                initialdir= " [BACKUP] " + file_name
            )
        
    return Path(path)

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
                    origin = get_file_origin()
                    if origin == Path():
                        print("The file was not added.")
                        return
                    
                    destiny = get_file_destiny(origin)
                    if destiny == Path():
                        print("The file was not added.")
                        return
                    
                    new_file = BackupFile(origin, destiny)
                    
                    all_lists.selected.add(new_file)
                    print(f"The file \"{new_file.origin.name}\" was added to the list.")
                    logging.info(f"The file \"{new_file.origin.name}\" was added to the list.")
                    
                case "dir":
                    compress = enter[2] in ("--compress", "-c")
                    
                    origin = get_dir_origin()
                    if origin == Path():
                        print("The dir was not added.")
                        return
                    
                    destiny = get_dir_destiny(zip_file= compress, file_name= origin.name)
                    if destiny == Path():
                        print("The dir was not added.")
                        return
                    
                    new_dir = BackupDir(origin, destiny, compress= compress)
                    
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
            print(f"Creating backups of {all_lists.selected.total_files} files...")
            for file_name, result, _ in all_lists.selected.backup_all():
                if result:
                    print(f"\"{file_name}\" was successfully copied.")
                    logging.info(f"\"{file_name}\" was successfully copied.")
                else:
                    print(f"\"{file_name}\" cannot be copied.")
                    logging.info(f"\"{file_name}\" cannot be copied.")
                    
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