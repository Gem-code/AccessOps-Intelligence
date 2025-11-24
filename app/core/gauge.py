import matplotlib.pyplot as plt
from math import pi

def draw_small_gauge(score):
    fig, ax = plt.subplots(figsize=(2.4, 1.2), subplot_kw={'projection':'polar'})
    fig.patch.set_facecolor('none')

    ax.set_theta_offset(pi)
    ax.set_theta_direction(-1)

    # Color zones
    for start, end, color in [(0,30,"#22C55E"),(30,60,"#F59E0B"),(60,100,"#EF4444")]:
        ax.barh(1, (end-start)/100*pi, left=start/100*pi, height=1.2, color=color)

    # Needle
    angle = (score / 100) * pi
    ax.arrow(angle, 0, 0, 1, width=0.03, head_width=0.08, color="black")

    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.set_ylim(-1, 1.2)
    plt.tight_layout()

    return fig
