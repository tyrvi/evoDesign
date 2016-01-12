# -*- coding: UTF-8 -*-
from __future__ import print_function

import warnings

from neat.statistics import get_average_fitness, get_species_sizes

#try:
import graphviz
#except ImportError:
#    graphviz = None
#    warnings.warn('Could not import optional dependency graphviz.')

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None
    warnings.warn('Could not import optional dependency matplotlib.')

try:
    import numpy as np
except ImportError:
    np = None
    warnings.warn('Could not import optional dependency NumPy.')


def plot_stats(population, ylog=False, view=False, filename='avg_fitness.svg'):
    """ Plots the population's average and best fitness. """
    if plt is None:
        warnings.warn("This display is not available due to a missing optional dependency (matplotlib)")
        return

    generation = range(len(population.most_fit_genomes))
    best_fitness = [c.fitness for c in population.most_fit_genomes]
    avg_fitness = get_average_fitness(population)

    plt.plot(generation, avg_fitness, 'b-', label="average")
    plt.plot(generation, best_fitness, 'r-', label="best")

    plt.title("Population's average and best fitness")
    plt.xlabel("Generations")
    plt.ylabel("Fitness")
    plt.grid()
    plt.legend(loc="best")
    if ylog:
        plt.gca().set_yscale('symlog')

    plt.savefig(filename)
    if view:
        plt.show()

    plt.close()


def plot_spikes(spikes, view=False, filename=None, title=None):
    """ Plots the trains for a single spiking neuron. """
    if plt is None:
        warnings.warn("This display is not available due to a missing optional dependency (matplotlib)")
        return

    t_values = [t for t, I, v, u in spikes]
    v_values = [v for t, I, v, u in spikes]
    u_values = [u for t, I, v, u in spikes]
    I_values = [I for t, I, v, u in spikes]

    plt.subplot(3, 1, 1)
    plt.ylabel("Potential (mv)")
    plt.xlabel("Time (in ms)")
    plt.grid()
    plt.plot(t_values, v_values, "g-")

    if title is None:
        plt.title("Izhikevich's spiking neuron model")
    else:
        plt.title("Izhikevich's spiking neuron model ({0!s})".format(title))

    plt.subplot(3, 1, 2)
    plt.ylabel("Recovery (u)")
    plt.xlabel("Time (in ms)")
    plt.grid()
    plt.plot(t_values, u_values, "r-")

    plt.subplot(3, 1, 3)
    plt.ylabel("Current (I)")
    plt.xlabel("Time (in ms)")
    plt.grid()
    plt.plot(t_values, I_values, "r-o")

    if filename is not None:
        plt.savefig(filename)

    if view:
        plt.show()
    plt.close()


def plot_species(population, view=False, filename='speciation.svg'):
    """ Visualizes speciation throughout evolution. """
    if plt is None:
        warnings.warn("This display is not available due to a missing optional dependency (matplotlib)")
        return

    species_sizes = get_species_sizes(population)
    num_generations = len(species_sizes)
    curves = np.array(species_sizes).T

    fig, ax = plt.subplots()
    ax.stackplot(range(num_generations), *curves)

    plt.title("Speciation")
    plt.ylabel("Size per Species")
    plt.xlabel("Generations")

    plt.savefig(filename)

    if view:
        plt.show()

    plt.close()


def draw_net(genome, view=False, filename=None, node_names=None):
    """ Receives a genome and draws a neural network with arbitrary topology. """
    # Attributes for network nodes.
    if graphviz is None:
        warnings.warn("This display is not available due to a missing optional dependency (graphviz)")
        return

    if node_names is None:
        node_names = {}

    assert type(node_names) is dict

    node_attrs = {
        'shape': 'circle',
        'fontsize': '9',
        'height': '0.2',
        'width': '0.2'}

    # Attributes for network input nodes.
    input_attrs = {
        'style': 'filled',
        'shape': 'box'}

    # Attributes for network output nodes.
    output_attrs = {
        'style': 'filled',
        'color': 'lightblue'}

    dot = graphviz.Digraph(format='svg', node_attr=node_attrs)

    for ng_id, ng in genome.node_genes.items():
        if ng.type == 'INPUT':
            name = node_names.get(ng_id, str(ng_id))
            dot.node(name, _attributes=input_attrs)

    for ng_id, ng in genome.node_genes.items():
        if ng.type == 'OUTPUT':
            name = node_names.get(ng_id, str(ng_id))
            dot.node(name, _attributes=output_attrs)

    for cg in genome.conn_genes.values():
        a = node_names.get(cg.in_node_id, str(cg.in_node_id))
        b = node_names.get(cg.out_node_id, str(cg.out_node_id))
        style = 'solid' if cg.enabled else 'dotted'
        color = 'green' if cg.weight > 0 else 'red'
        width = str(0.1 + abs(cg.weight / 5.0))
        dot.edge(a, b, _attributes={'style': style, 'color': color, 'penwidth': width})

    return dot.render(filename, view=view)
