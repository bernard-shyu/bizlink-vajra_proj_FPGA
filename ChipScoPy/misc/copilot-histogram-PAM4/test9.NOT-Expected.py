"""
<<<
in numpy histogram, the data pattern will give 4 peaks of mountain like distribution with 3 valeys in between. How to find the peak position? How to get the spead (or width) of these 4 data clusters?

>>>
Certainly! Let’s break down the steps to find the peak positions and widths of the clusters in a NumPy histogram:

Compute the Histogram:
    First, create a histogram of your data using numpy.histogram(). This function computes the histogram of a dataset based on the flattened array.
	You can specify the number of bins or provide custom bin edges. If you don’t provide any, it defaults to 10 bins.
    The result will be an array of histogram values and an array of bin edges.

Peak Positions:
    To find the peak positions (i.e., the centers of the clusters), you can use the scipy.signal.find_peaks() function.
    This function identifies local maxima in the histogram.
    The returned peaks correspond to the bin indices where the peaks occur.

Peak Widths:
    To calculate the width of each peak, you can use the scipy.signal.peak_widths() function.
    This function estimates the width of each peak based on its prominence and relative height.
    The result will give you the half-widths of the peaks (i.e., the distance from the peak center to where the histogram value drops to half of its peak value).

Here’s an example of how you can apply these steps:
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, peak_widths

# Generate some example data (replace with your actual data)
data = np.random.randn(1000)  # Replace with your data

# Compute the histogram
hist, bin_edges = np.histogram(data, bins='auto')

# Find peak positions
peaks, _ = find_peaks(hist)

# Calculate peak widths
results_half = peak_widths(hist, peaks, rel_height=0.5)
half_widths = results_half[0] * (bin_edges[1] - bin_edges[0])

# Plot the histogram
plt.hist(data, bins='auto', alpha=0.7, color='blue')
plt.xlabel('Value')
plt.ylabel('Frequency')
plt.title('Histogram with Peak Positions and Widths')
plt.axvline(bin_edges[peaks[0]], color='red', linestyle='--', label='Peak 1')
plt.axvline(bin_edges[peaks[1]], color='green', linestyle='--', label='Peak 2')
plt.axvline(bin_edges[peaks[2]], color='purple', linestyle='--', label='Peak 3')
plt.axvline(bin_edges[peaks[3]], color='orange', linestyle='--', label='Peak 4')
plt.legend()
plt.show()

print(f"Peak positions (bin centers): {bin_edges[peaks]}")
print(f"Peak widths (half-widths): {half_widths}")

