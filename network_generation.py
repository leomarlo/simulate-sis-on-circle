# network_generation.py
import networkx as nx

def generate(N, initial):
    # Create a directed circular graph
    G = nx.DiGraph()
    for i in range(N):
        G.add_edge(i, (i + 1) % N)
    
    # Assign states to nodes
    if isinstance(initial, (int, float)):
        num_ones = int(N * initial)
        states = [1] * num_ones + [0] * (N - num_ones)
    elif isinstance(initial, list) and len(initial) == N:
        states = initial
    else:
        raise ValueError("Invalid initial value")
    
    for i, state in enumerate(states):
        G.nodes[i]['state'] = state
    
    return G
