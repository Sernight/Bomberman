import sys
import threading

import numpy as np

import main as terminal
from configuration import *
from PySide2.QtCore import Qt, QTimer
from PySide2.QtGui import QPainterPath, QColor, QBrush, QPixmap
from PySide2.QtWidgets import (
    QGraphicsItem,
    QPushButton,
    QGraphicsScene,
    QWidget,
    QVBoxLayout,
    QMainWindow,
    QApplication,
    QGraphicsView,
    QGraphicsProxyWidget
)


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
        super().__init__(0, 0, width, height)
        self.scene_width = width
        self.scene_height = height

        # self._grid_pattern = QBrush(QColor("#282828"), Qt.Dense7Pattern)

        #     self.setBackgroundBrush(QColor("#393939"))
        # self.setSceneRect(-self.scene_width // 2, -self.scene_height // 2,
        #                   self.scene_width, self.scene_height)

    #
    # def drawBackground(self, painter, rect):
    #     super().drawBackground(painter, rect)
    #     painter.fillRect(rect, self._grid_pattern)
    def addItems(self, items: list[GraphicsItem]):
        for item in items:
            self.addItem(item)


class MainWidgets(QWidget):
    def __init__(self):
        super().__init__()

        self.plane = terminal.Plane(map_size[0], map_size[1])

        agents_thread = threading.Thread(target=terminal.agent_handler, args=[self.plane])
        agents_thread.daemon = True
        agents_thread.start()

        self.scene = GraphicsScene(cut_size[1] * tile_size, cut_size[0] * tile_size)
        self.view = QGraphicsView(self.scene)

        _layout = QVBoxLayout()
        _layout.addWidget(self.view)
        self.setLayout(_layout)

        self.draw_scene()

        self.scene.update()

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

        # add agents
        for ind, agent in np.ndenumerate(self.plane.agents):
            if offset_y[0] < agent.pos[0] < offset_y[1] and offset_x[0] < agent.pos[1] < offset_x[1]:
                self.scene.addItem(Agent((agent.pos[1] - offset_x[0]) * tile_size,
                                         (agent.pos[0] - offset_y[0]) * tile_size,
                                         agent.type))

        # add player
        self.scene.addItem(Player((self.plane.player.pos[1] - offset_x[0]) * tile_size,
                                  (self.plane.player.pos[0] - offset_y[0]) * tile_size))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize((cut_size[1] + 1) * tile_size, (cut_size[0] + 1) * tile_size)
        self.mainWidget = MainWidgets()
        self.setCentralWidget(self.mainWidget)

        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_scene)
        self.timer.start()

    def update_scene(self):
        self.mainWidget.scene.clear()
        self.mainWidget.plane.update()
        self.mainWidget.draw_scene()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
