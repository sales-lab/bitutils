""" Functions to work on paths. """

__author__ = "Gabriele Sales <gbrsales@gmail.com>"
__copyright__ = "2012-2020 Gabriele Sales"

import errno
import os
from os import environ, symlink, unlink
from os.path import abspath, dirname, isdir, islink, join, relpath

from .util import exit


def bit_root():
    """ Retrieves the root path of BioinfoTree.

        If the path is not defined or does not exist, the function
        calls L{exit} with an informative error message.

        @returns: the root path.
    """
    try:
        root = environ['BIOINFO_ROOT']
        if len(root) == 0: raise KeyError
    except KeyError:
        exit('BIOINFO_ROOT is not defined or empty.')

    root = abspath(root)
    if not isdir(root):
        exit('BIOINFO_ROOT does not point to a valid directory.')

    return root


def subdir_of(path, root):
    """ Checks whether C{path} is a subdir of C{root} or C{root} itself.

        @returns: a C{Bool}.
    """
    path = abspath(path)
    root = abspath(root)
    return path == root or path.startswith(root + '/')


def link_relative(src, dest, force=False):
    """ Creates a symbolic link C{dest} referencing C{src} using a relative path.

        @param src: the path to link.
        @param dest: the link path.
        @param force: if C{True}, silently replaces C{dest}.
    """
    dest = abspath(dest)
    if force:
        try:
            unlink(dest)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    symlink(relpath(src, dirname(dest)), dest)


def readlink(path, max_depth=20):
    """ Retrieves the path to which a symbolic link points.

        When the symbolink link refers to another link, the function
        follows the chain up to C{max_depth}. If after that many steps
        there is still a link, the function raises a C{IOError} with an
        C{ELOOP} error code.

        @param path: the link path.
        @param max_depth: the maximum number of chained links to follow.
        @returns: the pointed path.
    """
    original_path = path

    while max_depth > 0 and islink(path):
        path = join(dirname(path), os.readlink(path))
        max_depth -= 1

    if max_depth <= 0 and islink(path):
        raise IOError(errno.ELOOP, original_path, 'too many chained symbolic links')

    return path


def get_workdir():
    """ Returns the full path of the current working directory.

        @returns: the path string.
    """

    # Stolen from
    # http://bugs.python.org/issue1154351#msg61185

    cwd = os.getcwd()

    try:
        pwd = os.environ["PWD"]
    except KeyError:
        return cwd

    cwd_stat, pwd_stat = list(map(os.stat, [cwd, pwd]))

    if cwd_stat.st_dev == pwd_stat.st_dev and \
            cwd_stat.st_ino == pwd_stat.st_ino:
        return pwd
    else:
        return cwd
