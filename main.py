from pathlib import Path
import tkinter.filedialog as tkFd
import pickle, logging
from ctypes import windll
from models import *

windll.shcore.SetProcessDpiAwareness(1)

__version__ = "0.1.0"

file_list:list[BackupMeta] = []

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

def save_file_list():
    """
    Save the list of files.
    """
    print("Saving list of files...")
    logging.info("Saving the file list...")
    with PROJECT_DIR.joinpath("files").open("wb") as stream:
        pickle.dump(file_list, stream)

def load_file_list():
    """
    Load the list of files.
    """
    global file_list
    
    if not PROJECT_DIR.joinpath("files").exists():
        return
    
    print("Loading list of files...")
    logging.info("Loading the file list...")
    
    with PROJECT_DIR.joinpath("files").open("rb") as stream:
        data = pickle.load(stream)
        if isinstance(data, list):
            file_list = data.copy()

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
            save_file_list()
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
                    
                    file_list.append(new_file)
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
                    
                    new_dir = BackupDir(origin, destiny)
                    
                    file_list.append(new_dir)
                    print(f"The dir \"{new_dir.origin.name}\" was added to the list.")
                    logging.info(f"The dir \"{new_dir.origin.name}\" was added to the list.")            
                    
                case _:
                    print("You must add \"file\" or \"dir\".")
        
        case "del":
            del_index = input("What index you want to delete?: ")
            
            if not del_index.isdigit():
                print("You must input a real number.")
                return
            
            del_index = int(del_index)

            if len(file_list) <= del_index or del_index < 0:
                print(f"The index must be between 0 and {len(file_list) - 1}.")
                return
            
            deleted = file_list.pop(del_index)

            print(f"The file \"{deleted.name}\" was deleted from the list.")
            logging.info(f"The file \"{deleted.name}\" was deleted from the list.")
        
        case "show":
            if len(file_list) == 0:
                print("The list of files is empty.")
            
            for file in file_list:
                print(file.report(file_list.index(file)))
                
                # If the file is not the last in the list, print a space
                if file_list.index(file) < len(file_list) - 1:
                    print()
        
        case "backup":
            print(f"Creating backups of {len(file_list)} files...")
            logging.info("Starting backups...")
            for file in file_list:
                if file.backup():
                    print(f"The file \"{file.origin.name}\" was successfully copied.")
                    logging.info(f"The file \"{file.origin.name}\" was successfully copied.")
                else:
                    print(f"The file \"{file.origin.name}\" cannot be copied.")
                    logging.info(f"The file \"{file.origin.name}\" cannot be copied.")
            logging.info("Backups finished.")
                    
        case _:
            print("Unknown command")

if __name__ == "__main__":
    logging.basicConfig(filename= PROJECT_DIR / "logs" / "Nicko's Backuper Last Log.log", level= logging.INFO, 
                        format= "[%(asctime)s] %(levelname)s: %(message)s", datefmt= "%b %d, %Y %H:%M:%S")
    
    logging.info("Starting...")
    
    if not PROJECT_DIR.exists():
        logging.info("Creating the project directory...")
        PROJECT_DIR.mkdir()
        PROJECT_DIR.joinpath("logs").mkdir()

    load_file_list()
    while True:
        main()