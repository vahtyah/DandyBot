import random
import time
import sys
import json
from importlib import import_module
from pathlib import Path
from random import randrange, shuffle
import tkinter as tk
from plitk import load_tileset, PliTk

SCALE = 1
DELAY = 50

UP = "up"
DOWN = "down"
LEFT = "left"
RIGHT = "right"
TAKE = "take"
PASS = "pass"
PLAYER = "player"
GOLD = "gold"
WALL = "wall"
EMPTY = "empty"
COLPLA = "colpla"


class Board:
    def __init__(self, game, canvas, label, root):
        self.root = root
        self.game = game
        self.canvas = canvas
        self.label = label
        self.tileset = load_tileset(game["tileset"])
        self.screen = PliTk(canvas, 0, 0, 0, 0, self.tileset, SCALE)
        self.level_index = 0
        self.isStart = False
        self.load_players()
        self.load_level()
        self.button()
        root.bind("<KeyPress>", self.on_key_press)

    def on_key_press(self, event):
        if self.level_index < 5 or not self.isStart or self.steps >= self.level["steps"]:
            return
        if event.keysym == "a":
            self.player.act(LEFT)
        elif event.keysym == "d":
            self.player.act(RIGHT)
        elif event.keysym == "w":
            self.player.act(UP)
        elif event.keysym == "s":
            self.player.act(DOWN)

    def onPlayPauseButtonClick(self):
        self.isStart = not self.isStart

    def onNextLevelButtonClick(self):
        if self.level_index == 5:
            self.level_index = -1
        self.select_next_level()

    def onQuitButtonClick(self):
        self.root.quit()

    @staticmethod
    def onIncreaseDelayButtonClick():
        global DELAY
        DELAY += 50
        print(DELAY)

    @staticmethod
    def onDecreaseDelayButtonClick():
        global DELAY
        if DELAY > 50:
            DELAY -= 50
        print(DELAY)

    def button(self):
        buttonPlayPause = tk.Button(self.root, text="Start/Pause", command=self.onPlayPauseButtonClick)
        buttonPlayPause.grid(row=1, column=1, sticky="ewn")
        buttonNextLV = tk.Button(self.root, text="Next Level", command=self.onNextLevelButtonClick)
        buttonNextLV.grid(row=2, column=1, sticky="ewn")
        buttonExit = tk.Button(self.root, text="Exit", command=self.onQuitButtonClick)
        buttonExit.grid(row=3, column=1, sticky="ewn")
        buttonIncreaseDelay = tk.Button(self.root, text="Increase Delay", command=self.onIncreaseDelayButtonClick)
        buttonIncreaseDelay.grid(row=4, column=1, sticky="ewn")
        buttonDecreaseDelay = tk.Button(self.root, text="Decrease Delay", command=self.onDecreaseDelayButtonClick)
        buttonDecreaseDelay.grid(row=5, column=1, sticky="ewn")

    def load_players(self):
        self.players = []
        for i, name in enumerate(self.game[f"playersLevel{self.level_index + 1}"]):
            script = import_module(name).script
            tile = self.game["tiles"]["@"][i]
            self.players.append(Player(name, script, self, tile))
        self.player = self.players[0]

    def random_gold(self):
        typeGold = random.randint(1, 9)
        x = random.randint(1, self.screen.cols - 2)
        y = random.randint(1, self.screen.rows - 2)
        self.screen.set_tile(x, y, self.game["tiles"][f"{typeGold}"])
        self.map[x][y] = f"{typeGold}"

    def load_level(self):
        self.gold = 0
        self.steps = 0
        self.level = self.game["levels"][self.level_index]
        data = self.game["maps"][self.level["map"]]
        cols, rows = len(data[0]), len(data)
        self.map = [[data[y][x] for y in range(rows)] for x in range(cols)]
        self.has_player = [[None for y in range(rows)] for x in range(cols)]
        self.canvas.config(width=cols * self.tileset["tile_width"] * SCALE,
                           height=rows * self.tileset["tile_height"] * SCALE)
        self.level["gold"] = sum(sum(int(cell)
                                     if cell.isdigit() else 0 for cell in row) for row in data)
        self.screen.resize(cols, rows)
        for y in range(rows):
            for x in range(cols):
                self.update(x, y)
        i = 1
        for p in self.players:
            self.add_player(p, *self.level[f"start{i}"])
            i += 1
        self.update_score()

    def get(self, x, y):
        if x < 0 or y < 0 or x >= self.screen.cols or y >= self.screen.rows:
            return "#"
        return self.map[x][y]

    def update(self, x, y):
        if self.has_player[x][y]:
            self.screen.set_tile(x, y, self.has_player[x][y].tile)
        else:
            self.screen.set_tile(x, y, self.game["tiles"][self.map[x][y]])

    def remove_player(self, player):
        self.has_player[player.x][player.y] = None
        self.update(player.x, player.y)

    def add_player(self, player, x, y):
        player.x, player.y = x, y
        self.has_player[x][y] = player
        self.update(x, y)

    def take_gold(self, x, y):
        self.gold += self.check("gold", x, y)
        self.map[x][y] = " "
        self.update(x, y)
        self.update_score()

    def check(self, cmd, *args):
        if cmd == "level":
            return self.level_index + 1
        x, y = args
        item = self.get(x, y)
        if cmd == "wall":
            return item == "#"
        if cmd == "gold":
            return int(item) if item.isdigit() else 0
        if cmd == "player":
            return item != "#" and self.has_player[x][y]

    def play(self):
        for p in self.players:
            if self.isStart:
                mesAct = p.script(self.check, p.x, p.y)
                p.act(mesAct)
                if mesAct == TAKE and self.level_index >= 5:
                    self.random_gold()
            if self.gold >= self.level["gold"] and self.level_index < 5:
                return self.select_next_level()
        if self.isStart:
            self.steps += 1
        return self.steps < self.level["steps"]

    def update_score(self):
        lines = [("Level:%4d\n" % (self.level_index + 1))]
        players = sorted(self.players, key=lambda x: x.gold, reverse=True)
        for p in players:
            lines.append("%s:%4d" % (p.name, p.gold))
        self.label["text"] = "\n".join(lines)

    def select_next_level(self):
        self.level_index += 1
        if self.level_index < len(self.game["levels"]):
            self.load_players()
            self.load_level()
            return True
        return False


class Player:
    def __init__(self, name, script, board, tile):
        self.name = name
        self.script = script
        self.board = board
        self.tile = tile
        self.x, self.y = 0, 0
        self.gold = 0

    def act(self, cmd):
        dx, dy = 0, 0
        if cmd == UP:
            dy -= 1
        elif cmd == DOWN:
            dy += 1
        elif cmd == LEFT:
            dx -= 1
        elif cmd == RIGHT:
            dx += 1
        elif cmd == TAKE:
            self.take()
        elif cmd == COLPLA:
            self.board.steps = self.board.level["steps"]
        if self.board.check("player", self.x + dx, self.y + dy) and self == self.board.player and (dx != 0 or dy != 0):
            print("GAME OVER!")
            self.board.steps = self.board.level["steps"]
        self.move(dx, dy)

    def move(self, dx, dy):
        x, y = self.x + dx, self.y + dy
        board = self.board
        board.remove_player(self)
        if not board.check("wall", x, y) and not board.check("player", x, y):
            self.x, self.y = x, y
        board.add_player(self, self.x, self.y)

    def take(self):
        gold = self.board.check("gold", self.x, self.y)
        if gold:
            self.gold += gold
            self.board.take_gold(self.x, self.y)


def start_game():
    def update():
        t = time.time()
        if board.play():
            dt = int((time.time() - t) * 1000)
            root.after(max(DELAY - dt, 0), update)
        else:
            label["text"] += "\n\nGAME OVER!"

    root = tk.Tk()
    root.configure(background="black")
    canvas = tk.Canvas(root, bg="black", highlightthickness=0)
    canvas.grid(row=0, column=0, rowspan=6)
    label = tk.Label(root, font=("TkFixedFont",),
                     justify=tk.RIGHT, fg="white", bg="gray20")
    label.grid(row=0, column=1, sticky="n")
    filename = sys.argv[1] if len(sys.argv) == 2 else "game.json"
    game = json.loads(Path(filename).read_text())
    board = Board(game, canvas, label, root)
    root.after(0, update)
    root.mainloop()


start_game()
