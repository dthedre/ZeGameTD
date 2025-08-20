import pygame, sys
from pytmx.util_pygame import load_pygame


class Tile(pygame.sprite.Sprite):
    def __init__(self,pos,surf,groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)


pygame.init()
screen = pygame.display.set_mode((480,320))
tmx_data = load_pygame(r"C:\Users\FluffyOwl\Desktop\Stuff for games\1 Tiled\Cute_Maps\export\map_test.tmx")
sprite_group = pygame.sprite.Group()


# cycle through all layers
for layer in tmx_data.visible_layers:
    if hasattr(layer,"data"): # find all my tiled layers 
        for x,y,surf in layer.tiles(): # need to be miltiplied by the tiles size ? Me thinks 
            pos = (x * 16, y * 16)
            Tile(pos = pos, surf = surf, groups = sprite_group)


# objects 
for obj in tmx_data.objects:
    pos = obj.x,obj.y
    if obj.type in ("Tree", "chest"): # use clear names for the objects 
        Tile(pos = pos, surf = obj.image, groups = sprite_group)


# polyline 
object_layer = tmx_data.get_layer_by_name("Object Layer 1")
for obj in object_layer:
    if obj.name == "enemy_path":
        print(obj.points)


# shapes enemy_path (Polyline)
for obj in tmx_data.objects:
    if obj.name == "enemy_path" and hasattr(obj, "points"):
        enemy_path_points = [pygame.math.Vector2((obj.x / 72) + p[0], (obj.y / 72) + p[1]) for p in obj.points] # so / by 72 works for now but needs to be fixed ^^ (the path seems to be the correct place without the miltiplier, I Have no clue why it doesn't draw it corretly then)
# when I draw a cicle on the x,y position of the obj.points everything seems correct hmmm


while True: 
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()



    screen.fill("black")
    sprite_group.draw(screen)



    for obj in tmx_data.objects:
        pos = obj.x,obj,y
        if obj.type == "area":
            if obj.name == "Spawn_enemy":
                pygame.draw.circle(screen,"blue",(obj.x,obj.y),5)
            if obj.name == "End_enemy":
                pygame.draw.circle(screen,"red",(obj.x,obj.y),5)


            if enemy_path_points:
                pygame.draw.lines(screen, "#0c36038b", False, enemy_path_points, 10)

            pygame.draw.circle(screen, "#e209c9", (350.62467000000004, 284.41667),10)

    pygame.display.update()