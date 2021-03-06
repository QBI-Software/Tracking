#!/usr/bin/python
#Custom Tracker plots
import numpy as np
import matplotlib.pyplot as plt




if __name__ == "__main__":
    x = np.arange(0, 5, 0.1);
    y = np.sin(x)
    plt.figure(1)                # the first figure

    plt.subplot(211)             # the first subplot in the first figure
    plt.plot([1,2,3])
    plt.subplot(212)             # the second subplot in the first figure
    plt.plot([4,5,6])


    plt.figure(2)                # a second figure
    plt.plot([4,5,6])            # creates a subplot(111) by default

    plt.figure(1)                # figure 1 current; subplot(212) still current
    plt.subplot(211)             # make subplot(211) in figure1 current
    plt.title('Easy as 1,2,3')   # subplot 211 title

    plt.show()