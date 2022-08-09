from pathlib import Path
import tkinter.filedialog as tkFd
import pickle, os, logging, sys

__version__ = "0.1.0"

PROJECT_DIR = Path(os.getenv("APPDATA") + "/Nicko's Backuper") if sys.platform == "win32" else Path.home() / ".Nicko's Backuper"

class BackupFile:
    def __init__(self, origin_path:Path, destiny_path:Path = ...) -> None:
        assert origin_path.exists()

        self.__origin = origin_path
        self.__destiny = destiny_path if destiny_path != Ellipsis else None
    
    @property
    def origin(self) -> Path:
        """
        The path of the origin file.
        """
        return self.__origin
    
    @property
    def destiny(self) -> Path|None:
        """
        The path of the destiny of the backup.
        """
        return self.__destiny
    
    @property
    def file_name(self) -> str:
        """
        The name of the origin file.
        """
        return self.__origin.name
    
    def backup(self) -> bool:
        """
        Backup the file.
        """
        try:
            with self.__origin.open("rb") as file, self.__destiny.open("wb") as backup:
                for line in file.readlines():
                    backup.write(line)
        
            return True
        except BaseException as exc:
            logging.error(exc)
            return False
        
    def report(self, index:int = ...) -> str:
        """
        Return a report about the origin and the destiny of the file.
        """
        report = ""
        underlines = 72
        
        if index != Ellipsis:
            index_str = f"[{index}] "
            report += index_str
            underlines -= len(index_str)
        
        report += (" " + self.file_name[:32] + " ").center(underlines, "-") + "\n"
        report += f"ORIGIN\t: {self.__origin}\n"
        report += f"DESTINY\t: {self.__destiny}\n"
        report += "-" * 72
        
        return report

file_list:list[BackupFile] = []

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
    
    match enter:
        case "exit":
            save_file_list()
            exit()
        
        case "add":
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
            print(f"The file \"{new_file.origin.name}\" was added to the list of files.")
            logging.info(f"The file \"{new_file.origin.name}\" was added to the list of files.")
        
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

            print(f"The file \"{deleted.file_name}\" was deleted from the list.")
            logging.info(f"The file \"{deleted.file_name}\" was deleted from the list.")
        
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
    
    logging.info("Starting program...")
    
    if not PROJECT_DIR.exists():
        logging.info("Creating the project directory...")
        PROJECT_DIR.mkdir()
        PROJECT_DIR.joinpath("logs").mkdir()

    load_file_list()
    while True:
        main()