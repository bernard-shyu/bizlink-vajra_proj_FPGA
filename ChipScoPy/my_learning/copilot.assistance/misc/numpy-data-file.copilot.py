"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
Can you give me python example codes of the below functions?
1. Use numpy to generate a normal distribution data of 8000 entries, and output the result into a disk file.
2. Another python to read from this disk file to get the data, and do 2 matplotlib plots of scatter and histogram on the data. Also perform statistical analysis on the data, and put the result into GUI label.


<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
Generating Normal Distribution Data with Numpy: You can use numpy.random.normal() to generate a normal distribution with a specified mean and standard deviation.
Here’s an example code snippet to create 8000 entries of normally distributed data and save it to a file:

#-------------------------------------------------------------------------------------------------
```
import numpy as np

# Parameters for the normal distribution
mean = 0  # Mean (center)
std_dev = 1  # Standard deviation

# Generate 8000 samples from the normal distribution
data = np.random.normal(mean, std_dev, 8000)

# Save the data to a text file (one value per line)
np.savetxt('YK_SlicerData_Files.Cable-B1.56Gpbs.2024-06201404.txt', data)
```
#-------------------------------------------------------------------------------------------------

Reading Data from the Disk File and Creating Matplotlib Plots: Now let’s read the data from the file and create scatter and histogram plots using Matplotlib.
Additionally, we’ll calculate some basic statistical measures:
"""

import matplotlib.pyplot as plt
import numpy as np

# Read data from the file
loaded_data = np.loadtxt('YK_SlicerData_Files.Cable-B1.56Gpbs.2024-06201404.txt')

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
plt.hist(loaded_data, bins=30, color='g', edgecolor='black', alpha=0.7)
plt.title('Histogram of Normal Distribution Data')
plt.xlabel('Value')
plt.ylabel('Frequency')
plt.grid(True)
plt.show()

# Calculate statistical measures
mean_value = np.mean(loaded_data)
std_dev_value = np.std(loaded_data, ddof=1)  # Sample standard deviation

# Display the results (you can integrate this with your GUI label)
print(f"Mean: {mean_value:.4f}")
print(f"Standard Deviation: {std_dev_value:.4f}")

