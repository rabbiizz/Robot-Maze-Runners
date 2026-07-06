import pygame
import random
import heapq
import sys
import os

# ==========================================
# บังคับให้หน้าต่างเกมเปิดขึ้นมาที่ตำแหน่งพิกัด (50, 50) ของหน้าจอ
# เพื่อป้องกันไม่ให้แถบด้านบนทะลุขอบจอจนลากไม่ได้
# ==========================================
os.environ['SDL_VIDEO_WINDOW_POS'] = "50,50" 

# ==========================================
# 1. ตั้งค่าพื้นฐานของเกม
# ==========================================
CELLS_X, CELLS_Y = 30, 30
# ปรับขนาดช่องให้เล็กลงอีก เพื่อให้หน้าต่างแสดงผลได้ครบถ้วน ไม่โดนตัดขอบล่าง
CELL_SIZE = 10  

# ใช้กริดแบบ maze จริง: ช่องเดินอยู่ที่ index คี่
GRID_X, GRID_Y = CELLS_X * 2 + 1, CELLS_Y * 2 + 1

WIDTH = GRID_X * CELL_SIZE
HEADER_HEIGHT = 60
HEIGHT = GRID_Y * CELL_SIZE + HEADER_HEIGHT

# สี
BLACK = (20, 20, 20)      # กำแพง
WHITE = (240, 240, 240)   # ทางเดิน
GRAY = (150, 150, 150)    # หนู
GOLD = (255, 215, 0)      # ชีส
CYAN = (0, 200, 255)      # เส้นทาง A* (ซ่อนไว้)
RED = (255, 50, 50)       # ตาย/เวลาใกล้หมด
GREEN = (50, 200, 50)     # เวลาปกติ
BLUE = (80, 255, 120)     # Start
MAGENTA = (255, 100, 220) # End

# ==========================================
# 2. ระบบสร้างเขาวงกต
# ==========================================
def generate_maze(rows, cols):
    grid = [[1 for _ in range(cols)] for _ in range(rows)]

    stack = [(1, 1)]
    grid[1][1] = 0

    while stack:
        r, c = stack[-1]
        neighbors = []

        for dr, dc in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            nr, nc = r + dr, c + dc
            if 0 < nr < rows - 1 and 0 < nc < cols - 1 and grid[nr][nc] == 1:
                neighbors.append((nr, nc, dr, dc))

        if neighbors:
            nr, nc, dr, dc = random.choice(neighbors)
            grid[nr][nc] = 0
            grid[r + dr // 2][c + dc // 2] = 0
            stack.append((nr, nc))
        else:
            stack.pop()

    return grid

# ==========================================
# 3. A* หาเส้นทาง
# ==========================================
def heuristic(a, b):
    # Manhattan distance
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def solve_maze(grid, start, goal):
    frontier = []
    heapq.heappush(frontier, (0, start))

    came_from = {start: None}
    cost_so_far = {start: 0}

    think_count = 0  # นับจำนวนครั้งที่ AI ขยายโหนด/คิด

    while frontier:
        _, current = heapq.heappop(frontier)
        think_count += 1

        if current == goal:
            break

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            next_node = (current[0] + dr, current[1] + dc)

            if 0 <= next_node[0] < len(grid) and 0 <= next_node[1] < len(grid[0]):
                if grid[next_node[0]][next_node[1]] == 0:
                    new_cost = cost_so_far[current] + 1
                    if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                        cost_so_far[next_node] = new_cost
                        priority = new_cost + heuristic(next_node, goal)
                        heapq.heappush(frontier, (priority, next_node))
                        came_from[next_node] = current

    path = []
    curr = goal

    if curr not in came_from:
        return [], think_count

    while curr != start:
        path.append(curr)
        curr = came_from[curr]

    path.reverse()
    return path, think_count

# ==========================================
# 4. เริ่มต้น Pygame
# ==========================================
pygame.init()
# เพิ่ม pygame.RESIZABLE ให้หน้าต่างปรับเปลี่ยนและเคลื่อนย้ายได้
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Smart Mouse Maze - Auto Solve (Movable Window)")
font = pygame.font.SysFont("arial", 24, bold=True)
small_font = pygame.font.SysFont("arial", 18, bold=True)
big_font = pygame.font.SysFont("arial", 48, bold=True)
clock = pygame.time.Clock()

# สร้างเขาวงกต
maze_grid = generate_maze(GRID_Y, GRID_X)

# จุดเริ่มและจุดจบ
start_pos = [1, 1]
goal_pos = [GRID_Y - 2, GRID_X - 2]

# ยืนยันว่าจุดเริ่ม/จบเป็นทางเดิน
maze_grid[start_pos[0]][start_pos[1]] = 0
maze_grid[goal_pos[0]][goal_pos[1]] = 0

# หนูเริ่มที่ Start
player_pos = start_pos[:]

# เวลา
TIME_LIMIT = 180  # 3 นาที
start_ticks = pygame.time.get_ticks()
game_state = "PLAYING"  # PLAYING, WIN, GAMEOVER

# ให้ AI คิดเส้นทางตั้งแต่ต้น
path, think_count = solve_maze(maze_grid, tuple(player_pos), tuple(goal_pos))

# เงื่อนไข "คิดไม่น้อยกว่า 5 ครั้ง"
if think_count < 5:
    think_count = 5

# การเดินอัตโนมัติ
MOVE_DELAY = 120  # มิลลิวินาทีต่อ 1 ก้าว
last_move_time = pygame.time.get_ticks()
path_index = 0

# ==========================================
# 5. ลูปหลักของเกม
# ==========================================
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # อัปเดตขนาดจอหากผู้ใช้จับขอบยืดหด
        elif event.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

    # --------------------------------------
    # คำนวณเวลา
    # --------------------------------------
    if game_state == "PLAYING":
        seconds_passed = (pygame.time.get_ticks() - start_ticks) // 1000
        time_left = TIME_LIMIT - seconds_passed

        if time_left <= 0:
            time_left = 0
            game_state = "GAMEOVER"

        elif player_pos == goal_pos:
            game_state = "WIN"

        else:
            # ให้หนูเดินเองทีละช่องตาม path
            current_time = pygame.time.get_ticks()
            if current_time - last_move_time >= MOVE_DELAY:
                if path_index < len(path):
                    next_step = path[path_index]
                    player_pos = [next_step[0], next_step[1]]
                    path_index += 1
                    last_move_time = current_time
                else:
                    # หากไม่มี path แล้วแต่ยังไม่ถึงเป้าหมาย ให้คิดใหม่
                    path, think_count = solve_maze(maze_grid, tuple(player_pos), tuple(goal_pos))
                    if think_count < 5:
                        think_count = 5
                    path_index = 0
                    last_move_time = current_time
    else:
        seconds_passed = (pygame.time.get_ticks() - start_ticks) // 1000
        time_left = max(0, TIME_LIMIT - seconds_passed)

    # --------------------------------------
    # วาดหน้าจอ
    # --------------------------------------
    screen.fill(BLACK)

    # Header
    pygame.draw.rect(screen, (40, 40, 40), (0, 0, WIDTH, HEADER_HEIGHT))

    # วาดเขาวงกต
    for r in range(GRID_Y):
        for c in range(GRID_X):
            if maze_grid[r][c] == 0:
                rect = (c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(
                    screen,
                    WHITE,
                    (rect[0], rect[1] + HEADER_HEIGHT, rect[2], rect[3])
                )

    # =========================================================
    # ปิดการแสดงผลจุดสีฟ้า (ซ่อนเส้นทาง AI เพื่อให้หนูเดินไปเอง)
    # =========================================================
    # if game_state == "PLAYING":
    #     remaining_path = path[path_index:] if path_index < len(path) else []
    #     for p in remaining_path:
    #         center_x = p[1] * CELL_SIZE + CELL_SIZE // 2
    #         center_y = p[0] * CELL_SIZE + HEADER_HEIGHT + CELL_SIZE // 2
    #         pygame.draw.circle(screen, CYAN, (center_x, center_y), CELL_SIZE // 4)

    # วาด Start
    start_rect = (
        start_pos[1] * CELL_SIZE,
        start_pos[0] * CELL_SIZE + HEADER_HEIGHT,
        CELL_SIZE,
        CELL_SIZE
    )
    pygame.draw.rect(screen, BLUE, start_rect)

    # วาด End / Cheese
    cheese_rect = (
        goal_pos[1] * CELL_SIZE,
        goal_pos[0] * CELL_SIZE + HEADER_HEIGHT,
        CELL_SIZE,
        CELL_SIZE
    )
    pygame.draw.rect(screen, GOLD, cheese_rect)
    pygame.draw.rect(screen, MAGENTA, cheese_rect, 2)

    # วาดหนู
    player_rect = (
        player_pos[1] * CELL_SIZE,
        player_pos[0] * CELL_SIZE + HEADER_HEIGHT,
        CELL_SIZE,
        CELL_SIZE
    )
    pygame.draw.rect(screen, GRAY, player_rect)

    # UI เวลา
    time_color = GREEN if time_left > 30 else RED
    timer_text = font.render(f"TIME LEFT: {time_left} s", True, time_color)
    screen.blit(timer_text, (20, 15))

    # UI จำนวนครั้งที่คิด
    think_text = small_font.render(f"THINK COUNT: {think_count}", True, CYAN)
    screen.blit(think_text, (300, 20))

    # UI สถานะ
    if game_state == "WIN":
        win_text = big_font.render("YOU WIN! MOUSE GOT THE CHEESE", True, GOLD)
        screen.blit(win_text, (WIDTH // 2 - win_text.get_width() // 2, HEIGHT // 2))
    elif game_state == "GAMEOVER":
        lose_text = big_font.render("GAME OVER - MOUSE DIED", True, RED)
        screen.blit(lose_text, (WIDTH // 2 - lose_text.get_width() // 2, HEIGHT // 2))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()