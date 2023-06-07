import time
import threading
import pygame

import flashbox
import logger

logger.reset_log()
logger.log(f"Initializing Flashbox {flashbox.VERSION}...")

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.mixer.init()
pygame.init()

size = (0, 0)
screen = pygame.display.set_mode(size, pygame.RESIZABLE)
size = screen.get_size()

f = flashbox.Flashbox(screen)

FPS = 60
clock = pygame.time.Clock()

logger.log(f"Screen size: {size[0]}, {size[1]}")

pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.TEXTINPUT, pygame.MOUSEBUTTONUP])
pygame.display.set_caption(f"Flashbox {flashbox.VERSION}")
pygame.display.set_icon(pygame.image.load("images/flashbox.ico"))

run = 1

f.load()

class PeriodicSleeper(threading.Thread):
    def __init__(self, task_function, period):
        super().__init__()
        self.task_function = task_function
        self.period = period
        self.i = 0
        self.t0 = time.time()
        self.start()

    def sleep(self):
        self.i += 1
        delta = self.t0 + self.period * self.i - time.time()
        if delta > 0:
            time.sleep(delta)

    def run(self):
        while True:
            self.task_function()
            self.sleep()

if run:
    sleeper = PeriodicSleeper(f.update_time, 0.001)

while run:
    run = f.run
    clock.tick(FPS)
    f.update()
    f.draw()
    pygame.display.update()

logger.log("Not anymore inside the loop! Quitting...")
f.save()
pygame.quit()
