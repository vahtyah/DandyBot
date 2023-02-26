import queue


class Coordinate:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Coordinate(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Coordinate(self.x - other.x, self.y - other.y)


class Node:
    def __init__(self, coordinate, connectionTo=None):
        self.coordinate = coordinate
        self.connectionTo = connectionTo


def CreateGrid(check, x, y):
    grid = {}
    for i in range(30):
        for j in range(30):
            coordinate = Coordinate(i, j)
            node = Node(coordinate)
            grid[f"{coordinate.x};{coordinate.y}"] = node
    return grid


def ExploreNeighbors(check, grid, currentSearchNode, reached, frontQue):
    neighbors = []
    directions = [Coordinate(1, 0), Coordinate(-1, 0), Coordinate(0, -1), Coordinate(0, 1)]
    for direction in directions:
        neighborCoordinates = currentSearchNode.coordinate + direction
        if grid.get(f"{neighborCoordinates.x};{neighborCoordinates.y}") is not None:
            neighbors.append(grid[f"{neighborCoordinates.x};{neighborCoordinates.y}"])

    for neighbor in neighbors:
        if reached.get(f"{neighbor.coordinate.x};{neighbor.coordinate.y}") is None and not check("wall", neighbor.coordinate.x, neighbor.coordinate.y) \
                and not check("player", neighbor.coordinate.x, neighbor.coordinate.y):
            neighbor.connectionTo = currentSearchNode
            reached[f"{neighbor.coordinate.x};{neighbor.coordinate.y}"] = neighbor
            frontQue.put(neighbor)


def BreadthFistSearch(check, grid, starNode):
    currentSearchNode = None
    frontQue = queue.Queue()
    frontQue.put(starNode)
    reached = {f"{starNode.coordinate.x};{starNode.coordinate.y}": starNode}
    while not frontQue.empty():
        currentSearchNode = frontQue.get()
        ExploreNeighbors(check, grid, currentSearchNode, reached, frontQue)
        if check("gold", currentSearchNode.coordinate.x, currentSearchNode.coordinate.y):
            break
    return currentSearchNode


def BuildPath(endNode):
    path = []
    currentNode = endNode

    path.append(currentNode.coordinate)
    while currentNode.connectionTo is not None:
        currentNode = currentNode.connectionTo
        path.append(currentNode.coordinate)

    return path[len(path) - 2]


def ChooseDirector(x, y, coordinate):
    offset = Coordinate(x - coordinate.x, y - coordinate.y)
    if offset.x > 0:
        return "left"
    if offset.x < 0:
        return "right"
    if offset.y < 0:
        return "down"
    if offset.y > 0:
        return "up"
    return "pass"


def script(check, x, y):
    if check("gold", x, y):
        return "take"
    if check("level") < 6:
        grid = CreateGrid(check, x, y)
        nodePlayer = Node(Coordinate(x, y))
        nodeGold = BreadthFistSearch(check, grid, nodePlayer)
        direction = BuildPath(nodeGold)
        return ChooseDirector(x, y, direction)
