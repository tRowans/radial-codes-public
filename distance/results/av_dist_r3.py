import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def get_averages(dataset,s):
    dists = []
    ns = []
    for i in range(100):
        with open("{}/r3_s{}_100/code_{}.out".format(dataset,s,i+1),'r') as f:
            lines = f.readlines()
            d1 = int(lines[2].strip())
            d2 = int(lines[4].strip())
            if d1 <= d2:
                dists.append(d1)
                start = lines[1].find('=')
                end = lines[1].find(' ')
                ns.append(float(lines[1][start+1:end]))
            else:
                dists.append(d2)
                start = lines[3].find('=')
                end = lines[3].find(' ')
                ns.append(float(lines[3][start+1:end]))
    av_dist = sum(dists)/len(dists)
    stderr = np.std(np.array(dists))/np.sqrt(100)
    av_n = sum(ns)/len(ns)
    return av_dist, stderr, av_n

def linear_model(x, a0, a1):
    return a0 + a1*x

if __name__ == "__main__":
    
    s_vals = np.array([3,5,7,11,13,17])
    datasets = ['r3_absame_nodiffcheck', 'r3_abdiff_nodiffcheck']
    #datasets = ['r3_absame_nodiffcheck', 'r3_abdiff_nodiffcheck', 'r3_abdiff_diffcheck']
    all_av_dists = []
    all_stderrs = []
    all_av_ns = []
    fits = []
    for dataset in datasets:
        av_dists = []
        stderrs = []
        av_ns = []

        for s in s_vals:
            av_dist, stderr, av_n = get_averages(dataset,s)
            av_dists.append(av_dist)
            stderrs.append(stderr)
            av_ns.append(av_n)
        all_av_dists.append(av_dists)
        all_stderrs.append(stderrs)
        all_av_ns.append(av_ns)

        popt, pcov = curve_fit(linear_model, s_vals[2:], av_dists[2:])
        fits.append(popt)

    all_f_probs = [[1/np.exp(i) for i in ns] for ns in all_av_ns]

    colours = ['C0','C1','C2']
    labels = [r'$H_1 = H_2$', r'$H_1 \neq H_2$']

    plt.rc('axes', labelsize=14)
    plt.rc('xtick', labelsize=12)
    plt.rc('ytick', labelsize=12)
    plt.rc('legend', fontsize=14)

    for i in range(len(datasets)):
        plt.errorbar(s_vals, all_av_dists[i], all_stderrs[i], linestyle='', marker='o', color=colours[i])
        plt.plot(s_vals[2:],linear_model(s_vals[2:],fits[i][0],fits[i][1]), color=colours[i], label=labels[i])
        #for j in range(len(s_vals)):
        #    plt.text(s_vals[j], all_av_dists[i][j]-1, '{:.2e}'.format(all_f_probs[i][j]),horizontalalignment='center')
    plt.xticks(s_vals)
    plt.xlabel(r"$s$")
    plt.ylabel("average distance")
    plt.legend()
    plt.savefig('av_dist_r3.pdf', format='pdf')
    plt.show()
