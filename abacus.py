def get_vertical_beads_pos(number):
    if number < 5:
        return 0, number
    else:
        return 1, number - 5


class SimpleAbacus:
    def __init__(self):
        self.beads = []
        self.value = 0
        self.range = 23

        for i in range(self.range):
            self.beads.append(VerticalBeads())

    def add_value(self, amount):
        self.value += amount

        list_of_digits = [int(i) for i in str(self.value)]

        for i in range(len(list_of_digits)):
            self.beads[-i - 1].current_sum = list_of_digits[-i - 1]

    def reset(self):

        self.value = 0

        for i in range(self.range):
            self.beads[i].current_sum = 0

class VerticalBeads:

    def __init__(self):
        self.current_sum = 0
