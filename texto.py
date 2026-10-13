import math
import random
import sys
import threading
import time
from pathlib import Path
import pygame

WIDTH, HEIGHT = 2000, 1200
BACKGROUND_COLOR = (0, 0, 0)
FPS = 30
CIRCLE_RADIUS = 250

CENTER_TEXT = "DAIA"
COLORS = [
    (70, 130, 180),
    (30, 144, 255),  
    (0, 191, 255),  
    (100, 149, 237), 
    (65, 105, 225)
]

class Particle:
    __slots__= ('x', 'y', 'order', 'kind', 'color', 'alpha', 'flicker', 'delay', 'radius', 'surf_glow_big', 'surf_glow_small', 'rect_glow_big', 'rect_glow_small')

    def __init__(self, x, y, order, kind):
        self.x = x
        self.y = y
        self.order = order
        self.kind = kind
        self.color = random.choice(COLORS)
        self.alpha = 0
        self.flicker = random.uniform(0, math.pi * 2)
        self.delay = 0
        self.radius = random.uniform(3, 6) if kind == "outline" else random.uniform(2, 4)
        
        self.surf_glow_big = None
        self.surf_glow_small = None
        self.rect_glow_big = None
        self.rect_glow_small = None

    def pre_render(self):
        size_big = int(self.radius * 6)
        size_small = int(self.radius * 3)
        
        if size_big > 0:
            self.surf_glow_big = pygame.Surface((size_big * 2, size_big * 2), pygame.SRCALPHA)
            pygame.draw.circle(self.surf_glow_big, self.color, (size_big, size_big), size_big)
            self.rect_glow_big = self.surf_glow_big.get_rect(center=(self.x, self.y))
            
        if size_small > 0:
            self.surf_glow_small = pygame.Surface((size_small * 2, size_small * 2), pygame.SRCALPHA)
            pygame.draw.circle(self.surf_glow_small, self.color, (size_small, size_small), size_small)
            self.rect_glow_small = self.surf_glow_small.get_rect(center=(self.x, self.y))

def circle_xy(t):
    x = math.cos(t) * CIRCLE_RADIUS
    y = math.sin(t) * CIRCLE_RADIUS
    return x, y

def to_screen(x, y):
    return x + WIDTH / 2, y + HEIGHT / 2

def build_outline_particles(n_outline, min_gap=15):
    particles = []
    placed = []
    for i in range(n_outline):
        t = (i / n_outline) * 2 * math.pi
        bx, by = circle_xy(t)
        sx, sy = to_screen(bx, by)
        if any(math.hypot(sx - px, sy - py) < min_gap for (px, py) in placed):
            continue
        placed.append((sx, sy))
        particles.append(Particle(sx, sy, i, "outline"))
    return particles

def build_fill_particles(n_fill, min_gap=20):
    particles = []
    placed = []
    attempts = 0
    max_attempts = n_fill * 120

    while len(particles) < n_fill and attempts < max_attempts:
        attempts += 1
        t = random.uniform(0, 2 * math.pi)
        r = math.sqrt(random.uniform(0.0, 0.9)) 
        bx, by = circle_xy(t)
        px, py = bx * r, by * r
        sx, sy = to_screen(px, py)
        
        if any(math.hypot(sx - qx, sy - qy) < min_gap for (qx, qy) in placed):
            continue

        placed.append((sx, sy))
        particles.append(Particle(sx, sy, random.randint(0, 150), "fill"))  # Rango de orden reducido para el relleno

    return particles

def printlyrics():
    print()
    print()

def lyrics_worker():
    lines = [
        ("Bienvenidos a las carreras CDIA y EGAD"),
        ("mi nombre es un asistente virtual y estoy aqui para guiarlos en este espacio"),
        ("el cual ha sido diseñado con el firme proposito de brindarles informacion sobre las carreras"),
        ("integrando el analisis productivo y el pensamiento inteligente de datos"),
        ("para que puedan tomar decisiones acertadas en su futuro profesional"),
        ("en este espacio podran encontrar informacion sobre las carreras, sus planes de estudio, materias, docentes y mucho mas"),
        ("ademas de poder conocer a los estudiantes que forman parte de la comunidad de CDIA"),
        ("y poder conocer sus experiencias y opiniones sobre la carrera"),
        ("para que puedan tomar decisiones acertadas en su futuro profesional"),
        ("gracias por su atencion y esperamos que disfruten de este espacio")
    ]

    time.sleep(30)  # Se redujo el tiempo de espera inicial en consola para acoplarse al ritmo rápido gráfico
    
    for line in lines:
        for char in line:
            print(char, end='')
            sys.stdout.flush()
            time.sleep(0.095)
        print()
        time.sleep(0.05) 
    printlyrics()

def main():
    pygame.init()
   
    
    pygame.mixer.init()
    audio_path = Path(__file__).resolve().parent / "voz.WAV"
    if audio_path.exists():
        pygame.mixer.music.load(str(audio_path))
        pygame.mixer.music.play()
        
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF)
    pygame.display.set_caption("DAIA")
    clock = pygame.time.Clock()
    
    font_center = pygame.font.SysFont("georgia", 54, bold=True)
    
    background = pygame.Surface((WIDTH, HEIGHT))
    background.fill(BACKGROUND_COLOR)
    
    outline = build_outline_particles(n_outline=200)
    fill = build_fill_particles(n_fill=150)
    
    outline_span = max(p.order for p in outline) if outline else 0
    frames_per_step = 0.4  # CAMBIO: Antes 1.0. El contorno se traza mucho más rápido.
    fill_start_frame = int(outline_span * frames_per_step) + 10  # CAMBIO: El relleno empieza antes.
    
    for p in fill:
        p.delay = fill_start_frame + p.order
    for p in outline:
        p.delay = int(p.order * frames_per_step)
    
    particles = outline + fill
    
    for p in particles:
        p.pre_render()
    
    center_surf_base = font_center.render(CENTER_TEXT, True, (255, 250, 245)).convert_alpha()
    
    lyrics_thread = threading.Thread(target=lyrics_worker, daemon=True)
    lyrics_thread.start()
    
    running = True
    frame = 0
    glow_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    text_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
        
        screen.blit(background, (0, 0))
        glow_layer.fill((0, 0, 0, 0))
        text_layer.fill((0, 0, 0, 0))
        frame += 1
        
        for p in particles:
            if frame > p.delay and p.alpha < 255:
                p.alpha = min(255, p.alpha + 25 + random.randint(0, 5))  # CAMBIO: Antes +10. Ahora se desvanece de forma rápida y agresiva.
            
            if p.alpha >= 255:
                flick = 0.70 + 0.30 * math.sin(frame * 0.06 + p.flicker)
            else:
                flick = 1.0
            
            alpha = int(p.alpha * flick)
            if alpha <= 0:
                continue
            
            if alpha > 10:
                if p.surf_glow_big:
                    p.surf_glow_big.set_alpha(max(0, alpha // 10))
                    glow_layer.blit(p.surf_glow_big, p.rect_glow_big)
                if p.surf_glow_small:
                    p.surf_glow_small.set_alpha(max(0, alpha // 5))
                    glow_layer.blit(p.surf_glow_small, p.rect_glow_small)
            
            pygame.draw.circle(text_layer, (*p.color, alpha), (int(p.x), int(p.y)), int(p.radius))
        
        screen.blit(glow_layer, (0, 0))
        screen.blit(text_layer, (0, 0))
        
        center_start = fill_start_frame + 10  # CAMBIO: La palabra "Daia" aparece antes debido a la velocidad global.
        if frame > center_start:
            progress = min(1.0, (frame - center_start) / 45)  # CAMBIO: Animación de entrada de texto acelerada de 60 a 45 frames.
            center_alpha = int(255 * (1 - math.exp(-progress * 8)))
            
            pulse = 1.0 + 0.025 * math.sin(frame * 0.05)
            
            new_width = int(center_surf_base.get_width() * pulse)
            new_height = int(center_surf_base.get_height() * pulse)
            
            if new_width > 0 and new_height > 0:
                center_surf = pygame.transform.smoothscale(center_surf_base, (new_width, new_height))
                center_surf.set_alpha(center_alpha)
                
                if center_alpha > 10:
                    glow_center = pygame.transform.smoothscale(
                        center_surf, (int(center_surf.get_width() * 1.4), int(center_surf.get_height() * 1.4))
                    )
                    glow_center.set_alpha(center_alpha // 5)
                    glow_rect = glow_center.get_rect(center=(WIDTH/2, HEIGHT/2))
                    screen.blit(glow_center, glow_rect)
                
                text_rect = center_surf.get_rect(center=(WIDTH/2, HEIGHT/2))
                screen.blit(center_surf, text_rect)

        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("OCURRIO UN ERROR:", e)
        import traceback
        traceback.print_exc()
