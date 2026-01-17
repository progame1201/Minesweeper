import sys
import time
import numpy
import pygame
from config import *
from objects import *


pygame.init()
sys.setrecursionlimit(10000)

loaded_images = {}
cells: list[Cell] = []
remove_color_in_next_tick = []
x, y = WINDOW_SIZE
mines_count = int((x // CELL_SIZE) * (y // CELL_SIZE) * MINES_PERCENT / 100)

time_from_start = 0
last_click_time = 0  # for phone mode
flagged = 0
wins = 0
show_bombs = False
running = True

screen = pygame.display.set_mode((x, y + 30), pygame.HWSURFACE | pygame.DOUBLEBUF)
clock = pygame.time.Clock()
info_font = pygame.font.Font(None, 15)
cell_font = pygame.font.Font(None, CELL_SIZE)
text_font = pygame.font.Font(None, int(min(x, y) * 0.1))

if x % CELL_SIZE != 0 or x % CELL_SIZE != 0:
    print(f"CAN'T CONTINUE! RESOLUTION NOT DIVISIBLE BY {CELL_SIZE}")
    exit()
if not RANDOMIZE_SEED:
    numpy.random.seed(SEED)

print(f"Window size: {x // CELL_SIZE}x{y // CELL_SIZE}")

def show_text_and_freeze_game(text, color, seconds, background=False):
    text_width, text_height = text_font.size(text)
    text_pos_x, text_pos_y = x / 2 - text_width / 2, y / 2 - text_height / 2
    if background:
        pygame.draw.rect(screen, (255, 255, 255, 255), pygame.Rect(text_pos_x, text_pos_y, text_width, text_height))
    screen.blit(text_font.render(text, True, color), (text_pos_x, text_pos_y))
    pygame.display.flip()
    time.sleep(seconds)
    pygame.event.clear()

def open_cell(cell):
    cell.text = str(cell.mines_around)
    cell.color = COLORS[cell.mines_around]
    cell.opened = True

def zero_cell_recursion(cell):
    if cell.opened:
        return

    neighbors = get_neighbors(cell)

    if cell.mines_around == 0:
        if cell.flagged:
            return
        open_cell(cell)
        for _cell in neighbors:
            zero_cell_recursion(_cell)
    else:
        if cell.flagged:
            return
        open_cell(cell)

def get_neighbors(cell: Cell, cursor=0) -> list[Cell]:
    neighbors = []
    x, y = cell.rect.x, cell.rect.y
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            if dx == 0 and dy == 0:
                continue

            neighbor_x = x + dx * CELL_SIZE
            neighbor_y = y + dy * CELL_SIZE
            for i, other_cell in enumerate(cells[cursor:]):
                if other_cell.rect.x == neighbor_x and other_cell.rect.y == neighbor_y:
                    cursor = i
                    if DEBUG:
                        redraw_cell(other_cell, (0, 200, 50))
                        pygame.display.flip()
                        redraw_cell(other_cell)
                    neighbors.append(other_cell)

                    break

    return neighbors

def show_first_zero_cell():
    zero_cells = []
    s = time.time()
    for cell in cells:
        if cell.mines_around == 0 and not cell.mine:
            if len(cells) > 1000:
                if numpy.random.random() <= 0.005:
                    zero_cell_recursion(cell)
                    return
            zero_cells.append(cell)
    print(time.time() - s)
    if not zero_cells:
        return

    zero_cell_recursion(numpy.random.choice(zero_cells))

def start_game():
    global time_from_start
    global show_bombs
    global flagged

    show_text_and_freeze_game("Generating level...", (0, 200, 100), 0, True)
    if DEBUG:
        show_bombs = True
    else:
        show_bombs = False

    flagged = 0
    cells.clear()

    i = 0
    for _y in range(0, int(WINDOW_SIZE[1] / CELL_SIZE)):
        for _x in range(0, int(WINDOW_SIZE[0] / CELL_SIZE)):
            rect = pygame.Rect(CELL_SIZE * _x, CELL_SIZE * _y, CELL_SIZE, CELL_SIZE)
            cell = Cell(rect, COLORS["closed"], "")
            cells.append(cell)
            redraw_cell(cell)
        if i >= 3:
            i = 0
        i+=1
        show_text_and_freeze_game(f"Generating level {["/", "|", "\\", "-"][i]}", (0, 0, 0), 0, True)
        #time.sleep(0.1)

    redraw_cells()
    show_text_and_freeze_game("Generating mines...", (0, 0, 0), 0, True)

    time_from_start = time.time()

    cells_copy = cells.copy()
    numpy.random.shuffle(cells_copy)

    need_to_create = mines_count
    for cell in cells_copy:
        if need_to_create <= 0:
            break
        need_to_create -= 1
        cell.mine = True
        if DEBUG:
            cell.color = (255, 0, 0)
            redraw_cell(cell)
            pygame.display.update(cell.rect)

    redraw_cells()
    for cell in cells:
        cell.mines_around = len([cell_neighbor for cell_neighbor in get_neighbors(cell) if cell_neighbor.mine])

    show_text_and_freeze_game("Choosing first cells...", (0, 0, 0), 0, True)
    show_first_zero_cell()
    print(len(cells))

def draw_image_on_cell(cell, image_path):
    if image_path not in loaded_images:
        loaded_images[image_path] = pygame.image.load(image_path)
        loaded_images[image_path] = pygame.transform.scale(loaded_images[image_path], (CELL_SIZE / 1.3, CELL_SIZE / 1.3))

    screen.blit(loaded_images[image_path], (cell.rect.x + CELL_SIZE // 6, cell.rect.y + CELL_SIZE // 6))

def redraw_cell(cell, color=None):
    pygame.draw.rect(screen, cell.color if color is None else color, cell.rect)

    if cell.text:
        screen.blit(cell_font.render(f"{cell.text}", False, (0, 0, 0)),
                    (cell.rect.x + CELL_SIZE // 4, cell.rect.y + CELL_SIZE // 4))

    if show_bombs:
        if cell.mine and not cell.flagged:
            draw_image_on_cell(cell, "assets/bomb.png")

    if cell.flagged:
        draw_image_on_cell(cell, "assets/flag.png")

    if not cell.opened:
        pygame.draw.rect(screen, (185, 184, 192), pygame.Rect(cell.rect.x, cell.rect.y, CELL_SIZE, CELL_SIZE), width=1)

def redraw_cells():
    for cell in cells:
        redraw_cell(cell)

def game_over(cell_that_killed_player):
    global show_bombs

    show_bombs = True

    for cell in cells:
        if cell.mine and cell.flagged:
            cell.color = (82, 171, 99)
    cell_that_killed_player.color = (255, 0, 0)

    redraw_cells()
    show_text_and_freeze_game("Game Over", (200, 34, 34), 5)

    start_game()
    pygame.event.clear()

def check_for_win():
    global wins
    good = []
    opened = []
    for cell in cells:
        if cell.flagged and cell.mine:
            good.append(cell)
        if cell.opened and not cell.mine:
            opened.append(cell)
    good = len(good)
    opened = len(opened)

    if good == mines_count and opened == len(cells) - mines_count:
        show_text_and_freeze_game(f"You won!", (66, 170, 96), 2)
        wins += 1
        start_game()

def get_cell_on_point(point) -> Cell | None:
    cell: list[Cell] = [_cell for _cell in cells if _cell.rect.collidepoint(point)]

    if not cell:
        return None

    return cell[0]

def clear_cells_that_can_be_opened():
    for cell in cells:
        if cell.color == COLORS["will be opened"]:
            cell.color = COLORS["closed"]

def safety_open(cell):
    if cell.mines_around == 0:
        return

    neighbors = get_neighbors(cell)
    flagged = len([cell_neighbor for cell_neighbor in neighbors if cell_neighbor.flagged])

    if flagged == cell.mines_around:
        for cell_neighbor in neighbors:
            if cell_neighbor.mine and not cell_neighbor.flagged:
                game_over(cell_neighbor)
                continue

            if cell_neighbor.flagged:
                continue

            if cell_neighbor.mines_around == 0:
                zero_cell_recursion(cell_neighbor)
                continue
            open_cell(cell_neighbor)
    check_for_win()

def left_click_handler(point):
    cell = get_cell_on_point(point)
    if not cell:
        return

    if cell.flagged:
        return
    if cell.mine:
        game_over(cell)
        return

    if cell.opened:
        safety_open(cell)
        return

    if cell.mines_around == 0:
        zero_cell_recursion(cell)

    open_cell(cell)
    check_for_win()

def right_click_handler(point):
    global flagged
    cell = get_cell_on_point(point)
    if not cell:
        return

    if cell.opened:
        return

    if not cell.flagged:
        if flagged >= mines_count:
            return
        cell.flagged = True
        flagged += 1
    else:
        cell.flagged = False
        flagged -= 1

    check_for_win()

def show_what_will_be_opened(point):
    cell = get_cell_on_point(point)

    if not cell:
        return

    if not cell.opened or cell.flagged:
        return

    neighbors = get_neighbors(cell)
    flagged = len([cell_neighbor for cell_neighbor in neighbors if cell_neighbor.flagged])

    if flagged == cell.mines_around:
        for cell_neighbor in neighbors:
            if cell_neighbor.opened or cell_neighbor.flagged:
                continue
            cell_neighbor.color = COLORS["will be opened"]

start_game()

while running:
    for cell in remove_color_in_next_tick:
        if cell.opened:
            cell.color = COLORS[cell.mines_around]
        else:
            cell.color = COLORS["closed"]
        remove_color_in_next_tick.remove(cell)

    if not PHONE_MODE:
        cursor_changed = False
        for cell in cells:
            if not cell.opened:
                if cell.rect.collidepoint(pygame.mouse.get_pos()):
                    cell.color = COLORS["will be opened"]
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                    cursor_changed = True
                    remove_color_in_next_tick.append(cell)
                    break
        if not cursor_changed:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            last_click_time = time.time()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                start_game()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                show_what_will_be_opened(event.pos)

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                clear_cells_that_can_be_opened()
                if not PHONE_MODE:
                    left_click_handler(event.pos)
                    continue
                if time.time() - last_click_time <= 0.15:
                    left_click_handler(event.pos)
                else:
                    right_click_handler(event.pos)
            if event.button == 3:
                right_click_handler(event.pos)
    redraw_cells()
    pygame.draw.rect(screen, "white", pygame.Rect(0, y, x, 30))
    screen.blit(
        info_font.render(f"Flags count: {mines_count - flagged}", True, (0, 0, 0)), (0, y))
    screen.blit(
        info_font.render(f"Time from start: {round(time.time() - time_from_start)}", True, (0, 0, 0)), (0, y + 10))
    screen.blit(
        info_font.render(f"FPS: {clock.get_fps():.2f}", True, (0, 0, 0)),
        (0, y+20))

    pygame.display.flip()
    clock.tick(144)


pygame.quit()