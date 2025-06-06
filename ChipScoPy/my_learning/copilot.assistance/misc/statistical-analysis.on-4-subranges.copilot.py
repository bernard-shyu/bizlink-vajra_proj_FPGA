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

import numpy as np

# Generate your numpy array (assuming you already have it)
# Replace 'your_array' with your actual data
your_array = np.random.randint(0, 100, size=8000)

# Split the array into subarrays based on value ranges
subarray_1 = your_array[(your_array >= 0) & (your_array < 30)]
subarray_2 = your_array[(your_array >= 30) & (your_array < 50)]
subarray_3 = your_array[(your_array >= 50) & (your_array < 70)]
subarray_4 = your_array[(your_array >= 70) & (your_array <= 100)]

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
print("Statistics for (0, 30):", stats_1)
print("Statistics for (30, 50):", stats_2)
print("Statistics for (50, 70):", stats_3)
print("Statistics for (70, 100):", stats_4)


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

print("Error probability (stats_1 to stats_2):", error_1_to_2)
print("Error probability (stats_2 to stats_3):", error_2_to_3)
print("Error probability (stats_3 to stats_4):", error_3_to_4)

