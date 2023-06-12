"""

Flashbox v0.5b by Chromatic Vision. For more, visit https://chromatic-vision.github.io

"""

import json
import os
import platform
import webbrowser
import pygame
import random

from pathlib import Path

import logger

VERSION = "v0.5c"

def play_sound(sound):
    pygame.mixer.music.stop()
    pygame.mixer.Sound.play(sound)

def smash():
    pass


class Flashbox:

    def __init__(self, screen: pygame.Surface):

        self.config_file = "config.json"

        self.run = 1
        self.screen = screen
        self.size = screen.get_size()

        self.buttons = [
            Flashbox.Button(self, self.size[0] - 116, 5, 50, 50, 0, "!"),
            Flashbox.Button(self, self.size[0] - 55, 5, 50, 50, 0, "?", x_offset=1),
            Flashbox.Button(self, 5, 5, 50, 50, 1, "<"),
            Flashbox.Button(self, self.size[0] / 3 - 100, 270, 605, 50, 1, "Create shortcut on your desktop...")
        ]

        self.digits = 1
        self.amount = 4
        self.seconds = 2.5

        self.t = 0
        self.cs = 5
        self.phase = 0

        self.first_refresh_done = False

        self.total_sum = 0
        self.displayed_amount = 0
        self.last_displayed_number = 0

        self.input = ""
        self.correct = -1

        self.countdown_seconds = 4
        self.render_countdown = False
        self.number_font_size = 150

        self.number_font = pygame.font.Font("fonts/abacus.ttf", self.number_font_size)
        self.normal_font = pygame.font.Font("fonts/noto-sans-mono-light.ttf", 25)

        self.tournament_mode = False

    def create_shortcut(self):

        import main

        if platform.system() == "Windows":
            try:
                import winshell
                from win32com.client import Dispatch

                path = os.path.join(os.path.join(os.environ["USERPROFILE"]), "Desktop") + "\\Flashbox.lnk"
                target = os.path.abspath(main.__file__)
                work_dir = os.path.dirname(os.path.abspath(main.__file__))

                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(path)
                shortcut.Targetpath = target
                shortcut.WorkingDirectory = work_dir
                shortcut.save()

            except ModuleNotFoundError:
                try:
                    path = Path(os.path.join(os.path.join(os.environ["USERPROFILE"]), "Desktop") + "\\Flashbox.lnk")
                    target = Path(os.path.abspath(main.__file__))

                    path.symlink_to(target)
                except Exception as e:
                    logger.warn("Could not create shortcut file on your desktop. Probably unsupported windows version?")
                    logger.error(repr(e))
                    pass

        else:
            try:
                link = Path("~/Desktop/Flashbox")
                target = Path(os.path.realpath(main.__file__))

                link.symlink_to(target)
            except Exception as e:
                logger.warn(f'Could not create shortcut file on your desktop. Probably unsupported os "{platform.system()}"?')
                logger.error(repr(e))

    def save_config(self, filename):
        with open(filename, 'w') as file:
            data = {
                "digits": self.digits,
                "amount": self.amount,
                "total_seconds": self.seconds,
                "countdown_seconds": self.countdown_seconds,
                "render_countdown": self.render_countdown,
                "number_font_size": self.number_font_size,
                "tournament_mode": self.tournament_mode
            }

            json.dump(data, file)

    def load_config(self, filename):

        if filename not in os.listdir('.'):
            logger.warn("No config file found! Creating new...")

            self.save_config(filename)
            return

        with open(filename, "r") as file:
            try:
                data: dict = json.load(file)
            except json.decoder.JSONDecodeError as e:
                logger.error(f"Syntax error (JSONDecodeError) occurred while trying to load json '{filename}':")
                file.seek(0)
                logger.error(str(e) + ": '" + str(file.read()) + "'")
                return

            self.digits = data["digits"]
            self.amount = data["amount"]
            self.seconds = data["total_seconds"]
            self.countdown_seconds = data["countdown_seconds"]
            self.render_countdown = data["render_countdown"]
            self.number_font_size = data["number_font_size"]
            self.tournament_mode = data["tournament_mode"]

            self.number_font = pygame.font.Font("fonts/abacus.ttf", self.number_font_size)

    class Inner(object):
        pass

    def Button(self, x, y, width, height, render_phase, button_text='Button', x_offset=0, y_offset=0):

        parent = self

        class Button(Flashbox.Inner):
            def __init__(self, x, y, width, height, render_phase, button_text='Button', x_offset=0, y_offset=0):
                self.x = x
                self.y = y
                self.x_offset = x_offset
                self.y_offset = y_offset
                self.width = width
                self.height = height
                self.render_phase = render_phase
                self.button_text = button_text
                self.clicked = False

                self.fill_colors = {
                    'normal': (255, 255, 255),
                    'hover': (100, 100, 100),
                    'pressed': (100, 100, 100)
                }

                self.button_surface = pygame.Surface((self.width, self.height))
                self.button_rect = pygame.Rect(self.x, self.y, self.width, self.height)

            def update_mouse(self):

                mouse = pygame.mouse.get_pos()

                if self.button_rect.collidepoint(mouse):
                    self.clicked = True

            def draw(self):

                c = 0

                mouse = pygame.mouse.get_pos()

                if self.button_rect.collidepoint(mouse):
                    c = 1

                    if pygame.mouse.get_pressed()[0]:
                        c = 2
                    else:
                        self.clicked = False
                else:
                    self.clicked = False

                pygame.draw.rect(parent.screen, self.fill_colors['normal'] if c == 0 else (self.fill_colors['hover'] if c == 1 else self.fill_colors['pressed']), self.button_rect, 0 if self.button_rect.collidepoint(mouse) else 2)
                parent.render_normal_text(str(self.button_text), self.x + self.x_offset + 17, self.y + self.y_offset + 7, (255, 255, 255))

        return Button(x, y, width, height, render_phase, button_text, x_offset, y_offset)

    def save(self):
        self.save_config(self.config_file)

    def load(self):
        self.load_config(self.config_file)

    def update_time(self):

        self.t += 1

        if self.phase == 0:

            if pygame.key.get_pressed()[pygame.K_m]:
                if self.t % 80 == 0:
                    self.seconds -= 0.01

        if self.phase == 2:  # reset and start countdown

            self.t = 0
            self.cs = self.countdown_seconds
            self.first_refresh_done = False
            self.total_sum = 0
            self.displayed_amount = 0
            self.last_displayed_number = -1
            self.input = ""
            self.correct = -1

            self.phase = 3

        if self.phase == 3:

            if self.cs == 2 and self.t == 232: # TODO: ???
                play_sound(pygame.mixer.Sound("sounds/start.wav"))

            if self.cs <= 0:
                self.phase = 4
                self.t = 0
            elif self.t >= 1000:
                self.cs -= 1
                self.t = 0

        if self.phase == 4:

            if not self.first_refresh_done:
                self.refresh_numbers()
                self.first_refresh_done = True
            elif self.displayed_amount >= self.amount:
                if self.t >= self.seconds / self.amount * 1000:
                    self.phase = 5
            elif self.t >= self.seconds / self.amount * 1000:
                self.refresh_numbers()

        if self.phase == 6:

            if self.t >= 5000:
                if self.correct == 0:
                    self.phase = 7
                elif self.correct == 1:
                    self.phase = 0

                self.t = 0

        if self.phase == 7:
            if self.t >= 5000:
                self.phase = 0


    def update(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.run = 0

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.run = 0

                if self.phase == 0:

                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self.phase = 2
                        logger.log(f"Starting! digits={self.digits}, amount={self.amount}, seconds={self.seconds}")

                    if event.key == pygame.K_LEFT and self.digits - 1 > 0:
                        self.digits -= 1
                    if event.key == pygame.K_RIGHT:
                        self.digits += 1
                    if event.key == pygame.K_DOWN and self.amount - 1 > 0:
                        self.amount -= 1
                    if event.key == pygame.K_UP:
                        self.amount += 1
                    if event.key == pygame.K_COMMA and self.seconds - 1 > 0:
                        self.seconds -= 1
                    if event.key == pygame.K_PERIOD:
                        self.seconds += 1

                elif self.phase == 1:

                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self.phase = 0

                    if event.key == pygame.K_LEFT and self.countdown_seconds - 1 > 0:
                        self.countdown_seconds -= 1
                    if event.key == pygame.K_RIGHT:
                        self.countdown_seconds += 1
                    if event.key == pygame.K_DOWN and self.number_font_size - 1 > 0:
                        self.number_font_size -= 1
                        self.number_font = pygame.font.Font("fonts/abacus.ttf", 130)
                    if event.key == pygame.K_UP:
                        self.number_font_size += 1
                        self.number_font = pygame.font.Font("fonts/abacus.ttf", 130)
                    if event.key == pygame.K_COMMA and self.render_countdown:
                        self.render_countdown = False
                    if event.key == pygame.K_PERIOD and not self.render_countdown:
                        self.render_countdown = True
                    if event.key == pygame.K_n and self.tournament_mode:
                        self.tournament_mode = False
                    if event.key == pygame.K_m and not self.tournament_mode:
                        self.tournament_mode = True

                elif self.phase == 5:

                    if event.key == pygame.K_BACKSPACE or event.key == pygame.K_DELETE:

                        self.input = self.input[:-1]

                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:

                        if self.tournament_mode:
                            self.phase = 6

                            play_sound(pygame.mixer.Sound("sounds/answer_reveal.wav"))
                        else:

                            if self.input == "":
                                return

                            self.phase = 6

                            try:
                                self.correct = int(int(self.input) == self.total_sum)
                            except ValueError:
                                logger.warn("You are typing invalid numbers!!")
                                return

                            if self.correct == 0:
                                play_sound(pygame.mixer.Sound("sounds/incorrect.wav"))
                            elif self.correct == 1:
                                play_sound(pygame.mixer.Sound("sounds/correct.wav"))

                elif self.phase == 6:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        if self.correct == -1:
                            self.phase = 0
                        elif self.correct == 0:
                            self.phase = 7
                        elif self.correct == 1:
                            self.phase = 0

                elif self.phase == 7:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self.phase = 0

            if event.type == pygame.TEXTINPUT:
                if self.phase == 5:
                    if event.text.isnumeric():
                        if event.text == "" or event.text == "0":
                            if self.input == "0":
                                return
                        self.input += event.text

            if event.type == pygame.MOUSEBUTTONUP:

                for button in self.buttons:

                    if button.render_phase != self.phase:
                        continue

                    button.update_mouse()

            for i in range(len(self.buttons)):

                button = self.buttons[i]

                if button.render_phase != self.phase:
                    continue

                if button.clicked:
                    if i == 0:
                        self.phase = 1
                    elif i == 1:
                        webbrowser.open("https://chromatic-vision.github.io/flashbox")
                        logger.log("Navigating to help page on your browser...")
                    elif i == 2:
                        self.phase = 0
                    elif i == 3:
                        self.create_shortcut()
                    else:
                        logger.warn("?!")

                button.draw()

    def draw(self):

        screen = self.screen

        screen.fill((0, 0, 0))

        for button in self.buttons:
            if button.render_phase != self.phase:
                continue

            button.draw()

        if self.phase == 0:

            self.render_normal_text("Flashbox " + VERSION, 5, 5, (255, 255, 255))

            self.render_normal_text(f"Digits: {self.digits}", self.size[0] / 3 - 100, 100, (255, 255, 255))
            self.render_normal_text(f"Amount: {self.amount}", self.size[0] / 3 - 100, 135, (255, 255, 255))
            self.render_normal_text(f"Total seconds: {round(self.seconds, 3)}", self.size[0] / 3 - 100, 170, (255, 255, 255))

            self.render_normal_text("decrease / increase", self.size[0] / 3 + 320, 65, (255, 255, 255))
            self.render_normal_text("← / →", self.size[0] / 3 + 425, 100, (255, 255, 255))
            self.render_normal_text("↓ / ↑", self.size[0] / 3 + 425, 135, (255, 255, 255))
            self.render_normal_text("M", self.size[0] / 3 + 385, 170, (255, 255, 255))
            self.render_normal_text(", / .", self.size[0] / 3 + 425, 170, (255, 255, 255))

            self.render_normal_text("Press esc to exit, space/enter to start.", 5, self.size[1] - 40, (255, 255, 255))

        elif self.phase == 1:
            self.render_normal_text(f"Countdown seconds: {self.countdown_seconds}", self.size[0] / 3 - 100, 100, (255, 255, 255))
            self.render_normal_text(f"Font size: {self.number_font_size}", self.size[0] / 3 - 100, 135, (255, 255, 255))
            self.render_normal_text(f"Render countdown: {self.render_countdown}", self.size[0] / 3 - 100, 170, (255, 255, 255))
            self.render_normal_text(f"Tournament mode: {self.tournament_mode}", self.size[0] / 3 - 100, 205, (255, 255, 255))

            self.render_normal_text("decrease / increase", self.size[0] / 3 + 320, 65, (255, 255, 255))
            self.render_normal_text("← / →", self.size[0] / 3 + 425, 100, (255, 255, 255))
            self.render_normal_text("↓ / ↑", self.size[0] / 3 + 425, 135, (255, 255, 255))
            self.render_normal_text(", / .", self.size[0] / 3 + 425, 170, (255, 255, 255))
            self.render_normal_text("N / M", self.size[0] / 3 + 425, 205, (255, 255, 255))

        elif self.phase == 3:
            if self.render_countdown:
                if self.cs > 0:
                    self.render_number(f"{self.cs}", (255, 255, 255))
            else:
                if self.cs >= 4:
                    screen.blit(pygame.font.Font("fonts/noto-sans-mono-light.ttf", 60).render(f"{self.digits}d {self.amount}x {round(self.seconds, 3)}s", True, (255, 255, 255)),(self.get_middle_x_font(f"{self.digits}d {self.amount}x {round(self.seconds, 3)}s", pygame.font.Font("fonts/noto-sans-mono-light.ttf", 60)), self.get_middle_y_font(f"{self.digits}d {self.amount}x {round(self.seconds, 3)}s", pygame.font.Font("fonts/noto-sans-mono-light.ttf", 60))))

        elif self.phase == 4:
            if self.last_displayed_number > -1 and self.t <= self.seconds / self.amount * 1000 * 0.725:
                self.render_number(f"{self.last_displayed_number}", (0, 255, 0))

        elif self.phase == 5:

            if self.tournament_mode:
                self.render_normal_text("Fill in your answers...", 5, 5, (255, 255, 255))
            else:
                self.render_normal_text("Write your answer down...", 5, 5, (255, 255, 255))
                self.render_number(f"{self.input}", (0, 0, 255))

        elif self.phase == 6:

            if self.tournament_mode:

                screen.blit(pygame.font.Font("fonts/noto-sans-mono-light.ttf", 60).render("Answer:", True, (255, 255, 255)), (200, self.size[1] / 2 - 200))
                self.render_number(f"{self.total_sum}", (255, 255, 0), self.size[0] - 225 - self.number_font.size(f"{self.total_sum}")[0])

                # ly = 85
                ly = round(self.number_font_size / 1.52941176471)

                pygame.draw.line(screen, (255, 255, 255), (200, self.size[1] / 2 + ly), (self.size[0] - 150, self.size[1] / 2 + ly), 5)

                # - 25

                pygame.draw.line(screen, (255, 255, 255), (self.size[0] - 185, self.size[1] / 2 + ly - 15), (self.size[0] - 200, self.size[1] / 2 + ly + 15), 5)
                pygame.draw.line(screen, (255, 255, 255), (self.size[0] - 170, self.size[1] / 2 + ly - 15), (self.size[0] - 185, self.size[1] / 2 + ly + 15), 5)
                smash

            else:
                if self.correct == 0:
                    self.draw_incorrect_cross(self.size[0] / 2, self.size[1] / 2 + 30)
                else:
                    self.draw_correct_circle(self.size[0] / 2 - 10, self.size[1] / 2, 100)

        elif self.phase == 7:
            self.render_number(f"{self.total_sum}", (255, 255, 0))

    def random_with_custom_digits(self, n):

        range_start = 10 ** (n - 1)
        range_end = (10 ** n) - 1

        for j in range(range_end):

            result = random.randint(range_start, range_end)

            if result == self.last_displayed_number:
                continue
            else:
                break

        return result

    def refresh_numbers(self): # TOOD: remove the lag

        self.t = 0

        self.last_displayed_number = self.random_with_custom_digits(self.digits)

        play_sound(pygame.mixer.Sound("sounds/number_update.wav"))

        self.total_sum += self.last_displayed_number

        self.displayed_amount += 1

    def draw_correct_circle(self, x, y, r):
        pygame.draw.circle(self.screen, (50, 255, 50), (x, y), r, 15)
        pygame.draw.circle(self.screen, (50, 255, 50), (x, y), r / 1.65, 15)

    def draw_incorrect_cross(self, x, y):

        x -= 75
        y -= 100

        j = 150
        t = 12

        pygame.draw.polygon(self.screen, (255, 0, 0), ((x, y), (x - t, y + t), (x + j - t, y + j + t), (x + j, y + j)))
        pygame.draw.polygon(self.screen, (255, 0, 0), ((x + j - t, y), (x + j, y + t), (x, y + j + t), (x - t, y + j)))

    def get_middle_x_font(self, text: str, font: pygame.font.Font):
        return self.size[0] / 2 - font.size(text)[0] / 2 - 3

    def get_middle_y_font(self, text: str, font: pygame.font.Font):
        return self.size[1] / 2 - font.size(text)[1] / 2

    def render_normal_text(self, text: str, x, y, color):
        self.screen.blit(self.normal_font.render(text, True, color), (x, y))

    def render_number(self, text: str, color, x=-32768, y=-32768):
        self.screen.blit(self.number_font.render(text, True, color), (x if x > -32768 else self.get_middle_x_font(text, self.number_font), y if y > -32768 else self.get_middle_y_font(text, self.number_font)))


