import os
import asyncio
import curses
import time
import random

from itertools import cycle
from curses_tools import draw_frame, read_controls, get_frame_size


TIC_TIMEOUT = 0.1
ROW_SPEED = 5
COLUMN_SPEED = 5
STARS_COUNT = 50
COROUTINES = []


class EventLoopCommand():

    def __await__(self):
        return (yield self)


class Sleep(EventLoopCommand):

    def __init__(self, seconds):
        self.seconds = seconds


def get_random_xy(max_x, max_y):
    return random.randint(1, max_x - 2), random.randint(1, max_y - 2)


def get_center_xy(max_x, max_y):
    return max_x / 2, max_y / 2


def get_random_star():
    return random.choice('+*.:')


def get_random_column(max_y):
    return random.randint(1, max_y - 2)


def read_file(filepath):
    with open(filepath, "r") as my_file:
        return my_file.read()


def get_all_files_in_folder(folder_path):
    file_contents = []

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
                file_contents.append(content)

    return file_contents


def get_starship_frames():
    rocket_frame_1 = read_file("frames/rocket_frame_1.txt")
    rocket_frame_2 = read_file("frames/rocket_frame_2.txt")
    return rocket_frame_1, rocket_frame_2


def get_garbage_frames():
    garbage_frames = get_all_files_in_folder("frames/garbage")
    return garbage_frames


async def sleep(tics=0):
    for _ in range(tics):
        await asyncio.sleep(0)


async def blink(canvas, row, column, symbol='*'):

    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await Sleep(2)

        canvas.addstr(row, column, symbol)
        await Sleep(0.3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await Sleep(0.5)

        canvas.addstr(row, column, symbol)
        await Sleep(0.3)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


def control_starship(canvas, current_row, current_column, frame):
    rows_direction, columns_direction, space_pressed = read_controls(canvas)
    frame_row, frame_column = get_frame_size(frame)
    max_rows, max_columns = canvas.getmaxyx()

    new_row = current_row + rows_direction * ROW_SPEED
    new_column = current_column + columns_direction * COLUMN_SPEED

    if new_row <= 0 or new_row + frame_row >= max_rows:
        new_row = current_row
    if new_column <= 0 or new_column + frame_column >= max_columns:
        new_column = current_column
    return new_row, new_column


async def animate_spaceship(canvas, current_row, current_column):
    for frame in cycle(item for item in get_starship_frames() for _ in range(2)):
        draw_frame(canvas, current_row, current_column, frame)
        await asyncio.sleep(0)

        new_row, new_column = control_starship(canvas, current_row, current_column, frame)
        draw_frame(canvas, current_row, current_column, frame, negative=True)
        current_row, current_column = new_row, new_column


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed


async def fill_orbit_with_garbage(canvas):
    _, max_y = curses.window.getmaxyx(canvas)
    garbage_frames = get_garbage_frames()
    while True:
        column = get_random_column(max_y)
        garbage_frame = random.choice(garbage_frames)
        COROUTINES.extend([fly_garbage(canvas, column=column, garbage_frame=garbage_frame)])

        await sleep(tics=5)


def draw(canvas):
    curses.curs_set(False)
    canvas.border()
    canvas.nodelay(True)
    max_x, max_y = curses.window.getmaxyx(canvas)

    global COROUTINES
    COROUTINES.extend([blink(canvas, *get_random_xy(max_x, max_y), get_random_star()) for _ in range(STARS_COUNT)])
    COROUTINES.extend([animate_spaceship(canvas, *get_center_xy(max_x, max_y))])
    COROUTINES.extend([fill_orbit_with_garbage(canvas)])

    while COROUTINES:
        for coroutine in COROUTINES.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                COROUTINES.remove(coroutine)
        time.sleep(TIC_TIMEOUT)
        canvas.refresh()


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
