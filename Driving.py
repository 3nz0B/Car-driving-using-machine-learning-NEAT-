import pygame
import sys
import math
import neat
import os
import time

#Display/Car/Background setup
pygame.init()
screen = pygame.display.set_mode((1400, 800))
pygame.display.set_caption("NEAT Car Driving")
TRACK_IMAGE = pygame.image.load("Track1.png")
TRACK_IMAGE = pygame.transform.scale(TRACK_IMAGE, (1400, 800))
CAR_IMAGE = pygame.image.load("car1.png")
CAR_IMAGE = pygame.transform.scale(CAR_IMAGE,(30,52))
CAR_RED_IMAGE = CAR_IMAGE.copy()
CAR_RED_IMAGE.fill((255, 0, 0))
CAR_BLUE_IMAGE = CAR_IMAGE.copy()
CAR_BLUE_IMAGE.fill((0, 0, 255))
CAR_GREEN_IMAGE = CAR_IMAGE.copy()
CAR_GREEN_IMAGE.fill((0, 255, 0))

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
        if self.off_track == True :
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
            if TRACK_IMAGE.get_at((int(corner[0]), int(corner[1]))) == (255, 255, 255):
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
                    test_pos = self.position + pygame.math.Vector2(math.sin(math.radians(self.angle + angle)), -math.cos(math.radians(self.angle + angle))) * j
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

font = pygame.font.Font(None, 36)
config_path = "config-feedforward"

def eval_genomes(genomes, config):
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

    highest_fitness = 0
    highest_fitness_car_index = -1

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
        highest_fitness_text = font.render(f"Highest Fitness: {highest_fitness:.2f}", True, (0, 0, 0))
        screen.blit(highest_fitness_text, (50, 100))

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
                outputs = nets[i].activate(inputs)
                
                #Update cars action based on outputs of neural network
                cars[i].update(outputs)

                #Fitness rewards/penalties

                #Reward speed
                ge[i].fitness += 0.1 * (cars[i].distance_covered) / (time.time() - start_time)
                
                #Penalize immobility
                if cars[i].velocity.length() < 0.1:
                    cars[i].off_track = True
                    ge[i].fitness -= 1000
                
                #Penalize going off track/Reward staying on track
                if cars[i].off_track == True : 
                    ge[i].fitness -= 1000
                else :
                    ge[i].fitness += 10

                if ge[i].fitness > highest_fitness:
                    highest_fitness = ge[i].fitness
                    highest_fitness_car_index = i

            #Draw cars and lines
            if cars[i].image:
                cars[i].draw(screen)
            cars[i].draw_lines(screen)

            if cars[i].off_track:
                pygame.draw.circle(screen, (255, 0, 0), cars[i].rect.center, 5)

        #Car color based on fitness
        for j in range(len(cars)):
            if j == highest_fitness_car_index:
                cars[j].highest_fitness = True
                cars[j].image = cars[j].green_image
            else:
                cars[j].highest_fitness = False
                cars[j].image = cars[j].blue_image if not cars[j].off_track else None

        #Check for lap completion
        for car in cars:
            if time.time() - start_time > 30:
                if abs(car.position.x - car.start_position.x) < 10 and abs(car.position.y - car.start_position.y) < 100:
                    if car.distance_covered > 100:
                        run = False
                        break
        
        #End simulation after 2 minutes
        if time.time() - start_time > 120:
            run = False
        
        pygame.display.flip()
        clock.tick(30)

def run(config_file):
    #Run NEAT algorithm
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_file)
    p = neat.Population(config)
    global generation
    generation = 0
    while True:
        generation += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        screen.blit(TRACK_IMAGE, (0, 0))
        p.run(eval_genomes, 1)
        generation_text = font.render("Generation: " + str(generation), True, (0, 0, 0))
        screen.blit(generation_text, (50, 50))
        pygame.display.flip()

#Start NEAT program
local_dir = os.path.dirname(__file__)
config_path = os.path.join(local_dir, 'config-feedforward.txt')
run(config_path)

