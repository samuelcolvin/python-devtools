import re


def normalise_output(s):
    s = re.sub(r':\d{2,}', ':<line no>', s)
    s = re.sub(r'(at 0x)\w+', r'\1<hash>', s)
    s = s.replace('\\', '/')
    return s
