import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import dates, patches
import matplotlib as mpl


# Créer le dossier 'output' s'il n'existe pas déjà
if not os.path.exists('python/output'):
    os.makedirs('python/output')

def plotCDF():
    font = {'family': 'verdana',
            'weight': 'bold',
            'size': 10}
    plt.rc('font', **font)

    data = pd.read_csv('python/input/result.csv', parse_dates=['@timestamp'], date_parser=lambda x: pd.to_datetime(x, format='%b %d, %Y @ %H:%M:%S.%f'))
    data = data.iloc[::-1].reset_index()
    data['message'] = data['message'].str.extract('latency is (\\d+)')
    data['message'] = data['message'].astype(float)
    data['@timestamp'] = pd.to_datetime(data['@timestamp'])
    fig, ax = plt.subplots()
    ax.set_xlabel("Latency (ms)", **font)
    ax.set_ylabel("CDF", **font)
    data['message'].hist(cumulative=True, density=1, bins=1000, alpha=1, grid=False,
                                        linewidth=1.5, histtype='step', fill=None, legend=True)
    fix_hist_step_vertical_line_at_end(ax)

    plt.legend(["Heartbeat = 3s", "heartbeat=500ms"])

    # Supprimer l'ancienne image s'il existe
    if os.path.exists('python/output/result_cdf.png'):
        os.remove('python/output/result_cdf.png')

    # Enregistrer le plot comme un fichier PNG dans le dossier 'output'
    plt.savefig('python/output/result_cdf.png')
    plt.close()


def fix_hist_step_vertical_line_at_end(ax):
    axpolygons = [poly for poly in ax.get_children() if isinstance(poly, mpl.patches.Polygon)]
    for poly in axpolygons:
        poly.set_xy(poly.get_xy()[:-1])


if __name__ == '__main__':
    plotCDF()
