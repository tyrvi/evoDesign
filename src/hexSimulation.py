from __future__ import print_function
import copy
from .cell import Cell
from .hexmap import Map
from .views.drawHexMap import draw_hex_map
from .modules import Module

class HexSimulation(object):
    def __init__(self, genome, bounds=(8,8), verbose=False, max_steps=64,
                                                         break_on_repeat=False):
        self.genome = genome
        self.bounds = bounds
        self.verbose = verbose
        self.max_steps = max_steps

        # State data
        self.hmap = Map(bounds, 0)
        self.cells = []
        self.next_cell_id = 0
        self.last_change = 0

        # Step statistics
        self.step_count = 0
        self.created_cells = 0
        self.destroyed_cells = 0

        self.module_simulations = []
        self._init_module_simulations()

        self.break_on_repeat = break_on_repeat
        if self.break_on_repeat:
            self.seen_states = set()

    def _init_module_simulations(self):
        """ Each module may have its own simulation class. Initialize them here.
            Only called from self.init
        """
        for module in self.genome.modules:
            if module.simulation:
                sim = module.simulation(self, module, **module.simulation_config)
                self.module_simulations.append(sim)

    def _get_cell_id(self):
        self.next_cell_id += 1
        return self.next_cell_id

    def cell_init(self, cell):
        for module in self.module_simulations:
            module.cell_init(cell)

    def create_cell(self, coords, cell_type=0):
        assert(self.hmap.valid_coords(coords))
        assert(not self.hmap[coords])

        if self.hmap[coords]:
            return None

        self.last_change = self.step_count

        cell = Cell(self._get_cell_id(), self.genome)

        cell.userData['coords'] = (coords[0], coords[1])
        self.hmap[coords] = cell
        self.cells.append(cell)

        self.created_cells += 1

        self.cell_init(cell)

        return cell

    def destroy_cell(self, cell):
        self.last_change = self.step_count
        for module in self.module_simulations:
            module.cell_destroy(cell)
        self.cells.remove(cell)
        self.hmap[cell.userData['coords']] = 0
        self.destroyed_cells += 1
        cell.alive = False

    def divide_cell(self, cell, direction):
        parent_coords = cell.userData['coords']
        coords = self.hmap.neighbor(parent_coords, direction)

        if self.hmap.valid_coords(coords) and not self.hmap[coords]:
            # self.hmap[parent_coords] = 0
            # cell.userData['coords'] = coords
            # self.hmap[coords] = cell
            # self.create_cell(parent_coords)
            self.create_cell(coords)

    def create_input(self, cell):
        raise NotImplementedError()

    def handle_output(self, cell, outputs):
        raise NotImplementedError()

    def step(self):
        pass

    def create_all_outputs(self):
        """ Collect all inputs first so simulation
            state does not change during input collection
        """
        all_outputs = []

        for cell in self.cells:
            inputs = self.create_input(cell)
            assert len(inputs) == self.genome.non_module_inputs

            for mod_sim in self.module_simulations:
                mod_input = mod_sim.create_input(cell)
                assert(len(mod_input) == len(mod_sim.module.total_inputs()))
                inputs.extend(mod_input)

            assert(len(inputs) == self.genome.num_inputs)

            all_outputs.append(cell.outputs(inputs))

            assert(len(all_outputs[-1]) == self.genome.num_outputs)

        return all_outputs

    def handle_all_outputs(self, all_outputs):
        # Handle all outputs.
        # Make a list copy because self.cells will change during iteration.
        for cell, outputs in list(zip(self.cells, all_outputs)):

            nmi = self.genome.non_module_outputs
            self.handle_output(cell, outputs[:nmi])
            if not cell.alive:
                continue

            # Handle Module outputs
            i = nmi
            for module, sim in zip(self.genome.modules, self.module_simulations):
                k = len(module.total_outputs())
                module_output = outputs[i:i+k]
                assert(len(module_output) == k)
                sim.handle_output(cell, module_output)
                i += k
                if not cell.alive:
                    break

    def super_step(self):
        self.created_cells = 0
        self.destroyed_cells = 0

        if self.verbose:
            print('#'*40,'step', self.step_count,'#'*40)

        all_outputs = self.create_all_outputs()
        self.handle_all_outputs(all_outputs)

        # Handle experiment logic.
        self.step()

        ### Handle Module Logic
        for mod_sim in self.module_simulations:
            mod_sim.step()

        if self.verbose:
            print('destroyed %i cells' % self.destroyed_cells)
            print('created %i cells:' % self.created_cells)
            print('final cells: %i' % len(self.cells))

        self.step_count += 1

    def run(self, renderer=None):
        max_fitness = 0

        # if renderer:
        #     renderer.render()

        for _ in range(self.max_steps):
            self.super_step()

            max_fitness = max(max_fitness, self.fitness())

            if renderer:
                renderer.render()

            # We are repeating the run to visualize. So we dont want to render
            # past reaching the max score.
            if self.genome.fitness and max_fitness == self.genome.fitness:
                return max_fitness

            # Check for inactivity.
            if self.step_count - self.last_change > 5:
                if self.verbose:
                    print('Simulation end due to inactivity.')
                return max_fitness

            # Check for looping.
            if self.break_on_repeat:
                state_hash = self.hmap.hash()
                if state_hash in self.seen_states:
                    if self.verbose:
                        print('Simulation end due to repeat state.')
                    return self.fitness()

                self.seen_states.add(state_hash)

        return max_fitness


    def render(self, surface):
        draw_hex_map(surface, self.hmap)
