from model import SISModel, giffify_fun, midi_to_musicxml
from network_generation import generate





if __name__ == '__main__':
    # # Create a model
    
    # model.clear_figures()
    # # Run the model for 10 time units
    # snapshots = model.run_and_visualize(total_time=29, update_interval=0.01, inverted=False, giffify=0.5, show=False)

    # model = SISModel(N=100, initial=0.5, lambda_=0.1, r=0.05, dt=0.1)
    # filename should have the date and hours
    
    lambda_ = 0.13
    r = 0.08
    dt = 0.1
    N=40
    initial=0.2
    total_time = 4000
    model = SISModel(N=N, initial=initial, lambda_=lambda_, r=r, dt=0.1, K=300)

    basefilename = "sis_N{N}_lamb{lam}_rec{rec}_time{time}".format(
        N=N,
        lam=int(lambda_*1000),
        rec=int(r*1000),
        time=total_time
    )

    model.run_with_midi_out(
        total_time=total_time, filename=basefilename + ".mid", midi_ticks_per_dt=1, debug=False)
    midi_to_musicxml(basefilename + ".mid", basefilename + ".xml")
    # giffify_fun(output_filename="my_simulation_2.gif", howmany=289, duration=0.5)
    # model.clear_figures()
    # Visualize the results
    # model.visualize(snapshots)
    # print(snapshots)