import timeit

#------------------------------------------------------------------------------------------
# GIT commit df622bb77fe290b7c1d82d2c9170a6e4e1256258
# Date:   Wed Jun 5 14:54:11 2024 +0800
#------------------------------------------------------------------------------------------
setup="""\
import numpy as np

peak_positions = [20, 40, 60, 80]
YKSCAN_SLICER_SIZE = 2000
std_dev = 1.5
YKScan_slicer_buf = np.zeros((0, YKSCAN_SLICER_SIZE))
"""

old_algorithm="""\
slice_buf = []
for _ in range(YKSCAN_SLICER_SIZE):
    peak_pos = peak_positions[np.random.randint(4)]  # Randomly select a peak position
    slice_data = np.random.normal(loc=peak_pos, scale=std_dev)
    slice_buf.append(slice_data)

YKScan_slicer_buf = np.append(YKScan_slicer_buf, [slice_buf], axis=0)          # append new data
"""

new_algorithm="""\
slice_data = []
for peak_pos in peak_positions:
    slice_data.append( np.random.normal(loc=peak_pos, scale=std_dev, size=int(YKSCAN_SLICER_SIZE/4)) )
slice_buf = np.column_stack(( slice_data[0], slice_data[1], slice_data[2], slice_data[3] ))

YKScan_slicer_buf = np.append(YKScan_slicer_buf, [slice_buf.flatten('c')], axis=0)          # append new data
"""

#----------------------------------------------------------------------------------
# number=100:
#       old_algorithm = 0.8298889470024733
#       new_algorithm = 0.018701716006034985
# number=500:
#       old_algorithm = 16.409538741005235
#       new_algorithm = 0.20408151199808344
#----------------------------------------------------------------------------------
old_time = timeit.timeit(stmt=old_algorithm, setup=setup, number=100, globals=globals())
new_time = timeit.timeit(stmt=new_algorithm, setup=setup, number=100, globals=globals())
print(f"old_algorithm = {old_time}\nnew_algorithm = {new_time}\n\n")


#----------------------------------------------------------------------------------
exec(setup)
exec(old_algorithm)
print(f"OLD Shape:{YKScan_slicer_buf.shape}  array: {YKScan_slicer_buf[:,0:10]}\n\t{YKScan_slicer_buf[:,100:110]}\n")

exec(setup)
exec(new_algorithm)
print(f"NEW Shape:{YKScan_slicer_buf.shape}  array: {YKScan_slicer_buf[:,0:10]}\n\t{YKScan_slicer_buf[:,100:110]}\n")

