#! /usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import hashlib
import os
import shutil
import stat
import time
import logging
import sys
import signal

RUN = True


def signal_handler(signal, frame):
    """ soft interrupt with 'ctrl+c' """
    global RUN
    logging.info("Stopped by user. Synchronization ending...please wait.")
    RUN = False


def make_meta(src, meta=None):
    """creating metadata dictionary"""
    if meta is None:
        meta = {}
    for name in os.listdir(src):
        path = os.path.join(src, name)
        if not os.path.isfile(path):
            make_meta(path, meta)
        else:
            with open(path, mode='rb') as f:
                meta[path] = hashlib.md5(f.read()).hexdigest()
    return meta


def make_tree(src):
    """creating directory tree"""
    tree = [(root, dirs, files) for root, dirs, files in os.walk(src)]
    return tree


def del_file_and_dir(deleted):
    if os.path.isdir(deleted):
        tree = make_tree(deleted)
        for elem in tree[::-1]:
            root, dirs, files = elem
            for file in files:
                logging.info(msg=f'Delete file "{os.path.basename(file)}" from "{root}"')
            logging.info(msg=f'Delete directory "{root}"')
        shutil.rmtree(deleted)
    else:
        os.chmod(deleted, stat.S_IWRITE)
        os.remove(deleted)
        logging.info(msg=f'Delete file "{os.path.basename(deleted)}" from "{os.path.dirname(deleted)}"')
    assert not os.path.exists(deleted)


def copy(src, dst):
    if os.path.exists(src):
        shutil.copy(src, dst)
        logging.info(msg=f'File "{os.path.basename(src)}" coped from '
                         f'"{os.path.dirname(src)}" to "{os.path.dirname(dst)}"')


def check(src, dst):
    """checking the identity of directories"""
    logging.info(msg='Checking...')
    tree_src = make_tree(src=src)
    tree_dst = make_tree(src=src)
    meta_src = make_meta(src=src)
    meta_dst = make_meta(src=dst)

    if len(meta_src.keys()) != len(meta_dst.keys()):
        return False

    for file_s_hash, file_d_hash in zip(meta_src.values(), meta_dst.values()):
        if file_s_hash != file_d_hash:
            return False

    if len(tree_src) != len(tree_dst):
        return False

    for source, target in zip(tree_src, tree_dst):
        if len(source[1]) != len(target[1]):
            return False
        for dir_s, dir_t in zip(source[1], target[1]):
            if dir_s != dir_t:
                return False
    return True


def sync_dirs(src: str, dst: str, meta: dict, tree: list, new_meta=None, new_tree=None):
    """directory synchronization"""
    logging.info(f'Update information...')
    if new_meta is None:
        new_meta = make_meta(src)

    if new_tree is None:
        new_tree = make_tree(src)

    for element in tree:
        root, files = element[::2]
        new_root = root.replace(src, dst)
        if not os.path.exists(new_root) and os.path.exists(root):
            os.mkdir(new_root)
            logging.info(msg=f'Create directory "{new_root}"')

        for file in files:
            new_path_to_file = os.path.join(new_root, file)
            old_path_to_file = os.path.join(root, file)

            if old_path_to_file in new_meta and not os.path.exists(new_path_to_file):
                copy(src=old_path_to_file, dst=new_path_to_file)
            elif os.path.exists(new_path_to_file) and not os.path.exists(old_path_to_file):
                del_file_and_dir(new_path_to_file)
            elif old_path_to_file in new_meta and meta[old_path_to_file] != new_meta[old_path_to_file]:
                copy(src=old_path_to_file, dst=new_path_to_file)

        if os.path.exists(new_root) and not os.path.exists(root):
            del_file_and_dir(new_root)

    return new_meta, new_tree


def main():
    try:
        source, destination, logs, interval = (int(elem) if elem.isdigit() else elem for elem in sys.argv[1:])
    except ValueError:
        print("Invalid number of arguments!")
        return

    source = os.path.abspath(source)
    destination = os.path.abspath(destination)
    logs = os.path.abspath(logs)
    path_log = os.path.join(logs, 'logs.txt')
    os.makedirs(logs, exist_ok=True)

    logging.basicConfig(format='%(asctime)s | %(message)s',
                        datefmt='%m.%d.%Y %H:%M:%S',
                        level=logging.INFO,
                        handlers=[
                            logging.StreamHandler(stream=sys.stdout),
                            logging.FileHandler(path_log, mode='a')
                        ],)

    signal.signal(signal.SIGINT, signal_handler)
    logging.info(f'Start sync "{os.path.abspath(source)}" and "{os.path.abspath(destination)}"')

    meta = make_meta(source)
    tree = make_tree(source)
    while RUN:
        meta, tree = sync_dirs(src=source, dst=destination, meta=meta, tree=tree)
        if not check(src=source, dst=destination):
            logging.info('Resynchronization...')
            meta, tree = sync_dirs(src=source, dst=destination, meta=meta, tree=tree)
        logging.info(f'Synchronization complete. '
                     f'Next in {(datetime.now() + timedelta(seconds=interval)).time().strftime("%H:%M:%S")}')
        time.sleep(interval)


if __name__ == '__main__':
    main()
