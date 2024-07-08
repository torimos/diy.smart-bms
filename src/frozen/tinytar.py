import math
import os

TAR_BLOCK_SIZE = 512

TAR_T_NORMAL1 = 0
TAR_T_NORMAL2 = '0'
TAR_T_HARD = '1'
TAR_T_SYMBOLIC = '2'
TAR_T_CHARSPECIAL = '3'
TAR_T_BLOCKSPECIAL = '4'
TAR_T_DIRECTORY = '5'
TAR_T_FIFO = '6'
TAR_T_CONTIGUOUS = '7'
TAR_T_GLOBALEXTENDED = 'g'
TAR_T_EXTENDED = 'x'

def is_base256_encoded(buffer):
    return (buffer[0] & 0x80) > 0

def get_num_blocks(filesize):
    return int(math.ceil(filesize / TAR_BLOCK_SIZE))

def get_last_block_portion_size(filesize):
    partial = filesize % TAR_BLOCK_SIZE
    return partial if partial > 0 else TAR_BLOCK_SIZE

class EntryType:
    T_NORMAL = 0
    T_HARDLINK = 1
    T_SYMBOLIC = 2
    T_CHARSPECIAL = 3
    T_BLOCKSPECIAL = 4
    T_DIRECTORY = 5
    T_FIFO = 6
    T_CONTIGUOUS = 7
    T_GLOBALEXTENDED = 8
    T_EXTENDED = 9
    T_OTHER = 10

class Header:
    def __init__(self):
        self.filename = ""
        self.filemode = ""
        self.uid = ""
        self.gid = ""
        self.filesize = ""
        self.mtime = ""
        self.checksum = ""
        self.type = ""
        self.link_target = ""
        self.ustar_indicator = ""
        self.ustar_version = ""
        self.user_name = ""
        self.group_name = ""
        self.device_major = ""
        self.device_minor = ""

class TranslatedHeader:
    def __init__(self):
        self.filename = ""
        self.filemode = 0
        self.uid = 0
        self.gid = 0
        self.filesize = 0
        self.mtime = 0
        self.checksum = 0
        self.type = EntryType.T_OTHER
        self.link_target = ""
        self.ustar_indicator = ""
        self.ustar_version = ""
        self.user_name = ""
        self.group_name = ""
        self.device_major = 0
        self.device_minor = 0

def trim(raw):
    return raw.strip()

def decode_base256(buffer):
    return 0

def parse_header(buffer):
    header = Header()
    header.filename = buffer[:100].decode().strip()
    header.filemode = buffer[100:108].decode().strip()
    header.uid = buffer[108:116].decode().strip()
    header.gid = buffer[116:124].decode().strip()
    header.filesize = buffer[124:136].decode().strip()
    header.mtime = buffer[136:148].decode().strip()
    header.checksum = buffer[148:156].decode().strip()
    header.type = buffer[156:157].decode().strip()
    header.link_target = buffer[157:257].decode().strip()
    header.ustar_indicator = buffer[257:263].decode().strip()
    header.ustar_version = buffer[263:265].decode().strip()
    header.user_name = buffer[265:297].decode().strip()
    header.group_name = buffer[297:329].decode().strip()
    header.device_major = buffer[329:337].decode().strip()
    header.device_minor = buffer[337:345].decode().strip()
    return header

def translate_header(raw_header):
    parsed = TranslatedHeader()
    parsed.filename = trim(raw_header.filename).replace('\x00', '')

    def safe_int_conversion(value, base=10):
        trimmed_value = trim(value).rstrip('\x00')
        return int(trimmed_value, base) if trimmed_value.isdigit() else 0

    parsed.filemode = safe_int_conversion(raw_header.filemode, 8)
    parsed.uid = safe_int_conversion(raw_header.uid, 8)
    parsed.gid = safe_int_conversion(raw_header.gid, 8)
    parsed.filesize = safe_int_conversion(raw_header.filesize, 8)
    parsed.mtime = safe_int_conversion(raw_header.mtime, 8)
    parsed.checksum = safe_int_conversion(raw_header.checksum, 8)
    parsed.type = get_type_from_char(raw_header.type)
    parsed.link_target = trim(raw_header.link_target)
    parsed.ustar_indicator = trim(raw_header.ustar_indicator)
    parsed.ustar_version = trim(raw_header.ustar_version)
    parsed.user_name = trim(raw_header.user_name).replace('\x00', '')
    parsed.group_name = trim(raw_header.group_name).replace('\x00', '')

    device_major_str = trim(raw_header.device_major).rstrip('\x00')
    device_minor_str = trim(raw_header.device_minor).rstrip('\x00')

    parsed.device_major = int(device_major_str, 8) if device_major_str.isdigit() else 0
    parsed.device_minor = int(device_minor_str, 8) if device_minor_str.isdigit() else 0

    return parsed


def get_type_from_char(raw_type):
    if raw_type in [TAR_T_NORMAL1, TAR_T_NORMAL2]:
        return EntryType.T_NORMAL
    elif raw_type == TAR_T_HARD:
        return EntryType.T_HARDLINK
    elif raw_type == TAR_T_SYMBOLIC:
        return EntryType.T_SYMBOLIC
    elif raw_type == TAR_T_CHARSPECIAL:
        return EntryType.T_CHARSPECIAL
    elif raw_type == TAR_T_BLOCKSPECIAL:
        return EntryType.T_BLOCKSPECIAL
    elif raw_type == TAR_T_DIRECTORY:
        return EntryType.T_DIRECTORY
    elif raw_type == TAR_T_FIFO:
        return EntryType.T_FIFO
    elif raw_type == TAR_T_CONTIGUOUS:
        return EntryType.T_CONTIGUOUS
    elif raw_type == TAR_T_GLOBALEXTENDED:
        return EntryType.T_GLOBALEXTENDED
    elif raw_type == TAR_T_EXTENDED:
        return EntryType.T_EXTENDED
    else:
        return EntryType.T_OTHER

def read_tar(f, callbacks, context_data):
    empty_count = 0
    entry_index = 0
    while empty_count < 2:
        buffer = f.read(TAR_BLOCK_SIZE)
        if len(buffer) < TAR_BLOCK_SIZE:
            break

        header = parse_header(buffer)
        if not header.filename:
            empty_count += 1
            continue

        header_translated = translate_header(header)
        if 'header_cb' in callbacks:
            callbacks['header_cb'](header_translated, entry_index, context_data)

        num_blocks = get_num_blocks(header_translated.filesize)
        for i in range(num_blocks):
            buffer = f.read(TAR_BLOCK_SIZE)
            if len(buffer) < TAR_BLOCK_SIZE:
                break

            current_data_size = get_last_block_portion_size(header_translated.filesize) if i == num_blocks - 1 else TAR_BLOCK_SIZE
            if 'data_cb' in callbacks:
                callbacks['data_cb'](header_translated, entry_index, context_data, buffer[:current_data_size])

        if 'end_cb' in callbacks:
            callbacks['end_cb'](header_translated, entry_index, context_data)
        entry_index += 1

def read_tar_file(file_path, callbacks, context_data):
    with open(file_path, 'rb') as f:
        read_tar(f, callbacks, context_data)
            
#########################################################################

def test_pc():
    def dump_header(header, include_user_info = False):
        print("===========================================")
        print(f"      filename: {header.filename}")
        print(f"      filemode: {hex(header.filemode)} ({header.filemode})")
        print(f"           uid: {hex(header.uid)} ({header.uid})")
        print(f"           gid: {hex(header.gid)} ({header.gid})")
        print(f"      filesize: {hex(header.filesize)} ({header.filesize})")
        print(f"         mtime: {hex(header.mtime)} ({header.mtime})")
        print(f"      checksum: {hex(header.checksum)} ({header.checksum})")
        print(f"          type: {header.type}")
        print(f"   link_target: {header.link_target}")
        print()
        if (include_user_info):
            print(f"     ustar ind: {header.ustar_indicator}")
            print(f"     ustar ver: {header.ustar_version}")
            print(f"     user name: {header.user_name}")
            print(f"    group name: {header.group_name}")
            print(f"device (major): {header.device_major}")
            print(f"device (minor): {header.device_minor}")
            print()
        print(f"  data blocks = {get_num_blocks(header.filesize)}")
        print(f"  last block portion = {get_last_block_portion_size(header.filesize)}")
        print("-------------------------------------------")

    
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

    # Example usage:
    def header_callback(header, entry_index, context_data):
        if header.type == EntryType.T_NORMAL:
            print(f"Header Callback: Entry {entry_index}")
            dump_header(header)
            file_name = header.filename.replace("./", "out/")
            remove_file(file_name)

    def data_callback(header, entry_index, context_data, block):
        if header.type == EntryType.T_NORMAL:
            print(f"Data Callback: Entry {entry_index}, Length: {len(block)}")
            file_name = header.filename.replace("./", "out/")
             # Ensure directory exists
            create_directories(file_name)
            # Write the data block to file
            with open(file_name, 'ab') as file:
                file.write(block)

    def end_callback(header, entry_index, context_data):
        if header.type == EntryType.T_NORMAL:
            print(f"End Callback: Entry {entry_index}")

    callbacks = {
        'header_cb': header_callback,
        'data_cb': data_callback,
        'end_cb': end_callback
    }

    context_data = {}

    # Call the function to read a TAR file
    read_tar_file('releases/release.tar', callbacks, context_data)

#test_pc()