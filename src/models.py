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
from concurrent.futures import ThreadPoolExecutor
from abc import ABC, abstractmethod
from consoletools import format_delta, format_number, format_size
import os, logging, sys, pickle, json
import typing as typ, datetime as dt, shutil as sh

__all__ = ["BackupMeta", "BackupFile", "BackupDir", "PROJECT_DIR", "ResourcesArray", "AllLists", "NextRoundAdvice", "all_lists"]
_AT = typ.TypeVar("_AT")

PROJECT_DIR:Path = Path(os.getenv("APPDATA") + "/Nicko's Backup Manager") if sys.platform == "win32" else Path.home() / ".Nicko's Backup Manager"

class BackupMeta(ABC):
    def __init__(self, origin_path:Path, destiny_path:Path) -> None:
        self._origin = origin_path
        self._destiny = destiny_path
        self._last_backup:dt.datetime|None = None
        
    @classmethod
    def from_dict(cls, dictt:dict):
        self = object.__new__(cls)
        self._origin = Path(dictt['origin_path'])
        self._destiny = Path(dictt['destiny_path'])
        if dictt.get('last', None):
            self._last_backup = dt.datetime.fromtimestamp(dictt['last'])
        else:
            self._last_backup = None
        
        return self
        
    @property
    def origin(self) -> Path:
        """
        The path of the origin resource.
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
        The name of the origin resource.
        """
        return self._origin.name
    
    @property
    def type(self) -> typ.Literal['dir', 'file']:
        """
        Whether the path is a dir or a file. Another way to know this is `isinstance(x, BackupFile/BackupDir)`
        """
        from re import fullmatch
        return fullmatch("Backup(\w+)", type(self).__name__).group(1).lower()

    @property
    def last_backup(self) -> dt.datetime|None:
        """
        The last time when the resource was backed up.
        """
        return self._last_backup
    
    @property
    @abstractmethod
    def resource_size(self) -> int:
        """
        The size of the resource in bytes.
        """
        pass
    
    @abstractmethod
    def backup(self, force:bool = False) -> bool:
        """
        Backup the resource.
        """
        pass
    
    @abstractmethod
    def restore(self, force:bool = False) -> bool:
        """
        Restore the resource.
        """
        pass

    @abstractmethod
    def are_different(self, strict:bool = False) -> bool:
        """
        Check if the origin and destiny resources are different.
        """
        pass
    
    def report(self, index:int = ...) -> str:
        """
        Return a report about the origin and the destiny of the file.
        """
        report = ""
        underlines = 72
        
        if index != Ellipsis:
            index_str = f"[{format_number(index)}] "
            report += index_str
            underlines -= len(index_str)
        
        report += (" " + self.name[:32] + " ").center(underlines, "-") + "\n"
        report += f"ORIGIN\t: {self._origin}\n"
        report += f"DESTINY\t: {self._destiny}\n"
        report += f"TYPE\t: {self.type.upper()}\n"
        report += f"SIZE\t: {format_size(self.resource_size)}\n"
        
        if self.last_backup != None:
            diff = dt.datetime.now() - self._last_backup
            report += f"LAST\t: {self._last_backup.strftime('%B %d, %Y; %H:%M:%S')} ({format_delta(diff)} ago)\n"
        else:
            report += "LAST\t: N/A\n"
        
        report += "-" * 72
        
        return report
    
    def to_dict(self) -> dict:
        """
        Return self represented in a dict.
        """
        return {
            "origin_path": os.fspath(self._origin),
            "destiny_path": os.fspath(self._destiny),
            "type": self.type,
            "last": self._last_backup.timestamp()
        }    
    
    def __getstate__(self):
        state = {
            "for_init": {
                "origin_path": self._origin,
                "destiny_path": self._destiny
            },
            "type": self.type,
            "last": self._last_backup
        }
        return state
    
    def __setstate__(self, state:dict):
        if "for_init" in state.keys():
            self.__init__(**state['for_init'])
            self._last_backup = state.get('last', None)
        else: # Support for old versions
            if "origin_path" in state.keys() and "destiny_path" in state.keys():
                self.__init__(**state)
            self._last_backup = state.get('last', None)
            
    def __enter__(self):
        return self
    
    def __exit__(self, t, v, tck):
        logging.exception(v)
        
    def __str__(self):
        return self.report()
    
    def __repr__(self) -> str:
        return f"{type(self).__name__}(origin= {self._origin}, destiny= {self._destiny})"
    
    def __eq__(self, value):
        if isinstance(value, type(self)):
            return self._origin == value._origin and self._destiny == value._destiny
        
        return False
    
    def __ne__(self, value):
        return not self.__eq__(value)

class BackupFile(BackupMeta):
    @property
    def resource_size(self) -> int:
        return self._origin.stat(follow_symlinks= True).st_size
    
    def are_different(self, strict:bool = False) -> bool:
        if not (self._origin.exists() and self._destiny.exists()):
            return True
        
        if self._origin.stat().st_mtime == self._destiny.stat().st_mtime:
            return False
        
        if strict:
            with self._origin.open("rb") as ofp, self._destiny.open("rb") as dfp:
                for o_line, d_line in zip(ofp.readlines(), dfp.readlines()):
                    if o_line != d_line:
                        return True
                
        return False
    
    def backup(self, force:bool = False) -> bool:
        if not self._origin.exists():
            logging.warning("Tried to backup a resource that doesn't exits.")
            return False
        
        if not force and not self.are_different():
            logging.info(f"{self.name!r} has not been changed.")
            return False
        
        try:
            self._destiny.parent.mkdir(parents= True, exist_ok= True)
            sh.copy2(self._origin, self._destiny)
            self._last_backup = dt.datetime.now()
            logging.info(f"{self.name!r} was successfully backuped.")
            return True
        except BaseException as exc:
            logging.exception(exc)
            logging.info(f"{self.name!r} wasn't backuped.")
            return False
        
    def restore(self, force:bool = False) -> bool:
        if not self._destiny.exists():
            logging.warning("Tried to restore a backup that doesn't exists.")
            return False
        
        if not force and not self.are_different():
            logging.info(f"{self.name!r} has not been changed.")
            return False

        try:
            self._origin.parent.mkdir(parents= True, exist_ok= True)
            sh.copy2(self._destiny, self._origin)
            logging.info(f"{self._destiny.name!r} was successfully restored.")
            return True
        except BaseException as exc:
            logging.info(f"{self._destiny.name!r} wasn't restored.")
            logging.exception(exc)
            return False
    
class BackupDir(BackupMeta):
    def __init__(self, origin_path: Path, destiny_path: Path = ..., *, compress:bool = False) -> None:
        super().__init__(origin_path, destiny_path)
        self._compress = compress
        
    @classmethod
    def from_dict(cls, dictt: dict):
        self = super().from_dict(dictt)
        self._compress = dictt.get("compress", False)
        return self
        
    @property
    def resource_size(self) -> int:
        size = 0
        for path, _, files in os.walk(self._origin):
            for file in files:
                size += Path(path).joinpath(file).stat().st_size
            
        return size
    
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
    
    def are_different(self, strict:bool = False) -> bool:
        with ThreadPoolExecutor() as pool:
            return any(pool.map(lambda file: file.are_different(strict= strict), self._walk()))
    
    def backup(self, force:bool = False) -> bool:
        if not force and not self.are_different():
            logging.info(f"{self.name!r} has not been changed.")
            return False
        
        if self._compress:
            return self._save_compressed()
        
        try:
            for file in self._walk():        
                file.backup(force= force)
            
            self._last_backup = dt.datetime.now()
            return True
        except BaseException as exc:
            logging.exception(exc)
            return False 
    
    def restore(self, force:bool = False) -> bool:
        if not force and not self.are_different():
            logging.info(f"{self.name!r} has not been changed.")
            return False
        
        try:
            if self._destiny.is_dir():
                for file in self._walk('d'):
                    file.origin.parent.mkdir(parents= True, exist_ok= True)
                    file.restore()
                
                return True
            else:
                with ZipFile(self._destiny, "r") as zip_fp:
                    zip_fp.extractall(self._origin)
            
                return True
        except BaseException as exc:
            logging.exception(exc)
            return False

    def report(self, index: int = ...) -> str:
        report:list[str] = super().report(index).splitlines()
        report.insert(-1, f"FILES\t: {format_number(self.file_count)}")
        report.insert(-1, f"COMPRESS: {'Yes' if self._compress else 'No'}")
        
        return "\n".join(report)

    def to_dict(self) -> dict[str, typ.Any]:
        dictt:dict = super().to_dict()
        dictt['compress'] = self._compress
        return dictt
    
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
                        read_path = Path(path) / file
                        zip_stream.write(read_path, arcname= Path("/".join(read_path.parts[path_limit:])))

            return True 
        except BaseException as exc:
            logging.exception(exc)
            return False
    
    def _walk(self, target:typ.Literal['o', 'd'] = 'o') -> typ.Generator[BackupFile, None, None]:
        """
        Walk over the directory.
        """
        assert target in ('o', 'd')
        
        if target == "o":
            x, y = self._origin, self._destiny
        else:
            x, y = self._destiny, self._origin
        
        path_limit = 0
        for path, _, files in os.walk(x):
            if path_limit == 0:
                path_limit = len(Path(path).parts)
            
            for file in files:
                z:Path = y / "/".join(Path(path).parts[path_limit:]) / file
                if target == "o":
                    yield BackupFile(Path(path) / file, z)
                else:
                    yield BackupFile(z, Path(path) / file)

    def __getstate__(self):
        state = super().__getstate__()
        state['for_init']['compress'] = self._compress
        return state

    def __eq__(self, value) -> bool:
        return super().__eq__(value) and self._compress == value._compress

class ResourcesArray(typ.Sequence[BackupMeta]):
    """
    Base class for arrays of paths of files or directories that will be copied.
    """
    def __init__(self, name:str = "") -> None:
        self.name = name
        
        self._data:list[BackupMeta] = []
        
    @classmethod
    def from_import(cls, path:os.PathLike): 
        with open(path, "r") as fp:
            loaded:dict = json.load(fp)
        
        if not isinstance(loaded, dict):
            raise TypeError(
                "The loaded data is not a dict."
            )
                
        self = object.__new__(cls)
        self.name = loaded.get("list_name", "")
        
        self._data = []
        for dictt in loaded.get("content", []):
            dictt:dict
            if dictt['type'] == "dir":
                self._data.append(BackupDir.from_dict(dictt))
            elif dictt['type'] == "file":
                self._data.append(BackupFile.from_dict(dictt))
        
        return self        
        
    @property
    def total_files(self):
        """
        The total of files in the array. It is not the same as 'len'.
        """
        total = len(self.files_only())
        for backup_dir in self.dirs_only():
            total += backup_dir.file_count
            
        return total
    
    @property
    def total_size(self):
        """
        The size of all the resources in the array.
        """
        size = 0
        for meta in self._data:
            size += meta.resource_size
            
        return size
        
    def add(self, value:BackupMeta) -> None:
        assert isinstance(value, BackupMeta), "'value' must be an instance of a subclass of BackupMeta."
        self._data.append(value)
        
    @typ.overload
    def get(self, index:int) -> BackupMeta: ...
    @typ.overload
    def get(self, index:int, default:_AT = ...) -> BackupMeta|_AT: ...
        
    def get(self, index:int, default:_AT = ...):
        try:
            return self._data[index]
        except IndexError:
            if default != Ellipsis:
                return default
            raise
        
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
    
    def backup(self, index:int|slice = ..., *, force:bool = False) -> typ.Generator[tuple[bool, BackupMeta], None, None]:
        """
        Backup resources of the array.
        """
        if isinstance(index, int):
            index = slice(index, index + 1)
        elif index == Ellipsis:
            index = slice(0, None)
        
        data = self._data[index]
        
        logging.info(f"Starting backups of {self.name!r}...")
        for meta in data:
            yield (meta.backup(force= force), meta)
        logging.info(f"The backup of {self.name!r} has ended.")
        
    def restore(self, index:int|slice = ..., *, force:bool = False) -> typ.Generator[tuple[bool, BackupMeta], None, None]:
        """
        Restore resources of the array.
        """
        if isinstance(index, int):
            index = slice(index, index + 1)
        elif index == Ellipsis:
            index = slice(0, None)
        
        data = self._data[index]
        
        logging.info(f"Starting restore of {self.name!r}...")
        for meta in data:
            yield (meta.restore(force= force), meta)
        logging.info(f"The restoring of {self.name!r} has ended.")
    
    def files_only(self):
        """
        Return a copy of the array with files only.
        """
        new = ResourcesArray(self.name)
        new._data = list(filter(lambda x: isinstance(x, BackupFile), self._data))
        return new
    
    def dirs_only(self):
        """
        Return a copy of the array with dirs only.
        """
        new = ResourcesArray(self.name)
        new._data = list(filter(lambda x: isinstance(x, BackupDir), self._data))
        return new

    def copy(self):
        """
        Return a copy of the array.
        """
        copy = ResourcesArray(self.name)
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
        Return all the reports of the resources in the array in a string.
        """
        report = ""
        if len(self._data) == 0:
            return "The list is empty"
        
        for index, file in enumerate(self._data):
            report += file.report(index)
            
            # If the file is not the last in the list, print a space
            if self._data.index(file) < len(self._data) - 1:
                report += "\n"
                
        report += f"\n\nTOTAL FILES: {format_number(self.total_files)}\n"
        report += f"TOTAL SIZE:  {format_size(self.total_size)}"
        
        return report
    
    def export(self, destiny:os.PathLike) -> None:
        """
        Serialize the Array to a json object.
        """
        with open(destiny, "w") as fp:
            json.dump({
                "list_name": self.name,
                "content": [meta.to_dict() for meta in self._data]
            }, fp, indent= 4)
    
    def __iter__(self) -> typ.Iterator[BackupMeta]:
        return iter(self._data)
    
    def __getitem__(self, index) -> BackupMeta:
        return self._data[index]
    
    def __delitem__(self, index) -> None:
        self._data.pop(index)
        
    def __len__(self) -> int:
        return len(self._data)
    
    def __contains__(self, value: object) -> bool:
        if isinstance(value, BackupMeta):
            return (value._origin, value._destiny) in map(lambda x: (x._origin, x._destiny), self._data)

        return False
    
    def __repr__(self) -> str:
        return type(self).__name__ + f"(name= {self.name})"
    
# Convert PathBackupArrays to ResourcesArrays
class PathBackupArray(ResourcesArray):
    def __new__(cls):
        return super().__new__().copy()

class AllLists():
    def __init__(self) -> None:
        self._data:list[ResourcesArray] = []
        self._selected = None
        
    @property
    def selected(self) -> ResourcesArray|None:
        """
        The list that is selected.
        """
        return self._selected
    
    @property
    def selected_index(self) -> str:
        """
        The index of the selected list.
        """
        if self._selected == None:
            return "X"
        
        return str(self._data.index(self._selected))
        
    def load(self):
        if not PROJECT_DIR.joinpath("all_lists").exists():
            return
        
        with PROJECT_DIR.joinpath("all_lists").open("rb") as fp:
            data:AllLists = pickle.load(fp)
            if isinstance(data, AllLists) and isinstance(data._data, list):
                self._data = data._data
                self._selected = data._selected
    
    def save(self):
        with PROJECT_DIR.joinpath("all_lists").open("wb") as fp:
            pickle.dump(self, fp)
    
    def add(self, value:ResourcesArray):
        assert isinstance(value, ResourcesArray)
        new = self.__check_repetition(value)
        self._data.append(new)
        if len(self._data) == 1 and self._selected == None:
            self._selected = new
    
    def get(self, index:int, default:ResourcesArray = ...) -> ResourcesArray:
        try:
            return self._data[index]
        except:
            if default != Ellipsis:
                return default
            
            raise
    
    def pop(self, index:int) -> ResourcesArray|None:
        if self._data[index] is self._selected:
            self._selected = None
        return self._data.pop(index)

    def remove(self, value:ResourcesArray):
        if value == self._selected:
            self._selected = None
        return self._data.remove(value)
    
    def index(self, value:ResourcesArray) -> int:
        return self._data.index(value)
    
    def mention(self) -> str:
        """
        Mention all the lists that are in the list.
        """
        if len(self._data) == 0:
            return "There are not lists."

        string = ""

        for index, array in enumerate(self._data):
            string += "[%s] - \"%s\""%(format_number(index), array.name[:32])
            if len(array.name) >= 32:
                string += "...,"
                
            string += " | %s elements"%format_number(len(array))
            
            if index + 1 < len(self._data):
                string += "\n"
        
        return string
    
    def select(self, index:int) -> ResourcesArray:
        """
        Select a list and return it.
        """
        self._selected = self._data[index]
        return self._selected
    
    def __check_repetition(self, value:ResourcesArray):
        if value.name in map(lambda x: x.name, self._data):
            raise RepeteanceError(
                "The list is repeated."
            )
        
        return value
                
    def __getitem__(self, index):
        return self._data[index]
    
    def __len__(self):
        return len(self._data)
    
    def __iter__(self):
        return iter(self._data)
    
    def __contains__(self, value):
        if isinstance(value, ResourcesArray):
            return value.name in map(lambda x: x.name, self._data)

        return False
    
all_lists = AllLists()    

#* ----------------------
#*      EXCEPTIONS
#* ----------------------

class NotAFileError(OSError):
    """
    The operation works in files only.
    """
    pass

class RepeteanceError(Exception):
    """
    The value is repeated.
    """
    pass

class NextRoundAdvice(Exception):
    """
    Exception to jump to the next round of the mainloop.
    """
    pass