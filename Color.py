BLACK = '\033[30m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
PURPLE = '\033[35m'
CYAN = '\033[36m'
WHITE = '\033[37m'
ENDC = '\033[m'    # Resets color to default


def sample_colors():
    print(BLACK + "BLACK",
          RED + "RED",
          GREEN + "GREEN",
          YELLOW + "YELLOW",
          BLUE + "BLUE",
          PURPLE + "PURPLE",
          CYAN + "CYAN",
          WHITE + "WHITE" + ENDC)

