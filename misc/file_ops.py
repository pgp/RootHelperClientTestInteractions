import abc
import os
import shutil
import stat
from typing import List, Tuple

import paramiko


class FileOps(object):
    __metaclass__ = abc.ABCMeta

    def existsIsFileIsDir(self, path):
        try:
            a = self.stat(path)
            if stat.S_ISDIR(a.st_mode): return 2  # directory
            else: return 1  # file
        except FileNotFoundError:
            return 0  # not-existing path
        except:
            return -1  # access error or anything else

    def mkpath(self, path):
        if path in {'.', '/'}: # current dir and root always exist
            return

        path1 = path + '/' # just to avoid code duplication after for loop

        for i in range(1,len(path1)):
            if path1[i] == '/':
                partialPath = path1[:i]
                print(f'Creating partial path: {partialPath}')
                try:
                    self.mkdir(partialPath)
                except FileExistsError:
                    if self.existsIsFileIsDir(partialPath) != 2:
                        raise

    def rmpath(self, path):
        """
        BEWARE! For SFTP, this function is very slow in that involves listing and statting and separate sftp commands.
        Use it only when you have SFTP access alone (i.e. you cannot open a SSH session for issuing 'rm -rf' command
        """
        ret = 0
        S: List[Tuple[str, bool]] = []
        S.append((path, False))

        while S:
            p = S.pop()
            x = p[0]
            efd = self.existsIsFileIsDir(x)
            if efd == 0:
                print(f'warning: not-existing remote path {x}')
            elif efd == 1:
                print(f'regular file: {x}')
                try:
                    self.rmfile(x)
                except:
                    ret = -1
            elif efd == 2:
                l = self.listdir(x)
                if not l:  # directory is empty
                    print(f'empty dir: {x}')
                    try:
                        self.rmdir(x)  # delete empty dir
                    except:
                        ret = -1
                else:
                    '''
                    non-empty directory that was already visited
                    it means some files within cannot be deleted
                    so, remove it from stack anyway
                    '''
                    if p[1]:
                        print(f'non-empty dir, already visited: {x}')
                        continue

                    print(f'non-empty dir, first visit: {x}')
                    # leave on stack (set visited flag to true) and add children on top
                    p = (p[0], True)
                    S.append(p)

                    for y in l:
                        S.append((os.path.join(x, y), False))
        return ret

    @abc.abstractmethod
    def stat(self, path):
        pass

    @abc.abstractmethod
    def mkdir(self, path):
        pass

    @abc.abstractmethod
    def listdir(self, path):
        pass

    @abc.abstractmethod
    def rmfile(self, path):
        pass

    @abc.abstractmethod
    def rmdir(self, path):
        pass


class LocalFileOps(FileOps):

    def mkpath(self, path):
        os.makedirs(path, exist_ok=True)

    def rmpath(self, path):
        try:
            shutil.rmtree(path)
        except FileNotFoundError:
            pass

    def stat(self, path):
        return os.stat(path)

    def mkdir(self, path):
        try:
            os.mkdir(path)
        except FileExistsError:
            if self.existsIsFileIsDir(path) != 2: # already exists, but it's not a folder
                raise

    def listdir(self, path):
        return os.listdir(path)

    def rmfile(self, path):
        os.remove(path)

    def rmdir(self, path):
        os.rmdir(path)


class SftpFileOps(FileOps):

    def __init__(self, sftp_client: paramiko.SFTPClient) -> None:
        super().__init__()
        self.sftp_client = sftp_client

    def stat(self, path):
        return self.sftp_client.stat(path)

    def mkdir(self, path):
        self.sftp_client.mkdir(path)

    def listdir(self, path):
        return self.sftp_client.listdir(path)

    def rmfile(self, path):
        self.sftp_client.remove(path)

    def rmdir(self, path):
        self.sftp_client.rmdir(path)