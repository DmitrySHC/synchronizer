import os
import shutil
from sync import sync_dirs, check


DEL_AFTER_TEST = True


def make_test_folder(name):
    cur_dir = os.getcwd()
    test_source_path = os.path.join(cur_dir, name)
    try:
        os.mkdir(test_source_path)
    except FileExistsError:
        shutil.rmtree(test_source_path)
        os.mkdir(test_source_path)
    return test_source_path


def make_test_file(path, name):
    path_to_file = os.path.join(path, name)
    file = open(path_to_file, mode='w')
    file.close()
    return path_to_file


def test_empty_folder():
    source = make_test_folder(name='test_source')
    target = make_test_folder(name='test_target')
    sync_dirs(
        src=source,
        dst=target,
    )
    assert check(source, target), 'Folders are not identical!'
    if DEL_AFTER_TEST:
        shutil.rmtree(source)
        shutil.rmtree(target)


def test_with_file():
    source = make_test_folder(name='test_source')
    target = make_test_folder(name='test_target')
    make_test_file(path=source, name='test.txt')
    sync_dirs(
        src=source,
        dst=target,
    )
    assert check(source, target), 'Folders are not identical!'
    if DEL_AFTER_TEST:
        shutil.rmtree(source)
        shutil.rmtree(target)


def test_file_edit():
    source = make_test_folder(name='test_source')
    target = make_test_folder(name='test_target')
    path_to_file = make_test_file(path=source, name='test.txt')
    sync_dirs(
        src=source,
        dst=target,
    )
    assert check(source, target), 'Folders are not identical!'

    file_ = open(path_to_file, mode='a')
    file_.write("I'm new in this file!")
    file_.close()
    sync_dirs(
        src=source,
        dst=target,
    )
    assert check(source, target), 'Folders are not identical after edit!'

    if DEL_AFTER_TEST:
        shutil.rmtree(source)
        shutil.rmtree(target)


def test_file_remove():
    source = make_test_folder(name='test_source')
    target = make_test_folder(name='test_target')
    path_to_file = make_test_file(path=source, name='test.txt')
    sync_dirs(
        src=source,
        dst=target,
    )
    assert check(source, target), 'Folders are not identical!'

    os.remove(path_to_file)
    sync_dirs(
        src=source,
        dst=target,
    )
    assert check(source, target), 'Folders are not identical after remove!'
    if DEL_AFTER_TEST:
        shutil.rmtree(source)
        shutil.rmtree(target)
