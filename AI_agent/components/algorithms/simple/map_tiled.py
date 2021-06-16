import os
from random import randint

import pygame
from pygame.locals import *
import numpy as np

TILE_W, TILE_H = 32, 32
named_tile = {"grass":0,
			  "river":1,
			  "ocean":2,
			  "wall":3,
			  "flag_team_1":4,
			  "flag_team_2":5,
			  "player_team_1":6,
			  "player_team_2":7,
			  "bonus":8,
			  "barrier":9,
			  "trap":10}

debug = True

class MapPrinter():

	def __init__(self):
		self.screen_count = 0
		self.screen = pygame.display.get_surface()
		self.scrolling = False
		self.load_tileset( os.path.join("components","algorithms","simple","art","tileset.bmp"))


	def set(self, map):

		self.tiles_x = 32
		self.tiles_y = 32

		# create empty array , filled with zero
		self.tiles = np.zeros((self.tiles_x, self.tiles_y), dtype=int)

		map = np.rot90(map)
		for x in range(self.tiles_x):
			for y in range(self.tiles_y):
				if map[x][y] == '.':
					self.tiles[x][y] = named_tile['grass']
				elif map[x][y] == '~':
					self.tiles[x][y] = named_tile['river']
				elif map[x][y] == '#':
					self.tiles[x][y] = named_tile['wall']
				elif map[x][y] == '@':
					self.tiles[x][y] = named_tile['ocean']
				elif map[x][y] == 'x':
					self.tiles[x][y] = named_tile['flag_team_1']
				elif map[x][y] == 'X':
					self.tiles[x][y] = named_tile['flag_team_2']
				elif map[x][y] == '$':
					self.tiles[x][y] = named_tile['bonus']
				elif map[x][y] == '&':
					self.tiles[x][y] = named_tile['barrier']
				elif map[x][y] == '!':
					self.tiles[x][y] = named_tile['trap']
				elif map[x][y].isalpha():
					if map[x][y].islower():
						self.tiles[x][y] = named_tile['player_team_1']
					elif map[x][y].isupper():
						self.tiles[x][y] = named_tile['player_team_2']


	def load_tileset(self, image="tileset.bmp"):
		# load image
		self.tileset = pygame.image.load(image)
		self.rect = self.tileset.get_rect()

	def draw(self, map):
		self.set(map)
		# no optimization, just iterate to render tiles
		# You could start iterating at actual tiles on screen, instead.
		for y in range(self.tiles_x):
			for x in range(self.tiles_y):
				cur = self.tiles[x][y]
				cur_y = 0
				if cur > 7:
					cur = cur - 8
					cur_y = 32
				dest = Rect(x * TILE_W, y * TILE_H, TILE_W, TILE_H)
				src = Rect(cur * TILE_W, cur_y, TILE_W, TILE_H)

				self.screen.blit(self.tileset, dest, src)

		pygame.image.save(self.screen, os.path.join('snapshots', f"{self.screen_count}.jpg" ))
		self.screen_count += 1


