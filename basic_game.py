# Basic arcade shooter

# Imports
import random
import math
import time
import os
import arcade
from copy import deepcopy
# from IPython import embed

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Arcade Space Shooter"
SCALING = 1.0
PL_E_SCALING = 1.0
FULLSCREEN = False

HEALTHBAR_X = 600
HEALTHBAR_Y = 20
HEALTHBAR_WIDTH = 100
HEALTHBAR_HEIGHT = 20

PLAYER_DIRECTORY = "images/jet_anim/"
MISSILE_DIRECTORY = "images/missile_anim/"
EXPLOSION_DIRECTORY = "images/explosion_anim/"

class SpaceShooter(arcade.Window):
    """Space Shooter side scroller game
    Player starts on the left, enemies appear on the right
    Player can move anywhere, but not off screen
    Enemies fly to the left at variable speed
    Collisions end the game
    """

    def __init__(self, width, height, title):
        """Initialize the game
        """
        super().__init__(width, height, title, fullscreen=FULLSCREEN)

        # Set up the empty sprite lists
        self.enemies_list = arcade.SpriteList()
        self.clouds_list = arcade.SpriteList()
        self.explosions_list = arcade.SpriteList()
        self.all_sprites = arcade.SpriteList()
        self.player = None
        self.background_music = None
        self.score = 0
        self.paused = False
        self.destroyed = False
        self.collision_time = 0.0
        self.collision_length = 1.0
        self.explosion_textures = []

    def setup(self):
        """Get the game ready to play
        """

        # Set the background color
        arcade.set_background_color(arcade.color.SKY_BLUE)

        # Set up the player
        # self.player = arcade.Sprite("images/plane.png", PL_E_SCALING)
        player_img = os.path.join(PLAYER_DIRECTORY, "Plane_0.png")
        self.player = AnimatedSprite(player_img, PLAYER_DIRECTORY, PL_E_SCALING)
        self.player.center_y = self.height / 2
        self.player.left = 10
        self.all_sprites.append(self.player)

        # Spawn a new enemy every 0.25 seconds
        arcade.schedule(self.add_enemy, 0.2)

        # Spawn a new cloud every second
        arcade.schedule(self.add_cloud, 4.0)

        self.explosion_textures = load_anim_frames(EXPLOSION_DIRECTORY)
        self.explosion_img = os.path.join(EXPLOSION_DIRECTORY, "sprite_0.png")
        self.enemy_img = os.path.join(MISSILE_DIRECTORY, "Missile_0.png")
        self.enemy = AnimatedSprite(self.enemy_img, MISSILE_DIRECTORY, PL_E_SCALING)

        # Load your background music
        # Sound source: http://ccmixter.org/files/Apoxode/59262
        # License: https://creativecommons.org/licenses/by/3.0/
        self.background_music = arcade.load_sound(
            "sounds/Apoxode_-_Electric_1.wav"
        )

        # Load your sounds
        # Sound sources: Jon Fincher
        self.collision_sound = arcade.load_sound("sounds/Collision.wav")
        self.move_up_sound = arcade.load_sound("sounds/Rising_putter.wav")
        self.move_down_sound = arcade.load_sound("sounds/Falling_putter.wav")

        # Start the background music
        arcade.play_sound(self.background_music)

        # Unpause everything and reset the collision timer
        self.paused = False
        self.destroyed = False
        self.collision_time = 0.0
        self.collision_length = 1.0
        self.score = 0
        self.max_health = 100
        self.health = 100

        for i in range(5):
            self.add_cloud(0.0, on_screen=True)

    def add_enemy(self, delta_time: float):
        """Adds a new enemy to the screen

        Arguments:
            delta_time {float} -- How much time has passed since the last call
        """

        if self.paused:
            return

        # First, create the new enemy sprite
        enemy = deepcopy(self.enemy)

        # Set its position to a random height and off screen right
        enemy.left = random.randint(self.width, self.width + 10)
        enemy.top = random.randint(10, self.height - 10)

        # Set its speed to a random speed heading left
        enemy.velocity = (random.randint(-600, -100), 0)

        # Add it to the enemies list
        self.enemies_list.append(enemy)
        self.all_sprites.append(enemy)

    def add_cloud(self, delta_time: float, on_screen=False):
        """Adds a new cloud to the screen

        Arguments:
            delta_time {float} -- How much time has passed since the last call
        """
        if self.paused:
            return

        # First, create the new cloud sprite
        cloud = FlyingSprite("images/cloud.png", SCALING)

        # Set its position to a random height and off screen right
        if on_screen is True:
            cloud.left = random.randint(0, SCREEN_WIDTH)
        else:
            cloud.left = random.randint(self.width, self.width + 10)
        cloud.top = random.randint(10, self.height - 10)

        # Set its speed to a random speed heading left
        cloud.velocity = (random.randint(-50, -10), 0)

        # Add it to the enemies list
        self.clouds_list.append(cloud)
        self.all_sprites.append(cloud)

    def on_key_press(self, symbol, modifiers):
        """Handle user keyboard input
        Q: Quit the game
        P: Pause/Unpause the game
        I/J/K/L: Move Up, Left, Down, Right
        Arrows: Move Up, Left, Down, Right

        Arguments:
            symbol {int} -- Which key was pressed
            modifiers {int} -- Which modifiers were pressed
        """
        if symbol == arcade.key.Q:
            # Quit immediately
            arcade.close_window()

        if symbol == arcade.key.P:
            self.paused = not self.paused

        if symbol == arcade.key.I or symbol == arcade.key.UP:
            self.player.change_y = 250
            arcade.play_sound(self.move_up_sound)

        if symbol == arcade.key.K or symbol == arcade.key.DOWN:
            self.player.change_y = -250
            arcade.play_sound(self.move_down_sound)

        if symbol == arcade.key.J or symbol == arcade.key.LEFT:
            self.player.change_x = -250

        if symbol == arcade.key.L or symbol == arcade.key.RIGHT:
            self.player.change_x = 250

    def on_key_release(self, symbol: int, modifiers: int):
        """Undo movement vectors when movement keys are released

        Arguments:
            symbol {int} -- Which key was pressed
            modifiers {int} -- Which modifiers were pressed
        """
        if (
            symbol == arcade.key.I
            or symbol == arcade.key.K
            or symbol == arcade.key.UP
            or symbol == arcade.key.DOWN
        ):
            self.player.change_y = 0

        if (
            symbol == arcade.key.J
            or symbol == arcade.key.L
            or symbol == arcade.key.LEFT
            or symbol == arcade.key.RIGHT
        ):
            self.player.change_x = 0

    def on_update(self, delta_time: float):
        """Update the positions and statuses of all game objects
        If paused, do nothing

        Arguments:
            delta_time {float} -- Time since the last update
        """

        # If paused, don't update anything
        if self.paused:
            self.paused = False

        # Did you hit anything? If so, end the game
        collisions = self.player.collides_with_list(self.enemies_list)
        if len(collisions) > 0:
            arcade.play_sound(self.collision_sound)
            self.health -= collisions[0].damage
            self.collision_time = time.time()

            # Save off missile and plane location
            # remove missile and plane from lists
            explosion = Explosion(self.explosion_img, self.explosion_textures)

            # Move it to the location of the coin
            explosion.center_x = collisions[0].center_x
            explosion.center_y = collisions[0].center_y
            explosion.change_x = collisions[0].change_x

            # Call update() because it sets which image we start on
            # explosion.update()

            # Add to a list of sprites that are explosions
            self.explosions_list.append(explosion)
            self.all_sprites.append(explosion)
            collisions[0].remove_from_sprite_lists()

        if self.health <= 0:
            if time.time() - self.collision_time > self.collision_length:
                arcade.close_window()
        else:
            self.score += 1
        
        self.player.update(delta_time)
        self.enemies_list.update()
        self.explosions_list.update()
        self.clouds_list.update()

        # Keep the player on screen
        if self.player.top > self.height:
            self.player.top = self.height
        if self.player.right > self.width:
            self.player.right = self.width
        if self.player.bottom < 0:
            self.player.bottom = 0
        if self.player.left < 0:
            self.player.left = 0

    def on_draw(self):
        """Draw all game objects"""

        arcade.start_render()
        # self.all_sprites.draw()
        self.clouds_list.draw(pixelated=True)
        self.enemies_list.draw(pixelated=True)
        self.player.draw(pixelated=True)
        self.explosions_list.draw(pixelated=True)

        # for enemy in self.enemies_list:
        #     enemy.draw_hit_box()
        # self.player.draw_hit_box()

        # Draw the score in the lower left
        score_text = f"Score: {self.score}"

        # First a black background for a shadow effect
        arcade.draw_text(
            score_text,
            start_x=10,
            start_y=10,
            color=arcade.csscolor.BLACK,
            font_size=40,
        )
        # Now in white slightly shifted
        arcade.draw_text(
            score_text,
            start_x=12,
            start_y=12,
            color=arcade.csscolor.WHITE,
            font_size=40,
        )

        # Draw the 'unhealthy' background
        if self.health < self.max_health:
            arcade.draw_rectangle_filled(center_x=HEALTHBAR_X,
                                         center_y=HEALTHBAR_Y,
                                         width=HEALTHBAR_WIDTH,
                                         height=HEALTHBAR_HEIGHT,
                                         color=arcade.color.RED)

        # Calculate width based on health
        health_width = HEALTHBAR_WIDTH * (self.health / self.max_health)

        arcade.draw_rectangle_filled(center_x=HEALTHBAR_X - 0.5 * (HEALTHBAR_WIDTH - health_width),
                                     center_y=HEALTHBAR_Y,
                                     width=health_width,
                                     height=HEALTHBAR_HEIGHT,
                                     color=arcade.color.GREEN)


def load_anim_frames(directory):
    frames = []
    for filename in os.listdir(directory):
        if filename.endswith(".png"):
            path = os.path.join(directory, filename)
            frames.append(arcade.load_texture(path))
    return frames

class FlyingSprite(arcade.Sprite):
    """Base class for all flying sprites
    Flying sprites include enemies and clouds
    """

    def update(self, delta_time: float = 1/60):
        """Update the position of the sprite
        When it moves off screen to the left, remove it
        """

        # Move the sprite
        self.center_x = self.center_x + self.change_x * delta_time
        self.center_y = self.center_y + self.change_y * delta_time

        # Remove if off the screen
        if self.right < 0:
            self.remove_from_sprite_lists()


class AnimatedSprite(FlyingSprite):
    """Class for the character and animations"""

    def __init__(self, init_frame, sprite_directory, scale=1.0):
        super().__init__(init_frame, scale, hit_box_algorithm="Detailed")
        
        self.idle_textures = load_anim_frames(sprite_directory)
        self.frame_num = 0
        self.num_frames = len(self.idle_textures) - 1
        self.timer = 0
        self.change_per = 0.03
        self.texture = self.idle_textures[self.frame_num]
        self.damage = 20

    def update(self, delta_time: float = 1 / 60):
        super().update(delta_time)

        self.texture = self.idle_textures[self.frame_num]

        self.timer += delta_time
        if self.timer > self.change_per:
            self.frame_num += 1
            self.timer = 0
            if self.frame_num > self.num_frames:
                self.frame_num = 0

class Explosion(arcade.Sprite):
    """Generates an explosion animation"""
    def __init__(self, init_frame, texture_list, scale=1.0):
        super().__init__(init_frame, scale)
        self.texture_list = texture_list
        self.frame_num = 0
        self.num_frames = len(self.texture_list) - 1
        self.timer = 0
        self.texture = self.texture_list[self.frame_num]
        self.change_per = 0.05

    def update(self, delta_time: float = 1 / 60):
        # Move the sprite
        self.center_x = self.center_x + self.change_x * delta_time
        self.center_y = self.center_y + self.change_y * delta_time
        
        self.texture = self.texture_list[self.frame_num]

        self.timer += delta_time
        if self.timer > self.change_per:
            self.frame_num += 1
            self.timer = 0
            if self.frame_num > self.num_frames:
                self.remove_from_sprite_lists()



if __name__=='__main__':
    import os
    # if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    #     os.chdir(sys._MEIPASS)
    # Create a new Space Shooter window
    space_game = SpaceShooter(
        int(SCREEN_WIDTH * SCALING), int(SCREEN_HEIGHT * SCALING), SCREEN_TITLE
    )
    # Setup to play
    space_game.setup()
    # Run the game
    arcade.run()
