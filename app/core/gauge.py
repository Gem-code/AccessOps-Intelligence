import matplotlib.pyplot as plt
from math import pi

def draw_small_gauge(score):
    fig, ax = plt.subplots(figsize=(2.2, 1.2), subplot_kw={'projection': 'polar'})

    # Remove all whitespace around the gauge
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    fig.patch.set_facecolor('none')
    ax.set_theta_offset(pi)
    ax.set_theta_direction(-1)

    for start, end, color in [(0,30,"#22C55E"), (30,60,"#F59E0B"), (60,100,"#EF4444")]:
        ax.barh(1, (end-start)/100*pi, left=start/100*pi, height=1.2, color=color)

    angle = (score / 100) * pi
    ax.arrow(angle, 0, 0, 1, width=0.03, head_width=0.08, color="black")

    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.set_ylim(-1, 1.2)

    return fig