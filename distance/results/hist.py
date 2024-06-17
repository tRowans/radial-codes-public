import sys
import numpy as np
import matplotlib.pyplot as plt
import scipy.interpolate as sint

def read_dists(path,n_codes):
    dists = []
    fprobs = []
    for i in range(n_codes):
        with open("{}/code_{}.out".format(path,i+1),'r') as f:
            lines = f.readlines()
            d1 = int(lines[2].strip())
            d2 = int(lines[4].strip())
            if d1 <= d2:
                dists.append(d1)
                start = lines[1].find('=')
                end = lines[1].find(' ')
                fprobs.append(np.exp(-1*float(lines[1][start+1:end])))
            else:
                dists.append(d2)
                start = lines[3].find('=')
                end = lines[3].find(' ')
                fprobs.append(np.exp(-1*float(lines[3][start+1:end])))
    return dists, fprobs

def average_fprobs(fprobs,bins,dists):
    av_fprobs = []
    for i in range(len(bins)-1):
        locs = [j for j in range(len(dists)) if dists[j] == (bins[i]+0.5)]
        if len(locs) != 0:
            av_fprobs.append(sum([fprobs[j] for j in locs])/len(locs))
        else:
            av_fprobs.append(1)
    return av_fprobs

def interpolate(bins,counts):
    x = np.array([[bins[i]] for i in np.nonzero(counts)[0]]) + 0.5
    y = np.array([[counts[i]] for i in np.nonzero(counts)[0]])
    if len(x) == 1:
        left = x[0][0] - 0.5
        right = x[0][0] + 0.5
        x = np.array([[left],[x[0][0]],[right]])
        y = np.array([[0],[y[0][0]],[0]])
    x_inter = np.linspace(x[0][0],x[-1][0],100)[np.newaxis].T
    y_inter = sint.RBFInterpolator(x,y)(x_inter)
    return x_inter, y_inter

if __name__ == "__main__":

    dataset = sys.argv[1]
    r = dataset[1]
    s_vals = []
    for i in range(2,len(sys.argv)):
        s_vals.append(sys.argv[i])

    all_data = [read_dists(f"{dataset}/r{r}_s{s}_100",100) for s in s_vals]
    all_dists = [i for i,j in all_data]
    all_fprobs = [j for i,j in all_data]

    #remove outliers for nice plot
    #x1 = all_dists[0].index(min(all_dists[0]))
    #all_dists[0].pop(x1)
    #all_ns[0].pop(x1)
    #x2 = all_dists[-1].index(max(all_dists[-1]))
    #all_dists[-1].pop(x2)
    #all_ns[-1].pop(x2)

    min_dist = min(sum(all_dists,[]))
    max_dist = max(sum(all_dists,[]))

    bins = np.arange(min_dist-0.5,max_dist+1.5)
    all_counts = [np.histogram(dists,bins=bins)[0] for dists in all_dists]
    all_av_fprobs = [average_fprobs(all_fprobs[i],bins,all_dists[i]) for i in range(len(s_vals))]

    colours = ['C0','C1','C2','C4','C5','C6','C7','C8','C9']
    darker_colours = ['#175987','#ca5f00','#217821','#704299','#694038','#d42fa2','#5f5f5f','#8d8e1a','17becf']

    plt.rc('axes', labelsize=14)
    plt.rc('xtick', labelsize=12)
    plt.rc('ytick', labelsize=12)
    plt.rc('legend', fontsize=14)

    inter_data = [interpolate(bins,counts) for counts in all_counts]
    for i in range(len(s_vals)):
        plt.hist(all_dists[i],bins=bins,label='s={}'.format(s_vals[i]),color=colours[i])
        plt.plot(inter_data[i][0].T[0],inter_data[i][1].T[0],color=darker_colours[i])
        for j in range(len(all_counts[i])):
            if all_av_fprobs[i][j] != 1:
                plt.text(bins[j]+0.5,all_counts[i][j]+1,'{:.2e}'.format(all_av_fprobs[i][j]),horizontalalignment='center')
    plt.xlabel('distance')
    plt.ylabel('#codes')
    plt.ylim(0,None)
    plt.legend()
    plt.savefig(f"{dataset}_hist.pdf", format='pdf')
    plt.show()
