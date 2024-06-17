import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def get_averages(dataset,r,s):
    dists = []
    ns = []
    for i in range(100):
        with open("{}/r{}_s{}_100/code_{}.out".format(dataset,r,s,i+1),'r') as f:
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

def process_data(r,s_vals,datasets,all_av_dists,all_stderrs,all_av_ns,fits):
    for dataset in datasets:
        av_dists = []
        stderrs = []
        av_ns = []

        for s in s_vals:
            av_dist, stderr, av_n = get_averages(dataset,r,s)
            av_dists.append(av_dist)
            stderrs.append(stderr)
            av_ns.append(av_n)
        all_av_dists.append(av_dists)
        all_stderrs.append(stderrs)
        all_av_ns.append(av_ns)

        popt, pcov = curve_fit(linear_model, s_vals, av_dists)
        fits.append(popt)


if __name__ == "__main__":
    
    s_vals_r3 = np.array([3,5,7,11,13,17])
    datasets_r3 = ['r3_absame_nodiffcheck', 'r3_abdiff_nodiffcheck']
    #datasets = ['r3_absame_nodiffcheck', 'r3_abdiff_nodiffcheck', 'r3_abdiff_diffcheck']
    all_av_dists_r3 = []
    all_stderrs_r3 = []
    all_av_ns_r3 = []
    fits_r3 = []

    process_data(3,s_vals_r3,datasets_r3,all_av_dists_r3,all_stderrs_r3,all_av_ns_r3,fits_r3)
    all_f_probs_r3 = [[1/np.exp(i) for i in ns] for ns in all_av_ns_r3]

    s_vals_r4 = np.array([5,7,11,13,17,23])
    datasets_r4 = ['r4_absame_nodiffcheck', 'r4_abdiff_nodiffcheck']
    all_av_dists_r4 = []
    all_stderrs_r4 = []
    all_av_ns_r4 = []
    fits_r4 = []

    process_data(4,s_vals_r4,datasets_r4,all_av_dists_r4,all_stderrs_r4,all_av_ns_r4,fits_r4)
    all_f_probs_r4 = [[1/np.exp(i) for i in ns] for ns in all_av_ns_r4]

    colours = ['C0','C1','C2']
    labels = [r'$H_1 = H_2$', r'$H_1 \neq H_2$']

    fig, (ax1,ax2) = plt.subplots(1,2)
    for i in range(2):
        ax1.errorbar(s_vals_r3, all_av_dists_r3[i], all_stderrs_r3[i], linestyle='', marker='o', color=colours[i])
        ax1.plot(s_vals_r3, linear_model(s_vals_r3,fits_r3[i][0],fits_r3[i][1]), color=colours[i], label=labels[i])
        ax1.set_xticks(s_vals_r3)
        ax1.set_xlabel(r'$s$')
        ax1.set_ylabel("average distance")
        ax1.legend()
    for i in range(2):
        ax2.errorbar(s_vals_r4, all_av_dists_r4[i], all_stderrs_r4[i], linestyle='', marker='o', color=colours[i])
        ax2.plot(s_vals_r4, linear_model(s_vals_r4,fits_r4[i][0],fits_r4[i][1]), color=colours[i], label=labels[i])
        ax2.set_xticks(s_vals_r4)
        ax2.set_xlabel(r'$s$')
        ax2.legend()
    plt.savefig('av_dist_both.pdf', format='pdf', bbox_inches='tight')
    plt.show()
