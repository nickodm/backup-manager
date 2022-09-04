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
from sys import exit as sys_exit
import tkinter.filedialog as tkFd

__version__ = "0.1.1"

all_lists = AllLists()

def exit():
    all_lists.save()
    sys_exit()
    
def clear_terminal():
    from os import system
    from sys import platform
    system("cls" if platform == "win32" else "clear")
    
def prompt(prompt:str = "", *, extension:int = 12):
    try:
        enter = input(prompt)
    except (KeyboardInterrupt, EOFError) as exc:
        if isinstance(exc, KeyboardInterrupt):
            print("^C")
        
        print("Saving list...")
        print("Exiting...")
        exit()

    if enter.isspace() or enter == "":
        enter = [""]
    else:
        enter = enter.split()
    
    # Fill the list with empty strings
    for _ in range(extension - len(enter)):
        enter.append("")

    return enter

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
        title= "Seleccionar Ruta para Respaldar",
        initialfile= "[BACKUP] " + origin_path.name,
        defaultextension= origin_path.suffix,
        filetypes= (("*" + origin_path.suffix, origin_path.suffix), 
        )
    )

    return Path(path)
    
def get_file_origin():
    path = tkFd.askopenfilename(
        title= "Seleccionar Archivo a Respaldar",
        filetypes= (
            ("Cualquier Archivo", "*.*"), 
        )
    )

    return Path(path)

def get_dir_origin():
    path = tkFd.askdirectory(
        title= "Seleccionar Directorio a Respaldar",
        mustexist= True
    )
    
    return Path(path)

def get_dir_destiny(*, zip_file:bool = False, file_name:str = ""):
    if zip_file:
        path = tkFd.asksaveasfilename(
            title= "Seleccionar Archivo de Destino",
            filetypes= (("Archivo ZIP", "*.zip"), ),
            defaultextension= "*.zip",
            initialfile= " [BACKUP] " + file_name
        )
    else:
        path = tkFd.askdirectory(
                title= "Seleccionar Directorio de Destino",
                mustexist= False,
                initialdir= " [BACKUP] " + file_name
            )
        
    return Path(path)

def main():
    enter = prompt(f"[{all_lists.selected_index}] >> ")
    
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
                    compress = enter[2].lower() in ("--compress", "-c")
                    
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
            if enter[1] == "":
                print("You must input a number next to the word 'del'.")
                return
            elif not enter[1].isdigit():
                print("You must input a real number.")
                return
            
            enter[1] = int(enter[1])

            if len(all_lists.selected) <= enter[1] or enter[1] < 0:
                print(f"The index must be between 0 and {len(all_lists.selected) - 1}.")
                return
            
            deleted = all_lists.selected.pop(enter[1])

            print(f"The {deleted.type} \"{deleted.name}\" was deleted from the list.")
            logging.info(f"The {deleted.type} \"{deleted.name}\" was deleted from the list.")
        
        case "show":
            check_selected()
            print(all_lists.selected.report())
        
        case "backup":
            check_selected()
            print(f"Creating backups of {len(all_lists.selected)} files...")
            for file_name, result, _ in all_lists.selected.backup_all():
                if result:
                    print(f"\"{file_name}\" was successfully copied.")
                    logging.info(f"\"{file_name}\" was successfully copied.")
                else:
                    print(f"\"{file_name}\" cannot be copied.")
                    logging.info(f"\"{file_name}\" cannot be copied.")
                    
        case "restore":
            check_selected()
            print(f"Restoring {len(all_lists.selected)} files...")
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
                    if enter[2] == "":
                        print(all_lists.mention())
                        return
                    
                    index = check_index(enter[2])
                    
                    print(all_lists[index].report())
                    
                case "select":
                    index = check_index(enter[2])

                    print("The \"%s\" list was selected."%all_lists.select(index).name)
                    
                case "create":
                    name = " ".join(prompt("Enter a name for the list: "))
                    name = name.strip()

                    if name in ("exit", "cancel"):
                        print("The list was not created.")
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
                        print(f"Is \"{importing.name}\" the list?")
                        while True:
                            match prompt("[y|n] Confirm>> ")[0].lower():
                                case "y":
                                    break
                                
                                case "n":
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

                    print(f"The \"{all_lists.pop(index).name}\" list was removed.")
                    
                case "rename":
                    index = check_index(enter[2])
                    
                    print(f"Input a new name to \"{all_lists[index].name}\".")
                    new_name = " ".join(prompt(">> ")).strip()
                    
                    if new_name in map(lambda x: x.name, all_lists):
                        print(f"There is already a list named \"{new_name}\".")
                        return
                    
                    while True:
                        match prompt("[y|n] Confirm>> ")[0].lower():
                            case "y":
                                all_lists[index].name = new_name
                                print("The list was renamed.")
                                return
                            
                            case "n":
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
            clear_terminal()
        
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