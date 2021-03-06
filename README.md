# RTS-simulator
Simulator for a real-time system, comparing random scheduling vs EDF.

For a number of iterations, a task set is generated with defined utilization and scheduled using EDF and a random policy.
Whichever is deemed to have scheduled the task set better (less deadline misses, lower power consumption) 'wins' the task set.
The results including task set winner are saved to a .csv file locally.

Past results run for large iterations can be found at: https://drive.google.com/open?id=1HPduEbVbDkw3celx2CnpPkKFKkHlgk35 (2.5gb)

Usage: Run the python script named 'simulator.py'. Edit the variables, eg change the Utilization or turbo speed of the task set. View the results in the .csv file generated. Each row corresponds to a task set and lists its properties. The final columns of each row specify which algorithm performed better for that set.
