#!/usr/bin/python

import json
import socket
import time
import random
import pprint
import sys
from optparse import OptionParser

from strategies import Hide
from constants import *


class GameClient(object):
    def __init__(self, host, port, email, strategy):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

        self.email = email

        self.pos = (0, 0)

        self.token, self.map, self.mapwidth = self.start()
        self.strategy = strategy(self.map, self.mapwidth)

    def __str__(self):
        rows = []
        rows.append('   %s' % ' '.join(map(lambda i: str(i)[-1], range(len(self.map)))))
        
        for i, r in enumerate(self.map):
            rows.append('%s %s' % (str(i).rjust(2, ' '), ' '.join([OBJECTS[c][1] for c in r])))

        return '\n'.join(rows)

    def won(self):
        food = [(x, y) for x in range(len(self.map))
                for y in range(len(self.map[x]))
                if self.eatable_object(self.map[x][y])]

        return not bool(len(food))

    def send(self, action, data):
        """
        Sends a message of type action with data encoded as json,
        waits for the reply.
        """
        data['token'] = self.token
        data = json.dumps(data)

        message = "%s %s" % (action, data)
        self.sock.send(message)

        return self.recv()

    def start(self):
        self.sock.send("start %s" % json.dumps({
                    'email': self.email,
                    'ghosts': 1,
                    'map': "classic"
                    }))
        result = self.recv()

        map = self.parse_map(result['map'], result['mapwidth'])
        return result['token'], map, result['mapwidth']


    def state(self):
        """
        Fetches state from server and updates the local map
        """
        result = self.send('state', {})
        self.map = self.parse_map(result['map'], self.mapwidth)

        return ' '.join(list(result['mapstr']))

    def move(self):
        """Moves in random direction"""
        x, y = self.pos
        sides = self.get_sides(x, y)

        preferred_directions = [d for d, o in sides.items()
                                if self.eatable_object(o)]
        legal_directions = [d for d, o in sides.items()
                            if self.allowed_object(o)]

        direction = preferred_directions and random.choice(preferred_directions) \
            or random.choice(legal_directions)

        self.do_move(direction)

    def do_move(self, direction):
        x, y = self.pos

        new_pos = x, y
        if direction == 'up':
            new_pos = x-1, y
        elif direction == 'right':
            new_pos = x, y+1
        elif direction == 'down':
            new_pos = x+1, y
        elif direction == 'left':
            new_pos = x, y-1

        result = self.send('move', { 'direction': direction })

        state = result['state']
        if state == 'game_over':
            raise Exception("Game over, Pakku is dead")

        self.map = self.parse_map(result['map'], self.mapwidth)

        self.pos = new_pos

        # Notify the strategy of the updated map
        self.strategy.move_done(self.map, self.pos)

    def get_sides(self, x, y):
        """Peek into the distance.."""
        result = {
            'up': None,
            'right': None,
            'down': None,
            'left': None
            }

        if 0 < x: result['up'] = self.map[x-1][y]
        if x < self.mapwidth - 1: result['down'] = self.map[x+1][y]

        if 0 < y: result['left'] = self.map[x][y-1]
        if y < self.mapwidth - 1: result['right'] = self.map[x][y+1]
        
        return result

    def allowed_object(self, object):
        return object in ALLOWED_OBJECTS
    def eatable_object(self, object):
        return object in EATABLE_OBJECTS

    def parse_map(self, m, width):
        return [map(lambda m: int(m), m[i:i+width]) for i in range(0, len(m), width)]


    def recv(self):
        d = []
        while True:
            data = self.sock.recv(1024)
            d.append(data)
        
            if len(data) < 1024:
                break
        return json.loads(''.join(d))


if __name__ == '__main__':
    client = GameClient(HOST, PORT, 'knutin@gmail.com', Hide)

    manual = False
    if '--manual' in sys.argv:
        manual = True

    while not client.won():
        print "\x1B[2J"

        print client

        move = client.strategy.move()
        #print 'Moving', move
        client.do_move(move)

        if manual:
            raw_input('Press Enter to continue')

    print 'EPIC WIN!!'
