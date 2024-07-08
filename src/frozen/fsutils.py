import os, gc, io
import deflate
import tinytar

def exists(filename):
    try:
        os.stat(filename)
        return True
    except OSError:
        return False

def create_directories(filename):
    parts = filename.split('/')
    path = ''
    for part in parts[:-1]:  # Exclude the last part which is the file name
        if part:  # Skip any empty parts
            path = f'{path}/{part}' if path else part
            try:
                os.stat(path)
            except OSError:
                os.mkdir(path)

def remove_file(filename):
    try:
        os.remove(filename)
    except OSError:
        pass


def delete_directory(path):
    try:
        entries = os.listdir(path)
    except OSError:
        return
    for entry in entries:
        full_path = f"{path}/{entry}"
        try:
            os.remove(full_path)
        except OSError:
            delete_directory(full_path)
    try:
        os.rmdir(path)
    except OSError:
        pass

def decompress(stream, path):
    def header_callback(header, entry_index, context_data):
        if header.type == tinytar.EntryType.T_NORMAL:
            file_name = f"{path}/{header.filename}"
            remove_file(file_name)
            print(f"Decompressing file {header.filename} => {file_name}, Length: {header.filesize}")

    def data_callback(header, entry_index, context_data, block):
        if header.type == tinytar.EntryType.T_NORMAL:
            file_name = f"{path}/{header.filename}"
            create_directories(file_name)
            with open(file_name, 'ab') as file:
                file.write(block)

    callbacks = {
        'header_cb': header_callback,
        'data_cb': data_callback
    }
    context_data = {}
    f = io.BytesIO(stream)
    with deflate.DeflateIO(f, deflate.AUTO) as d:
        tinytar.read_tar(d, callbacks, context_data)
    f = None
    context_data = None
    gc.collect()