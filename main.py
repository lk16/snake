from dataclasses import dataclass
from random import randint
from time import sleep
from enum import Enum, auto
import sys, tty, os, termios
from threading import Thread
from typing import NoReturn, Optional
import queue


key_press_queue: queue.Queue["Direction"] = queue.Queue()


class GameOver(Exception):
    ...


class Direction(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()


@dataclass(frozen=True)
class Coordinate:
    x: int
    y: int

    def __hash__(self) -> int:
        return hash((self.x, self.y))


def wait_for_key() -> Direction:
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    try:
        while True:
            b = os.read(sys.stdin.fileno(), 3).decode()

            if len(b) == 3:
                k = ord(b[2])
            else:
                k = ord(b)

            key_mapping = {
                65: Direction.UP,
                66: Direction.DOWN,
                67: Direction.RIGHT,
                68: Direction.LEFT,
            }

            try:
                return key_mapping[k]
            except KeyError:
                # Ignore other keypresses
                print(f"Ignoring keypress {chr(k)}")

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def wait_for_key_loop() -> NoReturn:
    while True:
        direction = wait_for_key()
        key_press_queue.put(direction)


@dataclass
class Snake:
    head: Coordinate
    direction: Direction
    fields: dict[Coordinate, int]
    length: int

    def move(self, field_width: int, field_height: int) -> None:
        latest_direction_update: Optional[Direction] = None

        while True:
            try:
                latest_direction_update = key_press_queue.get(block=False)
            except queue.Empty:
                break

        if latest_direction_update is not None:
            if (
                self.direction in [Direction.LEFT, Direction.RIGHT]
                and latest_direction_update in [Direction.UP, Direction.DOWN]
            ):
                self.direction = latest_direction_update

            if (
                self.direction in [Direction.UP, Direction.DOWN]
                and latest_direction_update in [Direction.LEFT, Direction.RIGHT]
            ):
                self.direction = latest_direction_update

        if self.direction == Direction.UP:
            moved_head = Coordinate(self.head.x, self.head.y - 1)
        elif self.direction == Direction.DOWN:
            moved_head = Coordinate(self.head.x, self.head.y + 1)
        elif self.direction == Direction.LEFT:
            moved_head = Coordinate(self.head.x - 1, self.head.y)
        elif self.direction == Direction.RIGHT:
            moved_head = Coordinate(self.head.x + 1, self.head.y)

        if (
            moved_head.x not in range(field_width)
            or moved_head.y not in range(field_height)
            or moved_head in self.fields
        ):
            raise GameOver

        self.head = moved_head

        fields_to_removes: list[Coordinate] = []

        for coord in self.fields.keys():
            self.fields[coord] -= 1

            if self.fields[coord] == 0:
               fields_to_removes.append(coord)

        for coord in fields_to_removes:
            del self.fields[coord]

        self.fields[self.head] = self.length



class GameState:
    def __init__(self, width: int, height: int) -> None:
        if width < 8 or height < 8:
            raise ValueError("Height and width need to be at least 8.")

        self.width = width
        self.height = height

        self.snake = Snake(
            head=Coordinate(4,2),
            direction=Direction.RIGHT,
            fields={
                Coordinate(2,2): 1,
                Coordinate(3,2): 2,
                Coordinate(4,2): 3,
            },
            length=3
        )

        self.food = self.get_new_food_coordinate()

    def get_new_food_coordinate(self) -> None:
        while True:
            x = randint(0, self.width - 1)
            y = randint(0, self.height - 1)
            coord = Coordinate(x, y)

            if coord not in self.snake.fields:
                return coord

    def get_score(self) -> int:
        return self.snake.length - 3

    def show(self) -> None:
        print("\n" * 20)

        top_line = "+-" + (self.width * "--") + "+"

        print(top_line)
        for y in range(self.height):
            print("| ", end='')

            for x in range(self.width):
                coord = Coordinate(x,y)
                if coord in self.snake.fields:
                    print("o ", end='')
                elif coord == self.food:
                    print("x ", end='')
                else:
                    print("  ", end='')

            print("|")

        print(top_line)

        score = self.get_score()
        print(f"Score: {score}")
        print()

    def step(self) -> None:
        self.snake.move(self.width, self.height)

        if self.snake.head == self.food:
            self.snake.length += 1
            self.food = self.get_new_food_coordinate()


if __name__ == "__main__":
    thread = Thread(target=wait_for_key_loop)
    thread.start()

    game_state = GameState(width=20, height=15)

    while True:
        sleep(0.1)

        try:
            game_state.step()
        except GameOver:
            print(f"Game over.")
            break

        game_state.show()


    # TODO exit program more nicely
    old_settings = termios.tcgetattr(sys.stdin)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    exit(0)
