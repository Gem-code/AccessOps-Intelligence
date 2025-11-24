import matplotlib.pyplot as plt
from math import pi

def draw_risk_gauge(score: int):
    fig, ax = plt.subplots(figsize=(4, 2.4), subplot_kw={'projection': 'polar'})
    fig.patch.set_facecolor('none')

    ax.set_theta_offset(pi)
    ax.set_theta_direction(-1)

    # Color bands
    bands = [(0, 30, "#22C55E"), (30, 60, "#F59E0B"), (60, 100, "#EF4444")]
    for start, end, color in bands:
        ax.barh(1, (end-start)/100 * pi, left=start/100*pi, height=1.5, color=color)

    needle = score/100 * pi
    ax.arrow(needle, 0, 0, 1.25, width=0.03, head_width=0.1, color="black")

    ax.text(0, -0.45, f"{score}", ha='center', fontsize=20, fontweight='bold')

    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.set_ylim(-1.2, 1.5)

    return fig
