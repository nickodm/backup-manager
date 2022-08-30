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

__version__ = "0.1.1"

main_list = ResourcesArray("main")

all_lists = AllLists()

def exit():
    main_list.save()
    all_lists.save()
    sys_exit()
    
def prompt(prompt:str = ""):
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
    for _ in range(6 - len(enter)):
        enter.append("")

    return enter

def main():
    
    enter = prompt(">> ")
    
    match enter[0]:
        case "exit":
            print("Saving list...")
            print("Exiting...")
            exit()
        
        case "add":            
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
                    
                    main_list.add(new_file)
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
                    
                    main_list.add(new_dir)
                    print(f"The dir \"{new_dir.origin.name}\" was added to the list.")
                    logging.info(f"The dir \"{new_dir.origin.name}\" was added to the list.")            
                    
                case _:
                    print("You must add \"file\" or \"dir\".")
        
        case "del":
            if enter[1] == "":
                print("You must input a number next to the word 'del'.")
                return
            elif not enter[1].isdigit():
                print("You must input a real number.")
                return
            
            enter[1] = int(enter[1])

            if len(main_list) <= enter[1] or enter[1] < 0:
                print(f"The index must be between 0 and {len(main_list) - 1}.")
                return
            
            deleted = main_list.pop(enter[1])

            print(f"The {deleted.type} \"{deleted.name}\" was deleted from the list.")
            logging.info(f"The {deleted.type} \"{deleted.name}\" was deleted from the list.")
        
        case "show":
            print(main_list.report())
        
        case "backup":
            print(f"Creating backups of {len(main_list)} files...")
            for file_name, result, _ in main_list.backup_all():
                if result:
                    print(f"\"{file_name}\" was successfully copied.")
                    logging.info(f"\"{file_name}\" was successfully copied.")
                else:
                    print(f"\"{file_name}\" cannot be copied.")
                    logging.info(f"\"{file_name}\" cannot be copied.")
                    
        case "restore":
            print(f"Restoring {len(main_list)} files...")
            for file_name, result, _ in main_list.restore_all():
                if result:
                    print(f"\"{file_name}\" was successfully copied.")
                    logging.info(f"\"{file_name}\" was successfully copied.")
                else:
                    print(f"\"{file_name}\" cannot be copied.")
                    logging.info(f"\"{file_name}\" cannot be copied.")
                    
        case "list":
            match enter[1]:
                case "show":
                    print(all_lists.mention())
                    
                case "select":
                    ...
                    
                case "create":
                    name = "".join(prompt("Enter a name for the list: "))
                    if name in ("exit", "cancel"):
                        print("The list was not created.")
                        return
                    
                    all_lists.add(ResourcesArray(name))
                    print(f"Created list \"{name}\".")
                    
                case "import":
                    ...
                    
                case "export":
                    ...
                    
                case "remove":
                    ...
                    
                case _:
                    ...
                    
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
    main_list.load()
    
    while True:
        main()