import re

def convert_to_ascii(input_string):
    return re.sub(r'[^\x00-\x7F]+', '', input_string)

def truncate_string_by_bytes(s, n):
    return s.encode('utf-8')[:n].decode('utf-8', 'ignore')
