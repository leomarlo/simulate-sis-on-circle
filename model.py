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
        self.g = generate(N, initial)
        self.lambda_ = lambda_
        self.r = r
        self.dt = dt
        self.K = K

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
        
    
    def run(self, total_time):
        self.__check_number_of_iterations(total_time)
        snapshots = []
        for _ in range(int(total_time / self.dt)):
            self.update()
            snapshots.append([data['state'] for _, data in self.g.nodes(data=True)])
        return snapshots

    
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



    def run_midi_out(self, total_time, filename, ticks_per_beat=480, ramp=0.5, rampType='linear'):
        # Ensure rampType is valid
        if rampType != 'linear':
            raise ValueError("Only 'linear' rampType is currently supported.")

        # Create a new MIDI file
        mid = MidiFile()

        # Helper function to calculate velocity based on state and ramp
        def calculate_velocity(state, prev_velocity):
            target_velocity = 127 if state == 1 else 0
            if rampType == 'linear':
                return int(prev_velocity + ramp * (target_velocity - prev_velocity))
            # Other ramp types can be added here in the future

        # Create a track for each node
        tracks = [MidiTrack() for _ in self.g.nodes()]
        for track in tracks:
            mid.tracks.append(track)

        # Store velocities and previous velocities for each node
        prev_velocities = [0] * len(self.g.nodes())

        # Run the simulation and generate MIDI messages
        for _ in range(int(total_time / self.dt)):
            for node, track in enumerate(tracks):
                velocity = calculate_velocity(self.g.nodes[node]['state'], prev_velocities[node])
                track.append(Message('note_on', note=60, velocity=velocity, time=int(self.dt * ticks_per_beat), channel=node % 16))
                prev_velocities[node] = velocity
            self.update()

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
