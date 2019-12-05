import random

# Make a random 2D puzzle with angular shapes.

MAX_COMPONENT_SIZE = 9
MIN_COMPONENT_SIZE = 5

class Cell:
    """ A cell is a component within the grid.  Each cell has an x and y 
    component along with a potential set of walls to the North, East, South
    or West.  A wall can have one of the wall_types defined within this class.
    Wall_types are used to distinguish different types of walls which 
    may be rendered differently in the final output.
    """

    # Walls within a cell are 'complementary' to adjacent cells within
    # the grid.  It is important that cells within the grid are kept 
    # up to date to avoid one-way walls.
    wall_compliments = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}

    # A wall type of 'None' means that no wall exists.  Otherwise the walls
    # all impede movement between two adjacent cells however they are added
    # for different reasons and may also be rendered differently.
    wall_types = [ 'None', 'Normal', 'Interior', 'Extra' ]

    wall_colors = { 'Normal': '#000000',
            'Interior': '#00FF00',
            'Extra': '#FF0000',
            'None': '#FF00FF'
            }

    def __init__(self, x, y):
        """Initialize the cell at (x, y). At first it is surrounded by normal walls everywhere."""
        self.x = x
        self.y = y
        self.barriers = {'N': 'Normal', 'S': 'Normal', 'E': 'Normal', 'W': 'Normal'}

    def __str__(self):
        return "({}, {})".format(self.x, self.y)

    def is_completely_disconnected(self):
        """Is this cell completely closed off from all other cells?  That is, are there 
           normal walls on all four sides?"""
        f = list(filter(lambda t: t == 'Normal', self.barriers.values()))
        return len(f) == 4

    def has_wall(self, direction):
        return self.barriers[direction] != 'None'

    def get_wall_color(self, direction):
        return Cell.wall_colors[self.barriers[direction]]

    def remove_wall(self, other, direction):
        """Remove the wall between this cell and the other"""
        self.barriers[direction] = 'None'
        other.barriers[Cell.wall_compliments[direction]] = 'None'

    def set_wall(self, other, direction, wall_type):
        """Set the wall between cells this wall and another. 
           This method will return the prior wall type that
           stood between this cell and the next.
        """
        result = self.barriers[direction] 
        self.barriers[direction] = wall_type
        other.barriers[Cell.wall_compliments[direction]] = wall_type
        return result


class Grid:
    def __init__(self, width, height):
        """Initialize the grid.
        The grid consists of width x height cells.

        """
        self.width = width
        self.height = height
        self.grid_map = [[Cell(x, y) for y in range(height)] for x in range(width)]

    def cell_at(self, x, y):
        """Return the Cell object at (x, y)."""
        return self.grid_map[x][y]

    def has_wall(self, x, y, direction):
        cell = self.cell_at(x, y)
        return cell.has_wall(direction)

    def write_svg(self, filename):
        """Write an SVG image of the Grid to filename."""

        aspect_ratio = self.width / self.height
        # Pad the grid all around by this amount.
        padding = 10
        # Height and width of the grid image (excluding padding), in pixels
        pixel_height = 500
        pixel_width = int(pixel_height * aspect_ratio)
        # Scaling factors mapping grid coordinates to image coordinates
        scy, scx = pixel_height / self.height, pixel_width / self.width

        def write_svg_wall(f, x1, y1, x2, y2, color):
            print('<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}"/>'
                                .format(x1, y1, x2, y2, color), file=f)

        # Write the SVG image file for grid
        with open(filename, 'w') as f:
            # SVG preamble and styles.
            print('<?xml version="1.0" encoding="utf-8"?>', file=f)
            print('<svg xmlns="http://www.w3.org/2000/svg"', file=f)
            print('    xmlns:xlink="http://www.w3.org/1999/xlink"', file=f)
            print('    width="{:d}" height="{:d}" viewBox="{} {} {} {}">'
                    .format(pixel_width+2*padding, pixel_height+2*padding,
                        -padding, -padding, pixel_width+2*padding, pixel_height+2*padding),
                  file=f)
            print('<defs>\n<style type="text/css"><![CDATA[', file=f)
            print('line {', file=f)
            print('    stroke-linecap: square;', file=f)
            print('    stroke-width: 1;\n}', file=f)
            print(']]></style>\n</defs>', file=f)
            # Draw the "South" and "East" walls of each cell, if present.
            for x in range(self.width):
                for y in range(self.height):
                    cell = self.cell_at(x, y)
                    if cell.has_wall('S'):
                        x1, y1, x2, y2 = x*scx, (y+1)*scy, (x+1)*scx, (y+1)*scy
                        write_svg_wall(f, x1, y1, x2, y2, cell.get_wall_color('S'))
                    if cell.has_wall('E'): 
                        x1, y1, x2, y2 = (x+1)*scx, y*scy, (x+1)*scx, (y+1)*scy
                        write_svg_wall(f, x1, y1, x2, y2, cell.get_wall_color('E'))
                        
            # Draw the North and West grid border.
            write_svg_wall(f, 0, 0, pixel_width, 0, "#000000")
            write_svg_wall(f, 0, 0, 0, pixel_height, "#000000")

            print('</svg>', file=f)


    def find_unused_neighbors(self, cell):
        """Return a list of unvisited neighbours to cell."""
        return list(filter(lambda n: n[1].is_completely_disconnected(), self.get_valid_neighbors(cell)))


    def make_all_cells_reachable(self):
        # Total number of cells.
        n = self.width * self.height
        cell_stack = []
        current_cell = self.cell_at(0, 0)

        # Total number of visited cells during this construction.
        total_visited = 1

        while total_visited < n:
            neighbors = self.find_unused_neighbors(current_cell)

            if not neighbors:
                # We've reached a dead end: backtrack.
                current_cell = cell_stack.pop()
                continue

            # Choose a random cell that is adjacent to the current and move to it.
            direction, next_cell = random.choice(neighbors)
            current_cell.remove_wall(next_cell, direction)
            cell_stack.append(current_cell)
            current_cell = next_cell
            total_visited += 1

    def dfs_walk(self, x, y):
        """ Walk the entire grid from the given starting point.  Returns a list of 
            <x, y, direction, next_x, next_y> tuples.
        """
        result = []
        seen = []
        n = self.width * self.height
        path_stack = []
        current_cell = self.cell_at(x, y)

        return self.dfs_walk_recursive(current_cell, seen)

    def dfs_walk_recursive(self, current_cell, seen):
        if len(seen) == self.width * self.height:
            return []

        result = []
        for (direction, next_cell) in self.get_directly_reachable_neighbors(current_cell):
            if next_cell in seen:
                continue

            result.append((current_cell.x, current_cell.y, direction,
                next_cell.x, next_cell.y))
            seen.append(next_cell)
            result.extend(self.dfs_walk_recursive(next_cell, seen) )
        return result


    def is_reachable(self, c1, c2):
        """ Determine whether you can move from C1 to C2."""
        all_that_can_be_seen = self.all_reachable(c1)
        return c2 in all_that_can_be_seen

    def get_valid_neighbors(self, cell):
        delta = [('W', (-1,0)),
                 ('E', (1,0)),
                 ('S', (0,1)),
                 ('N', (0,-1))]
        result = []
        for direction, (dx, dy) in delta:
            x2, y2 = cell.x + dx, cell.y + dy
            if (0 <= x2 < self.width) and (0 <= y2 < self.height):
                result.append((direction, self.cell_at(x2,y2) ))

        return result

    def get_directly_reachable_neighbors(self, cell):
        return list(filter(lambda n: not cell.has_wall(n[0]), self.get_valid_neighbors(cell)))

    def find_interior_walls(self):
        for y in range(self.height):
            for x in range(self.width):
                c = self.cell_at(x, y)
                for direction, c2 in self.get_valid_neighbors(c):
                    # For each of the neighbors if there is a wall separating them 
                    # but you can still walk from one to the other then that wall
                    # is actually an interior wall.
                    if c.has_wall(direction):
                        if self.is_reachable(c, c2):
                            c.set_wall(c2, direction, 'Interior')

    def all_reachable(self, cell):
        return self.all_reachable_recursive(cell, [cell])
        
    def all_reachable_recursive(self, cell, seen):
        result = [cell]
        for direction, next_cell in self.get_directly_reachable_neighbors(cell):
            if next_cell in seen:
                continue
            seen.append(next_cell)
            result.extend(self.all_reachable_recursive(next_cell, seen))

        return result

    def optimize_small_pieces(self):
        """ Find an remove all 'small' pieces.  This looks for any cell which can reach some number of cells
            below a threshold.  If it finds it then it considers all neighbors of that cell and the smallest
            count of cells that it can join with and removes the wall to join with that grouping.
        """
        for y in range(self.height):
            for x in range(self.width):
                c = self.cell_at(x, y)
                reachable_cells = self.all_reachable(c)

                if len(reachable_cells) < 4:
                    print ("Optimize_walls; considering ({},{}) due to reachable count of {}".format(c.x, c.y, len(reachable_cells)))
                    # Tear down a wall between this cell and the neighbor who is unreachable with the smallest count
                    cell_smallest, direction_smallest, count_smallest = None, None, 10000

                    for direction, c2 in self.get_valid_neighbors(c):
                        # For each of the neighbors if you cannot move directly there then consider this as a coalescing point.
                        if not self.is_reachable(c, c2):
                            reachable_from_neighor = self.all_reachable(c2)
                            if len(reachable_from_neighor) < count_smallest:
                                cell_smallest = c2
                                direction_smallest = direction
                                count_smallest = len(reachable_from_neighor)

                    print ("Optimize_walls; found smallest neighbor of ({},{}).  It is ({},{}) due to reachable count of {}".format(c.x, c.y, cell_smallest.x, cell_smallest.y, count_smallest))
                    c.remove_wall(cell_smallest, direction_smallest)

    def find_neighbor(self, cell, direction):
        delta = {'W': (-1,0),
                 'E': (1,0),
                 'S': (0,1),
                 'N': (0,-1)}

        (dx, dy) = delta[direction]
        x2, y2 = cell.x + dx, cell.y + dy
        if (0 <= x2 < self.width) and (0 <= y2 < self.height):
            return self.cell_at(x2, y2)
        else:
            return None

    def is_square(self, cells):
        min_x = min(cells, key=lambda cell: cell.x).x
        max_x = max(cells, key=lambda cell: cell.x).x
        min_y = min(cells, key=lambda cell: cell.y).y
        max_y = max(cells, key=lambda cell: cell.y).y
        return min_x + 1 == max_x and min_y + 1 == max_y

    def optimize_square_pieces(self):
        for y in range(self.height):
            for x in range(self.width):
                cell = self.cell_at(x, y)
                reachable_cells = self.all_reachable(cell)

                # print("Reachable squares for ({},{}): {} -- {}".format(x, y, len(reachable_cells), ",".join([str(x) for x in reachable_cells])))
                if len(reachable_cells) == 4 and self.is_square(reachable_cells):
                    print("Found a square shape at ({},{}) -- {}".format(x, y, ", ".join([str(x) for x in reachable_cells])))
                    # Tear down a random wall.
                    random_direction_index = random.randint(0, 3)
                    random_direction = list(Cell.wall_compliments.keys())[random_direction_index]

                    adjacent_cell = self.find_neighbor(cell, random_direction)
                    print("Chose a random direction: {}, found cell: {}".format(random_direction, adjacent_cell))

                    if adjacent_cell != None:
                        cell.remove_wall(adjacent_cell, random_direction)

    def optimize_too_big_pieces(self):
        for y in range(self.height):
            for x in range(self.width):
                cell = self.cell_at(x, y)
                reachable_cells = self.all_reachable(cell)
                starting_length = len(reachable_cells)
                if starting_length > 15:
                    while True:
                        # Choose a random cell and direction and create a wall.
                        rand_cell = random.choice(reachable_cells)
                        random_direction = random.choice(list(Cell.wall_compliments.keys()))

                        adjacent_cell = self.find_neighbor(rand_cell, random_direction)
                        print("too big; Rand cell: {}, random direction: {}, found cell: {}".format(str(rand_cell),random_direction, adjacent_cell))

                        if adjacent_cell != None:
                            prior_wall = rand_cell.set_wall(adjacent_cell, random_direction, "Normal")

                            reachable_cells = self.all_reachable(cell)

                            # Avoid the situation where the resulting size is too small for either the remainder or the current.
                            if len(reachable_cells) <= 3 or starting_length - len(reachable_cells) <= 3:
                                rand_cell.set_wall(adjacent_cell, random_direction, prior_wall)
                            elif len(reachable_cells) != starting_length:
                                print("too big; done.  Starting cell ({},{}), starting size: {}, ending size: {}".format(x, y, starting_length, len(reachable_cells)))
                                break

    def optimize_pieces(self):
        self.optimize_small_pieces()
        self.optimize_square_pieces()
        self.optimize_too_big_pieces()


random.seed(0)

# Grid dimensions (ncols, nrows)
width, height = 20, 20

# Step 1 - make a grid where every cell can reach every other cell.
# Inspiration taken from here:  https://scipython.com/blog/making-a-maze/                                     
grid = Grid(width, height)
grid.make_all_cells_reachable()

print(grid)

walk = grid.dfs_walk(0,0)

priorX = walk[0][0]
priorY = walk[0][1]
for (x, y, direction, nextX, nextY) in walk:
    s = "({}, {} ) -> {} -> ({}, {} )".format(x, y, str(direction), nextX, nextY)
    if priorX != x or priorY != y:
        print("Backtracked!  ",s)
    else:
        print("              ",s)
    priorX = nextX
    priorY = nextY

# Partition the walk into components by drawing a random interior wall 
# within the grid.  
current_index = 0
while current_index < len(walk):
    cut_point = random.randint(MIN_COMPONENT_SIZE, MAX_COMPONENT_SIZE)

    # If the cut_point would result in a very small sized final part
    # then we skip the cut_point
    if current_index + cut_point + 3 >= len(walk):
        break

    (x1, y1, direction, x2, y2) = walk[current_index+cut_point]

    print ("Adding random wall; ({},{}) -> {} -> ({},{})".format(x1, y1, direction, x2, y2))

    cut_cell = grid.cell_at(x1,y1)
    cut_cell.set_wall(grid.cell_at(x2,y2), direction, 'Extra')

    current_index += cut_point

# Optimize the pieces
grid.optimize_pieces()

# Walk through each cell and its neighbors.  If there is a wall separating them but you can still get from one 
# to another then classify this wall as an interior wall.
grid.find_interior_walls()

grid.write_svg('grid.svg')
