import pygame
import sys
import math
import neat
import time

#Display/Car/Background/drawing setup
pygame.init()
screen = pygame.display.set_mode((1400, 800))
pygame.display.set_caption("NEAT Car Driving")
background_image = pygame.image.load("Track1.png").convert()
background_image = pygame.transform.scale(background_image, (1400, 800))
CAR_IMAGE = pygame.image.load("car1.png")
CAR_IMAGE = pygame.transform.scale(CAR_IMAGE, (30, 52))
CAR_RED_IMAGE = CAR_IMAGE.copy()
CAR_RED_IMAGE.fill((255, 0, 0))
CAR_BLUE_IMAGE = CAR_IMAGE.copy()
CAR_BLUE_IMAGE.fill((0, 0, 255))
CAR_GREEN_IMAGE = CAR_IMAGE.copy()
CAR_GREEN_IMAGE.fill((0, 255, 0))
font = pygame.font.Font(None, 36)
brush_size = 5
draw_color = (0, 0, 0)
eraser_color = (255, 255, 255)
drawing = []
undo_stack = []
track_beaten = False
track_generation_beaten = None

class Car:
    #Car properties
    def __init__(self):
        self.original_image = CAR_IMAGE
        self.red_image = CAR_RED_IMAGE
        self.blue_image = CAR_BLUE_IMAGE
        self.green_image = CAR_GREEN_IMAGE
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(285, 210))
        self.position = pygame.math.Vector2(self.rect.center)
        self.velocity = pygame.math.Vector2(0, 0)
        self.angle = 90
        self.acceleration = 0.15
        self.friction = 0.05
        self.rotation_speed = 3.5
        self.max_speed = 9
        self.min_speed = 0.1
        self.off_track = False
        self.line_distances = {"Forward": 0, "45 Left": 0, "45 Right": 0, "90 Left": 0, "90 Right": 0}
        self.distance_covered = 0
        self.highest_fitness = False
        self.car_brake_deceleration = 0.05
        self.start_position = self.position.copy()

    def draw(self, screen):
        if self.image:
            rotated_image = pygame.transform.rotate(self.image, -self.angle)
            new_rect = rotated_image.get_rect(center=self.position)
            screen.blit(rotated_image, new_rect.topleft)

    def update(self, action):
        #update position based on inputs
        if action[0] > 0.5:  # forward
            direction = pygame.math.Vector2(math.sin(math.radians(self.angle)), -math.cos(math.radians(self.angle)))
            self.velocity += direction * self.acceleration
        if action[1] > 0.5:  # brake
            self.velocity *= (1 - self.car_brake_deceleration)

        if self.velocity.length() > self.min_speed:
            effective_rotation_speed = self.rotation_speed * (self.max_speed / (self.velocity.length() + 1))
            if action[2] > 0.5:  # left
                if self.velocity.dot(pygame.math.Vector2(math.sin(math.radians(self.angle)), -math.cos(math.radians(self.angle)))) > 0:
                    self.angle -= effective_rotation_speed * (self.velocity.length() / self.max_speed)
                else:
                    self.angle += effective_rotation_speed * (self.velocity.length() / self.max_speed)
            if action[3] > 0.5:  # right
                if self.velocity.dot(pygame.math.Vector2(math.sin(math.radians(self.angle)), -math.cos(math.radians(self.angle)))) > 0:
                    self.angle += effective_rotation_speed * (self.velocity.length() / self.max_speed)
                else:
                    self.angle -= effective_rotation_speed * (self.velocity.length() / self.max_speed)

        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)

        self.velocity *= (1 - self.friction)
        self.position += self.velocity
        self.rect.center = self.position
        self.off_track = self.detect_collision_with_white_spaces()
        self.distance_covered += self.velocity.length()

        #off track handling
        if self.off_track:
            self.image = None  
            self.velocity = pygame.math.Vector2(0, 0)
            self.clear_line_distances()
        elif self.highest_fitness:
            self.image = self.green_image
        else:
            self.image = self.original_image

    def detect_collision_with_white_spaces(self):
        corners = self.get_corners()
        for corner in corners:
            x, y = int(corner[0]), int(corner[1])
            
            if 0 <= x < TRACK_IMAGE.get_width() and 0 <= y < TRACK_IMAGE.get_height():
                if TRACK_IMAGE.get_at((x, y)) == (255, 255, 255):  
                    return True
        return False

    def get_corners(self):
        #calculate the corners of the car for collision detection
        cos_a = math.cos(math.radians(self.angle))
        sin_a = math.sin(math.radians(self.angle))

        half_width = self.rect.width / 2
        half_height = self.rect.height / 2

        top_left = self.position + pygame.math.Vector2(-half_width * cos_a + half_height * sin_a, -half_width * sin_a - half_height * cos_a)
        top_right = self.position + pygame.math.Vector2(half_width * cos_a + half_height * sin_a, half_width * sin_a - half_height * cos_a)
        bottom_left = self.position + pygame.math.Vector2(-half_width * cos_a - half_height * sin_a, -half_width * sin_a + half_height * cos_a)
        bottom_right = self.position + pygame.math.Vector2(half_width * cos_a - half_height * sin_a, half_width * sin_a + half_height * cos_a)

        return [top_left, top_right, bottom_left, bottom_right]

    def draw_lines(self, screen):
        #draw lines from the car to visualize what it sees
        if self.image:
            angles = [0, -45, 45, -90, 90]
            angle_names = ["Forward", "45 Left", "45 Right", "90 Left", "90 Right"]

            for i, angle in enumerate(angles):
                end_pos = self.position
                for j in range(1, max(screen.get_width(), screen.get_height())):
                    test_pos = self.position + pygame.math.Vector2(
                        math.sin(math.radians(self.angle + angle)),
                        -math.cos(math.radians(self.angle + angle))
                    ) * j
                    
                    if (0 <= test_pos.x < TRACK_IMAGE.get_width() and
                        0 <= test_pos.y < TRACK_IMAGE.get_height()):
                        if TRACK_IMAGE.get_at((int(test_pos.x), int(test_pos.y))) == (255, 255, 255):
                            pygame.draw.circle(screen, (200, 0, 200), (int(test_pos.x), int(test_pos.y)), 5)
                            break
                    end_pos = test_pos

                self.line_distances[angle_names[i]] = int((end_pos - self.position).length())
                pygame.draw.line(screen, (200, 0, 200), self.position, end_pos, 2)

    def clear_line_distances(self):
        for key in self.line_distances.keys():
            self.line_distances[key] = 0

    def draw_line_distances(self, screen):
        y_offset = 10
        for angle_name, distance in self.line_distances.items():
            distance_text = font.render(f"{angle_name}: {distance}", True, (0, 0, 0))
            screen.blit(distance_text, (screen.get_width() - 200, y_offset))
            y_offset += 30

def display_track_beaten_message():
    if track_beaten:
        message = font.render(f"Track beaten in generation {track_generation_beaten}!", True, (0, 0, 0))
        screen.blit(message, (600, 50))

def eval_genomes(genomes, config):
    global track_beaten,track_generation_beaten
    cars = []
    nets = []
    ge = []

    #Initialize neural network and create car instances
    for genome_id, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        cars.append(Car())
        genome.fitness = 0
        ge.append(genome)

    run = True
    clock = pygame.time.Clock()
    start_time = time.time()

    while run and any(not car.off_track for car in cars):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                sys.exit()

        #Display information
        screen.blit(TRACK_IMAGE, (0, 0))
        generation_text = font.render(f"Generation: {generation}", True, (0, 0, 0))
        screen.blit(generation_text, (50, 50))
        
        for i in range(len(cars)):
            if not cars[i].off_track:
                #Gather inputs for neural network
                inputs = [
                    cars[i].line_distances["Forward"],
                    cars[i].line_distances["45 Left"],
                    cars[i].line_distances["45 Right"],
                    cars[i].line_distances["90 Left"],
                    cars[i].line_distances["90 Right"]
                ]
                #Update cars action based on outputs of neural network
                outputs = nets[i].activate(inputs)
                cars[i].update(outputs)
                #Fitness rewards/penalties

                #Reward speed
                ge[i].fitness += 0.1 * (cars[i].distance_covered) / (time.time() - start_time)
                
                #Penalize immobility
                if cars[i].velocity.length() < 0.1:
                    cars[i].off_track = True
                    ge[i].fitness -= 1000
                
                #Penalize going off track/Reward staying on track
                if cars[i].off_track:
                    ge[i].fitness -= 1000
                else:
                    ge[i].fitness += 10
                
                #Draw cars and lines
                if cars[i].image:
                    cars[i].draw(screen)
                cars[i].draw_lines(screen)

            #Check for lap completion
            if time.time() - start_time > 5 and abs(cars[i].position.x - cars[i].start_position.x) < 10 and abs(cars[i].position.y - cars[i].start_position.y) < 100:
                if cars[i].distance_covered > 50:
                    run = False
                    if not track_beaten:
                        track_beaten = True
                        if track_generation_beaten == None :
                            track_generation_beaten = generation
                        ge[i].fitness += 1000  
                    cars[i].off_track = True
        if track_beaten:
            display_track_beaten_message()
        
        pygame.display.flip()
        clock.tick(30)


def main():
    global draw_color, brush_size, TRACK_IMAGE, drawing, undo_stack, track_beaten
    #Setting up menu screen 
    def draw_menu_screen():
        screen.blit(background_image, (0, 0))
        title_text = font.render("Welcome to this simulation game.", True, (0,0,0))
        subtitle_text = font.render("Draw a track and see how fast AI can drive through it!", True, (0,0,0))
        draw_button_text = font.render("Draw Custom Track", True, (0,0,0))

        title_rect = title_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2.5 + 5))
        subtitle_rect = subtitle_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2.5 + 25))
        draw_button_rect = draw_button_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 50))

        pygame.draw.rect(screen, (100, 100, 100), draw_button_rect.inflate(20, 10))
        screen.blit(title_text, title_rect.topleft)
        screen.blit(subtitle_text, subtitle_rect.topleft)
        screen.blit(draw_button_text, draw_button_rect.topleft)

        return draw_button_rect

    #Drawing functionality
    def draw_drawing_screen():
        screen.fill((255, 255, 255))
        drawing_area_rect = pygame.Rect(50, 50, 1300, 600)

        pygame.draw.rect(screen, (50,205,50), pygame.Rect(270, 165, 20, 100))
        #Buttons
        if drawing_mode == True: 
            brush_button_text = font.render("Brush", True, (0, 0, 0))
            eraser_button_text = font.render("Eraser", True, (0, 0, 0))
            clear_button_text = font.render("Clear", True, (0, 0, 0))
            undo_button_text = font.render("Undo", True, (0, 0, 0))
            done_button_text = font.render("Done", True, (0, 0, 0))

            brush_button_rect = brush_button_text.get_rect(topleft=(50, 700))
            eraser_button_rect = eraser_button_text.get_rect(topleft=(200, 700))
            clear_button_rect = clear_button_text.get_rect(topleft=(350, 700))
            undo_button_rect = undo_button_text.get_rect(topleft=(500, 700))
            done_button_rect = done_button_text.get_rect(topleft=(650, 700))

            button_rects = [brush_button_rect, eraser_button_rect, clear_button_rect, undo_button_rect, done_button_rect]
            for rect in button_rects:
                pygame.draw.rect(screen, (200, 200, 200), rect.inflate(20, 10))

            screen.blit(brush_button_text, brush_button_rect.topleft)
            screen.blit(eraser_button_text, eraser_button_rect.topleft)
            screen.blit(clear_button_text, clear_button_rect.topleft)
            screen.blit(undo_button_text, undo_button_rect.topleft)
            screen.blit(done_button_text, done_button_rect.topleft)

            return (drawing_area_rect, brush_button_rect, eraser_button_rect, clear_button_rect, undo_button_rect, done_button_rect)
    
    #Save the drawing as an image file
    def save_drawing():
        global TRACK_IMAGE
        global drawing_mode
        drawing_surf = pygame.Surface((1300, 600))
        drawing_surf.fill((255, 255, 255))
        for line in drawing:
            pygame.draw.rect(screen, (50,205,50), pygame.Rect(270, 165, 20, 100))
            if len(line) > 1:
                for point in line[1:]:
                    if isinstance(point, tuple) and len(point) == 2:
                        pygame.draw.circle(drawing_surf, line[0], point, brush_size)
            else:
                pygame.draw.circle(drawing_surf, line[0], line[1], brush_size)
        TRACK_IMAGE = drawing_surf
        pygame.image.save(drawing_surf, "custom_track.png")
    
    #Run NEAT simulation
    def run_simulation(config_file):
        #Run NEAT algorithm
        config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_file)

        p = neat.Population(config)
        global generation
        global track_beaten
        generation = 0

        #Main simulation loop
        while True:
            generation += 1
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            screen.blit(TRACK_IMAGE, (0, 0))
            p.run(eval_genomes, 1)    
            pygame.display.flip()

    #Initializing drawing variables
    draw_color = (0, 0, 0)  
    brush_size = 50
    eraser_color = (255, 255, 255)
    drawing = []
    undo_stack = []

    menu = True
    config_path = "config-feedforward.txt"
    drawing_mode = True

    #Menu screen loop
    while menu:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if draw_button_rect.collidepoint(event.pos):
                    menu = False

        draw_button_rect = draw_menu_screen()
        pygame.display.flip()

    #Drawing screen loop
    while drawing_mode == True:
        draw_data = draw_drawing_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            #Check for button interactions
            if event.type == pygame.MOUSEBUTTONDOWN:
                if draw_data[1].collidepoint(event.pos):  # Brush
                    draw_color = (0, 0, 0)
                if draw_data[2].collidepoint(event.pos):  # Eraser
                    draw_color = eraser_color
                if draw_data[3].collidepoint(event.pos):  # Clear
                    drawing.clear()
                    undo_stack.clear()
                if draw_data[4].collidepoint(event.pos):  # Undo
                    if drawing:
                        undo_stack.append(drawing.pop())
                if draw_data[5].collidepoint(event.pos):  # Done
                    drawing_mode = False
                    menu = False
                    save_drawing()

            #Drawing     
            if event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0]:
                    if draw_data[0].collidepoint(event.pos):
                        if not drawing or drawing[-1][0] != draw_color:
                            drawing.append([draw_color])
                        drawing[-1].append(event.pos)
        
        #Draw lines on the screen
        for line in drawing:
            color = line[0]
            for position in line[1:]:
                size = brush_size  
                pygame.draw.circle(screen, color, position, size)
        
        pygame.display.flip()
    pygame.draw.rect(screen,(255,255,255), pygame.Rect(0,300,800,800))

    run_simulation(config_path)

main()
