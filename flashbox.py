"""

Flashbox v0.7 by Chromatic Vision. For more, visit https://chromatic-vision.github.io/flashbox

"""

import itertools
import json
import os
import platform
import sys
import webbrowser
import pygame
import random

from collections import defaultdict
from pathlib import Path

import abacus
import logger

VERSION = "v0.7"

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
            Flashbox.Button(self, self.size[0] / 3 - 100, 300, 605, 50, 1, "Create shortcut on your desktop...")
        ]

        self.digits = 1
        self.amount = 2
        self.seconds = 4

        self.flash_display_rate = 0.55

        self.t = 0
        self.cs = 5
        self.phase = 0

        self.first_refresh_done = False

        self.abacus = abacus.SimpleAbacus()
        self.total_sum = 0
        self.refreshed_amount = 0
        self.last_displayed_number = 0

        self.input = ""
        self.correct = -1

        self.countdown_seconds = 5
        self.render_countdown = False
        self.number_font_size = 160

        self.number_font = pygame.font.Font("fonts/abacus.ttf", self.number_font_size)
        self.normal_font = pygame.font.Font("fonts/generic.ttf", 25)

        self.tournament_mode = False
        self.render_abacus = False

        self.reset_latest()

    def create_shortcut(self):

        original_exec_file_name = sys.argv[0]

        logger.log(f"Creating desktop shortcut that links to {original_exec_file_name}")

        if platform.system() == "Windows":
            try:
                import winshell
                from win32com.client import Dispatch

                path = os.path.join(os.path.join(os.environ["USERPROFILE"]), "Desktop") + "\\Flashbox.lnk"
                target = os.path.abspath(original_exec_file_name)
                work_dir = os.path.dirname(os.path.abspath(original_exec_file_name))

                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(path)
                shortcut.Targetpath = target
                shortcut.WorkingDirectory = work_dir
                shortcut.save()

            except ModuleNotFoundError:
                try:
                    path = Path(os.path.join(os.path.join(os.environ["USERPROFILE"]), "Desktop") + "\\Flashbox.lnk")
                    target = Path(os.path.abspath(original_exec_file_name))

                    path.symlink_to(target)
                except Exception as e:
                    logger.warn("Could not create shortcut file on your desktop. Probably unsupported windows version?")
                    logger.error(repr(e))
                    pass

        else:
            try:
                link = Path("~/Desktop/Flashbox")
                target = Path(os.path.realpath(original_exec_file_name))

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
                "tournament_mode": self.tournament_mode,
                "render_abacus": self.render_abacus
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

                logger.warn(f"Removing {filename} from the directory...")

                file.close()
                os.remove(filename)
                return

            try:

                self.digits = data["digits"]
                self.amount = data["amount"]
                self.seconds = data["total_seconds"]
                self.countdown_seconds = data["countdown_seconds"]
                self.render_countdown = data["render_countdown"]
                self.number_font_size = data["number_font_size"]
                self.tournament_mode = data["tournament_mode"]
                self.render_abacus = data["render_abacus"]
            except KeyError as e:

                logger.error(f"Malformed config file '{filename}' found! Probably outdated version?")
                logger.error("Malformed key(s):", e)
                logger.warn(f"Removing {filename} from the directory...")

                file.close()
                os.remove(filename)

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

                pygame.draw.rect(parent.screen, self.fill_colors['normal'] if c == 0 else (
                    self.fill_colors['hover'] if c == 1 else self.fill_colors['pressed']), self.button_rect,
                                 0 if self.button_rect.collidepoint(mouse) else 2)
                parent.render_normal_text(str(self.button_text), self.x + self.x_offset + 17,
                                          self.y + self.y_offset + 7, (255, 255, 255))

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

            if pygame.key.get_pressed()[pygame.K_SLASH]:
                if self.t % 80 == 0:
                    self.seconds += 0.01

        if self.phase == 2:  # reset and start countdown

            self.t = 0
            self.cs = self.countdown_seconds
            self.first_refresh_done = False
            self.total_sum = 0
            self.refreshed_amount = 0
            self.last_displayed_number = -1
            self.input = ""
            self.correct = -1
            self.abacus.reset()
            self.reset_latest()
            pygame.mouse.set_visible(False)
            move_mouse() # otherwise mouse doesn't update and will remain on the screen

            self.phase = 3

        if self.phase == 3:

            if self.cs == 2 and self.t == 232:  # TODO: ???
                play_sound(pygame.mixer.Sound("sounds/start.wav"))

            if self.cs == 1 and self.t == 1:
                self.pre_refresh_numbers()

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
            elif self.refreshed_amount >= self.amount:
                if self.t >= self.seconds / self.amount * 1000:
                    self.phase = 5
            elif self.t == round(self.seconds / self.amount * 1000 * self.flash_display_rate) + 5:
                self.pre_refresh_numbers()
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
                self.t = 0

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
                        self.number_font = pygame.font.Font("fonts/abacus.ttf", self.number_font_size)
                    if event.key == pygame.K_UP:
                        self.number_font_size += 1
                        self.number_font = pygame.font.Font("fonts/abacus.ttf", self.number_font_size)
                    if event.key == pygame.K_COMMA and self.render_countdown:
                        self.render_countdown = False
                    if event.key == pygame.K_PERIOD and not self.render_countdown:
                        self.render_countdown = True
                    if event.key == pygame.K_n and self.render_abacus:
                        self.render_abacus = False
                    if event.key == pygame.K_m and not self.render_abacus:
                        self.render_abacus = True
                    if event.key == pygame.K_v and self.tournament_mode:
                        self.tournament_mode = False
                    if event.key == pygame.K_b and not self.tournament_mode:
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

                            try:
                                self.correct = int(int(self.input) == self.total_sum)
                            except ValueError:
                                logger.warn("You are typing invalid numbers!!")
                                return

                            if self.correct == 0:
                                play_sound(pygame.mixer.Sound("sounds/incorrect.wav"))
                            elif self.correct == 1:
                                play_sound(pygame.mixer.Sound("sounds/correct.wav"))

                            self.phase = 6
                            self.t = 0
                            return

                elif self.phase == 6:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:

                        if self.correct == 0:
                            self.phase = 7
                            self.t = 0
                        elif self.correct == 1 or self.correct == -1:
                            self.phase = 0
                            self.t = 0

                            pygame.mouse.set_visible(True)
                            move_mouse()


                elif self.phase == 7:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self.phase = 0
                        self.t = 0
                        pygame.mouse.set_visible(True)
                        move_mouse()

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
            self.render_normal_text("M", self.size[0] / 3 + 380, 170, (255, 255, 255))
            self.render_normal_text(", / .", self.size[0] / 3 + 425, 170, (255, 255, 255))
            self.render_normal_text("/", self.size[0] / 3 + 525, 170, (255, 255, 255))

            self.render_normal_text("Press esc to exit, space/enter to start.", 5, self.size[1] - 40, (255, 255, 255))

        elif self.phase == 1:
            self.render_normal_text(f"Countdown seconds: {self.countdown_seconds}", self.size[0] / 3 - 100, 100, (255, 255, 255))
            self.render_normal_text(f"Font size: {self.number_font_size}", self.size[0] / 3 - 100, 135, (255, 255, 255))
            self.render_normal_text(f"Render countdown: {self.render_countdown}", self.size[0] / 3 - 100, 170, (255, 255, 255))
            self.render_normal_text(f"Render abacus: {self.render_abacus}", self.size[0] / 3 - 100, 205, (255, 255, 255))
            self.render_normal_text(f"Tournament mode: {self.tournament_mode}", self.size[0] / 3 - 100, 240, (255, 255, 255))

            self.render_normal_text("decrease / increase", self.size[0] / 3 + 320, 65, (255, 255, 255))
            self.render_normal_text("← / →", self.size[0] / 3 + 425, 100, (255, 255, 255))
            self.render_normal_text("↓ / ↑", self.size[0] / 3 + 425, 135, (255, 255, 255))
            self.render_normal_text(", / .", self.size[0] / 3 + 425, 170, (255, 255, 255))
            self.render_normal_text("N / M", self.size[0] / 3 + 425, 205, (255, 255, 255))
            self.render_normal_text("V / B", self.size[0] / 3 + 425, 240, (255, 255, 255))

        elif self.phase == 3:
            if self.render_countdown:
                if self.cs > 0:
                    self.render_number(f"{self.cs}", (255, 255, 255))
            else:
                if self.cs >= 4:
                    screen.blit(pygame.font.Font("fonts/generic.ttf", 60).render(
                        f"{self.digits}d {self.amount}x {round(self.seconds, 3)}s", True, (255, 255, 255)), (
                                self.get_middle_x_font(f"{self.digits}d {self.amount}x {round(self.seconds, 3)}s",
                                                       pygame.font.Font("fonts/generic.ttf", 60)),
                                self.get_middle_y_font(f"{self.digits}d {self.amount}x {round(self.seconds, 3)}s",
                                                       pygame.font.Font("fonts/generic.ttf", 60))))

        elif self.phase == 4:
            if self.last_displayed_number > -1 and self.t <= self.seconds / self.amount * 1000 * self.flash_display_rate:
                self.render_number(f"{self.last_displayed_number}", (0, 255, 0))

            if self.render_abacus:
                self.draw_abacus()

        elif self.phase == 5:

            self.render_normal_text("Fill in your answers...", 5, 5, (255, 255, 255))

            if not self.tournament_mode:
                self.render_number(f"{self.input}", (0, 0, 255))

        elif self.phase == 6:

            if self.tournament_mode:

                screen.blit(pygame.font.Font("fonts/generic.ttf", 60).render("Answer:", True, (255, 255, 255)), (200, self.size[1] / 2 - 200))
                self.render_number(f"{self.total_sum}", (255, 255, 0), self.size[0] - 225 - self.number_font.size(f"{self.total_sum}")[0])

                # ly = 85
                ly = round(self.number_font_size / 1.52941176471)

                pygame.draw.line(screen, (255, 255, 255), (200, self.size[1] / 2 + ly), (self.size[0] - 150, self.size[1] / 2 + ly), 5)

                pygame.draw.line(screen, (255, 255, 255), (self.size[0] - 185, self.size[1] / 2 + ly - 15), (self.size[0] - 200, self.size[1] / 2 + ly + 15), 5)
                pygame.draw.line(screen, (255, 255, 255), (self.size[0] - 170, self.size[1] / 2 + ly - 15), (self.size[0] - 185, self.size[1] / 2 + ly + 15), 5)

            else:
                if self.correct == 0:
                    self.draw_incorrect_cross(self.size[0] / 2, self.size[1] / 2 + 30)
                else:
                    self.draw_correct_circle(self.size[0] / 2 - 10, self.size[1] / 2, 100)

        elif self.phase == 7:
            self.render_number(f"{self.total_sum}", (255, 255, 0))

    def count_carries(self, n1, n2):  # shhh

        n1, n2 = str(n1), str(n2)
        carry, answer = 0, 0

        for one, two in itertools.zip_longest(n1[::-1], n2[::-1], fillvalue='0'):
            carry = int(((int(one) + int(two) + carry) // 10) > 0)
            answer += ((int(one) + int(two) + carry) // 10) > 0
            carry += ((int(one) + int(two) + carry) // 10) > 0

        return answer

    def get_random(self, n):

        range_start = 10 ** (n - 1)
        range_end = (10 ** n) - 1

        result = random.randint(range_start, range_end)

        return result

    def get_max_carries(self, digits):

        if digits == 0:
            return "??????????????"
        elif digits == 1:
            return 1
        elif digits == 2:
            return 1
        elif digits == 3:
            return 2
        elif digits == 4:
            return 2
        elif digits == 5:
            return 3
        elif digits == 6:
            return 3
        elif digits == 7:
            return 4
        elif digits == 8:
            return 5
        elif digits == 9:
            return 6
        else:
            return 32767

    def get_next_number(self, n):

        max_carries = self.get_max_carries(n)

        while 1:

            res = self.get_random(n)

            if self.count_carries(res, self.total_sum) <= max_carries and check_for_same_digit(res):

                lres = [int(i) for i in str(res)]

                try:
                    lldn = [int(i) for i in str(self.last_displayed_number)]
                except ValueError:
                    return res

                valid = True

                for i in range(len(lres)):

                    if lres[i] == lldn[i]:
                        valid = False
                        break
                    else:
                        continue

                if valid:
                    break

        return res

    def pre_refresh_numbers(self):
        self.last_displayed_number = self.get_next_number(self.digits)
        self.total_sum += self.last_displayed_number

    def refresh_numbers(self):

        self.t = 0

        play_sound(pygame.mixer.Sound("sounds/number_update.wav"))
        self.abacus.add_value(self.last_displayed_number)

        self.refreshed_amount += 1

        self.write_latest(self.last_displayed_number)

    def write_latest(self, number):
        with open("latest.acf", "a") as f:
            f.write((10 - len(str(number))) * " " + str(number) + "\n")

            if self.refreshed_amount >= self.amount:
                f.write("==========\n")
                f.write((10 - len(str(self.total_sum))) * " " + str(self.total_sum))

    def reset_latest(self):
        with open("latest.acf", "w") as f:
            f.truncate()

    def draw_abacus(self):

        ax = 5

        pygame.draw.line(self.screen, (100, 100, 100), (5, self.size[1] - 100), (self.abacus.range * 20, self.size[1] - 100), 2)

        for i in range(self.abacus.range):

            vb = self.abacus.beads[i]
            upper, lower = abacus.get_vertical_beads_pos(vb.current_sum)

            # draw upper beads

            if upper == 0:
                pygame.draw.rect(self.screen, (255, 255, 255), (ax, self.size[1] - 130, 10, 10))
            elif upper == 1:
                pygame.draw.rect(self.screen, (255, 255, 255), (ax, self.size[1] - 115, 10, 10))
            else:
                logger.warn(f"Upper value of the vertical bead @ {i} is not 0 or 1?????????")

            # draw lower beads
            ay = self.size[1] - 108

            for j in range(5):

                ay += 15

                if j == lower:
                    continue

                pygame.draw.rect(self.screen, (255, 255, 255), (ax, ay, 10, 10))

            ax += 20

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
        self.screen.blit(self.number_font.render(text, True, color), (
        x if x > -32768 else self.get_middle_x_font(text, self.number_font),
        y if y > -32768 else self.get_middle_y_font(text, self.number_font)))


def check_for_same_digit(num):
    number = str(num)

    freq = defaultdict(int)
    n = len(number)

    for i in range(n):
        freq[int(number[i])] += 1

    freq_values = set(freq.values())

    if len(freq_values) == 1:
        return True

    return False

def play_sound(sound):
    pygame.mixer.music.stop()
    pygame.mixer.Sound.play(sound)

def move_mouse():
    pygame.mouse.set_pos((pygame.mouse.get_pos()[0] - 0.00069420, pygame.mouse.get_pos()[1]))