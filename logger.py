"""

This logger is a slightly modified and merged version of smort-agenda and micg's logger. for more, visit:

https://github.com/Chromatic-Vision/smort-agenda/blob/main/logger.py
https://github.com/huu-bo/micg/blob/main/logger.py

"""


from datetime import datetime

import pygame
import os
import io
import traceback


def _get_log(message, color, type) -> str:
    if type not in [0, 1, 2]:
        raise ValueError('unknown logger._get_log() type')

    out = ""

    if color:
        out += "\33[34m"

    out += "["
    out += datetime.now().strftime("%H:%M:%S")
    out += " / "
    out += str(pygame.time.get_ticks())
    out += "] "

    if color:
        if type == 0:
            out += "\033[32m"
        elif type == 1:
            out += "\033[33m"
        elif type == 2:
            out += "\033[31m"

    if type == 0:
        out += "[INFO]"
    elif type == 1:
        out += "[WARN]"
    elif type == 2:
        out += "[ERROR]"

    out += " "

    if color:
        out += "\33[36m"

    out += "("
    out += trace(color)

    if color:
        out += "\33[36m"

    out += ") "

    if color:
        if type == 2:
            out += "\33[31m"
        else:
            out += "\33[0m"

    out += message

    if not color:
        out += "\n"

    return out


def log(message):
    print(_get_log(message, True, 0))

    with open('latest.log', 'a', encoding="UTF-8") as f:
        f.write(_get_log(message, False, 0))


def warn(message):
    print(_get_log(message, True, 1))

    with open('latest.log', 'a', encoding="UTF-8") as f:
        f.write(_get_log(message, False, 1))


def error(message):
    print(_get_log(message, True, 2))

    with open('latest.log', 'a', encoding="UTF-8") as f:
        f.write(_get_log(message, False, 2))


def reset_log():
    if "latest.log" not in os.listdir('.'):
        with open("latest.log", 'w', encoding="UTF-8") as f:
            f.write("")
            return

    with open("latest.log", "w", encoding="UTF-8") as f2:
        f2.truncate()


def trace(colors: bool) -> str:
    trace = io.StringIO()
    traceback.print_stack(file=trace)
    trace_string = trace.getvalue()
    trace.close()
    trace_string_formatted = ''
    space = False
    even = True
    for c in trace_string:
        if c == '\n':
            if not even:
                trace_string_formatted += ';'
                even = True
            else:
                even = False

            trace_string_formatted += ' '
            space = True
        elif c == ' ':
            pass
        else:
            space = False

        if not space:
            trace_string_formatted += c

    trace_string_formatted2 = ''
    filename = ''
    state = 0
    line = ''
    i = 0
    while i < len(trace_string_formatted):
        c = trace_string_formatted[i]

        if state == 0:
            if c == '"':
                state = 1
        elif state == 1:
            if c != '"':
                filename += c
            else:
                if colors:
                    trace_string_formatted2 += '\33[36m'
                trace_string_formatted2 += os.path.basename(filename)
                filename = ''
                state = 2

        elif state == 2:

            j = i + 7

            while j < len(trace_string_formatted) and trace_string_formatted[j] != ',':
                line += trace_string_formatted[j]

                j += 1
            state = 3
            i = j

        elif state == 3:
            j = i + 4
            func = ''
            while j < len(trace_string_formatted) and trace_string_formatted[j] != ' ':
                func += trace_string_formatted[j]
                j += 1
            state = 4

            trace_string_formatted2 += f'/{func}:{line}, '
            line = ''
        elif state == 4:
            if trace_string_formatted[i] == ';':  # TODO: you can't have a semicolon in the python
                state = 0

        i += 1

    remove = -4

    lt = trace_string_formatted2[:-2].split(", ")
    trace_string_formatted3 = ""

    for i in range(5):
        try:
            trace_string_formatted3 = str(lt[remove + i]).replace(".py", "")
        except IndexError:
            continue
        else:
            trace_string_formatted3 = str(lt[remove + i]).replace(".py", "")
            break

    return trace_string_formatted3 # TODO: ?????