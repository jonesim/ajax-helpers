import string
import random


def random_string():
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _i in range(8))
