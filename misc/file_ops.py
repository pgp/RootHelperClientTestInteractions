import abc
import sys
import os
import platform
import shutil
import stat
from typing import List, Tuple
import paramiko
if not ('..' in sys.path or os.path.realpath('..') in sys.path): sys.path.append(os.path.realpath('..'))
from net_common import *

try:
    import colorama


    class ColoramaLogger(object):
        initialized = colorama.init()
        COLORS = {
            'CYAN': colorama.Fore.CYAN,
            'PINK': colorama.Fore.MAGENTA,
            'BLUE': colorama.Fore.BLUE,
            'GREEN': colorama.Fore.GREEN,
            'YELLOW': colorama.Fore.YELLOW,
            'RED': colorama.Fore.RED,
            'ENDC': colorama.Style.RESET_ALL
        }

        def __init__(self, color=None, logger_prefix=None):
            self.bcstart = ''
            self.bcend = ''
            self.logger_prefix = '' if logger_prefix is None else (str(logger_prefix) + ": ")
            if color is not None:
                self.bcstart = self.COLORS[color.upper()]
            if self.bcstart != '':
                self.bcend = self.COLORS['ENDC']

        def log(self, *args):
            print(self.bcstart +
                  self.logger_prefix +
                  (''.join([str(_) for _ in args])) +
                  self.bcend)

except ImportError:
    colorama = None


class ColorLogger(object):
    COLORS = {
        'CYAN': b'\033[96m',
        'PINK': b'\033[95m',
        'BLUE': b'\033[94m',
        'GREEN': b'\033[92m',
        'YELLOW': b'\033[93m',
        'RED': b'\033[91m',
        'BROWN': b'\033[90m',
        'ENDC': b'\033[0m',
        'BOLD': b'\033[1m',
        'UNDERLINE': b'\033[4m'
    }

    def __init__(self, color=None, logger_prefix=None):
        self.bcstart = b''
        self.bcend = b''
        self.logger_prefix = b'' if logger_prefix is None else (str(logger_prefix)+": ").encode('utf-8')
        if color is not None:
            self.bcstart = self.COLORS[color.upper()]
        if self.bcstart != '':
            self.bcend = self.COLORS['ENDC']

        # prevent outputting ANSI color escape sequences on Windows, or when using output redirection
        if (not os.isatty(1)) or platform.uname()[0].lower().startswith('win'):
            self.log = self.logpipe

    def log(self, *args):
        os.write(1,
                 self.bcstart +
                 self.logger_prefix +
                 (''.join([str(_) for _ in args])).encode('utf-8') +
                 b'\n' +
                 self.bcend)

    def logpipe(self, *args):
        os.write(1,
                 self.logger_prefix +
                 (''.join([str(_) for _ in args])).encode('utf-8') + b'\n')

    @staticmethod
    def getLogger(color=None, logger_prefix=None):
        return ColoramaLogger(color, logger_prefix) if colorama else ColorLogger(color, logger_prefix)


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


def create_sftp_client2(host, port, username, password, keyfilepath, keyfiletype):
    """
    create_sftp_client(host, port, username, password, keyfilepath, keyfiletype) -> SFTPClient

    Creates a SFTP client connected to the supplied host on the supplied port authenticating as the user with
    supplied username and supplied password or with the private key in a file with the supplied path.
    If a private key is used for authentication, the type of the keyfile needs to be specified as DSA or RSA.
    :rtype: SFTPClient object.
    """
    ssh = None
    sftp = None
    key = None
    try:
        if keyfilepath is not None:
            # Get private key used to authenticate user.
            if keyfiletype == 'DSA':
                # The private key is a DSA type key.
                key = paramiko.DSSKey.from_private_key_file(keyfilepath)
            else:
                # The private key is a RSA type key.
                key = paramiko.RSAKey.from_private_key(keyfilepath)

        # Connect SSH client accepting all host keys.
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port, username, password, key)

        # Using the SSH client, create a SFTP client.
        sftp = ssh.open_sftp()
        # Keep a reference to the SSH client in the SFTP client as to prevent the former from
        # being garbage collected and the connection from being closed.
        sftp.sshclient = ssh

        return sftp
    except Exception as e:
        print('An error occurred creating SFTP client: %s: %s' % (e.__class__, e))
        if sftp is not None:
            sftp.close()
        if ssh is not None:
            ssh.close()


def sftp_sync(local_dir: str, sftp: paramiko.SFTPClient, remote_dir: str):
    """Synchronizes local_dir towards remote_dir (i.e. files in remote_dir
    not in local_dir won't be copied to local_dir)"""
    info_ = ColorLogger.getLogger('blue')
    warn_ = ColorLogger.getLogger('yellow')
    info = info_.log
    warn = warn_.log

    o1 = LocalFileOps()
    o2 = SftpFileOps(sftp)

    # ensure both base paths exist and are actual folders
    o1.mkpath(local_dir)
    o2.mkpath(remote_dir)

    # stack of (local_relpath_including_base_dir, remote_relpath_including_remote_dir)
    S =  [(local_dir, remote_dir)]

    while S:
        relpath, remote_relpath = S.pop()
        efd = o1.existsIsFileIsDir(relpath)
        if efd == 1:
            p1 = relpath
            p2 = remote_relpath
            o2.mkpath(os.path.dirname(p2))
            # upload only if modification time of p1 > modification time of p2
            try:
                tmp = o2.stat(p2)
                remote_times = (int(tmp.st_atime), int(tmp.st_mtime))
            except:
                # assume remote file not existing
                remote_times = (0,0)
            tmp = o1.stat(p1)
            local_times = (int(tmp.st_atime), int(tmp.st_mtime))
            local_mtime = local_times[1]
            remote_mtime = remote_times[1]
            if local_mtime > remote_mtime:
                warn(f"Updating remote path {p2} with mtime {remote_mtime} from local path {p1} with mtime {local_mtime}")
                sftp.put(p1,p2)
                sftp.utime(p2, local_times)
            else:
                info(f"Won't update remote path {p2} with mtime {remote_mtime}, equal or more recent than local path {p1} with mtime {local_mtime}")
        elif efd == 2:
            S.extend(((pathConcat(relpath, filename, '/')),(pathConcat(remote_relpath, filename, '/'))) for filename in o1.listdir(relpath))


if __name__ == '__main__':
    s = create_sftp_client2('192.168.70.76', 22, 'effetipi', 'effetipi', None, None)
    sftp_sync('/media/pgp/Dati/m19/sdcard_mint19/apks', s, 'zzztest3')
