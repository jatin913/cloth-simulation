import pygame
import math
import sys

pygame.init()
screen_width, screen_height = 1000, 800 
main_window = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Fabric Physics Playground")

WHITE_COLOR = (255, 255, 255)
BLACK_COLOR = (0, 0, 0)
RED_COLOR = (255, 0, 0)
BLUE_COLOR = (0, 0, 255)
BRASS_COLOR = (255, 215, 0)
GREEN_COLOR = (0, 255, 0)
DARK_GREEN_COLOR = (0, 200, 0)


gravity_strength = 0.5
movement_damping = 0.99
node_size = 5
nail_size = 8


grid_columns_rows = 30
distance_between_nodes = 20


obstacle_width = 300
obstacle_height = 150
obstacle_x = (screen_width - obstacle_width) // 2
obstacle_y = screen_height - 200


left_anchor_x, left_anchor_y = screen_width // 3, 50
right_anchor_x, right_anchor_y = 2 * screen_width // 3, 50


cut_fabric_button = pygame.Rect(10, 10, 120, 30)
reset_fabric_button = pygame.Rect(10, 50, 120, 30)


class FabricNode:
    def __init__(self, pos_x, pos_y):
        self.current_x = pos_x
        self.current_y = pos_y
        self.previous_x = pos_x
        self.previous_y = pos_y
        self.being_dragged = False
        self.is_anchored = False
        self.is_active = True

    def move(self):
        if not self.being_dragged and not self.is_anchored:

            velocity_x = (self.current_x - self.previous_x) * movement_damping
            velocity_y = (self.current_y - self.previous_y) * movement_damping
            
            self.previous_x = self.current_x
            self.previous_y = self.current_y
            
            self.current_x += velocity_x
            self.current_y += velocity_y + gravity_strength

    def keep_in_bounds(self):
        if self.is_anchored:
            return
            
        self.current_x = max(0, min(screen_width, self.current_x))
        self.current_y = max(0, min(screen_height, self.current_y))

        if (obstacle_x < self.current_x < obstacle_x + obstacle_width and 
            obstacle_y < self.current_y < obstacle_y + obstacle_height):
            
            distances = [
                self.current_x - obstacle_x,  
                (obstacle_x + obstacle_width) - self.current_x,  
                self.current_y - obstacle_y,  
                (obstacle_y + obstacle_height) - self.current_y  
            ]
            
            min_distance = min(distances)
            
            if distances.index(min_distance) == 0: 
                self.current_x = obstacle_x
            elif distances.index(min_distance) == 1:  
                self.current_x = obstacle_x + obstacle_width
            elif distances.index(min_distance) == 2:  
                self.current_y = obstacle_y
            else:  
                self.current_y = obstacle_y + obstacle_height


class FabricConnection:
    def __init__(self, node1, node2):
        self.first_node = node1
        self.second_node = node2
        self.original_length = math.dist(
            (node1.current_x, node1.current_y), 
            (node2.current_x, node2.current_y))
        self.is_connected = True

    def maintain_distance(self):
        if not self.is_connected:
            return
            
        diff_x = self.second_node.current_x - self.first_node.current_x
        diff_y = self.second_node.current_y - self.first_node.current_y
        actual_distance = math.sqrt(diff_x**2 + diff_y**2)
        
        if actual_distance == 0:
            return

        adjustment = (actual_distance - self.original_length) / actual_distance
        move_x = diff_x * adjustment * 0.5
        move_y = diff_y * adjustment * 0.5

        if not self.first_node.being_dragged and not self.first_node.is_anchored:
            self.first_node.current_x += move_x
            self.first_node.current_y += move_y
            

        if not self.second_node.being_dragged and not self.second_node.is_anchored:
            self.second_node.current_x -= move_x
            self.second_node.current_y -= move_y


all_nodes = []
all_connections = []

def setup_fabric():
    global all_nodes, all_connections
    all_nodes = []
    all_connections = []
    

    for row in range(grid_columns_rows):
        for col in range(grid_columns_rows):
            node_x = col * distance_between_nodes + (screen_width - grid_columns_rows*distance_between_nodes)//2
            node_y = row * distance_between_nodes + 50
            all_nodes.append(FabricNode(node_x, node_y))


    for row in range(grid_columns_rows):
        for col in range(grid_columns_rows):
            current_index = row * grid_columns_rows + col
            if col < grid_columns_rows - 1:  
                all_connections.append(FabricConnection(all_nodes[current_index], all_nodes[current_index + 1]))
            if row < grid_columns_rows - 1: 
                all_connections.append(FabricConnection(all_nodes[current_index], all_nodes[current_index + grid_columns_rows]))

setup_fabric()


selected_node = None
cutting_mode = False
ui_font = pygame.font.SysFont('Arial', 16)

def attach_to_anchor(node, anchor_x, anchor_y):
    node.current_x = anchor_x
    node.current_y = anchor_y
    node.previous_x = anchor_x
    node.previous_y = anchor_y
    node.is_anchored = True

def find_closest_node(click_x, click_y):
    for node in all_nodes:
        if math.dist((node.current_x, node.current_y), (click_x, click_y)) < node_size:
            return node
    return None

def find_nearby_connection(click_x, click_y, max_distance=15):
    for connection in all_connections:
        if not connection.is_connected:
            continue
            
        x1, y1 = connection.first_node.current_x, connection.first_node.current_y
        x2, y2 = connection.second_node.current_x, connection.second_node.current_y
        
        line_length = math.dist((x1, y1), (x2, y2))
        if line_length == 0:
            continue
            
        t = ((click_x - x1) * (x2 - x1) + (click_y - y1) * (y2 - y1)) / (line_length ** 2)
        t = max(0, min(1, t))
        closest_x = x1 + t * (x2 - x1)
        closest_y = y1 + t * (y2 - y1)
        
        if math.dist((click_x, click_y), (closest_x, closest_y)) < max_distance:
            return connection
    return None

def draw_ui_button(button_rect, base_color, highlight_color, label, text_color=WHITE_COLOR):
    mouse_pos = pygame.mouse.get_pos()
    is_hovered = button_rect.collidepoint(mouse_pos)
    
    pygame.draw.rect(main_window, highlight_color if is_hovered else base_color, button_rect)
    pygame.draw.rect(main_window, BLACK_COLOR, button_rect, 2)
    
    label_surface = ui_font.render(label, True, text_color)
    label_rect = label_surface.get_rect(center=button_rect.center)
    main_window.blit(label_surface, label_rect)
    
    return is_hovered

simulation_running = True
frame_timer = pygame.time.Clock()

while simulation_running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            simulation_running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos_x, mouse_pos_y = pygame.mouse.get_pos()
            
            if event.button == 1:  

                if cut_fabric_button.collidepoint(mouse_pos_x, mouse_pos_y):
                    cutting_mode = not cutting_mode
                elif reset_fabric_button.collidepoint(mouse_pos_x, mouse_pos_y):
                    setup_fabric()
                    cutting_mode = False
                elif cutting_mode:  
                    connection = find_nearby_connection(mouse_pos_x, mouse_pos_y)
                    if connection:
                        connection.is_connected = False
                else:  
                    node = find_closest_node(mouse_pos_x, mouse_pos_y)
                    if node:
                        selected_node = node
                        selected_node.being_dragged = True
                        
            elif event.button == 3: 
                node = find_closest_node(mouse_pos_x, mouse_pos_y)
                if node:
                    if math.dist((mouse_pos_x, mouse_pos_y), (left_anchor_x, left_anchor_y)) < nail_size:
                        attach_to_anchor(node, left_anchor_x, left_anchor_y)
                    elif math.dist((mouse_pos_x, mouse_pos_y), (right_anchor_x, right_anchor_y)) < nail_size:
                        attach_to_anchor(node, right_anchor_x, right_anchor_y)
                        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and selected_node:
              
                selected_node.previous_x = selected_node.current_x - (pygame.mouse.get_pos()[0] - selected_node.current_x)
                selected_node.previous_y = selected_node.current_y - (pygame.mouse.get_pos()[1] - selected_node.current_y)
                selected_node.being_dragged = False
                selected_node = None
                
        elif event.type == pygame.MOUSEMOTION:
            if selected_node:
                mouse_pos_x, mouse_pos_y = pygame.mouse.get_pos()
                selected_node.current_x = mouse_pos_x
                selected_node.current_y = mouse_pos_y

    for node in all_nodes:
        node.move()

    for _ in range(3):  
        for connection in all_connections:
            connection.maintain_distance()

    for node in all_nodes:
        node.keep_in_bounds()

    main_window.fill(BLACK_COLOR)
    
    pygame.draw.rect(main_window, BLUE_COLOR, (obstacle_x, obstacle_y, obstacle_width, obstacle_height))
    
    pygame.draw.circle(main_window, BRASS_COLOR, (left_anchor_x, left_anchor_y), nail_size)
    pygame.draw.circle(main_window, BRASS_COLOR, (right_anchor_x, right_anchor_y), nail_size)
    
  
    for connection in all_connections:
        if connection.is_connected:
            pygame.draw.line(
                main_window, WHITE_COLOR, 
                (connection.first_node.current_x, connection.first_node.current_y), 
                (connection.second_node.current_x, connection.second_node.current_y), 
                1)
    
    for node in all_nodes:
        if node.is_anchored:
            node_color = BRASS_COLOR
        elif node.being_dragged:
            node_color = RED_COLOR
        else:
            node_color = WHITE_COLOR
        pygame.draw.circle(main_window, node_color, (int(node.current_x), int(node.current_y)), node_size)
    

    cut_button_state = draw_ui_button(
        cut_fabric_button, 
        GREEN_COLOR if cutting_mode else DARK_GREEN_COLOR,
        GREEN_COLOR if cutting_mode else (0, 150, 0),
        "Cut Fabric")
    
    reset_button_state = draw_ui_button(
        reset_fabric_button, 
        RED_COLOR, 
        (200, 0, 0),
        "Reset Fabric")
    
    pygame.display.flip()
    frame_timer.tick(60)

pygame.quit()
sys.exit()