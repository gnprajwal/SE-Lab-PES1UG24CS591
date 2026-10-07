import pygame
from game.game_engine import GameEngine

# Initialize pygame/Start application
# small audio buffer so sound effects play without noticeable lag (Task 4)
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 600, 500
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Marble Tilt Maze - Pygame Version")

# Clock
clock = pygame.time.Clock()
FPS = 60

# Game loop
engine = GameEngine(WIDTH, HEIGHT)

def main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            engine.handle_event(event)

        # the end screen / menu can ask to exit (ESC or "Exit")
        if engine.quit_requested:
            running = False

        engine.handle_input()
        engine.update()
        engine.render(SCREEN)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
