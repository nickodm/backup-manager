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

from pathlib import Path, PurePath
from abc import ABC, abstractmethod
from consoletools import format_delta, format_number, format_size
import os, logging, sys, pickle, json, zipfile
import typing as typ, datetime as dt, shutil as sh

__all__ = ["BackupMeta", "BackupFile", "BackupDir", "PROJECT_DIR", "ResourcesArray", "all_lists"]
_AT = typ.TypeVar("_AT")

PROJECT_DIR:Path = Path(os.getenv("APPDATA") + "/Nicko's Backup Manager") if sys.platform == "win32" else \
    Path.home() / ".Nicko's Backup Manager"

class BackupMeta(ABC):
    
    __slots__ = ['_origin', '_destiny', '_last_backup', '_hash']
    
    def __init__(self, origin_path:Path, destiny_path:Path) -> None:
        self._origin = origin_path
        self._destiny = destiny_path
        self._last_backup:dt.datetime|None = None
        self._hash:int|None = None
        
    @classmethod
    def from_dict(cls, dictt:dict):
        self = object.__new__(cls)
        self._origin = Path(dictt['origin_path'])
        self._destiny = Path(dictt['destiny_path'])
        if dictt.get('last', None) and dictt['last']:
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
    def size(self) -> int:
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
    
    def exists(self) -> tuple[bool, bool]:
        """
        Return a tuple representing the existence of the origin and the destiny (in that order) of the resource.
        """
        return self.origin.exists(), self.destiny.exists()
    
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
        report += f"SIZE\t: {format_size(self.size)}\n"
        
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
            "last": self._last_backup.timestamp() if isinstance(self._last_backup, dt.datetime) else None
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
        
    def __hash__(self):
        return hash((self.type, self.origin, self.destiny))    

    def __repr__(self) -> str:
        return f"{type(self).__name__}(origin= {self._origin}, destiny= {self._destiny})"
    
    def __eq__(self, value):
        if isinstance(value, type(self)):
            return self._origin == value._origin and self._destiny == value._destiny
        
        return False
    
    def __ne__(self, value):
        return not self.__eq__(value)

class BackupFile(BackupMeta):

    __slots__ = BackupMeta.__slots__ + ['_at']
    
    def __hash__(self):
        if self._hash:
            return self._hash
        self._hash = hash((super().__hash__(), self.at))
        return self._hash
    
    def __init__(self, origin_path: Path, destiny_path: Path) -> None:
        super().__init__(origin_path, destiny_path)
        self._at:PurePath|None = None
        
    @classmethod
    def in_dir(cls, origin_path:Path, destiny_path:Path, at_path:str|PurePath):
        self = object.__new__(cls)
        self.__init__(origin_path, destiny_path)
        self._at:PurePath = at_path if isinstance(at_path, PurePath) else PurePath(at_path)
        return self
    
    @classmethod
    def from_dict(cls, dictt: dict):
        self = super().from_dict(dictt)
        self._at = dictt.get('at_path', None)
        return self
    
    def to_dict(self) -> dict:
        dictt = super().to_dict()
        dictt['at_path'] = self._at
        return dictt
    
    @property
    def at(self) -> PurePath|None:
        """
        The path of the file relative to the parent directory.
        """
        return self._at
    
    def exists(self) -> tuple[bool, bool]:
        exists = super().exists()
        if not self.is_extfile():
            return exists
        exists = list(exists)
        exists[1] = zipfile.Path(self.destiny, self.at.as_posix()).exists()
        return tuple(exists)
    
    @property
    def size(self) -> int:
        return self._origin.stat(follow_symlinks= True).st_size
    
    def is_extfile(self) -> bool:
        """
        Check if the file is in a zipfile.
        """
        return (zipfile.is_zipfile(self.destiny) or self.destiny.suffix == '.zip') and bool(self.at)

    def are_different(self, strict:bool = False) -> bool:
        from math import trunc
        if not (self._origin.exists() and self._destiny.exists()):
            return True
        
        origin_mtime = dt.datetime.fromtimestamp(trunc(self._origin.stat().st_mtime))
        destiny_mtime = dt.datetime.fromtimestamp(trunc(self._destiny.stat().st_mtime))
        
        dfp = self._destiny.open('rb')
        
        if zipfile.is_zipfile(self._destiny):
            at_path = self._at.as_posix()
            with zipfile.ZipFile(self._destiny) as fp:
                if not at_path in fp.namelist():
                    return True # The file doesn't exists.
                destiny_mtime = dt.datetime(*fp.getinfo(at_path).date_time)
                dfp.close()
                dfp = fp.open(at_path, 'r')
        
        # Check the mtime diff
        if -1 < (origin_mtime - destiny_mtime).total_seconds() > 1:
            return True        
        
        if strict:
            with dfp, self._origin.open("rb") as ofp:
                if ofp.read() != dfp.read():
                    return True
        
        dfp.close()
        return False
    
    def backup(self, force:bool = False) -> bool: #TODO: Implement ext-file support.
        if self.is_extfile():
            logging.info("Tried to backup an ext-file.")
            return False
        
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
        
    def restore(self, force:bool = False) -> bool: #TODO: Implement ext-file support.
        if self.is_extfile():
            logging.info("Tried to restore an ext-file.")
            return False

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
        
    def report(self, index: int = ...) -> str:
        r = super().report(index)
        if not self._at:
            return r
        from re import sub
        return sub("(?=DESTINY\s:\s)(.*)\n", fr"\1 | {repr(str(self._at))[1:-1]}\n", r)
        
    def __repr__(self) -> str:
        if not self._at:
            return super().__repr__()
        return super().__repr__()[:-1] + f", at_path= {self._at})"
    
    def __eq__(self, value):
        return super().__eq__(value) and self._at == value._at
    
    def __getstate__(self):
        state = super().__getstate__()
        state['at_path'] = self._at
        return state
    
    def __setstate__(self, state: dict):
        super().__setstate__(state)
        self._at = state.get('at_path', None)
    
class BackupDir(BackupMeta):
    
    __slots__ = BackupMeta.__slots__ + ['_compress']
    
    def __hash__(self):
        if self._hash:
            return self._hash
        self._hash = hash((super().__hash__(), self._compress))
        return self._hash
    
    def __init__(self, origin_path: Path, destiny_path: Path = ..., *, compress:bool = False) -> None:
        assert origin_path.suffix != ".zip"
        super().__init__(origin_path, destiny_path)
        self._compress = compress
        
    @classmethod
    def from_dict(cls, dictt: dict):
        self = super().from_dict(dictt)
        self._compress = dictt.get("compress", False)
        return self
        
    @property
    def size(self) -> int:
        size = 0
        for file in self.walk():
            size += file.size
            
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
    
    def get(self, at_path:str|PurePath, *, source:typ.Literal['o', 'd'] = ...) -> BackupFile|None:
        """
        Get a file of the directory. Return `None` if it doesn't exists or if it's a dir.
        """
        o = self._get_source(source)
        at_path = PurePath(at_path)
        
        if zipfile.is_zipfile(o):
            with zipfile.ZipFile(o) as fp:
                if not at_path.as_posix() in fp.namelist() or fp.getinfo(at_path.as_posix()).is_dir():
                    return
                
                return BackupFile.in_dir(self._origin / at_path, self._destiny, at_path)
        else:
            if not o.joinpath(at_path).exists() or o.joinpath(at_path).is_dir():
                return
            
            return BackupFile.in_dir(self._origin / at_path, 
                                     self._destiny / (at_path if self.destiny.suffix != '.zip' else ''), 
                                     at_path)

    def __getitem__(self, at_path:str|PurePath):
        return self.get(at_path)

    def are_different(self, strict:bool = False) -> bool:
        if not (self._origin.exists() and self._destiny.exists()):
            return True
        
        for file in self.walk():
            if file.are_different(strict= strict):
                return True
            
        return False    
    
    def backup(self, force:bool = False, falses:typ.Literal['ignore', 'return'] = 'return') -> bool:
        falses = falses.lower()
        assert falses in ('ignore', 'return')
        if not force and not self.are_different():
            logging.info(f"{self.name!r} has not been changed.")
            return False
        
        if self._compress:
            return self._save_compressed()
    
        try:
            for file in self.walk('o'):
                file.destiny.parent.mkdir(parents= True, exist_ok= True)
                if not file.backup(force) and falses == 'return':
                    return False
                
            self._last_backup = dt.datetime.now()
            return True
        except BaseException as exc:
            logging.exception(exc)
            return False 
    
    def restore(self, force:bool = False, falses:typ.Literal['ignore', 'return'] = 'return') -> bool:
        falses = falses.lower()
        assert falses in ('ignore', 'return')
        if not force and not self.are_different():
            logging.info(f"{self.name!r} has not been changed.")
            return False
        
        try:
            if self._destiny.is_dir():
                for file in self.walk('d'):
                    file.origin.parent.mkdir(parents= True, exist_ok= True)
                    if not file.restore() and falses == 'return':
                        return False
                
                return True
            else:
                with zipfile.ZipFile(self._destiny) as zip_fp:
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
            with zipfile.ZipFile(destiny, "w") as zip_stream:
                for path, _, files in os.walk(self._origin):
                    for file in files:
                        zip_stream.write(Path(path) / file, (Path(path) / file).relative_to(self._origin))
            
            self._last_backup = dt.datetime.now()
            return True 
        except BaseException as exc:
            logging.exception(exc)
            return False
    
    def walk(self, source:typ.Literal['o', 'd'] = ...) -> typ.Generator[BackupFile, None, None]:
        """
        Walk over the directory.
        """
        src = self._get_source(source)
        logging.info(f"Walking; name= {self.name}, src= {src} ({'o' if src is self._origin else 'd'})")
        
        if zipfile.is_zipfile(src):
            with zipfile.ZipFile(src) as fp:
                for file in fp.namelist():
                    if fp.getinfo(file).is_dir():
                        continue
                    
                    yield BackupFile.in_dir(self._origin / file, self._destiny, PurePath(file))
        else:
            for path, dirs, files in os.walk(src):              
                for file in files:
                    at = PurePath(path).joinpath(file).relative_to(src)
                    yield BackupFile.in_dir(self._origin / at,
                                            self._destiny / (at if not self.destiny.suffix == '.zip' else ''), 
                                            at)
    @typ.overload
    def where(self, 
              filter:typ.Callable[[BackupFile], bool],
              *, source:typ.Literal['o', 'd'] = ...
    ) -> typ.Generator[BackupFile, None, None]: ...
    @typ.overload
    def where(self, 
              filter:typ.Callable[[BackupFile], bool],
              mapper:typ.Callable[[BackupFile], _AT] = ..., 
              *, source:typ.Literal['o', 'd'] = ...
    ) -> typ.Generator[_AT, None, None]: ...
    
    def where(self, 
              filter:typ.Callable[[BackupFile], bool],
              mapper:typ.Callable[[BackupFile], _AT] = ..., 
              *, source:typ.Literal['o', 'd'] = ...
    ):
        """
        Apply `mapper` to each file that returns `True` when passed to `filter` and yield it. If there are not a `mapper`, 
        it will yield the `BackupFile`.
        """
        if mapper == Ellipsis:
            mapper = lambda file: file
        
        for file in self.walk(source):
            if filter(file):
                yield mapper(file)

    def __iter__(self):
        return self.walk()
        
    def __getstate__(self):
        state = super().__getstate__()
        state['for_init']['compress'] = self._compress
        return state

    def __eq__(self, value) -> bool:
        return super().__eq__(value) and self._compress == value._compress
    
    def __repr__(self) -> str:
        return super().__repr__()[:-1] + f", compress= {self._compress})"
    
    def __contains__(self, value:str|BackupFile|PurePath):
        assert isinstance(value, (str, BackupFile, PurePath)), \
            f"The value must be an str, BackupFile or Path (an at path), not {type(value).__name__}."
        src = 'o' if self._origin.exists() else 'd'
        if isinstance(value, BackupFile):
            value:PurePath = value._at
        elif isinstance(value, str):
            value:PurePath = PurePath(value)
        
        return value in (file._at for file in self.walk(src))
        
    @typ.overload
    def _get_source(self, s:typ.Literal['o', 'd'] = ...) -> Path: ...
    @typ.overload
    def _get_source(self, s:typ.Literal['o', 'd'] = ..., order:bool = False) -> tuple[Path, Path]: ...
    
    def _get_source(self, s:typ.Literal['o', 'd'] = ..., order:bool = False):
        assert s in ('o', 'd', Ellipsis), \
            f"__s must be 'o' (by origin) or 'd' (by destiny), not '{s}'."

        x, y = (self._origin, self._destiny) if s in ('o', ...) else (self._destiny, self._origin)

        if order:
            return x, y
        
        if s == Ellipsis and not x.exists():
            return y
        return x

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
            size += meta.size
            
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
    
    def pop(self, index:int|slice) -> typ.Generator[BackupMeta, None, None]:
        if isinstance(index, int):
            index = slice(index, index + 1)
            
        for meta in self._data[index]:
            self._data.remove(meta)
            yield meta
    
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
        with open(destiny, "w", encoding= "utf-8") as fp:
            json.dump({
                "list_name": self.name,
                "content": [meta.to_dict() for meta in self._data]
            }, fp, indent= 4, )
    
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

class _AllLists():
    #TODO: Optimize this. When a resource array is requested, it should be loaded. If it is not requested, it is not loaded.
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
            data:_AllLists = pickle.load(fp)
            if isinstance(data, _AllLists) and isinstance(data._data, list):
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
        from colorama import Back
        
        if len(self._data) == 0:
            return "There are not lists."

        strings:list[str] = []

        for index, array in enumerate(self._data):
            string = "[%s] - \"%s\""%(format_number(index), array.name[:32])
            if len(array.name) >= 32:
                string += "..."
                
            string += " | %s element%s"%(format_number(len(array)), 's' if len(array) != 1 else '')
            
            if array is self.selected:
                string = Back.GREEN + string + Back.RESET
            
            strings.append(string)
        
        return "\n".join(strings)
    
    def select(self, index:int) -> ResourcesArray:
        """
        Select a list and return it.
        """
        self._selected = self._data[index]
        return self._selected
    
    def names(self) -> tuple[str]:
        """
        Return the names of all of the lists.
        """
        return tuple(map(lambda array: array.name, self._data))
    
    def __check_repetition(self, value:ResourcesArray):
        if value.name in self.names():
            raise RepetitionError(
                "The list is repeated."
            )
        
        return value
    
    def count_copies(self, value:ResourcesArray) -> int:
        """
        Count the number of copies of `value`. 
        Copies are `ResourcesArray` that are named like 'Copy [number] of [value.name]'.
        """
        if value not in self:
            return 0
        
        from re import fullmatch
        
        count = 0
        for array in self:
            if fullmatch(f"Copy \d of {value.name}", array.name):
                count += 1
                
        return count
        
    @typ.overload
    def __getitem__(self, index:int) -> ResourcesArray: ...
    @typ.overload
    def __getitem__(self, index:slice) -> tuple[ResourcesArray]: ...
    
    def __getitem__(self, index:int|slice):
        return self._data[index]
    
    def __len__(self):
        return len(self._data)
    
    def __iter__(self) -> typ.Iterator[ResourcesArray]:
        yield from self._data
    
    def __contains__(self, value):
        if isinstance(value, ResourcesArray):
            return value.name in self.names()

        return False

class AllLists(_AllLists):
    def __new__(cls):
        logging.info("Transforming AllLists to _AllLists.")
        return _AllLists()

all_lists = _AllLists()

#* ----------------------
#*      EXCEPTIONS
#* ----------------------

class NotAFileError(OSError):
    """
    The operation works in files only.
    """
    pass

class RepetitionError(Exception):
    """
    The value is repeated.
    """
    pass
