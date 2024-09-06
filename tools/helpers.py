import random

STRING_OPTIONS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

def generate_random_string(length):
    return ''.join(random.choice(STRING_OPTIONS) for i in range(length))