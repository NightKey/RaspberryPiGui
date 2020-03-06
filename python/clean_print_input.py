from __future__ import print_function
import sys

# Get the (current) number of lines in the terminal
import shutil
height = shutil.get_terminal_size().lines - 1

stdout_write_bytes = sys.stdout.buffer.write

# Some ANSI/VT100 Terminal Control Escape Sequences
CSI = b'\x1b['
CLEAR = CSI + b'2J'
CLEAR_LINE = CSI + b'2K'
SAVE_CURSOR = CSI + b's'
UNSAVE_CURSOR = CSI + b'u'

GOTO_INPUT = CSI + b'%d;0H' % (height + 1)

def emit(*args):
    stdout_write_bytes(b''.join(args))

def set_scroll(n):
    return CSI + b'0;%dr' % n