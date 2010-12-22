"""
This module contains different strategies for playing Pacman
"""
import game
import pprint

from djikstra import shortestPath

from constants import *

class Strategy(object):
    """
    Base class for all strategies. Contains helper methods for
     * creating graphs,
     * finding ghosts,
     * finding pacdots, etc.
    """
    def __init__(self, m, width):
        self.map = m
        self.width = width
        self.pos = self.find_pacman_pos(self.map)
        self.ghosts = self.find_ghosts_pos(self.map)

        self.graph = None

    def move_done(self, m, pos):
        self.map = m
        self.pos = pos
        self.ghosts = self.find_ghosts_pos(self.map)

    def find_pacman_pos(self, map):
        for x, y, column in self.map_iter():
            if column == PACMAN_TYPE:
                return x, y

        raise Exception("Pacman not found in map")

    def find_ghosts_pos(self, map):
        ghosts = []

        for x, y, column in self.map_iter():
            if column in GHOSTS:
                ghosts.append((x, y))

        return ghosts

    def map_iter(self):
        for x, row in enumerate(self.map):
            for y, column in enumerate(row):
                yield x, y, column

    def make_graph(self):
        """
        Creates a dictionary holding the graph found on the grid.
        A vertice(v) is (x, y) where x and y are the coordinates to that cell in the grid.
        
        G[v] gives a dictionary where the key is the neighbour and the value is the cost of getting there(always 1).
        """
        graph = {}

        for x, y, column in self.map_iter():
            if not game.allowed_position(self.map, (x, y)):
                continue

            # left, up, right, down
            edges = [(x, y-1), (x-1, y), (x, y+1), (x+1, y)]

            # Remove any illegal positions
            def f(p):
                return 0 <= p[0] < self.width and 0 <= p[1] < self.width
            edges = filter(f, edges)

            # Remove any invalid positions, including positions with ghosts
            edges = filter(lambda p: game.allowed_position(self.map, p), edges)

            graph[(x, y)] = dict([(p, 1) for p in edges])

        return graph

    def shortest_path(self, start, end):
        #return brute_shortest_path(self.graph, start, end)
        return shortestPath(self.graph, start, end)

    def pos_to_direction(self, old, new):
        """
        Takes the old position, the new position, and translates it into
        a string with the direction name that can be sent to the server.
        """
        # This could be improved..
        if old[0] + 1 == new[0] and old[1] == new[1]:
            return 'down'
        elif old[1] + 1 == new[1] and old[0] == new[0]:
            return 'right'
        elif old[0] - 1 == new[0] and old[1] == new[1]:
            return 'up'
        elif old[1] - 1 == new[1] and old[0] == new[0]:
            return 'left'

    def is_food(self, pos):
        return self.map[pos[0]][pos[1]] in EATABLE_OBJECTS

    def find_food(self, pos, maxdepth = 3):
        """
        Returns the coordinates of neighbours with food
        Uses a breadth-first search, which will terminate when three
        cells with food has been found.
        """
        food = []

        q = [pos]
        seen = []
        while q:
            current = q.pop(0)
            for n in self.graph[current]:
                if self.is_food(n):
                    food.append(n)

                    if len(food) > 3:
                        break

                if not n in seen:
                    seen.append(n)
                    q.append(n)
        
        return set(food)


class Random(Strategy):
    pass

class Dumb(Strategy):
    pass

class Suicidal(Strategy):
    """
    Heads strait for the closest ghost
    """

class Hide(Strategy):
    """
    Tries to move as far away from the ghosts as possible
    """
    previous_cells = []


    def move(self):
        """
        Returns the next move by inspecting the nearby tiles

        This strategy is pretty simple:
        Move towards the closest food time that takes Pacman the furthest away
        from the ghosts.

        """
        # TODO: Detect when the ghosts will corner pacman in a dead-end

        self.graph = self.make_graph()
        #pprint.pprint(self.graph)
        #pprint.pprint(self.map)
        #pprint.pprint(self.graph)

        #print shortestPath(self.graph, (0, 0), (4, 4))

        ghosts = self.find_ghosts_pos(self.map)

        # Find the closest food items, within a reasonable range
        food = self.find_food(self.pos, maxdepth = 8)
        #print 'food', list(food)

        # Simulate taking the first step toward every food item
        # Which step brings me the furthest away from the ghost?
        next_steps = []
        for food_position in food:
            # TODO: This should ignore paths where there are ghosts

            # Find shortest path to food. Remove the first step as it is
            # the starting position.
            path = self.shortest_path(self.pos, food_position)[1:]
            distance = len(path)

            # If Pacman were to take this step,
            # what is the distance to the ghosts?
            #distance_to_ghost = sum(map(lambda g: len(self.shortest_path(path[0], g)), ghosts))
            distance_to_ghost = min(map(lambda g: len(self.shortest_path(path[0], g)), ghosts))
            #print 'distance between', path[0], 'and', ghosts[0], 'is', distance_to_ghost

            next_steps.append((distance, distance_to_ghost, path[0]))

        def cmp(a, b):
            # First sort by distance to food
            diff = a[0] - b[0]
            # If two items are equal, reverse sort by distance to ghost
            return diff and diff or b[1] - a[1]

        next_steps = sorted(next_steps, cmp = cmp)

        # Discard steps where the distance is two or less to ghosts,
        # as they are suicide
        next_steps = filter(lambda (dist, g_dist, path): g_dist > 2, next_steps)
        print next_steps

        if next_steps:
            next = next_steps[0][2]

            # Check if we are stuck, if so, try to move away
            if next in self.previous_cells[-2:]:
                for distance, distance_to_ghost, n in next_steps:
                    if n not in self.previous_cells:
                        next = n
                        break

            self.previous_cells.append(next)
            self.previous_cells = self.previous_cells[-5:]
            return self.pos_to_direction(self.pos, next)

        else:
            # No obvious next step because there is no food nearby
            # Pick the direction that will take us the furthest away from
            # the ghosts.
            print 'no food nearby'
            neighbours = []
            for pos in self.graph[self.pos]:
                path = self.shortest_path(ghosts[0], pos)
                distance_to_ghost = min(map(lambda g: len(self.shortest_path(g, pos)), ghosts))
                if path:
                    neighbours.append((distance_to_ghost - 1, pos))
                
            neighbours = sorted(neighbours, reverse = True)
            print neighbours
            next = neighbours[0][1]

            self.previous_cells.append(next)
            self.previous_cells = self.previous_cells[-5:]
            return self.pos_to_direction(self.pos, next)

def brute_shortest_path(graph, start, end, path = []):
    """
    Returns the shortest path between start and end.
    Implemented with a depth-first search.
    """
    path = path + [start]
    if start == end:
        return path

    # If there are ghosts in the way, Pacman cannot go there, stupid
    #if self.map[start[0]][start[1]] in GHOSTS:
    #    return None

    if not graph.has_key(start):
        return None

    shortest = None
    for node in graph[start]:
        if node not in path:
            newpath = brute_shortest_path(graph, node, end, path)
            if newpath:
                if not shortest or len(newpath) < len(shortest):
                    shortest = newpath

    return shortest
