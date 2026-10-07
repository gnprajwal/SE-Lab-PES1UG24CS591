import math
import pygame
from .marble import Marble
from .wall import Wall
from .sounds import SoundBank

# Game Engine

WHITE = (255, 255, 255)
DARK = (40, 40, 50)
WALL_COLOR = (90, 90, 110)
GOAL_COLOR = (60, 200, 120)
LOSE_COLOR = (230, 90, 90)
MUTED = (175, 175, 195)
PANEL = (24, 24, 32)

START_POS = (50, 50)

# Task 3: difficulty presets - tilt strength, friction, top speed, time limit.
# "Medium" is the original game's tuning.
DIFFICULTIES = {
    "Easy":   {"tilt_strength": 0.45, "friction": 0.035, "max_speed": 7,  "time_limit_ms": 60000},
    "Medium": {"tilt_strength": 0.60, "friction": 0.020, "max_speed": 9,  "time_limit_ms": 45000},
    "Hard":   {"tilt_strength": 0.80, "friction": 0.008, "max_speed": 11, "time_limit_ms": 25000},
}
DIFFICULTY_COLORS = {"Easy": (90, 200, 130), "Medium": (230, 190, 80), "Hard": (230, 100, 100)}
MENU_OPTIONS = ["Easy", "Medium", "Hard", "Exit"]

# Task 4: sound tuning
BOUNCE_MIN_IMPACT = 1.0   # ignore tiny contacts (marble resting on a wall)
BOUNCE_FULL_IMPACT = 7.0  # impact speed that plays the bounce at full volume
BOUNCE_COOLDOWN_MS = 70
WARNING_SECONDS = 5       # tick once per second for the last few seconds
INPUT_DELAY_MS = 600  # ignore input briefly after the round ends so a stray
                      # click/keypress doesn't skip the end screen


class GameEngine:
    RESTITUTION = 0.3  # fraction of speed kept when bouncing off a wall

    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.difficulty = "Medium"
        self.apply_difficulty(self.difficulty)
        self.menu_index = MENU_OPTIONS.index(self.difficulty)

        self.walls = self._build_maze()
        self.goal_x, self.goal_y, self.goal_radius = width - 60, height - 60, 22

        self.font = pygame.font.SysFont("Arial", 26)
        self.big_font = pygame.font.SysFont("Arial", 52, bold=True)
        self.mid_font = pygame.font.SysFont("Arial", 30, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 20)

        self.quit_requested = False  # main loop exits when this is True
        self.sounds = SoundBank()
        self.reset()

    # ------------------------------------------------------------------ state
    def apply_difficulty(self, name):
        """Set tilt strength / friction / top speed / time limit (Task 3)."""
        preset = DIFFICULTIES[name]
        self.difficulty = name
        self.tilt_strength = preset["tilt_strength"]
        self.friction = preset["friction"]
        self.max_speed = preset["max_speed"]
        self.time_limit_ms = preset["time_limit_ms"]

    def start_round(self, difficulty):
        self.apply_difficulty(difficulty)
        self.reset()

    def reset(self):
        """Start a fresh round with the current settings."""
        self.marble = Marble(*START_POS)
        self.start_ticks = pygame.time.get_ticks()
        self.state = "playing"  # "playing" | "game_over" | "menu"
        self.game_over = False
        self.result = None  # "solved" or "timeout"
        self.finish_time_ms = None
        self.end_elapsed_ms = None
        self.end_ticks = None
        self.last_bounce_ticks = -BOUNCE_COOLDOWN_MS
        self.last_tick_second = None

    def _end_round(self, result, elapsed_ms):
        self.state = "game_over"
        self.game_over = True
        self.result = result
        self.end_elapsed_ms = elapsed_ms
        self.end_ticks = pygame.time.get_ticks()
        if result == "solved":
            self.finish_time_ms = elapsed_ms
            self.sounds.play("goal", 0.9)
        else:
            self.sounds.play("timeout", 0.9)

    def elapsed_ms(self):
        """Time used this round - frozen once the round is over."""
        if self.end_elapsed_ms is not None:
            return self.end_elapsed_ms
        return pygame.time.get_ticks() - self.start_ticks

    def _build_maze(self):
        walls = []
        t = 16  # wall thickness

        # outer boundary
        walls.append(Wall(0, 0, self.width, t))
        walls.append(Wall(0, self.height - t, self.width, t))
        walls.append(Wall(0, 0, t, self.height))
        walls.append(Wall(self.width - t, 0, t, self.height))

        # a few internal walls forming a simple winding path
        walls.append(Wall(0, 140, self.width - 140, t))
        walls.append(Wall(140, 260, self.width - 140, t))
        walls.append(Wall(0, 380, self.width - 140, t))

        return walls

    # ------------------------------------------------------------------ input
    def handle_event(self, event):
        # Tilting is driven by the continuous mouse position (handle_input);
        # discrete events are only used on the end screen and the menu.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
            self.sounds.toggle_mute()
            return
        if self.state == "game_over":
            self._handle_game_over_event(event)
        elif self.state == "menu":
            self._handle_menu_event(event)

    def _handle_game_over_event(self, event):
        if pygame.time.get_ticks() - self.end_ticks < INPUT_DELAY_MS:
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.quit_requested = True
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._open_menu()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._open_menu()

    def _open_menu(self):
        self.state = "menu"
        self.menu_index = MENU_OPTIONS.index(self.difficulty)

    def _choose(self, option):
        if option == "Exit":
            self.quit_requested = True
        else:
            self.start_round(option)

    def _handle_menu_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.quit_requested = True
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.menu_index = (self.menu_index - 1) % len(MENU_OPTIONS)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.menu_index = (self.menu_index + 1) % len(MENU_OPTIONS)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._choose(MENU_OPTIONS[self.menu_index])
            elif event.key in (pygame.K_1, pygame.K_KP1):
                self._choose("Easy")
            elif event.key in (pygame.K_2, pygame.K_KP2):
                self._choose("Medium")
            elif event.key in (pygame.K_3, pygame.K_KP3):
                self._choose("Hard")
        elif event.type == pygame.MOUSEMOTION:
            for i, (_, rect) in enumerate(self.buttons()):
                if rect.collidepoint(event.pos):
                    self.menu_index = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for label, rect in self.buttons():
                if rect.collidepoint(event.pos):
                    self._choose(label)
                    break

    def buttons(self):
        """(label, rect) for each menu button - used for clicks and drawing."""
        w, h, gap = 340, 46, 14
        top = 175
        out = []
        for i, label in enumerate(MENU_OPTIONS):
            rect = pygame.Rect(0, 0, w, h)
            rect.centerx = self.width // 2
            rect.top = top + i * (h + gap)
            out.append((label, rect))
        return out

    def handle_input(self):
        if self.state != "playing":
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx = mouse_x - self.width // 2
        dy = mouse_y - self.height // 2
        dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
        ax = (dx / dist) * self.tilt_strength
        ay = (dy / dist) * self.tilt_strength
        self.marble.vx += ax
        self.marble.vy += ay

    # ----------------------------------------------------------------- update
    def update(self):
        if self.state != "playing":
            return

        elapsed = self.elapsed_ms()
        if elapsed >= self.time_limit_ms:
            self._end_round("timeout", self.time_limit_ms)
            return

        self.marble.vx *= (1 - self.friction)
        self.marble.vy *= (1 - self.friction)

        speed = (self.marble.vx ** 2 + self.marble.vy ** 2) ** 0.5
        if speed > self.max_speed:
            scale = self.max_speed / speed
            self.marble.vx *= scale
            self.marble.vy *= scale

        self.marble.x += self.marble.vx
        self.marble.y += self.marble.vy

        impact = self._resolve_wall_collisions()
        self._bounce_sound(impact)
        self._warning_tick(elapsed)

        gx = self.goal_x - self.marble.x
        gy = self.goal_y - self.marble.y
        if (gx ** 2 + gy ** 2) ** 0.5 <= self.goal_radius:
            self._end_round("solved", elapsed)

    def _bounce_sound(self, impact):
        now = pygame.time.get_ticks()
        if impact < BOUNCE_MIN_IMPACT or now - self.last_bounce_ticks < BOUNCE_COOLDOWN_MS:
            return
        self.last_bounce_ticks = now
        volume = 0.25 + 0.75 * min(1.0, impact / BOUNCE_FULL_IMPACT)
        self.sounds.play("bounce", volume)

    def _warning_tick(self, elapsed):
        seconds_left = math.ceil((self.time_limit_ms - elapsed) / 1000)
        if 0 < seconds_left <= WARNING_SECONDS and seconds_left != self.last_tick_second:
            self.last_tick_second = seconds_left
            self.sounds.play("tick", 0.6)

    def _resolve_wall_collisions(self):
        """Circle-vs-rectangle collision (Task 1).

        For every wall we find the point on the wall rectangle closest to
        the marble's centre. The marble only collides when that point is
        closer than the marble's radius, so a bounce happens exactly when
        the round marble touches the wall - including at corners, where the
        old square bounding-box test produced "phantom" bounces.

        The marble is pushed out along the contact normal and only the
        velocity component going *into* the wall is reflected (with the
        same 0.3 restitution as before), so it bounces cleanly off flat
        faces and glances realistically off corners.
        Returns the strongest impact speed this frame (0 if none).
        """
        m = self.marble
        r = m.radius
        strongest_impact = 0.0

        for wall in self.walls:
            wr = wall.rect()

            # closest point on the rectangle to the circle centre
            nearest_x = min(max(m.x, wr.left), wr.right)
            nearest_y = min(max(m.y, wr.top), wr.bottom)
            dx = m.x - nearest_x
            dy = m.y - nearest_y
            dist_sq = dx * dx + dy * dy

            if dist_sq >= r * r:
                continue  # the round marble is not touching this wall

            if dist_sq > 1e-9:
                dist = dist_sq ** 0.5
                nx, ny = dx / dist, dy / dist
                penetration = r - dist
            else:
                # centre is inside the rectangle (very fast hit): push out
                # through the nearest face instead
                left = m.x - wr.left
                right = wr.right - m.x
                top = m.y - wr.top
                bottom = wr.bottom - m.y
                smallest = min(left, right, top, bottom)
                if smallest == left:
                    nx, ny, penetration = -1.0, 0.0, left + r
                elif smallest == right:
                    nx, ny, penetration = 1.0, 0.0, right + r
                elif smallest == top:
                    nx, ny, penetration = 0.0, -1.0, top + r
                else:
                    nx, ny, penetration = 0.0, 1.0, bottom + r

            # move the marble out of the wall
            m.x += nx * penetration
            m.y += ny * penetration

            # reflect only the velocity component heading into the wall
            v_normal = m.vx * nx + m.vy * ny
            if v_normal < 0:
                m.vx -= (1 + self.RESTITUTION) * v_normal * nx
                m.vy -= (1 + self.RESTITUTION) * v_normal * ny
                strongest_impact = max(strongest_impact, -v_normal)

        return strongest_impact

    # ----------------------------------------------------------------- render
    def render(self, screen):
        self._draw_board(screen)
        if self.state == "game_over":
            self._draw_game_over(screen)
        elif self.state == "menu":
            self._draw_menu(screen)

    def _draw_board(self, screen):
        screen.fill(DARK)

        for wall in self.walls:
            pygame.draw.rect(screen, WALL_COLOR, wall.rect())

        pygame.draw.circle(screen, GOAL_COLOR, (self.goal_x, self.goal_y), self.goal_radius)
        pygame.draw.circle(screen, WHITE, (int(self.marble.x), int(self.marble.y)), self.marble.radius)

        ms_left = max(0, self.time_limit_ms - self.elapsed_ms())
        seconds_left = math.ceil(ms_left / 1000)
        color = LOSE_COLOR if seconds_left <= 5 else WHITE
        timer_text = self.font.render(f"Time: {seconds_left}s", True, color)
        screen.blit(timer_text, (10, 10))

        diff_text = self.small_font.render(self.difficulty, True, DIFFICULTY_COLORS[self.difficulty])
        screen.blit(diff_text, (self.width - diff_text.get_width() - 12, 14))
        if self.sounds.muted:
            mute_text = self.small_font.render("muted (M)", True, MUTED)
            screen.blit(mute_text, (self.width - mute_text.get_width() - 12, 36))

    def _dim(self, screen, alpha=170):
        shade = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        shade.fill((10, 10, 16, alpha))
        screen.blit(shade, (0, 0))

    def _blit_center(self, screen, surf, y):
        screen.blit(surf, (self.width // 2 - surf.get_width() // 2, y))

    def _draw_panel(self, screen, top, height, accent):
        panel = pygame.Rect(0, 0, 420, height)
        panel.centerx, panel.top = self.width // 2, top
        pygame.draw.rect(screen, PANEL, panel, border_radius=14)
        pygame.draw.rect(screen, accent, panel, 3, border_radius=14)
        return panel

    def _draw_game_over(self, screen):
        self._dim(screen)
        solved = self.result == "solved"
        accent = GOAL_COLOR if solved else LOSE_COLOR
        panel = self._draw_panel(screen, 110, 270, accent)

        title = "Maze Solved!" if solved else "Time's Up!"
        self._blit_center(screen, self.big_font.render(title, True, accent), panel.top + 30)
        if solved:
            line = f"Finish time: {self.finish_time_ms / 1000:.2f}s"
        else:
            line = "The marble didn't reach the goal."
        self._blit_center(screen, self.font.render(line, True, WHITE), panel.top + 110)

        ready = pygame.time.get_ticks() - self.end_ticks >= INPUT_DELAY_MS
        hint_color = MUTED if ready else (90, 90, 105)
        self._blit_center(screen, self.small_font.render("ENTER / click  -  play again", True, hint_color), panel.top + 175)
        self._blit_center(screen, self.small_font.render("ESC  -  quit", True, hint_color), panel.top + 205)

    def _draw_menu(self, screen):
        self._dim(screen, 200)
        self._blit_center(screen, self.mid_font.render("Play again?", True, WHITE), 70)
        self._blit_center(screen, self.small_font.render("Choose a difficulty", True, MUTED), 112)

        details = {
            name: f"{p['time_limit_ms'] // 1000}s  -  tilt {p['tilt_strength']:.2f}"
            for name, p in DIFFICULTIES.items()
        }
        mouse = pygame.mouse.get_pos()
        buttons = self.buttons()
        hovered = next((i for i, (_, r) in enumerate(buttons) if r.collidepoint(mouse)), None)
        active = hovered if hovered is not None else self.menu_index
        for i, (label, rect) in enumerate(buttons):
            selected = i == active
            accent = DIFFICULTY_COLORS.get(label, (150, 150, 170))
            pygame.draw.rect(screen, (50, 50, 66) if selected else PANEL, rect, border_radius=10)
            pygame.draw.rect(screen, accent if selected else (70, 70, 90), rect, 2, border_radius=10)
            prefix = f"{i + 1}. " if label != "Exit" else ""
            text = self.font.render(prefix + label, True, accent if selected else WHITE)
            screen.blit(text, (rect.left + 18, rect.centery - text.get_height() // 2))
            if label in details:
                d = self.small_font.render(details[label], True, MUTED)
                screen.blit(d, (rect.right - d.get_width() - 14, rect.centery - d.get_height() // 2))

        self._blit_center(screen, self.small_font.render(
            "click, press 1/2/3, or use arrows + ENTER  -  ESC to exit", True, MUTED), self.height - 50)
