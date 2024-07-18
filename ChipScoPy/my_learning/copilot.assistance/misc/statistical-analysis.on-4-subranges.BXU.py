"""
I have a numpy array of 8000 samples, whose values range is (0, 100), i.e., between 0 and 100. I want to calculate the statistical analysis of samples on 4 separate values range.
That is, 1st statistical analysis on values range is (0, 30).
That is, 2nd statistical analysis on values range is (30, 50).
That is, 3rd statistical analysis on values range is (50, 70).
That is, 4th statistical analysis on values range is (70, 100).
Can you give me the complete Python code for this?
"""

"""
[normal distribution calculator](https://homepage.divms.uiowa.edu/~mbognar/applets/normal.html)
[reference picture](https://www.researchgate.net/figure/a-Received-PAM4-signal-and-b-PAM4-signal-at-the-mid-stage-DSP_fig4_270914570)
"""

import sys, os
import matplotlib.pyplot as plt
import numpy as np

#---------------------------------------------------------------------------------------------------
# Bernard's ChipScoPy's design: YKScan_slicer_buf
#---------------------------------------------------------------------------------------------------
def data_source_from_ramdom():
    # Generate your numpy array (assuming you already have it)
    # Replace 'your_array' with your actual data
    your_array = np.random.randint(0, 100, size=8000)

    peak_positions = [20, 40, 60, 80]
    YKSCAN_SLICER_SIZE = 8000
    std_devs = [1.5, 2.2, 1.2, 3.3]
    your_array = np.zeros((0, YKSCAN_SLICER_SIZE))

    print(f"peak_positions = {peak_positions}\nstd_devs = {std_devs}\n")

    slice_data = []
    for i in range(len(peak_positions)):
        peak_pos = peak_positions[i]
        std_dev = std_devs[i]
        slice_data.append( np.random.normal(loc=peak_pos, scale=std_dev, size=int(YKSCAN_SLICER_SIZE/4)) )
    slice_buf = np.column_stack(( slice_data[0], slice_data[1], slice_data[2], slice_data[3] ))

    return np.append(your_array, [slice_buf.flatten('c')], axis=0)          # append new data


#---------------------------------------------------------------------------------------------------
boundary_1 = 30
boundary_2 = 70
if len(sys.argv) > 1:
    fname = sys.argv[1]
    if len(sys.argv) > 3:
        boundary_1 = int(sys.argv[2])
        boundary_2 = int(sys.argv[3])
else:
    fname = 'Sample_YK-Slicer_Files.Cable-2m.txt'

if os.path.isfile(fname): your_array = np.loadtxt(fname)
else:                     your_array = data_source_from_ramdom()

#---------------------------------------------------------------------------------------------------
# Split the array into subarrays based on value ranges
subarray_1 = your_array[(your_array >= 0)          & (your_array < boundary_1)]
subarray_2 = your_array[(your_array >= boundary_1) & (your_array < 50)]
subarray_3 = your_array[(your_array >= 50)         & (your_array < boundary_2)]
subarray_4 = your_array[(your_array >= boundary_2) & (your_array <= 100)]

# Calculate descriptive statistics for each subarray
def analyze_subarray(subarray):
    return {
        'mean': np.mean(subarray),
        'std': np.std(subarray),
        'min': np.min(subarray),
        'max': np.max(subarray)
    }

stats_1 = analyze_subarray(subarray_1)
stats_2 = analyze_subarray(subarray_2)
stats_3 = analyze_subarray(subarray_3)
stats_4 = analyze_subarray(subarray_4)

# Print the results
print(f"Statistics for (0, {boundary_1}):", stats_1)
print(f"Statistics for ({boundary_1}, 50):", stats_2)
print(f"Statistics for (50, {boundary_2}):", stats_3)
print(f"Statistics for ({boundary_2}, 100):", stats_4)


"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
From the above calculation, I want to further add code to predict error probability of the future coming data with same statistical behavior as the previous data samples.
Specifically saying, for the above 1st to 4th value ranges, we get stats_1 to stats_4 statistical values respectively.
Based on these 4 pairs of (mean, std), we can get 4 theoritical normal distribution formula.
Can you give me the further "error" probability calculation python code? Where the "error" means for 1 statistical range, say in stats_1, with its (mean, std), what's the probability of its value will go cross to the stats_2's value range, and then be defined as "error".

Please give me the complete Python code for this, based on the code above.


<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
Certainly! To calculate the probability of an “error” (i.e., a value crossing from one statistical range to another), we can use the cumulative distribution function (CDF) of the normal distribution. Let’s break down the steps:

1. Calculate the CDF for each statistical range:
    * For each pair of (mean, std) (e.g., stats_1, stats_2, etc.), compute the CDF at the boundary values of the adjacent range.
    * The CDF represents the probability that a random variable from the distribution is less than or equal to a given value.

2. Subtract the CDF values:
    * Subtract the CDF value at the lower boundary of the next range from the CDF value at the upper boundary of the current range.
    * This difference represents the probability of crossing from one range to another.

Here’s the Python code to achieve this based on your existing code:
"""
import scipy.stats as stats

# Assuming you have stats_1, stats_2, stats_3, and stats_4
# Replace these with your actual statistical values

# Calculate the CDF values for each range
cdf_1_upper = stats.norm.cdf(stats_1['max'], loc=stats_1['mean'], scale=stats_1['std'])
cdf_2_lower = stats.norm.cdf(stats_2['min'], loc=stats_2['mean'], scale=stats_2['std'])
cdf_2_upper = stats.norm.cdf(stats_2['max'], loc=stats_2['mean'], scale=stats_2['std'])
cdf_3_lower = stats.norm.cdf(stats_3['min'], loc=stats_3['mean'], scale=stats_3['std'])
cdf_3_upper = stats.norm.cdf(stats_3['max'], loc=stats_3['mean'], scale=stats_3['std'])
cdf_4_lower = stats.norm.cdf(stats_4['min'], loc=stats_4['mean'], scale=stats_4['std'])

# Calculate the error probabilities
error_1_to_2 = cdf_1_upper - cdf_2_lower
error_2_to_3 = cdf_2_upper - cdf_3_lower
error_3_to_4 = cdf_3_upper - cdf_4_lower

print("\n")
print("Error probability (stats_1 to stats_2):", error_1_to_2)
print("Error probability (stats_2 to stats_3):", error_2_to_3)
print("Error probability (stats_3 to stats_4):", error_3_to_4)


#---------------------------------------------------------------------------------------------------
# Bernard's Error prediction
#---------------------------------------------------------------------------------------------------
boundary_12 = (stats_1['mean'] + stats_2['mean']) / 2
boundary_23 = (stats_2['mean'] + stats_3['mean']) / 2
boundary_34 = (stats_3['mean'] + stats_4['mean']) / 2

err_1_to_2 = 1 - stats.norm.cdf(boundary_12, loc=stats_1['mean'], scale=stats_1['std'])
err_2_to_1 = stats.norm.cdf(    boundary_12, loc=stats_2['mean'], scale=stats_2['std'])

err_2_to_3 = 1 - stats.norm.cdf(boundary_23, loc=stats_2['mean'], scale=stats_2['std'])
err_3_to_2 = stats.norm.cdf(    boundary_23, loc=stats_3['mean'], scale=stats_3['std'])

err_3_to_4 = 1 - stats.norm.cdf(boundary_34, loc=stats_3['mean'], scale=stats_3['std'])
err_4_to_3 = stats.norm.cdf(    boundary_34, loc=stats_4['mean'], scale=stats_4['std'])

total_error = err_1_to_2 + err_2_to_1 + err_2_to_3 + err_3_to_2 + err_3_to_4 + err_4_to_3

print("\n")
print(f"Bernard Error probability  err_1_to_2: {err_1_to_2:.3e}")
print(f"Bernard Error probability  err_2_to_1: {err_2_to_1:.3e}")
                                        
print(f"Bernard Error probability  err_2_to_3: {err_2_to_3:.3e}")
print(f"Bernard Error probability  err_3_to_2: {err_3_to_2:.3e}")
                                        
print(f"Bernard Error probability  err_3_to_4: {err_3_to_4:.3e}")
print(f"Bernard Error probability  err_4_to_3: {err_4_to_3:.3e}")

print(f"Bernard Error probability  total: {total_error:.3e}")

#---------------------------------------------------------------------------------------------------
def plot_data_graph(loaded_data):
    # Create scatter plot
    plt.figure(figsize=(8, 6))
    plt.scatter(range(len(loaded_data)), loaded_data, s=5, color='b', alpha=0.5)
    plt.title('Scatter Plot of Normal Distribution Data')
    plt.xlabel('Index')
    plt.ylabel('Value')
    plt.grid(True)
    plt.show()

    # Create histogram
    plt.figure(figsize=(8, 6))
    plt.hist(loaded_data, bins=100, color='g', edgecolor='black', alpha=0.7)
    plt.title('Histogram of Normal Distribution Data')
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.grid(True)
    plt.show()

plot_data_graph(your_array)
#---------------------------------------------------------------------------------------------------
