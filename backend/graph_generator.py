import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import numpy as np
from matplotlib.figure import Figure
from matplotlib.colors import LinearSegmentedColormap

def generate_rating_graph_svg(player_name, mode='rating'):
    # Mock Data Generation
    months = ['Mar', '', 'May', '', 'Jul', '', 'Sep', '', 'Nov', '', 'Jan']
    np.random.seed(sum(ord(c) for c in player_name))
    ratings = np.random.uniform(6.5, 8.2, 11)
    counts = np.random.randint(1, 10, 11) # Mock "Count" data
    
    # Consistent "no-game" months
    ratings[3] = 0; counts[3] = 0
    ratings[10] = 0; counts[10] = 0
    
    fig = Figure(figsize=(10, 4), facecolor='#121212')
    ax = fig.add_subplot(111)
    ax.set_facecolor('#121212')
    
    # Conditional Coloring (based on rating regardless of mode)
    def get_color(r):
        if r > 7.1: return '#00E676' 
        if r > 6.8: return '#FFD600'
        if r > 0: return '#FF3D00'
        return '#121212'
    
    colors = [get_color(r) for r in ratings]
    
    # Draw Bars
    x_pos = np.arange(len(ratings))
    ax.bar(x_pos, ratings, color=colors, width=0.7, zorder=3)
    
    # Average line based on ratings
    avg_rating = np.mean([r for r in ratings if r > 0])
    ax.axhline(y=avg_rating, color='#00E676', linestyle='--', linewidth=1, alpha=0.5, zorder=2)
    
    # Toggle Display Logic (Value labels below bars)
    for i, r in enumerate(ratings):
        if r > 0:
            val_text = f"{r:.1f}" if mode == 'rating' else f"{int(counts[i])}"
            ax.text(i, -0.6, val_text, color=get_color(r), ha='center', va='top', fontsize=9, fontweight='bold')
        else:
            ax.text(i, -0.6, "-", color='#444444', ha='center', va='top', fontsize=9)
            
    # FIXED: Month labels higher to avoid arrow overlap
    for i, m in enumerate(months):
        if m:
            ax.text(i, 11.5, m, color='#999999', ha='center', va='bottom', fontsize=10)
            
    # Transfer Indicator (Arrow lowered slightly to avoid month overlap)
    ax.axvline(x=0, color='#7C4DFF', linewidth=1.5, alpha=0.8, zorder=1)
    ax.text(0, 9.8, "➔", color='#7C4DFF', ha='center', va='center', 
            fontsize=12, bbox=dict(facecolor='#121212', edgecolor='#7C4DFF', boxstyle='circle,pad=0.2', zorder=4))
            
    # Right side Color Gauge
    ax_inset = ax.inset_axes([1.02, 0.2, 0.015, 0.6])
    gauge_colors = ["#FF3D00", "#FFD600", "#00E676", "#00B0FF"]
    gauge_cmap = LinearSegmentedColormap.from_list("gauge", gauge_colors)
    cb = fig.colorbar(matplotlib.cm.ScalarMappable(norm=matplotlib.colors.Normalize(vmin=6, vmax=9), cmap=gauge_cmap),
                    cax=ax_inset, orientation='vertical')
    cb.outline.set_visible(False)
    ax_inset.tick_params(labelsize=8, colors='#999999', length=0)
    
    # Remove all standard axes
    ax.set_ylim(-2, 11)
    ax.set_xlim(-1, 12)
    ax.axis('off')
    
    # Final styling
    ax.text(-1, -2, "Monthly average rating", color='#666666', fontsize=8, ha='left')
    
    try:
        img_data = io.StringIO()
        fig.savefig(img_data, format='svg', bbox_inches='tight', pad_inches=0.1, transparent=True)
        return img_data.getvalue()
    except Exception as e:
        print(f"Error in generate_rating_graph_svg: {e}")
        raise e
