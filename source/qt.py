import sys

import numpy as np
from PySide2 import QtCore
from PySide2.QtCore import QTimer
from PySide2.QtGui import QPainterPath, QIcon
from PySide2.QtWidgets import (
    QGraphicsItem,
    QPushButton,
    QGraphicsScene,
    QWidget,
    QVBoxLayout,
    QMainWindow,
    QApplication,
    QGraphicsView
)

import main as terminal
from configuration import *


class GraphicsItem(QGraphicsItem):
    def __init__(self, pixmap_path: str, x: int = 0, y: int = 0):
        super().__init__()
        self.x = x
        self.y = y
        # add pixmap
        self.pixmap = pixmap_path
        self.item_body = self.draw_item(x, y)

    def draw_item(self, x, y):
        path = QPainterPath()
        path.addRect(x, y, tile_size, tile_size)
        return path

    def paint(self, painter, option, widget):
        # painter.setPen(Qt.NoPen)
        # painter.setBrush(QBrush(QColor("#FF313131")))
        # painter.drawPath(self.item_body)

        painter.setOpacity(1)
        painter.drawPixmap(self.x, self.y, tile_size, tile_size, self.pixmap)

    def boundingRect(self):
        return self.item_body.boundingRect()


class EmptyTile(GraphicsItem):
    def __init__(self, x, y):
        super().__init__('../images/dirt.png', x, y)


class Obstacle(GraphicsItem):
    def __init__(self, x, y, health):
        if health == 3:
            super().__init__('../images/obstacle_3.png', x, y)
        elif health == 2:
            super().__init__('../images/obstacle_2.png', x, y)
        elif health == 1:
            super().__init__('../images/obstacle_1.png', x, y)
        else:
            super().__init__('../images/obstacle_inf.png', x, y)


class Bomb(GraphicsItem):
    def __init__(self, x, y):
        super().__init__('../images/bomb.png', x, y)


class Fire(GraphicsItem):
    def __init__(self, x, y):
        super().__init__('../images/fire.png', x, y)


class Character(GraphicsItem):
    def __init__(self, pixmap_path, x, y):
        super().__init__(pixmap_path, x, y)


class Player(GraphicsItem):
    def __init__(self, x, y):
        super().__init__('../images/bomberman.png', x, y)


class Agent(GraphicsItem):
    def __init__(self, x, y, typeof):
        if typeof >= 3:
            super().__init__('../images/bGhost.png', x, y)
        else:
            super().__init__('../images/smallGhost.png', x, y)


class Powerup(GraphicsItem):
    def __init__(self, x, y, typeof):
        if typeof == 1:
            super().__init__('../images/health.png', x, y)
        elif typeof == 2:
            super().__init__('../images/5x5.png', x, y)
        elif typeof == 3:
            super().__init__('../images/7x7.png', x, y)
        elif typeof == 4:
            super().__init__('../images/double.png', x, y)


class GraphicsScene(QGraphicsScene):
    def __init__(self, width: int, height: int):
        super().__init__(0, -20, width, height)
        self.scene_width = width
        self.scene_height = height

    def addItems(self, items: list[GraphicsItem]):
        for item in items:
            self.addItem(item)


class MainWidgets(QWidget):
    def __init__(self):
        super().__init__()

        self.plane = terminal.Plane(map_size[0], map_size[1])

        self.scene = GraphicsScene(cut_size[1] * tile_size, cut_size[0] * tile_size)
        self.view = QGraphicsView(self.scene)

        _layout = QVBoxLayout()
        _layout.addWidget(self.view)
        self.setLayout(_layout)

        self.draw_scene()

        self.scene.update()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_W:
            self.plane.player.move(self.plane, -1, 0)
        elif event.key() == QtCore.Qt.Key_S:
            self.plane.player.move(self.plane, 1, 0)
        elif event.key() == QtCore.Qt.Key_A:
            self.plane.player.move(self.plane, 0, -1)
        elif event.key() == QtCore.Qt.Key_D:
            self.plane.player.move(self.plane, 0, 1)
        elif event.key() == QtCore.Qt.Key_Space:
            self.plane.player.plant_bomb(self.plane)
        event.accept()

    def draw_scene(self):
        # add solid objects, bombs and fire
        plane, offset_y, offset_x = self.plane.get_plane()
        for ind, obj in np.ndenumerate(plane):
            if isinstance(obj, terminal.EmptyTile):
                self.scene.addItem(EmptyTile(ind[1] * tile_size, ind[0] * tile_size))
            elif isinstance(obj, terminal.Obstacle):
                self.scene.addItem(Obstacle(ind[1] * tile_size, ind[0] * tile_size, obj.health))
            elif isinstance(obj, terminal.Bomb):
                self.scene.addItem(EmptyTile(ind[1] * tile_size, ind[0] * tile_size))
                self.scene.addItem(Bomb(ind[1] * tile_size, ind[0] * tile_size))
            elif isinstance(obj, terminal.Fire):
                self.scene.addItem(EmptyTile(ind[1] * tile_size, ind[0] * tile_size))
                self.scene.addItem(Fire(ind[1] * tile_size, ind[0] * tile_size))
            elif isinstance(obj, terminal.Powerup):
                self.scene.addItem(EmptyTile(ind[1] * tile_size, ind[0] * tile_size))
                self.scene.addItem(Powerup(ind[1] * tile_size, ind[0] * tile_size, obj.type))

        # add agents
        for ind, agent in np.ndenumerate(self.plane.agents):
            if offset_y[0] < agent.pos[0] < offset_y[1] and offset_x[0] < agent.pos[1] < offset_x[1]:
                self.scene.addItem(Agent((agent.pos[1] - offset_x[0]) * tile_size,
                                         (agent.pos[0] - offset_y[0]) * tile_size,
                                         agent.type))

        # add player
        self.scene.addItem(Player((self.plane.player.pos[1] - offset_x[0]) * tile_size,
                                  (self.plane.player.pos[0] - offset_y[0]) * tile_size))

        # draw players health
        for i in range(self.plane.player.health):
            self.scene.addItem(Powerup(i * tile_size, -40, 1))

    def agent_handler(self):
        # global agents_count
        for ind, agent in np.ndenumerate(self.plane.agents):
            self.plane.agents[ind].update(self.plane)

    def move_player(self, dy, dx):
        self.plane.player.move(self.plane, dy, dx)

    def plant_bomb(self):
        self.plane.player.plant_bomb(self.plane)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(cut_size[1] * tile_size + 20, cut_size[0] * tile_size + 60)
        self.mainWidget = MainWidgets()
        self.setCentralWidget(self.mainWidget)

        self.l_button = QPushButton(QIcon('../images/left_arrow.png'), '', self)
        self.l_button.setGeometry((cut_size[1] - 3) * tile_size + 10,
                                  (cut_size[0] - 1) * tile_size + 10,
                                  tile_size, tile_size)
        self.r_button = QPushButton(QIcon('../images/right_arrow.png'), '', self)
        self.r_button.setGeometry((cut_size[1] - 1) * tile_size + 10,
                                  (cut_size[0] - 1) * tile_size + 10,
                                  tile_size, tile_size)
        self.d_button = QPushButton(QIcon('../images/bottom_arrow.png'), '', self)
        self.d_button.setGeometry((cut_size[1] - 2) * tile_size + 10,
                                  (cut_size[0]) * tile_size + 10,
                                  tile_size, tile_size)
        self.u_button = QPushButton(QIcon('../images/top_arrow.png'), '', self)
        self.u_button.setGeometry((cut_size[1] - 2) * tile_size + 10,
                                  (cut_size[0] - 2) * tile_size + 10,
                                  tile_size, tile_size)
        self.b_button = QPushButton(QIcon('../images/bomb.png'), '', self)
        self.b_button.setGeometry((cut_size[1] - 2) * tile_size + 10,
                                  (cut_size[0] - 1) * tile_size + 10,
                                  tile_size, tile_size)

        self.l_button.clicked.connect(lambda: self.mainWidget.move_player(0, -1))
        self.r_button.clicked.connect(lambda: self.mainWidget.move_player(0, 1))
        self.d_button.clicked.connect(lambda: self.mainWidget.move_player(1, 0))
        self.u_button.clicked.connect(lambda: self.mainWidget.move_player(-1, 0))
        self.b_button.clicked.connect(self.mainWidget.plant_bomb)

        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_scene)
        self.timer.start()

        self.agent_timer = QTimer()
        self.agent_timer.setInterval(500)
        self.agent_timer.timeout.connect(self.mainWidget.agent_handler)
        self.agent_timer.start()

    def update_scene(self):
        self.mainWidget.scene.clear()
        self.mainWidget.plane.update()
        self.mainWidget.draw_scene()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
