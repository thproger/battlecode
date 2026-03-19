from enum import Enum
import random

from cambc import Controller, Direction, EntityType, Environment, Position

DIRECTIONS = [d for d in Direction if d != Direction.CENTRE]

class State(Enum):
    FIND_ORE = 'find_ore',
    GO_TO_ORE = 'go_to_ore',
    CREATE_BRIDGE = 'create_bridge'

class CoreLogic:
    def __init__(self):
        self.num_spawned = 0

    def act(self, ct: Controller):
        if self.num_spawned < 1:
            spawn_pos = ct.get_position().add(Direction.EAST)
            if ct.can_spawn(spawn_pos):
                ct.spawn_builder(spawn_pos)
                self.num_spawned += 1


class BuilderLogic:
    def __init__(self):
        self.harvester = False
        self.direction = Direction.CENTRE
        self.state = State.FIND_ORE
        self.ore = None
        self.destroyed = False

    def act(self, ct: Controller):
        position = ct.get_position()
        self.try_build_harvester(ct)
        match self.state:
            case State.FIND_ORE:
                if ore := self.find_ore(ct):
                    self.state = State.GO_TO_ORE
                    self.find_direction(position, ore)
                else:
                    self.direction = Direction.NORTH
                if ct.can_build_road(position.add(self.direction)):
                    ct.build_road(position.add(self.direction))
                if ct.can_move(self.direction):
                    ct.move(self.direction)
            case State.GO_TO_ORE:
                if self.harvester:
                    self.state = State.CREATE_BRIDGE

                elif self.ore:
                    self.find_direction(position, ore)
                if ct.can_build_road(position.add(self.direction)):
                    ct.build_road(position.add(self.direction))
                if ct.can_move(self.direction):
                    ct.move(self.direction)
            case State.CREATE_BRIDGE:
                if ct.can_destroy(position) and not self.destroyed:
                    ct.destroy(position)
                    self.destroyed = True
                elif ct.can_build_conveyor(position, Direction.SOUTH):
                    ct.build_conveyor(position, Direction.SOUTH)
                elif ct.can_move(Direction.SOUTH):
                    ct.move(Direction.SOUTH)
                    self.destroyed = False

        
    def try_build_harvester(self, ct: Controller):
        for d in Direction:
            check_pos = ct.get_position().add(d)
            if ct.can_build_harvester(check_pos):
                ct.build_harvester(check_pos)
                self.harvester = True

    def find_ore(self, ct: Controller):
        for p in ct.get_nearby_tiles():
            if ct.get_tile_env(p) == Environment.ORE_AXIONITE or ct.get_tile_env(p) == Environment.ORE_TITANIUM:
                return p
        return None
    
    def find_direction(self, start: Position, end: Position):
        if start.x < end.x:
            self.direction = Direction.WEST
        elif start.x > end.x:
            self.direction = Direction.EAST
        elif start.y < end.y:
            self.direction = Direction.SOUTH
        elif start.y > end.y:
            self.direction = Direction.NORTH
        return Direction.NORTH

class Player:
    def __init__(self):
        self.num_spawned = 0 # number of builder bots spawned so far (core)
        self.core_logic = CoreLogic()
        self.builder_logic = BuilderLogic()

    def run(self, ct: Controller) -> None:
        etype = ct.get_entity_type()

        if etype == EntityType.CORE:
            self.core_logic.act(ct)

        elif etype == EntityType.BUILDER_BOT:
            base = ct.get_position()
            self.builder_logic.act(ct)