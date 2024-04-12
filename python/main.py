from datetime import datetime
from typing import Dict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import dates
import os

# Créer le dossier 'output' s'il n'existe pas déjà
if not os.path.exists('python/output'):
    os.makedirs('python/output')

def readPanda():
    font = {'family': 'verdana',
            'weight': 'bold',
            'size': 8}
    plt.rc('font', **font)

    ## change this to your csv file.
    data = pd.read_csv('python/input/result.csv', parse_dates=['@timestamp'], date_parser=lambda x: pd.to_datetime(x, format='%b %d, %Y @ %H:%M:%S.%f'))

    data = data.iloc[::-1].reset_index()
    print(data['message'])
    print(data['kubernetes.pod.name'])
    data['message'] = data['message'].str.extract('latency is (\\d+)')
    print(data['message'])
    data['message'] = data['message'].astype(float)

    print(data['message'])

    # Calculer la différence de temps par rapport à la première observation
    start_time = data['@timestamp'].min()
    data['time_diff'] = (data['@timestamp'] - start_time).dt.total_seconds()

    fig, ax = plt.subplots()
    plt.xticks(rotation=45, ha='right')
    your_counter = len(data[data['message'] > 500])
    print(your_counter)

    # Votre code existant pour le traçage du graphique
    ax.set_xlabel("Time (sec)", **font)
    ax.set_ylabel("latency (ms)", **font)
    ax.plot(data['time_diff'], data['message'])

    # Supprimer l'ancienne image s'il existe
    if os.path.exists('python/output/result_read_panda_plot.png'):
        os.remove('python/output/result_read_panda_plot.png')

    # Enregistrer le plot comme un fichier PNG dans le dossier 'output'
    plt.savefig('python/output/result_read_panda_plot.png')
    plt.close()


def getReplicasMinutes():
    data = pd.read_csv('python/input/result.csv', parse_dates=['@timestamp'], date_parser=lambda x: pd.to_datetime(x, format='%b %d, %Y @ %H:%M:%S.%f'))

    u = data['kubernetes.pod.name'].unique()
    print(u)
    totalseconds = 0
    for i in range(len(u)):
        print(u[i])
        h = data[data['kubernetes.pod.name'] == u[i]].index[-1]
        m = data[data['kubernetes.pod.name'] == u[i]].index[0]

        datem = data['@timestamp'][m]
        dateh = data['@timestamp'][h]
        print(datem)
        print(dateh)

        t = (datem - dateh).seconds

        print()
        totalseconds += t

    # Écriture du résultat dans un fichier texte dans le dossier 'output'
    with open('python/output/result_replicas_minutes.txt', 'w') as f:
        f.write(str(totalseconds / 60))


def plotByPod():
    font = {'family': 'verdana',
            'weight': 'bold',
            'size': 8}
    plt.rc('font', **font)

    data = pd.read_csv('python/input/result.csv', parse_dates=['@timestamp'], date_parser=lambda x: pd.to_datetime(x, format='%b %d, %Y @ %H:%M:%S.%f'))

    data = data.iloc[::-1].reset_index()

    print(data['message'])
    print(data['kubernetes.pod.name'])
    data['message'] = data['message'].str.extract('latency is (\\d+)')
    data['message'] = data['message'].astype(float)

    groups = data.groupby('kubernetes.pod.name')

    num_of_groups = len(groups.groups)
    print(num_of_groups)

    dfs = []

    fig, axs = plt.subplots(num_of_groups, 1, figsize=(30, 20), facecolor='w', edgecolor='k', sharex='all')
    fig.subplots_adjust(hspace=.5, wspace=.001)
    axs = axs if isinstance(axs, np.ndarray) else [axs]

    for ax in axs:
        ax.xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))
        ax.tick_params(axis='x', rotation=45)

    for name, group in groups:
        dfs.append(group)

    for i in range(0, num_of_groups):
        axs[i].title.set_text("")
        axs[i].plot(dfs[i]['@timestamp'], (dfs[i]['message']))
        axs[i].set_ylabel("Consumer " + str(i), **font)

    # Supprimer l'ancienne image s'il existe
    if os.path.exists('python/output/result_plot_by_pod.png'):
        os.remove('python/output/result_plot_by_pod.png')

    # Enregistrer le plot comme un fichier PNG dans le dossier 'output'
    plt.savefig('python/output/result_plot_by_pod.png')
    plt.close()

    print("------------------------")
    print(dfs[0])


if __name__ == '__main__':
    readPanda()
    getReplicasMinutes()
    plotByPod()
