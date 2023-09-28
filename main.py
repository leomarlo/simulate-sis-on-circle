from model import SISModel, giffify_fun, midi_to_musicxml
from network_generation import generate




if __name__ == '__main__':
    # # Create a model
    model = SISModel(N=12, initial=0.3, lambda_=0.8, r=0.1, dt=0.1, K=300)
    # model.clear_figures()
    # # Run the model for 10 time units
    # snapshots = model.run_and_visualize(total_time=29, update_interval=0.01, inverted=False, giffify=0.5, show=False)

    # model = SISModel(N=100, initial=0.5, lambda_=0.1, r=0.05, dt=0.1)
    model.run_midi_out(total_time=10, filename="output.mid", ticks_per_beat=480, ramp=0.5, rampType='linear')
    midi_to_musicxml("output.mid", "output.xml")
    # giffify_fun(output_filename="my_simulation_2.gif", howmany=289, duration=0.5)
    # model.clear_figures()
    # Visualize the results
    # model.visualize(snapshots)
    # print(snapshots)