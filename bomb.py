import asyncio
import time


class EventLoopCommand():

    def __await__(self):
        return (yield self)


class Sleep(EventLoopCommand):

    def __init__(self, seconds):
        self.seconds = seconds


async def do_ticking(amount_of_ticks, sound):
    for _ in range(amount_of_ticks):
        print(sound)
        await Sleep(1)


async def bang_the_bomb(amount_of_ticks=5, sound='tick'):
    clock = do_ticking(amount_of_ticks, sound)
    await clock
    print("BOOM!")

bombs = [
    bang_the_bomb(amount_of_ticks=3),
    bang_the_bomb(amount_of_ticks=5, sound='chick'),
    bang_the_bomb(amount_of_ticks=9, sound='click'),
]

# store timeout for each bomb coroutine
sleeping_bombs = [[0, bomb] for bomb in bombs]

while sleeping_bombs:
    # осторожно засыпаем так, чтобы не пропустить активацию бомб
    min_delay, _ = min(sleeping_bombs, key=lambda pair: pair[0])
    sleeping_bombs = [[timeout - min_delay, bomb] for timeout, bomb in sleeping_bombs]
    time.sleep(min_delay)

    # делим бомбы на активные и спящие
    active_bombs = [[timeout, bomb] for timeout, bomb in sleeping_bombs if timeout <= 0]
    sleeping_bombs = [[timeout, bomb] for timeout, bomb in sleeping_bombs if timeout > 0]

    for _, bomb in active_bombs:
        try:
            sleep_command = bomb.send(None)
        except StopIteration:
            continue  # выкидываем истощившуюся корутину
        seconds_to_sleep = sleep_command.seconds
        sleeping_bombs.append([seconds_to_sleep, bomb])