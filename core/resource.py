import random
import pygame
from core.utils import load_json

class ResourceManager:
    def __init__(self, json_path, tilemap):
        self.json_path = json_path
        self.resources_data = load_json(json_path)
        self.tilemap = tilemap
        self.spawn_resources()

    def reload(self):
        self.resources_data = load_json(self.json_path)

    def spawn_resources(self):
        for _ in range(120):
            x = random.randint(0, self.tilemap.width-1)
            y = random.randint(0, self.tilemap.height-1)
            t = random.choice(list(self.resources_data.keys()))
            tile = self.tilemap.get_tile(x, y)
            if tile and tile.resource is None:
                tile.resource = t

    def update(self):
        pass

    def has_nearby_resource(self, x, y):
        for dx in range(-4,5):
            for dy in range(-4,5):
                tx, ty = x+dx, y+dy
                tile = self.tilemap.get_tile(tx, ty)
                if tile and tile.resource:
                    return True
        return False

    def find_nearest_resource(self, x, y):
        min_dist = 99
        target = (None, None)
        for i in range(self.tilemap.width):
            for j in range(self.tilemap.height):
                tile = self.tilemap.get_tile(i,j)
                if tile and tile.resource:
                    dist = abs(x-i)+abs(y-j)
                    if dist < min_dist:
                        min_dist = dist
                        target = (i,j)
        return target

    def harvest(self, x, y):
        tile = self.tilemap.get_tile(x, y)
        if tile and tile.resource:
            tile.resource = None
            return True
        return False

    def render(self, screen, cam):
        pass