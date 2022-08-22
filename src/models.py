"""
This module includes the classes and functions that will be used by the program.
----------
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
from zipfile import ZipFile
import abc, os, logging, sys, pickle
import typing as typ, tkinter.filedialog as tkFd

__all__ = ["BackupMeta", "BackupFile", "BackupDir", "PROJECT_DIR", "PathBackupArray", "get_file_origin", "get_file_destiny",
           "get_dir_origin", "get_dir_destiny"]

PROJECT_DIR:Path = Path(os.getenv("APPDATA") + "/Nicko's Backup Manager") if sys.platform == "win32" else Path.home() / ".Nicko's Backup Manager"

class BackupMeta(abc.ABC):
    def __init__(self, origin_path:Path, destiny_path:Path = ...) -> None:
        assert origin_path.exists()

        self._origin = origin_path
        self._destiny = destiny_path if destiny_path != Ellipsis else None
        
    @property
    def origin(self) -> Path:
        """
        The path of the origin file.
        """
        return self._origin
    
    @property
    def destiny(self) -> Path|None:
        """
        The path of the destiny of the backup.
        """
        return self._destiny
    
    @property
    def name(self) -> str:
        """
        The name of the origin file.
        """
        return self._origin.name
    
    @property
    def type(self) -> typ.Literal['dir', 'file']:
        """
        Whether the path is a dir or a file. Another way to know this is `isinstance(x, BackupFile/BackupDir)`
        """
        return "dir" if self._origin.is_dir() else "file"
    
    @abc.abstractmethod
    def backup(self) -> bool:
        """
        Backup the source.
        """
        pass

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
        
        report += (" " + self.name[:32] + " ").center(underlines, "-") + "\n"
        report += f"ORIGIN\t: {self._origin}\n"
        report += f"DESTINY\t: {self._destiny}\n"
        report += f"TYPE\t: {self.type.upper()}\n"
        report += "-" * 72
        
        return report
    
    def __getstate__(self):
        state = {
            "origin_path": self._origin,
            "destiny_path": self._destiny
        }
        return state
    
    def __setstate__(self, state:dict):
        self.__init__(**state)

class BackupFile(BackupMeta):
    def backup(self) -> bool:
        try:
            with self._origin.open("rb") as file, self._destiny.open("wb") as backup:
                for line in file.readlines():
                    backup.write(line)
        
            return True
        except BaseException as exc:
            logging.error(exc)
            return False
    
class BackupDir(BackupMeta):
    def __init__(self, origin_path: Path, destiny_path: Path = ..., *, compress:bool = False) -> None:
        super().__init__(origin_path, destiny_path)
        self._compress = compress
    
    @property
    def file_count(self) -> int:
        """
        The count of all the files in the directory.
        """
        count = 0
        for _, _, files in os.walk(self._origin):
            count += len(files)
            
        return count
    
    @property
    def compress(self) -> bool:
        """
        Whether the dir will be compressed.
        """
        return self._compress
    
    def backup(self) -> bool:
        if self._compress:
            return self._save_compressed()
        
        path_limit = 0
        try:
            for path, _, files in os.walk(self._origin):
                if path_limit == 0:
                    path_limit = len(Path(path).parts)
                
                for file in files:
                    destiny:Path = self._destiny / "/".join(Path(path).parts[path_limit:]) / file
                    if not destiny.parent.exists():
                        destiny.parent.mkdir(parents= True)
                    
                    BackupFile(Path(path).joinpath(file), destiny).backup()
        except BaseException as exc:
            logging.exception(exc)
            return False
        
        return True
                
    def report(self, index: int = ...) -> str:
        report = super().report(index).splitlines()
        report.insert(-1, f"FILES\t: {self.file_count}")
        report.insert(-1, f"COMPRESS: {self.compress}")
        
        return "\n".join(report)
    
    def _save_compressed(self) -> bool:
        """
        Save the dir in a compressed file in `self.destiny`.
        """
        if self._destiny.is_dir():
            destiny = self._destiny / (self._origin.name + ".zip")
        else:
            destiny = self._destiny
            
        try:        
            with ZipFile(destiny, "w") as zip_stream:
                path_limit = 0
                for path, _, files in os.walk(self._origin):
                    if path_limit == 0:
                        path_limit = len(Path(path).parts)
                    
                    for file in files:
                        with Path(path).joinpath(file) as read_path:
                                zip_stream.write(read_path, arcname= Path("/".join(read_path.parts[path_limit:])))
        except BaseException as exc:
            logging.exception(exc)
            return False
        
        return True
    
    def __getstate__(self):
        state = super().__getstate__()
        state['compress'] = self._compress
        return state

class PathBackupArray(typ.Sequence[BackupMeta]):
    """
    Base class for arrays of paths of files or directories that will be copied.
    """
    def __init__(self, name:str = "") -> None:
        self.name = name
        
        self._data:list[BackupMeta] = []
        
    @property
    def total_files(self):
        """
        The total of files in the array. It is not the same as 'len'.
        """
        total = len(self.files_only())
        for backup_dir in self.dirs_only():
            total += backup_dir.file_count
            
        return total        
        
    def add(self, value:BackupMeta) -> None:
        assert isinstance(value, BackupMeta), "'value' must be an instance of a subclass of BackupMeta."
        self._data.append(value)
        
    def clear(self) -> None:
        self._data.clear()
        
    def count(self, value:BackupMeta) -> int:
        return self._data.count(value)
    
    def index(self, value:BackupMeta) -> int:
        return self._data.index(value)
    
    def pop(self, index:BackupMeta) -> BackupMeta:
        return self._data.pop(index)
    
    def remove(self, value:BackupMeta) -> None:
        self._data.remove(value)
    
    def extend(self, iter:typ.Iterable[BackupMeta]):
        for i in iter:
            self.add(i)
    
    def backup_all(self) -> typ.Generator[tuple[str, bool, BackupMeta], None, None]:
        """
        Backup all the paths in the array.
        """
        logging.info(f"Starting backups of {self.name!r} ({len(self._data)} items)...")
        for meta in self._data:
            yield (meta.name, meta.backup(), meta)
        logging.info(f"The backup of {self.name!r} has ended.")
    
    def files_only(self) -> tuple[BackupFile]:
        """
        Return a copy of the array with BackupFiles only.
        """
        return tuple(filter(lambda x: isinstance(x, BackupFile), self._data))
    
    def dirs_only(self) -> tuple[BackupDir]:
        """
        Return a copy of the array with BackupDirs only.
        """
        
        return tuple(filter(lambda x: isinstance(x, BackupDir), self._data))
    
    def copy(self):
        """
        Return a copy of the array.
        """
        copy = PathBackupArray(self.name)
        copy._data = self._data.copy()
        return copy
    
    def save(self, *, path:Path = ...) -> None:
        """
        Save the array in a binary file.
        """
        if path == Ellipsis:
            path = PROJECT_DIR / "files"
        
        logging.info(f"Saving the array on '{path}'...")
        with path.open("wb") as stream:
            pickle.dump(self, stream)
        
    def load(self, *, path:Path = ...) -> None:
        """
        Load the array from a binary file.
        """
        if path == Ellipsis:
            path = PROJECT_DIR / "files"
        
        if not path.exists():
            logging.warning(f"The array from '{path}' wasn't loaded because the file doesn't exists.")
            return
        
        logging.info(f"Loading the array from '{path}'...")
        with path.open("rb") as stream:
            data = pickle.load(stream)
            if isinstance(data, type(self)):
                self._data = data._data
                self.name = data.name
                
    def report(self) -> str:
        """
        Return all the report of the BackupMeta's in the array in a string.
        """
        report = ""
        if len(self._data) == 0:
            return "The list of files is empty"
        
        for index, file in enumerate(self._data):
            report += file.report(index)
            
            # If the file is not the last in the list, print a space
            if self._data.index(file) < len(self._data) - 1:
                report += "\n"
        
        return report        
    
    def __iter__(self) -> typ.Iterator[BackupMeta]:
        return iter(self._data)
    
    def __getitem__(self, index) -> BackupMeta:
        return self._data[index]
    
    def __delitem__(self, index) -> None:
        self._data.pop(index)
        
    def __len__(self) -> int:
        return len(self._data)

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

def get_dir_destiny(*, zip_file:bool = False):
    if zip_file:
        path = tkFd.asksaveasfilename(
            title= "Seleccionar Archivo de Destino",
            filetypes= (("Archivo ZIP", "*.zip"), ),
            defaultextension= "*.zip"
        )
    else:
        path = tkFd.askdirectory(
                title= "Seleccionar Directorio de Destino",
                mustexist= False
            )
        
    return Path(path)