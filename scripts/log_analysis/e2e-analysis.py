import sys
import json
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates

X_SMALL_SIZE = 10
SMALL_SIZE = 14
MEDIUM_SIZE = 20
BIGGER_SIZE = 26

plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=SMALL_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 e2e-analysis.py <e2e-analyzer.json>")
        sys.exit(1)

    e2e_file_path = sys.argv[1]

    # Charger le fichier JSON
    with open(e2e_file_path, 'r') as f:
        data = json.load(f)

    # Extraire les données
    trackers = data['data']

    # Préparer les données pour les graphiques
    finish_times = []  # Timestamp de fin (dernier événement)
    durations = []     # Durée end-to-end (ms)

    for tracker in trackers:
        if not tracker['events']:
            continue

        # Convertir les timestamps en objets datetime
        timestamps = [datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00'))
                      for e in tracker['events']]

        # Calculer la durée (utiliser endToEndDurationMs si présent, sinon calculer)
        duration = tracker.get('endToEndDurationMs', 0)
        if duration == 0 and len(timestamps) > 1:
            duration = int((max(timestamps) - min(timestamps)).total_seconds() * 1000)

        finish_times.append(max(timestamps))
        durations.append(duration)

    # Créer la figure avec 2 sous-graphiques
    plt.figure(figsize=(16, 6))
    
    color = '#5C669F'

    # --- GRAPHIQUE 1 : Durée end-to-end en fonction du timestamp de fin ---
    plt.scatter(finish_times, durations, alpha=0.3, s=5, color=color)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xlabel('Heure de fin')
    plt.ylabel('Durée end-to-end (ms)')
    plt.title('Durée end-to-end par événement')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)

    nb_events = data["metadata"]["count"]

    text_str_replicas = f"total events: {nb_events}"
    plt.text(0.99, 0.98, text_str_replicas, transform=plt.axes().transAxes,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8), fontsize=13)
    frame1 = plt.gca()
    frame1.axes.get_xaxis().set_visible(False)
    frame1.axes.get_yaxis().set_visible(False)


    plt.savefig('e2e_latency.png', dpi=300, bbox_inches='tight', transparent=True)
    plt.close()

    plt.figure(figsize=(16, 6))
    # --- GRAPHIQUE 2 : Courbe cumulative ---
    sorted_durations = np.sort(durations)
    cumulative_counts = np.arange(1, len(sorted_durations) + 1)
    plt.plot(sorted_durations, cumulative_counts)
    plt.xlabel('Durée end-to-end (ms)')
    plt.ylabel('Nombre cumulé d\'événements')
    plt.title('Courbe cumulative des événements par durée')
    plt.grid(True, alpha=0.3)

    # Ajouter les percentiles
    if len(sorted_durations) > 0:
        for percentile in [50, 90, 95, 99]:
            p = np.percentile(sorted_durations, percentile)
            plt.axvline(p, color='r', linestyle='--', alpha=0.7,
                       label=f'{percentile}th percentile')
        plt.legend()

    plt.savefig('e2e_percentile_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()