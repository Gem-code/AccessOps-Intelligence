import matplotlib.pyplot as plt
from math import pi

def draw_small_gauge(score):
    # 200px width → 2 inches at 100 DPI
    fig, ax = plt.subplots(
        figsize=(2, 1.2),       # ~200px width
        dpi=100,
        subplot_kw={'projection': 'polar'}   # FIX: Polar axis
    )

    # Remove whitespace
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.patch.set_facecolor('none')

    # Gauge configuration
    ax.set_theta_offset(pi)
    ax.set_theta_direction(-1)

    # Colored arcs
    ranges = [
        (0, 30, "#22C55E"),   # green
        (30, 60, "#F59E0B"),  # yellow
        (60, 100, "#EF4444")  # red
    ]

    for start, end, color in ranges:
        ax.barh(1, (end-start)/100*pi, left=start/100*pi, height=1.2, color=color)

    # Needle
    angle = (score / 100) * pi
    ax.arrow(angle, 0, 0, 1, width=0.03, head_width=0.08, color="black")

    # Clean view
    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.set_ylim(-1, 1.2)

    return fig
