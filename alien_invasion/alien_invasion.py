import sys
from time import sleep

import pygame

from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from ship import Ship
from bullet import Bullet
from aliens import Alien
from button import Button

class AlienInvasion:
	"""Overall class to manage game assets and behavior"""

	def __init__(self):
		"""Init the game, and create game resources"""
		pygame.init()
		self.settings = Settings()

		self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
		self.settings.screen_width = self.screen.get_rect().width
		self.settings.screen_height = self.screen.get_rect().height
		pygame.display.set_caption("Alien Invasion")

		#Create an isntance to store game stats and create scoreboard
		self.stats = GameStats(self)
		self.sb = Scoreboard(self)

		self.ship=Ship(self)
		self.bullets = pygame.sprite.Group()
		self.aliens = pygame.sprite.Group()

		self._create_fleet()

		#Make the Play button
		self.play_button = Button(self, "Play")

	def run_game(self):
		"""Start the main loop for the game"""
		while True:
			self._check_events()

			if self.stats.game_active:
				self.ship.update()
				self._update_bullets()
				self._update_aliens()

			self._update_screen()

	def _check_events(self):
		"""Respond to key press and mouse events"""
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				sys.exit()
			
			elif event.type == pygame.KEYDOWN:
				self._check_keydown_events(event)
				
			elif event.type == pygame.KEYUP:
				self._check_keyup_events(event)
			elif event.type == pygame.MOUSEBUTTONDOWN:
				mouse_pos = pygame.mouse.get_pos()
				self._check_play_button(mouse_pos)

	def _check_play_button(self, mouse_pos):
		"""Start new game when player clicks play"""
		button_clicked = self.play_button.rect.collidepoint(mouse_pos)
		if button_clicked and not self.stats.game_active:
			#Reset the game settings
			self.settings.initialize_dynamic_settings()

			#Reset game stats
			self.stats.reset_stats() 
			self.stats.game_active = True
			self.sb.prep_score()
			self.sb.prep_level()
			self.sb.prep_ships()

			#Get rid of any bullets and aliens
			self.aliens.empty()
			self.bullets.empty()

			#Create new fleet and center ship
			self._create_fleet()
			self.ship.center_ship()
			pygame.mouse.set_visible(False)

				

	def _check_keydown_events(self, event):
		"""Respond to key presses"""
		if event.key == pygame.K_RIGHT:
			self.ship.moving_right = True
		elif event.key == pygame.K_LEFT:
			self.ship.moving_left = True
		elif event.key == pygame.K_q:
			sys.exit()
		elif event.key == pygame.K_SPACE:
			self._fire_bullet()
				
	def _check_keyup_events(self, event):
		"""Respond to key releases"""
		if event.key == pygame.K_RIGHT:
			self.ship.moving_right = False
		elif event.key == pygame.K_LEFT:
			self.ship.moving_left = False

	def _fire_bullet(self):
		"""Create new bullet and add to bullets group"""
		if len(self.bullets) < self.settings.bullets_allowed:
			new_bullet = Bullet(self)
			self.bullets.add(new_bullet)

	def _update_bullets(self):
		"""Update bullet position and remove old bullets"""
		self.bullets.update()

		#Get rid of old bullets
		for bullet in self.bullets.copy():
			if bullet.rect.bottom <= 0:
				self.bullets.remove(bullet)
		#print(len(self.bullets))

		self._check_bullet_alien_collision()


	def _check_bullet_alien_collision(self):
		#Check for any bullets that have hit aliens
		#If so, get rid of bullet and alien
		collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)

		if collisions:
			for aliens in collisions.values():
				self.stats.score += self.settings.alien_points * len(aliens)
			self.sb.prep_score()
			self.sb.check_high_score()

		if not self.aliens:
			#Destroy existing bullets and create new fleet
			self.bullets.empty()
			self._create_fleet()
			self.settings.increase_speed()

			#Increase level
			self.stats.level += 1
			self.sb.prep_level()

	def _update_aliens(self):
		"""Check if fleet is on edge, Update the pos of all aliens"""
		self._check_fleet_edges()
		self.aliens.update()

		#Check for alien-ship collision
		if pygame.sprite.spritecollideany(self.ship, self.aliens):
			self._ship_hit()

		#Look for aliens reaching the bottom
		self._check_aliens_bottom()

	def _check_aliens_bottom(self):
		"""Check if any aliens reach the bottom"""
		screen_rect = self.screen.get_rect()
		for alien in self.aliens.sprites():
			if alien.rect.bottom >= screen_rect.bottom:
				#Treat same as ship hit
				self._ship_hit()
				break

	def _create_fleet(self):
		"""Create a whole fleet of aliens"""
		#Make alien and find number of aliens in a row
		#Spacing between each alien is equal to one alien width
		alien = Alien(self)
		alien_width, alien_height = alien.rect.size
		available_space_x = self.settings.screen_width - (2 * alien_width)
		number_aliens_x = available_space_x // (2 * alien_width)

		#Determine the number of rows of aliens that fit
		ship_height = self.ship.rect.height
		available_space_y = (self.settings.screen_height - (3 * alien_height) - ship_height)
		number_rows = available_space_y // (2 * alien_height)

		#Create the fill fleet of aliens
		for row_number in range(number_rows):
			for alien_number in range(number_aliens_x):
				self._create_alien(alien_number, row_number)


	def _create_alien(self, alien_number, row_number):
		#Create alien and place in row
		alien = Alien(self)
		alien_width, alien_height = alien.rect.size
		alien.x = alien_width + 2 * alien_width * alien_number
		alien.rect.x = alien.x
		alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
		self.aliens.add(alien)

	def _check_fleet_edges(self):
		"""Respond appropriately if aliens reach edge"""
		for alien in self.aliens.sprites():
			if alien.check_edges():
				self._change_fleet_direction()
				break

	def _change_fleet_direction(self):
		"""Drop entire fleet down, move other direction"""
		for alien in self.aliens.sprites():
			alien.rect.y += self.settings.fleet_drop_speed
		self.settings.fleet_direction *= -1

	def _ship_hit(self):
		"""Respond to the ship being hit by alien"""

		if self.stats.ships_left > 0:
			#Decrement ships_left and update display
			self.stats.ships_left -= 1
			self.sb.prep_ships()

			#Get rid of all remaining aliens and bullets
			self.aliens.empty()
			self.bullets.empty()

			#Create a new fleet and center the ship
			self._create_fleet()
			self.ship.center_ship()

			#Pause.
			sleep(.5)
		else:
			self.stats.game_active = False
			pygame.mouse.set_visible(True)

	def _update_screen(self):
		'''Update images on the screen and flip to the new screen'''
		self.screen.fill(self.settings.bg_color)
		self.ship.blitme()
		for bullet in self.bullets.sprites():
			bullet.draw_bullet()
		self.aliens.draw(self.screen)

		#Draw scoreboard
		self.sb.show_score()

		#Draw the play button if game inactive
		if not self.stats.game_active:
			self.play_button.draw_button()

		#Make the most recently drawn screen visible
		pygame.display.flip()

if __name__ == '__main__':
	#Make a game instance and run the thing!
	ai = AlienInvasion()
	ai.run_game()