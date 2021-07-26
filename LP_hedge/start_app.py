from LP_hedge.tg.tg_bot import start_bot
# todo structure https://docs.python-guide.org/writing/structure/
# better this structure https://dev.to/codemouse92/dead-simple-python-project-structure-and-imports-38c6

import subprocess

current_subprocess = {}

if __name__ == "__main__":
    price_update = subprocess.Popen(['python', 'scripts/price_update_process.py'], shell=True)
    # , stdout=subprocess.PIPE
    current_subprocess['price update'] = price_update

    start_bot()
