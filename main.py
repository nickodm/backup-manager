from pathlib import Path
import tkinter.filedialog as tkFd
import logging
from ctypes import windll
from models import *

__version__ = "0.1.0"

main_list = PathBackupArray("main")

def ask_origin_file():
    path = tkFd.askopenfilename(
        title= "Seleccionar Archivo a Copiar",
        filetypes= (
            ("Cualquier Archivo", "*.*"), 
        )
    )
    
    return Path(path)

def ask_destiny_file(origin_path:Path):
    path = tkFd.asksaveasfilename(
        title= "Seleccionar Ruta para Respaldar",
        initialfile= "[BACKUP] " + origin_path.name,
        defaultextension= origin_path.suffix,
        filetypes= (("*" + origin_path.suffix, origin_path.suffix), )
    )
    
    return Path(path)

def main():
    enter = input(">> ")
    if enter.isspace() or enter == "":
        enter = [""]
    else:
        enter = enter.split()
    
    # Fill the list with empty strings
    for _ in range(6 - len(enter)):
        enter.append("")
    
    match enter[0]:
        case "exit":
            print("Saving list...")
            main_list.save()
            print("Exiting...")
            exit()
        
        case "add":            
            match enter[1]:
                case "file":
                    origin = ask_origin_file()
                    if origin == Path():
                        print("The file was not added.")
                        return
                    
                    destiny = ask_destiny_file(origin)
                    if destiny == Path():
                        print("The file was not added.")
                        return
                    
                    new_file = BackupFile(origin, destiny)
                    
                    main_list.add(new_file)
                    print(f"The file \"{new_file.origin.name}\" was added to the list.")
                    logging.info(f"The file \"{new_file.origin.name}\" was added to the list.")
                    
                case "dir":
                    origin = Path(tkFd.askdirectory(title= "Seleccionar Directorio a Respaldar", mustexist= True))
                    if origin == Path():
                        print("The dir was not added.")
                        return
                    
                    destiny = Path(tkFd.askdirectory(title= "Seleccionar Directorio de Destino", mustexist= False))
                    if destiny == Path():
                        print("The dir was not added.")
                        return
                    
                    new_dir = BackupDir(origin, destiny, compress= enter[2].lower() in ("--compress", "-c"))
                    
                    main_list.add(new_dir)
                    print(f"The dir \"{new_dir.origin.name}\" was added to the list.")
                    logging.info(f"The dir \"{new_dir.origin.name}\" was added to the list.")            
                    
                case _:
                    print("You must add \"file\" or \"dir\".")
        
        case "del":
            if enter[1] == "":
                print("You must input a number next to the word 'del'.")
                return
            
            if not enter[1].isdigit():
                print("You must input a real number.")
                return
            
            enter[1] = int(enter[1])

            if len(main_list) <= enter[1] or enter[1] < 0:
                print(f"The index must be between 0 and {len(main_list) - 1}.")
                return
            
            deleted = main_list.pop(enter[1])

            print(f"The file \"{deleted.name}\" was deleted from the list.")
            logging.info(f"The file \"{deleted.name}\" was deleted from the list.")
        
        case "show":
            print(main_list.report())
        
        case "backup":
            print(f"Creating backups of {len(main_list)} files...")
            for file_name, result, file_instance in main_list.backup_all():
                if result:
                    print(f"The file \"{file_name}\" was successfully copied.")
                    logging.info(f"The file \"{file_name}\" was successfully copied.")
                else:
                    print(f"The file \"{file_name}\" cannot be copied.")
                    logging.info(f"The file \"{file_name}\" cannot be copied.")
            
        case _:
            print("Unknown command")

if __name__ == "__main__":
    windll.shcore.SetProcessDpiAwareness(1) # To avoid blurred windows

    logging.basicConfig(filename= PROJECT_DIR / "logs" / "Nicko's Backuper Last Log.log", level= logging.INFO, 
                        format= "[%(asctime)s] %(levelname)s: %(message)s", datefmt= "%b %d, %Y %H:%M:%S")
    
    logging.info("Starting...")
    
    if not PROJECT_DIR.exists():
        logging.info("Creating the project directory...")
        PROJECT_DIR.mkdir()
        PROJECT_DIR.joinpath("logs").mkdir()

    print("Loading list...")
    main_list.load()
    while True:
        main()