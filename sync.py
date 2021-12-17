#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import hashlib
import logging
import os
import signal
import shutil
import stat
import sys
import time
from datetime import datetime, timedelta

RUN = True


def signal_handler(signal, frame):
    """ soft interrupt with 'ctrl+c' """
    global RUN
    logging.info("Stopped by user. Synchronization ending...please wait.")
    RUN = False


def make_set(path):
    path_set = set()
    for root, dirs, files in os.walk(path):
        for file in files:
            path_to_file = os.path.relpath(path=os.path.join(root, file), start=path)
            path_set.add(path_to_file)
        for directory in dirs:
            path_to_dir = os.path.relpath(path=os.path.join(root, directory), start=path)
            path_set.add(path_to_dir)
    return path_set


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
    shutil.copyfile(src, dst)
    logging.info(msg=f'File "{os.path.basename(src)}" coped from "{os.path.dirname(src)}" to "{os.path.dirname(dst)}"')


def check(src, dst):
    """checking the identity of directories"""
    logging.info(msg='Checking...')

    set_s = make_set(src)
    set_d = make_set(dst)

    if len(set_d - set_s):
        return False

    if len(set_s - set_d):
        return False

    for element in set_s & set_d:
        if os.path.isfile(os.path.join(dst, element)):
            path_s = os.path.join(src, element)
            path_d = os.path.join(dst, element)
            with open(path_s, mode='rb') as file_s, open(path_d, mode='rb') as file_d:
                if hashlib.md5(file_s.read()).hexdigest() != hashlib.md5(file_d.read()).hexdigest():
                    return False
    return True


def sync_dirs(src: str, dst: str):
    """directory synchronization"""
    if not os.path.exists(dst):
        os.mkdir(dst)
        logging.info(msg=f'Create directory "{dst}"')

    logging.info(f'Update information...')
    set_s = make_set(src)
    set_d = make_set(dst)
    delete_list = []
    create_list = []
    check_set = set_s & set_d

    for element in check_set:
        if os.path.isfile(os.path.join(dst, element)):
            path_s = os.path.join(src, element)
            path_d = os.path.join(dst, element)
            with open(path_s, mode='rb') as file_s, open(path_d, mode='rb') as file_d:
                if hashlib.md5(file_s.read()).hexdigest() != hashlib.md5(file_d.read()).hexdigest():
                    delete_list.append(element)
                    create_list.append(element)

    delete_list.extend(set_d - set_s)
    delete_list.sort(reverse=True)
    create_list.extend(set_s - set_d)
    create_list.sort()

    for element in delete_list:
        path_to_delete = os.path.join(dst, element)
        if os.path.exists(path_to_delete):
            del_file_and_dir(path_to_delete)

    for element in create_list:
        path_to_copy = os.path.join(src, element)
        path_to_create = os.path.join(dst, element)
        if os.path.isdir(path_to_copy):
            os.mkdir(path_to_create)
            logging.info(msg=f'Create directory "{path_to_create}"')
        else:
            copy(path_to_copy, path_to_create)
    return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', help='Path to the folder you want to track')
    parser.add_argument('target', help='Path to the replica folder')
    parser.add_argument('log', help='Path to the logs')
    parser.add_argument('interval', help='Synchronization interval (in seconds)', type=int)
    args = parser.parse_args()

    source = os.path.abspath(args.source)
    destination = os.path.abspath(args.target)
    logs = os.path.abspath(args.log)
    path_log = os.path.join(logs, 'logs.txt')
    os.makedirs(logs, exist_ok=True)

    logging.basicConfig(format='%(asctime)s | %(message)s',
                        datefmt='%m.%d.%Y %H:%M:%S',
                        level=logging.INFO,
                        handlers=[
                            logging.StreamHandler(stream=sys.stdout),
                            logging.FileHandler(path_log, mode='a', encoding='utf-8')
                        ], )

    signal.signal(signal.SIGINT, signal_handler)
    logging.info(f'Start sync "{os.path.abspath(source)}" and "{os.path.abspath(destination)}"')

    while RUN:
        sync_dirs(src=source, dst=destination)
        if not check(src=source, dst=destination):
            logging.info('Resynchronization...')
            sync_dirs(src=source, dst=destination)
        logging.info(f'Synchronization complete. '
                     f'Next in {(datetime.now() + timedelta(seconds=args.interval)).time().strftime("%H:%M:%S")}')
        time.sleep(args.interval)


if __name__ == '__main__':
    main()
