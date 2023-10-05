# sis_model.py
import networkx as nx
import numpy as np
from network_generation import generate
import os
import matplotlib.pyplot as plt
import networkx as nx
import time
import imageio
import mido
from mido import MidiFile, MidiTrack, Message
import subprocess

BASEPITCH = 60
PITCH_INC = 1



def midi_to_musicxml(midi_filename, xml_filename):
    # Path to the MuseScore executable - adjust this to your installation path
    musescore_path = "musescore"  # This might be something like "/Applications/MuseScore 3.app/Contents/MacOS/mscore" on macOS or "C:\\Program Files\\MuseScore 3\\bin\\MuseScore3.exe" on Windows

    # Convert MIDI to MusicXML
    subprocess.run([musescore_path, midi_filename, "-o", xml_filename])



def giffify_fun(howmany, output_filename="visualization.gif", duration=0.1):
        filenames = sorted([f"visualization/figure_{i}.png" for i in range(howmany)])
        with imageio.get_writer(output_filename, mode='I', duration=duration) as writer:  # 0.1 seconds per frame

            for filename in filenames:
                image = imageio.imread(filename)
                writer.append_data(image)

class SISModel:
    def __init__(self, N, initial, lambda_, r, dt, K=200):
        self.N = N
        self.g = generate(N, initial)
        self.lambda_ = lambda_
        self.r = r
        self.dt = dt
        self.K = K
        self.stored_run = []

    def update(self):
        new_states = {}
        for node, data in self.g.nodes(data=True):
            if data['state'] == 1:  # If infected
                # Check for recovery
                if np.random.poisson(self.r * self.dt) > 0:
                    new_states[node] = 0
                continue

            # If susceptible, check for infection from neighbors
            infected_neighbors = sum([self.g.nodes[neighbor]['state'] for neighbor in self.g.predecessors(node)])

            if np.random.poisson(self.lambda_ * infected_neighbors * self.dt) > 0:
                new_states[node] = 1

        for node, state in new_states.items():
            self.g.nodes[node]['state'] = state

    def __check_number_of_iterations(self, total_time):
        num_updates = int(total_time / self.dt)
        if num_updates > self.K:
            errormessage = f"Number of iterations ({num_updates}) exceeds the maximum number of iterations ({self.K})"
            print(errormessage)
            raise ValueError(errormessage)
        
    
    def run(self, total_time, store_run=True):
        # self.__check_number_of_iterations(total_time)
        if store_run:
            self.stored_run = []
        for _ in range(int(total_time / self.dt)):
            self.update()
            if store_run:
                self.stored_run.append([data['state'] for _, data in self.g.nodes(data=True)])

    
    def run_and_visualize(self, total_time, update_interval, inverted=False, giffify=0, show=True):
        self.__check_number_of_iterations(total_time)
        # Create a dedicated folder for saving figures if it doesn't exist
        if not os.path.exists("visualization"):
            os.makedirs("visualization")
        
        # Create initial figure and axis
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Get fixed node positions in a circular layout
        pos = nx.circular_layout(self.g)
        
        # Turn on interactive mode
        if show:
            plt.ion()
        
        num_updates = int(total_time / self.dt)
        # Initial drawing
        colors = [self.g.nodes[node]['state'] for node in self.g.nodes()]
        node_collection = nx.draw_networkx_nodes(self.g, pos, node_color=colors, node_size=150, edgecolors='black', ax=ax)
        nx.draw_networkx_edges(self.g, pos, ax=ax)
        
        for i in range(num_updates):
            # Update node colors
            colors = []
            for _, data in self.g.nodes(data=True):
                if data['state'] == 1:
                    colors.append('black' if not inverted else 'white')
                else:
                    colors.append('white' if not inverted else 'black')
            node_collection.set_color(colors)

            nx.draw(self.g, pos, ax=ax, node_color=colors, with_labels=False, node_size=175, edgecolors='black')  # node_size increased to 150

            
            # Save the figure
            fig.savefig(f"visualization/figure_{i}.png")
            
            # Show the plot and wait for the update interval
            plt.pause(update_interval)
            
            # Update the model
            self.update()
        
        # Turn off interactive mode and show the final figure
        if show:
            plt.ioff()
            plt.show()

        if giffify:
            giffify_fun(howmany=num_updates, duration=giffify)



    def run_with_midi_out(self, total_time, midi_ticks_per_dt, filename, store_run=True, debug=True):
        # Create a new MIDI file
        mid = MidiFile()
        track = MidiTrack() 
        mid.tracks.append(track) 
        CHANNEL = 0

        if store_run:
            self.stored_run = []

        # Create a track for each node
        pitches = {node:BASEPITCH + node * PITCH_INC for node, _ in enumerate(self.g.nodes()) }

        nrNodes = len(self.g.nodes())  ## same as self.N in this implementation 

        # initialize previous midi states 
        states = {
            'last_message': 0,
            'nodes': {
                node: {'prev': 0, 'curr': 0} for node in range(nrNodes)}
        }
        
        t = 0
        # Run the simulation and generate MIDI messages
        for i in range(int(total_time / self.dt)):
            if debug:
                if (i%10)==0:
                    print('current time is', i)
                    # print('the current state is', states)
            for node in range(nrNodes):
                states['nodes'][node]['curr'] = self.g.nodes[node]['state']

                velocity = 127 if self.g.nodes[node]['state'] == 1 else 0
                ## if previous notes are different do the action
                if (states['nodes'][node]['prev'] != states['nodes'][node]['curr']):
                    if debug:
                        if (i%10)==0:
                            print('the state changed for node', node)
                    # something changed for this node
                    if states['nodes'][node]['curr'] == 1:
                        # the node has turned on
                        track.append(Message(
                            'note_on', 
                            note=pitches[node], 
                            velocity=127, 
                            time=int(states['last_message']),
                            channel=CHANNEL))
                        states['last_message'] = 0
                    else:
                        track.append(Message(
                            'note_off', 
                            note=pitches[node], 
                            velocity=0, 
                            time=int(states['last_message']),
                            channel=CHANNEL))
                        states['last_message'] = 0                    
                states['nodes'][node]['prev'] = states['nodes'][node]['curr']
            if store_run:
                self.stored_run.append([data['state'] for _, data in self.g.nodes(data=True)])
            self.update()
            if debug:
                if (i%10)==0:
                    print([self.g.nodes[node]['state'] for node in range(nrNodes)])
            
            # update the states
            states['last_message'] += midi_ticks_per_dt
        # Save the MIDI file
        mid.save(filename)



    def clear_figures(self):
        folder = "visualization"
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) and filename.startswith("figure_") and filename.endswith(".png"):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")



    # Placeholder for the visualize function
    def visualize(self):
        pass
