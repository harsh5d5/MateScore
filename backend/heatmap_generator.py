import matplotlib
matplotlib.use('Agg') # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns
import io
import numpy as np
from matplotlib.figure import Figure
from matplotlib.colors import LinearSegmentedColormap

def draw_pitch(ax):
    # Colors for "Vibrant Matchday"
    natural_green_1 = '#2D5A27'
    natural_green_2 = '#356631'
    line_color = '#FFFFFF'
    line_width = 2.5
    
    # Rounded Background Frame (to match screenshot)
    ax.add_patch(patches.FancyBboxPatch((-10, -10), 120, 130, 
                                     boxstyle="round,pad=0,rounding_size=10", 
                                     fill=True, color=natural_green_1, zorder=-1))
    
    # Draw Background (Stripes)
    ax.add_patch(patches.Rectangle((0, 0), 100, 100, fill=True, color=natural_green_1, zorder=0))
    
    # Draw Vertical Stripes
    stripe_width = 100 / 10
    for i in range(1, 10, 2):
        ax.add_patch(patches.Rectangle((i * stripe_width, 0), stripe_width, 100, fill=True, color=natural_green_2, zorder=0.1))
    
    # Boundary and Center Line
    ax.plot([0, 100, 100, 0, 0], [0, 0, 100, 100, 0], color=line_color, lw=line_width, zorder=1)
    ax.plot([50, 50], [0, 100], color=line_color, lw=line_width, zorder=1)
    
    # Center Circle and Spot
    ax.add_patch(patches.Circle((50, 50), 9.15, fill=False, color=line_color, lw=line_width, zorder=1))
    ax.add_patch(patches.Circle((50, 50), 0.5, fill=True, color=line_color, zorder=1.1))
    
    # Penalty Areas (Left & Right)
    ax.add_patch(patches.Rectangle((0, 21.1), 16.5, 57.8, fill=False, color=line_color, lw=line_width, zorder=1)) # Box
    ax.add_patch(patches.Rectangle((0, 36.8), 5.5, 26.4, fill=False, color=line_color, lw=line_width, zorder=1))  # Goal area
    
    ax.add_patch(patches.Rectangle((83.5, 21.1), 16.5, 57.8, fill=False, color=line_color, lw=line_width, zorder=1))
    ax.add_patch(patches.Rectangle((94.5, 36.8), 5.5, 26.4, fill=False, color=line_color, lw=line_width, zorder=1))
    
    # Penalty Arcs
    ax.add_patch(patches.Arc((11, 50), 18.3, 18.3, theta1=308, theta2=52, color=line_color, lw=line_width, zorder=1))
    ax.add_patch(patches.Arc((89, 50), 18.3, 18.3, theta1=128, theta2=232, color=line_color, lw=line_width, zorder=1))
    
    # Corner Arcs
    ax.add_patch(patches.Arc((0, 0), 2, 2, theta1=0, theta2=90, color=line_color, lw=line_width, zorder=1))
    ax.add_patch(patches.Arc((100, 0), 2, 2, theta1=90, theta2=180, color=line_color, lw=line_width, zorder=1))
    ax.add_patch(patches.Arc((100, 100), 2, 2, theta1=180, theta2=270, color=line_color, lw=line_width, zorder=1))
    ax.add_patch(patches.Arc((0, 100), 2, 2, theta1=270, theta2=0, color=line_color, lw=line_width, zorder=1))

    # Attacking Arrow (Cleaner, Thicker, no text)
    ax.arrow(35, 110, 30, 0, width=1.5, head_width=5, head_length=7, fc='#FFFFFF', ec='#FFFFFF', clip_on=False, zorder=1.2)

def generate_heatmap_svg(pos):
    # High-Contrast Colormap: Dark Green -> Dark Yellow -> Blood Red
    # Using hex codes with better saturation
    colors = ["#22332200", "#C7D84B", "#E6B800", "#D32F2F", "#8B0000"]
    n_bins = 100
    cmap_name = "high_contrast_theme"
    custom_cmap = LinearSegmentedColormap.from_list(cmap_name, colors, N=n_bins)

    fig = Figure(figsize=(12, 9), facecolor='none')
    ax = fig.add_subplot(111)
    
    draw_pitch(ax)
    
    # Data Generation for sharper clusters
    points_count = 120 # Reduced for specialized focus
    
    if "Forward" in pos:
        x = np.concatenate([np.random.normal(75, 8, int(points_count*0.7)), np.random.normal(15, 4, int(points_count*0.3))])
        y = np.random.normal(50, 12, points_count)
    elif "Midfielder" in pos:
        x_left = np.random.normal(30, 6, int(points_count*0.5))
        x_center = np.random.normal(50, 8, int(points_count*0.3))
        x_right = np.random.normal(70, 10, int(points_count*0.2))
        x = np.concatenate([x_left, x_center, x_right])
        y = np.random.normal(50, 15, points_count)
    elif "Defender" in pos:
        x = np.random.normal(25, 8, int(points_count))
        y = np.random.normal(50, 20, points_count)
    else: # Goalkeeper
        x = np.random.normal(10, 2, points_count)
        y = np.random.normal(50, 5, points_count)
    
    x = np.clip(x, 1, 99)
    y = np.clip(y, 1, 99)
    
    # Smooth Intensity Heatmap using KDE with specialized sharper clusters
    try:
        # bw_adjust=0.35 makes the clusters MUCH tighter and more sharp/defined
        # clip is slightly expanded to prevent the "hard cut" look on the white lines
        kde = sns.kdeplot(
            x=x, y=y, 
            fill=True, 
            thresh=0.08, 
            levels=40, 
            cmap=custom_cmap, 
            alpha=0.85, 
            ax=ax,
            zorder=2,
            bw_adjust=0.35,
            clip=((-5, 105), (-5, 105)) 
        )
    except:
        ax.hexbin(x, y, gridsize=20, cmap=custom_cmap, alpha=0.7, zorder=2, mincnt=1)
    
    # Extended limits to show the full rounded background frame
    ax.set_xlim(-12, 112)
    ax.set_ylim(-12, 125)
    ax.axis('off')
    
    try:
        print(f"Generating high-contrast heatmap for position: {pos}")
        img_data = io.StringIO()
        fig.savefig(img_data, format='svg', bbox_inches='tight', pad_inches=0.1, transparent=True)
        return img_data.getvalue()
    except Exception as e:
        print(f"Error in generate_heatmap_svg: {e}")
        raise e
