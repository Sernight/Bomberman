# Mateusz Szmyd 179920
import numpy as np
import threading
from time import sleep

import atexit
from getch import getch
from kbhit import *

map_size = (81, 121)
cut_size = (21, 41)


# brak nachodzenia na siebie gracza i agenta
# agent nie stawia bomb
# brak nagród

class Plane:
    def __init__(self, ys: int, xs: int):
        self.object_plane = np.zeros((ys, xs), dtype=Object)
        self.character_plane = np.full((ys, xs), EmptyTile(), dtype=Object)
        for ind, obj in np.ndenumerate(self.object_plane):
            y, x = ind
            if y % 2 == 1 and x % 2 == 1 and y > 0 and x > 0:
                self.object_plane[y][x] = Obstacle()
            else:
                self.generate_obstacles(y, x)
        yc, xc = self.character_plane.shape[0] - 1, int((self.character_plane.shape[1] - 1) / 2)
        self.player = Player(yc, xc)
        self.character_plane[yc][xc] = self.player

    def __str__(self):
        global cut_size
        merged_plane = np.copy(self.character_plane)
        for ind, obj in np.ndenumerate(self.object_plane):
            y, x = ind
            if isinstance(merged_plane[y][x], EmptyTile):
                merged_plane[y][x] = self.object_plane[y][x]

        # cutting fragment of map
        center = (self.player.pos[0], self.player.pos[1])
        if center[0] - int(cut_size[0] / 2) < 0:
            cut_y = (0, cut_size[0])
        elif center[0] + int(cut_size[0] / 2) >= merged_plane.shape[0]:
            cut_y = (merged_plane.shape[0] - cut_size[0], merged_plane.shape[0])
        else:
            cut_y = (center[0] - int(cut_size[0] / 2), center[0] + int(cut_size[0] / 2) + 1)

        if center[1] - int(cut_size[1] / 2) < 0:
            cut_x = (0, cut_size[1])
        elif center[1] + int(cut_size[1] / 2) >= merged_plane.shape[1]:
            cut_x = (merged_plane.shape[1] - cut_size[1], merged_plane.shape[1])
        else:
            cut_x = (center[1] - int(cut_size[1] / 2), center[1] + int(cut_size[1] / 2) + 1)

        return str(merged_plane[cut_y[0]:cut_y[1], cut_x[0]:cut_x[1]]) \
               + f'\nHP: {self.player.health}' \
               + "\nh - add 1 hp\ne - extent bomb to 4\nf - extent bomb to 5\nd - add damage of bomb"

    def update(self):
        for ind, obj in np.ndenumerate(self.object_plane):
            y, x = ind
            if isinstance(obj, Bomb):
                if self.object_plane[y][x].update():
                    self.object_plane[y][x].kaboom(self)
            elif isinstance(obj, Fire):
                if self.object_plane[y][x].update():
                    self.object_plane[y][x] = EmptyTile()

    def generate_obstacles(self, y, x):
        random = np.random.randint(0, 5)
        if random == 0:
            random_type = np.random.randint(1, 4)
            self.object_plane[y][x] = Obstacle(random_type)
        else:
            self.object_plane[y][x] = EmptyTile()
            self.generate_agents(y, x)

    def generate_agents(self, y, x):
        random = np.random.randint(0, 5)
        if random == 0:
            random_type = np.random.randint(0, 6)
            self.character_plane[y][x] = Agent(y, x, random_type)


class Object:
    def __init__(self, y: int = 0, x: int = 0, shape: str = ''):
        self.shape = shape
        self.pos = np.array([y, x], dtype=int)

    def __repr__(self):
        return self.shape


class Character(Object):
    def __init__(self, y: int, x: int, shape: str, health: int, bomb_power: int = 1, bomb_extent: int = 1):
        super().__init__(y, x, shape)
        self.health = health
        self.bomb_power = bomb_power
        self.bomb_extent = bomb_extent

    def move(self, plane: Plane, dy: int = 0, dx: int = 0):
        temp_pos = self.pos + np.array([dy, dx])
        if 0 <= temp_pos[0] < plane.character_plane.shape[0] and 0 <= temp_pos[1] < plane.character_plane.shape[1]:
            if not isinstance(plane.object_plane[temp_pos[0]][temp_pos[1]], Obstacle) and not \
                    isinstance(plane.character_plane[temp_pos[0]][temp_pos[1]], Character):
                if isinstance(plane.object_plane[temp_pos[0]][temp_pos[1]], Powerup):
                    if isinstance(self, Player):
                        typeof = plane.object_plane[temp_pos[0]][temp_pos[1]].type
                        self.get_powerup(typeof)
                    plane.object_plane[temp_pos[0]][temp_pos[1]] = EmptyTile()
                plane.character_plane[self.pos[0]][self.pos[1]] = EmptyTile()
                self.pos += np.array([dy, dx])
                plane.character_plane[self.pos[0]][self.pos[1]] = self

    def plant_bomb(self, plane: Plane):
        if not isinstance(plane.object_plane[self.pos[0]][self.pos[1]], Bomb):
            plane.object_plane[self.pos[0]][self.pos[1]] = Bomb(self.pos[0], self.pos[1],
                                                                power=self.bomb_power,
                                                                extent=self.bomb_extent)

    def get_powerup(self, typeof):
        if typeof == 1:
            self.health += 1
        elif typeof == 2 and self.bomb_power != 3:
            self.bomb_extent = 2
        elif typeof == 3:
            self.bomb_extent = 3
        elif typeof == 4:
            if self.bomb_power < 3:
                self.bomb_power += 1


class Agent(Character):
    """
    typeof:
        [0, 2] - agent without bomb
        [3, 5] - agent with bomb
        0, 3   - move range 3
        1, 4   - move range 5
        2, 5   - move range 7
    """

    def __init__(self, y0: int = 0, x0: int = 0, typeof: int = 0):
        self.type = typeof
        if self.type >= 3:
            super().__init__(y0, x0, 'A', 1)
        else:
            super().__init__(y0, x0, 'a', 1)

        axis = np.random.randint(0, 2)
        a_range = 0
        if self.type in [0, 3]:
            a_range = 3
        elif self.type in [1, 4]:
            a_range = 5
        elif self.type in [2, 5]:
            a_range = 7
        if axis == 0:
            self.y_range = (y0 - a_range, y0 + a_range)
            self.x_range = (x0, x0)
        else:
            self.y_range = (y0, y0)
            self.x_range = (x0 - a_range, x0 + a_range)

    def move(self, plane: Plane, dy: int = 0, dx: int = 0):
        temp_pos = self.pos + np.array([dy, dx])
        if self.y_range[0] <= temp_pos[0] <= self.y_range[1] and self.x_range[0] <= temp_pos[1] <= self.x_range[1]:
            super().move(plane, dy, dx)

    def update(self, plane: Plane):
        dx = np.random.randint(-1, 2)
        dy = np.random.randint(-1, 2)
        # randomize planting bomb
        self.move(plane, dy, dx)
        # returns True when should be destroyed
        if self.health <= 0:
            return True
        else:
            return False


class Player(Character):
    def __init__(self, y0: int = 0, x0: int = 0):
        super().__init__(y0, x0, '0', 3)


class Bomb(Object):
    def __init__(self, y: int, x: int, lifespan: int = 20, power: int = 1, extent: int = 1):
        super().__init__(y, x, 'x')
        self.timer = lifespan
        self.power = power
        self.extent = extent

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            return True
        else:
            return False

    def kaboom(self, plane):
        dx = [0, 1, 0, -1, 0]
        dy = [0, 0, 1, 0, -1]
        for i in range(len(dx)):
            for j in range(1, self.extent + 1):
                y = self.pos[0] + dy[i] * j
                x = self.pos[1] + dx[i] * j
                if 0 <= y < plane.object_plane.shape[0] and 0 <= x < plane.object_plane.shape[1]:
                    if isinstance(plane.object_plane[y][x], Obstacle):
                        if -10 < plane.object_plane[y][x].damage(self.power) <= 0:
                            is_powerup = np.random.randint(0, 3)
                            if is_powerup == 0:
                                powerup_type = np.random.randint(1, 5)
                                plane.object_plane[y][x] = Powerup(powerup_type)
                            else:
                                plane.object_plane[y][x] = EmptyTile()
                        break
                    elif isinstance(plane.character_plane[y][x], Character):
                        plane.character_plane[y][x].health -= self.power
                        plane.object_plane[y][x] = Fire()
                    elif isinstance(plane.object_plane[y][x], Bomb) and (y != self.pos[0] or x != self.pos[1]):
                        pass
                    else:
                        plane.object_plane[y][x] = Fire()


class Powerup(Object):
    def __init__(self, typeof: int):
        self.type = typeof
        if typeof == 1:
            super().__init__(shape='h')
        elif typeof == 2:
            super().__init__(shape='f')
        elif typeof == 3:
            super().__init__(shape='e')
        elif typeof == 4:
            super().__init__(shape='d')
        else:
            raise ValueError('Wrong type of powerup')


class Fire(Object):
    def __init__(self, lifespan: int = 5):
        super().__init__(shape='+')
        self.timer = lifespan

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            return True
        else:
            return False


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


def agent_handler(plane: Plane):
    while True:
        for ind, obj in np.ndenumerate(plane.character_plane):
            y, x = ind
            if isinstance(obj, Agent):
                if plane.character_plane[y][x].update(plane):
                    plane.character_plane[y][x] = EmptyTile()
        sleep(0.5)


def main():
    atexit.register(set_normal_term)
    set_curses_term()
    np.set_printoptions(threshold=np.inf, linewidth=125)
    plane = Plane(map_size[0], map_size[1])
    kb_thread = threading.Thread(target=keyboard_handler, args=[plane])
    kb_thread.daemon = True
    kb_thread.start()
    agents_thread = threading.Thread(target=agent_handler, args=[plane])
    agents_thread.daemon = True
    agents_thread.start()
    while True:
        os.system('clear')
        plane.update()
        print(plane)
        sleep(0.1)


if __name__ == '__main__':
    main()
