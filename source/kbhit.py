# Source code: https://code.activestate.com/recipes/572182-how-to-implement-kbhit-on-linux/
import sys
import termios
from select import select
import os

# save the terminal settings
fd = sys.stdin.fileno()
new_term = termios.tcgetattr(fd)
old_term = termios.tcgetattr(fd)

# new terminal setting unbuffered
new_term[3] = (new_term[3] & ~termios.ICANON & ~termios.ECHO)


# switch to normal terminal
def set_normal_term():
    termios.tcsetattr(fd, termios.TCSAFLUSH, old_term)


# switch to unbuffered terminal
def set_curses_term():
    termios.tcsetattr(fd, termios.TCSAFLUSH, new_term)


def kbhit():
    dr, dw, de = select([sys.stdin], [], [], 0)
    return dr != []
