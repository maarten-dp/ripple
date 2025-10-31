from dataclasses import dataclass

import arcade
from ripple.ecs.world import World
from ripple.utils import UInt16

SPRITE_SCALING = 0.5

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Move Sprite with Keyboard Example"

MOVEMENT_SPEED = 5

WORLD = World()


@dataclass
class Position:
    x: UInt16 = UInt16(0)
    y: UInt16 = UInt16(0)


@dataclass
class Velocity:
    dx: UInt16 = UInt16(0)
    dy: UInt16 = UInt16(0)


class Player(arcade.Sprite):
    def __init__(self, *args, **kwargs):
        self.pos = Position()
        self.vel = Velocity()
        self.entity = WORLD.create_entity(self.pos, self.vel)
        super().__init__(*args, **kwargs)

    def update(self, delta_time: float = 1 / 60):
        """Move the player"""
        # Move player.
        # Remove these lines if physics engine is moving player.
        # print(self.pos)

        self.center_x = float(self.pos.x)
        self.center_y = float(self.pos.y)

        # Check for out-of-bounds
        if self.left < 0:
            self.left = 0
        elif self.right > WINDOW_WIDTH - 1:
            self.right = WINDOW_WIDTH - 1

        if self.bottom < 0:
            self.bottom = 0
        elif self.top > WINDOW_HEIGHT - 1:
            self.top = WINDOW_HEIGHT - 1


class GameView(arcade.View):
    """
    Main application class.
    """

    def __init__(self):
        """
        Initializer
        """

        # Call the parent class initializer
        super().__init__()

        # Variables that will hold sprite lists
        self.player_list = None

        # Set up the player info
        self.player_sprite = None

        # Set the background color
        self.background_color = arcade.color.AMAZON

    def setup(self):
        """Set up the game and initialize the variables."""

        # Sprite lists
        self.player_list = arcade.SpriteList()

        # Set up the player
        self.player_sprite = Player(
            ":resources:images/animated_characters/female_person/femalePerson_idle.png",
            scale=SPRITE_SCALING,
        )
        self.player_sprite.center_x = 50
        self.player_sprite.center_y = 50
        self.player_list.append(self.player_sprite)

    def on_draw(self):
        """
        Render the screen.
        """

        # This command has to happen before we start drawing
        self.clear()

        # Draw all the sprites.
        self.player_list.draw()

    def on_update(self, delta_time):
        """Movement and game logic"""

        # Move the player
        for entity, (pos, vel) in WORLD.get_components(Position, Velocity):
            pos.x += vel.dx
            pos.y += vel.dy
        self.player_list.update(delta_time)

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""

        # If the player presses a key, update the speed
        for entity, (vel,) in WORLD.get_components(Velocity):
            if key == arcade.key.UP:
                vel.dy = MOVEMENT_SPEED
            elif key == arcade.key.DOWN:
                vel.dy = -MOVEMENT_SPEED
            elif key == arcade.key.LEFT:
                vel.dx = -MOVEMENT_SPEED
            elif key == arcade.key.RIGHT:
                vel.dx = MOVEMENT_SPEED

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key."""

        # If a player releases a key, zero out the speed.
        # This doesn't work well if multiple keys are pressed.
        # Use 'better move by keyboard' example if you need to
        # handle this.
        for entity, (vel,) in WORLD.get_components(Velocity):
            if key == arcade.key.UP or key == arcade.key.DOWN:
                vel.dy = 0
            elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
                vel.dx = 0


def main():
    """Main function"""
    # Create a window class. This is what actually shows up on screen
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)

    # Create and setup the GameView
    game = GameView()
    game.setup()

    # Show GameView on screen
    window.show_view(game)

    # Start the arcade game loop
    arcade.run()


if __name__ == "__main__":
    main()
