import pywt
import matplotlib.pyplot as plt
import numpy as np

"""
Some useful wavelet function from the website:
    http://ataspinar.com/2018/12/21/a-guide-for-using-the-wavelet-transform-in-machine-learning/
"""

def plot_wavelet(time, signal, scales,
                 waveletname = 'db4',
                 cmap = plt.cm.seismic,
                 title = 'Wavelet Transform (Power Spectrum) of signal',
                 ylabel = 'Period (years)',
                 xlabel = 'Time'):

    dt = time[1] - time[0]
    [coefficients, frequencies] = pywt.dwt(signal, waveletname, scales)
    power = (abs(coefficients)) ** 2
    period = 1. / frequencies
    print(coefficients.shape)
    print(frequencies.shape)
    print(period.shape)
    levels = [0.0625, 0.125, 0.25, 0.5, 1, 2, 4, 8]
    contourlevels = np.log2(levels)

    fig, ax = plt.subplots(figsize=(15, 10))
    print(f'time {time.shape}')
    print(f'period {period.shape}')
    print(f'power {power.shape}')
    im = ax.contourf(time, np.log2(period), np.log2(power), contourlevels, extend='both',cmap=cmap)

    ax.set_title(title, fontsize=20)
    ax.set_ylabel(ylabel, fontsize=18)
    ax.set_xlabel(xlabel, fontsize=18)

    yticks = 2**np.arange(np.ceil(np.log2(period.min())), np.ceil(np.log2(period.max())))
    ax.set_yticks(np.log2(yticks))
    ax.set_yticklabels(yticks)
    ax.invert_yaxis()
    ylim = ax.get_ylim()
    ax.set_ylim(ylim[0], -1)

def lowpassfilter(signal, threshold = 0.63, wavelet="db4"):
    """ Deconstruct the series using a waveform. Apply a threshold filter
        then reconstruct
    """
    threshold = threshold*np.nanmax(signal)
    coeff = pywt.wavedec(signal, wavelet, mode="per" )
    coeff[1:] = (pywt.threshold(i, value=threshold, mode="soft" ) for i in coeff[1:])
    reconstructed_signal = pywt.waverec(coeff, wavelet, mode="per" )
    return reconstructed_signal
