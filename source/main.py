# Mateusz Szmyd 179920
import numpy as np
import threading
from time import sleep
import os

import atexit
from getch import getch
from kbhit import *


class Plane:
    def __init__(self, ys: int, xs: int):
        self.object_plane = np.zeros((ys, xs), dtype=Object)
        self.character_plane = np.full((ys, xs), EmptyTile(), dtype=Object)
        for y in range(self.object_plane.shape[0]):
            for x in range(self.object_plane.shape[1]):
                if y % 2 == 1 and x % 2 == 1 and y > 0 and x > 0:
                    self.object_plane[y][x] = Obstacle()
                else:
                    self.object_plane[y][x] = EmptyTile()
        yc, xc = self.character_plane.shape[0] - 1, int((self.character_plane.shape[1] - 1) / 2)
        self.player = Player(yc, xc)
        self.character_plane[yc][xc] = self.player

    def __str__(self):
        merged_plane = np.copy(self.character_plane)
        for y in range(merged_plane.shape[0]):
            for x in range(merged_plane.shape[1]):
                if isinstance(merged_plane[y][x], EmptyTile):
                    merged_plane[y][x] = self.object_plane[y][x]
        return str(merged_plane)

    def update(self):
        for y in range(self.object_plane.shape[0]):
            for x in range(self.object_plane.shape[1]):
                if isinstance(self.object_plane[y][x], Bomb):
                    if self.object_plane[y][x].update():
                        self.object_plane[y][x].kaboom(self)
                elif isinstance(self.object_plane[y][x], Fire):
                    if self.object_plane[y][x].update():
                        self.object_plane[y][x] = EmptyTile()


class Object:
    def __init__(self, y: int = 0, x: int = 0, shape: str = ''):
        self.shape = shape
        self.pos = np.array([y, x], dtype=int)

    def __repr__(self):
        return self.shape


class Character(Object):
    def __init__(self, y: int, x: int, shape: str, health: int):
        super().__init__(y, x, shape)
        self.health = health

    def move(self, plane: Plane, dy: int = 0, dx: int = 0):
        temp_pos = self.pos + np.array([dy, dx])
        if 0 <= temp_pos[0] < plane.character_plane.shape[0] and 0 <= temp_pos[1] < plane.character_plane.shape[1]:
            if not isinstance(plane.object_plane[temp_pos[0]][temp_pos[1]], Obstacle):
                plane.character_plane[self.pos[0]][self.pos[1]] = EmptyTile()
                self.pos += np.array([dy, dx])
                plane.character_plane[self.pos[0]][self.pos[1]] = self

    def plant_bomb(self, plane: Plane):
        if not isinstance(plane.object_plane[self.pos[0]][self.pos[1]], Bomb):
            plane.object_plane[self.pos[0]][self.pos[1]] = Bomb(self.pos[0], self.pos[1])


class Player(Character):
    def __init__(self, y0: int = 0, x0: int = 0):
        super().__init__(y0, x0, '0', 3)


class Bomb(Object):
    def __init__(self, y: int, x: int, lifespan: int = 20):
        super().__init__(y, x, 'x')
        self.timer = lifespan

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            return True
        else:
            return False

    def kaboom(self, plane, power: int = 1, extent: int = 1):
        dx = [0, 1, 0, -1, 0]
        dy = [0, 0, 1, 0, -1]
        for i in range(len(dx)):
            for j in range(1, extent + 1):
                y = self.pos[0] + dy[i] * j
                x = self.pos[1] + dx[i] * j
                if 0 <= y < plane.object_plane.shape[0] and 0 <= x < plane.object_plane.shape[1]:
                    if isinstance(plane.object_plane[y][x], Obstacle):
                        if -10 < plane.object_plane[y][x].damage(power) <= 0:
                            plane.object_plane[y][x] = EmptyTile()
                        break
                    elif isinstance(plane.character_plane[y][x], Character):
                        plane.character_plane[y][x].health -= power
                        plane.object_plane[y][x] = Fire()
                    elif isinstance(plane.object_plane[y][x], Bomb) and (y != self.pos[0] or x != self.pos[1]):
                        pass
                    else:
                        plane.object_plane[y][x] = Fire()


class Fire(Object):
    def __init__(self, lifespan: int = 5):
        Object.__init__(self, shape='+')
        self.timer = lifespan

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            return True
        else:
            return False


class Agent(Character):
    def __init__(self, y0: int = 0, x0: int = 0):
        super().__init__(y0, x0, 'a', 1)


class Obstacle(Object):
    def __init__(self, health: int = -10):
        self.health = health
        if health == -10:
            super().__init__(shape='#')
        elif health == 1:
            super().__init__(shape='1')
        elif health == 2:
            super().__init__(shape='2')
        elif health == 3:
            super().__init__(shape='3')
        else:
            raise ValueError('Wrong obstacles health value')

    def damage(self, dmg: int = 1):
        self.health -= dmg
        if self.health == 1:
            self.shape = '1'
        elif self.health == 2:
            self.shape = '2'
        elif self.health == 3:
            self.shape = '3'
        return self.health


class EmptyTile(Object):
    def __init__(self):
        super().__init__(shape=' ')


def keyboard_handler(plane: Plane):
    while True:
        if kbhit():
            key = getch()
            dy, dx = 0, 0
            if key in ['w', 's', 'a', 'd']:
                if key == 'a':
                    dx = -1
                elif key == 'd':
                    dx = 1
                elif key == 'w':
                    dy = -1
                elif key == 's':
                    dy = 1
                plane.player.move(plane, dy, dx)
            elif key == ' ':
                plane.player.plant_bomb(plane)


def main():
    atexit.register(set_normal_term)
    set_curses_term()
    plane = Plane(11, 11)
    kb_thread = threading.Thread(target=keyboard_handler, args=[plane])
    kb_thread.daemon = True
    kb_thread.start()
    while True:
        os.system('clear')
        plane.update()
        print(plane)
        sleep(0.1)


if __name__ == '__main__':
    main()
