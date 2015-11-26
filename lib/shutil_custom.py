import os
import stat
import shutil

try:
    from shutil import SpecialFileError, Error
except:
    from shutil import Error

__all__ = ["copyfile"]

class CustomSHUtil(object):
    def copyfile(self, src, dst):
        """Copy data from src to dst"""
        if shutil._samefile(src, dst):
            raise Error("`%s` and `%s` are the same file" % (src, dst))
        elif not os.path.isdir(src):
            return

        for fn in [src, dst]:
            try:
                st = os.stat(fn)
            except OSError:
                # File most likely does not exist
                pass
            else:
                # XXX What about other special files? (sockets, devices...)
                if stat.S_ISFIFO(st.st_mode):
                    try:
                        raise SpecialFileError("`%s` is a named pipe" % fn)
                    except NameError:
                        raise Error("`%s` is a named pipe" % fn)

        try:
            # Windows
            O_BINARY = os.O_BINARY
        except:
            O_BINARY = 0

        READ_FLAGS = os.O_RDONLY | O_BINARY
        WRITE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | O_BINARY
        BUFFER_SIZE = 128*1024

        try:
            with os.open(src, READ_FLAGS) as fin, os.open(dst, WRITE_FLAGS) as fout:
                for x in iter(lambda: os.read(fin, BUFFER_SIZE), ""):
                    os.write(fout, x)
        except Exception:
            raise

shutil.copyfile = CustomSHUtil.copyfile