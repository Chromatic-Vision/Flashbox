"""

Huge thanks to pygame and my friends to make this project possible.

"""

import json
import os
import random
import webbrowser
import pygame
import logger
from enum import Enum

VERSION = "v0.4d"

size = (0, 0)

logger.reset_log()
logger.log(f"Initializing Flashbox {VERSION}...")

pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.mixer.init()
pygame.init()

screen = pygame.display.set_mode(size, pygame.RESIZABLE)
clock = pygame.time.Clock()
size = screen.get_size()  # different because (0, 0) makes it fit to the screen

logger.log(f"Screen size: {size[0]}, {size[1]}")

pygame.display.set_caption("Flashbox " + VERSION)
pygame.display.set_icon(pygame.image.load("images/flashbox.ico"))

class Language(Enum):
    ENGLISH = 1
    JAPANESE = 2

# configs
config_file = "config.json"
number_font_size = 115

render_countdown = True
countdown_seconds = 3
tournament_mode = False
current_lang = Language.ENGLISH

# system variables
digits = 1
amount = 6
seconds = 3.55

phase = 0
displayed_amount = 0
last_number = None
total_sum = 0
answer_input = ""

t = 0
cs = 0

def save_config(filename):
    with open(filename, 'w') as file:

        data = {
            "digits": digits,
            "amount": amount,
            "total_seconds": seconds,
            "countdown_seconds": countdown_seconds,
            "render_countdown": render_countdown,
            "number_font_size": number_font_size,
            "tournament_mode": tournament_mode
        }

        json.dump(data, file)

def load_config(filename):

    global digits
    global amount
    global seconds
    global countdown_seconds
    global render_countdown
    global number_font_size
    global tournament_mode

    if filename not in os.listdir('.'):

        logger.warn("No config file found! Creating new...")

        with open(filename, 'w') as file:
            json.dump({
                "digits": digits,
                "amount": amount,
                "total_seconds": seconds,
                "countdown_seconds": countdown_seconds,
                "render_countdown": render_countdown,
                "number_font_size": number_font_size,
                "tournament_mode": tournament_mode
            }, file)
            return

    with open(filename, "r") as file:
        try:
            data: dict = json.load(file)
        except json.decoder.JSONDecodeError as e:
            logger.error(f"Syntax error (JSONDecodeError) occurred while trying to load json '{config_file}':")
            file.seek(0)
            logger.error(str(e) + ": '" + str(file.read()) + "'")
            return

        digits = data["digits"]
        amount = data["amount"]
        seconds = data["total_seconds"]
        countdown_seconds = data["countdown_seconds"]
        render_countdown = data["render_countdown"]
        number_font_size = data["number_font_size"]
        tournament_mode = data["tournament_mode"]


logger.log(f"Loading config, filename: {config_file}")
load_config(config_file)
logger.log(f"Language set to {current_lang}")

# fonts
big_font = pygame.font.Font("fonts/abacus.ttf", number_font_size)
normal_text_font = pygame.font.Font("fonts/noto-sans-mono-light.ttf", 25)
japanese_text_font = pygame.font.Font("fonts/noto-sans-jp-light.ttf", 25)


def get_middle_x(text: str, font: pygame.font.Font):
    return size[0] / 2 - font.size(text)[0] / 2 - 3

def get_middle_y(text: str, font: pygame.font.Font):
    return size[1] / 2 - font.size(text)[1] / 2

def render_big_text(text, x, y, color, center: bool):
    screen.blit(big_font.render(text, True, color), (get_middle_x(text, big_font) if center else x, get_middle_y(text, big_font) if center else y))

def render_normal_text(text, x, y, color, center: bool):
    screen.blit(normal_text_font.render(text, True, color), (get_middle_x(text, normal_text_font) if center else x, get_middle_y(text, normal_text_font) if center else y))

def render_japanese_text(text, x, y, color, center: bool):
    screen.blit(japanese_text_font.render(text, True, color), (get_middle_x(text, japanese_text_font) if center else x, get_middle_y(text, japanese_text_font) if center else y))

def draw_correct_circle(x, y, r):
    pygame.draw.circle(screen, (0, 255, 0), (x, y), r, 5)
    pygame.draw.circle(screen, (0, 255, 0), (x, y), r / 2, 5)

def draw_incorrect_cross(x, y):

    x -= 60
    y -= 60

    pygame.draw.line(screen, (255, 0, 0), (x, y), (x + 100, y + 100), 8)
    pygame.draw.line(screen, (255, 0, 0), (x + 100, y), (x, y + 100), 8)


def play_sound(filename):
    pygame.mixer.music.stop()
    pygame.mixer.Sound.play(pygame.mixer.Sound(filename))


def random_with_custom_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    return random.randint(range_start, range_end)

def refresh():

    global last_number
    global total_sum
    global displayed_amount

    last_number = random_with_custom_digits(digits)

    play_sound("sounds/number_update.wav")

    total_sum += last_number
    displayed_amount += 1


# random variables
pressdelay_decrease_seconds = 0

class Button:
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

        cc = 0

        mouse = pygame.mouse.get_pos()

        if self.button_rect.collidepoint(mouse):
            cc = 1

            if pygame.mouse.get_pressed()[0]:
                cc = 2
            else:
                self.clicked = False
        else:
            self.clicked = False

        pygame.draw.rect(screen, self.fill_colors['normal'] if cc == 0 else (self.fill_colors['hover'] if cc == 1 else self.fill_colors['pressed']), self.button_rect, 0 if self.button_rect.collidepoint(mouse) else 2)
        render_normal_text(str(self.button_text), self.x + self.x_offset + 17, self.y + self.y_offset + 7, (255, 255, 255), False)


buttons = [
    Button(size[0] - 116, 5, 50, 50, 0, "!"),
    Button(size[0] - 55, 5, 50, 50, 0, "?", x_offset=1),
    Button(5, 5, 50, 50, 0.1, "<")
]

run = True

while run:

    dt = clock.tick()
    screen.fill((0, 0, 0))  # clear

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.TEXTINPUT:
            if phase == 4:
                if event.text.isnumeric():
                    answer_input += event.text
        elif event.type == pygame.MOUSEBUTTONUP:
            for button in buttons:
                if button.render_phase == phase:
                    button.update_mouse()

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                run = False

            if phase == 0:

                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    phase = 1
                    logger.log(f"Starting! digits={digits}, amount={amount}, seconds={seconds}")

                if event.key == pygame.K_LEFT and digits - 1 > 0:
                    digits -= 1
                if event.key == pygame.K_RIGHT:
                    digits += 1
                if event.key == pygame.K_DOWN and amount - 1 > 0:
                    amount -= 1
                if event.key == pygame.K_UP:
                    amount += 1
                if event.key == pygame.K_COMMA and seconds - 1 > 0:
                    seconds -= 1
                if event.key == pygame.K_PERIOD:
                    seconds += 1

            elif phase == 0.1:

                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    phase = 0

                if event.key == pygame.K_LEFT and countdown_seconds - 1 > 0:
                    countdown_seconds -= 1
                if event.key == pygame.K_RIGHT:
                    countdown_seconds += 1
                if event.key == pygame.K_DOWN and amount - 1 > 0:
                    number_font_size -= 1
                if event.key == pygame.K_UP:
                    number_font_size += 1
                if event.key == pygame.K_COMMA and render_countdown:
                    render_countdown = False
                if event.key == pygame.K_PERIOD and not render_countdown:
                    render_countdown = True
                if event.key == pygame.K_n and tournament_mode:
                    tournament_mode = False
                if event.key == pygame.K_m and not tournament_mode:
                    tournament_mode = True
            elif phase == 4:
                if event.key == pygame.K_BACKSPACE or event.key == pygame.K_DELETE:
                    answer_input = answer_input[:-1]
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:

                    if tournament_mode:
                        phase = 5
                        t = 0
                        break

                    if answer_input == "":
                        break

                    if int(answer_input) == total_sum:
                        play_sound("sounds/correct.wav")
                    else:
                        play_sound("sounds/incorrect.wav")

                    phase = 5
                    t = 0
            elif phase >= 4:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    phase += 1
                    t = 0

    t += dt

    # button settings
    for i in range(len(buttons)):
        button = buttons[i]

        if button.render_phase == phase:

            if button.clicked:
                if i == 0:
                    phase = 0.1
                elif i == 1:
                    webbrowser.open("https://chromatic-vision.github.io/flashbox")
                    logger.log("Navigating to help page on your browser...")
                elif i == 2:
                    phase = 0
                else:
                    logger.warn("?!?!")

            button.draw()


    if phase == 0: # TODO: fix this shitty code

        pressdelay_decrease_seconds -= 1

        if pygame.key.get_pressed()[pygame.K_m] and seconds - 0.01 > 0 and pressdelay_decrease_seconds <= 0:  # so you can hold the key tp get -0.01 every 5 ticks, and you don't have to spam
            seconds -= 0.01
            pressdelay_decrease_seconds = 24

        render_normal_text("Flashbox " + VERSION, 5, 5, (255, 255, 255), False)

        render_normal_text(f"Digits: {digits}", size[0] / 3 - 100, 100, (255, 255, 255), False)
        render_normal_text(f"Amount: {amount}", size[0] / 3 - 100, 135, (255, 255, 255), False)
        render_normal_text(f"Total seconds: {round(seconds, 3)}", size[0] / 3 - 100, 170, (255, 255, 255), False)

        render_normal_text("decrease / increase", size[0] / 3 + 320, 65, (255, 255, 255), False)
        render_normal_text("← / →", size[0] / 3 + 425, 100, (255, 255, 255), False)
        render_normal_text("↓ / ↑", size[0] / 3 + 425, 135, (255, 255, 255), False)
        render_normal_text("M", size[0] / 3 + 385, 170, (255, 255, 255), False)
        render_normal_text(", / .", size[0] / 3 + 425, 170, (255, 255, 255), False)

        render_normal_text("Press esc to exit, space/enter to start.", 5, size[1] - 40, (255, 255, 255), False)
    
    elif phase == 0.1: # settings screen
        render_normal_text(f"Countdown seconds: {countdown_seconds}", size[0] / 3 - 100, 100, (255, 255, 255), False)
        render_normal_text(f"Font size: {number_font_size}", size[0] / 3 - 100, 135, (255, 255, 255), False)
        render_normal_text(f"Render countdown: {render_countdown}", size[0] / 3 - 100, 170, (255, 255, 255), False)
        render_normal_text(f"Tournament mode: {tournament_mode}", size[0] / 3 - 100, 205, (255, 255, 255), False)

        render_normal_text("decrease / increase", size[0] / 3 + 320, 65, (255, 255, 255), False)
        render_normal_text("← / →", size[0] / 3 + 425, 100, (255, 255, 255), False)
        render_normal_text("↓ / ↑", size[0] / 3 + 425, 135, (255, 255, 255), False)
        render_normal_text(", / .", size[0] / 3 + 425, 170, (255, 255, 255), False)
        render_normal_text("N / M", size[0] / 3 + 425, 205, (255, 255, 255), False)

    elif phase == 1: # reset
        t = 0

        cs = countdown_seconds
        total_sum = 0
        displayed_amount = 0
        answer_input = ""

        phase = 2

    elif phase == 2: # countdown phase

        if t >= 1000:
            cs -= 1
            t = 0

        if cs == 2 and 225 <= t <= 235:
            play_sound("sounds/start.wav")

        if cs <= 0:
            t = 0
            refresh() # so we don't have to wait seconds / amount * 1000 ms after starting
            phase = 3

        if render_countdown and cs > 0:
            render_big_text(f"{cs}", 0, 400, (255, 255, 255), True)

    elif phase == 3:

        if displayed_amount >= amount:
            if t >= seconds / amount * 1000:
                phase = 4
                t = 0
        elif t >= seconds / amount * 1000:
            refresh()
            t = 0

        if t <= seconds / amount * 1000 * 0.75:
            render_big_text(f"{last_number}", 0, 400, (0, 255, 0), True)

    elif phase == 4:
        if tournament_mode:
            render_normal_text("Fill in your answers...", 5, 5, (255, 255, 255), False)
        else:
            render_normal_text("Write your answer down....", 5, 5, (255, 255, 255), False)
            render_big_text(f"{answer_input}", 0, 400, (0, 0, 255), True)
    elif phase == 5:

        if tournament_mode:
            phase = 6
            t = 0
        else:
            correct = int(answer_input) == total_sum

            if t >= 1500:
                if correct:
                    phase = 0
                else:
                    phase = 6
                t = 0
            if correct:
                draw_correct_circle(size[0] / 2 - 10, size[1] / 2, 80)
            else:
                draw_incorrect_cross(size[0] / 2, size[1] / 2 + 30)

    elif phase == 6:
        if tournament_mode:

            big_non_numeric_font = pygame.font.Font("fonts/noto-sans-mono-light.ttf", 60)

            screen.blit(big_non_numeric_font.render("Answer:", True, (255, 255, 255)), (size[0] / 3 - 200, size[1] / 2 - 200))
            render_big_text(f"{total_sum}", 0, 400, (0, 0, 255), True)

            if t >= 4000:
                phase = 0
                t = 0
        else:
            render_big_text(f"{total_sum}", 0, 400, (255, 0, 0), True)

            if t >= 1500:
                phase = 0
                t = 0
    elif phase >= 7:
        phase = 0
        t = 0

    pygame.display.update()

logger.log("Not anymore in the run loop... saving config and quitting!")
save_config(config_file)