import os
import time
from typing import Tuple , Optional
from pathlib import Path

class FileValidator:
    def __init__(self , max_size_mb :int =10 , timeout_sec :int = 30):
        self.max_size_bytes = max_size_mb*1024*1024
        self.timeout_sec = timeout_sec
        self.start_time : Optional[float] = None
    def validate_magic_bytes(self , content:bytes)-> Tuple[bool , str]:
        if len(content) < 5:
            return False,"file to small to validate(<5 bytes)"
        if content[:5] != b'%PDF-':
            if b'%PDF-' in content[:1024]:
                return False ,"PDF header not at start of file (potential malware)"
            return False , "Invalid PDF format: Missing '%PDF-' header"
        return True,""
    def velidate_file_size(self , content:bytes) -> Tuple[bool , str]:
        if len(content) > self.max_size_bytes:
            actual_mb = len(content) / (1024*1024)
            max_mb = self.max_size_bytes/ (1024*1024)
            return False , f"File size ({actual_mb:.1f}MB) exceeds limit ({max_mb}MB)"
        if len(content) == 0:
            return False , "empty file"
        return True,""
    def validate_filename(self , filename:str) ->Tuple[bool , str]:
        if any(pattern in filename for pattern in ['../', '..\\', '/etc/', 'C:\\']):
            return False, "Filename contains path traversal patterns"
        if not filename.lower().endswith('.pdf'):
            return False, "Filename must have .pdf extension"
        safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._- ")
        if not all(c in safe_chars for c in filename):
            return False, "Filename contains invalid characters"
        return True,""
    def validate_upload(self , content:bytes , filename:str)-> Tuple[bool , str]:
        is_valid , error = self.validate_filename(filename)
        if not is_valid:
            return False, f"Size validation failed: {error}"
        is_valid , error = self.velidate_file_size(content)
        if not is_valid:
            return False, f"Size validation failed: {error}"
        is_valid, error = self.validate_magic_bytes(content)
        if not is_valid:
            return False, f"Format validation failed: {error}"
        return True ,"Pass"
    def start_timeout(self):
        self.start_time = time.time()
    def check_timeout(self)-> Tuple[bool ,str]:
        if self.start_time is None:
            return True
        elapsed_time = time.time() - self.start_time
        if elapsed_time > self.timeout_sec:
            return False, f"Processing timeout exceeded ({elapsed_time:.1f}s > {self.timeout_sec}s)"
        return True,""
    def get_time_remain(self)->float:
        if self.start_time is None:
            return self.timeout_sec
        return max(0, self.timeout_sec - (time.time() - self.start_time))
    
    

    