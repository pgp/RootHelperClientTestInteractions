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

    def mkpath(self, path, exist_ok=True):
        if path in {'.', '/'}: # current dir and root always exist
            return

        path1 = path + '/' # just to avoid code duplication after for loop

        for i in range(1,len(path1)):
            if path1[i] == '/':
                partialPath = path1[:i]
                if (exist_ok and self.existsIsFileIsDir(partialPath) != 2) or (not exist_ok):
                    print(f'Creating partial path: {partialPath}')
                    self.mkdir(partialPath)

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

    @abc.abstractmethod
    def rename(self, path1, path2):
        pass


class LocalFileOps(FileOps):

    def mkpath(self, path, exist_ok=True):
        os.makedirs(path, exist_ok=exist_ok)

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

    def rename(self, path1, path2):
        os.renames(path1, path2)


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

    def rename(self, path1, path2):
        self.sftp_client.posix_rename(path1, path2)


def sftp_sync(local_dir: str, sftp: paramiko.SFTPClient, remote_dir: str):
    """Synchronizes local_dir towards remote_dir (i.e. files in remote_dir
    not in local_dir won't be copied to local_dir)"""
    o1 = LocalFileOps()
    o2 = SftpFileOps(sftp)

    # ensure both base paths exist and are actual folders
    o1.mkpath(local_dir)
    o2.mkpath(remote_dir)

    # stack of (filename, local_relpath_including_base_dir, remote_relpath_including_remote_dir)
    S =  [(local_dir, remote_dir)]

    while S:
        relpath, remote_relpath = S.pop()
        efd = o1.existsIsFileIsDir(relpath)
        if efd == 1:
            p1 = relpath
            p2 = remote_relpath
            o2.mkpath(os.path.dirname(p2))
            print(f'Uploading local file {p1} to remote path {p2}')
            sftp.put(p1, p2) # TODO upload only if modification time of p1 > modification time of p2
        elif efd == 2:
            S.extend(((os.path.join(relpath, filename)),(os.path.join(remote_relpath, filename))) for filename in o1.listdir(relpath))