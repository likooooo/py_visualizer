#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse

# points : 矢量的起点
# dir_angle : 矢量的方向
# scala : 矢量的模场
# ellipticity 椭圆度， 如果为0 代表 绘制矢量箭头， 1 代表绘制圆(此时 points 表示圆心, scala 表示半径,dir_angle 是一个不起作用的参数), 0~1之间代表椭圆( 此时 Points代表椭圆圆心， dir_angle代表椭圆长轴方向)
# color 表示每个场的颜色
def plot_source_field(
    points: list[list],
    dir_angle: list[float],
    scala: list[float],
    ellipticity: list[float], # Now a list of floats, one for each point
    color: list[str], # Now a list of strings, one for each point
    title: str = "Single Field Visualization" # Added for standalone plotting
):
    ax=None # Optional: Matplotlib Axes object to plot on
    arrow_width: float = 0.005
    ellipse_linewidth: float = 1.5
    ellipse_alpha: float = 0.7

    #  fig_size 单位是英寸：1 英寸 ≈ 2.54 厘米。
    # DPI（每英寸像素数）的影响：
    # 屏幕显示：默认 DPI 通常为 100（plt.show()）。
    fig_size = (10, 10) # Added for standalone plotting

    """
    Plots a single 2D field with precise control over each graphic's properties.
    Each point can have its own direction, scale, ellipticity, and color.

    Parameters:
    points (list[list]): List of [x, y] coordinates for each graphic's center/origin.
    dir_angle (list[float]): List of direction angles (radians) for each graphic.
                             For circles (ellipticity=1), this parameter has no effect.
                             For ellipses (0 < ellipticity < 1), it defines the major axis direction.
    scala (list[float]): List of scale values for each graphic.
                         - For arrows (ellipticity=0): Represents the desired arrow length.
                         - For circles (ellipticity=1): Represents the desired circle radius.
                         - For ellipses (0 < ellipticity < 1): Represents the desired major axis length.
    ellipticity (list[float]): List of ellipticity values for each graphic.
                               - 0: Plots an arrow (scala is arrow length).
                               - 1: Plots a circle (scala is circle radius).
                               - (0, 1): Plots an ellipse (scala is major axis length).
    color (list[str]): List of colors for each graphic.
    ax (matplotlib.axes.Axes, optional): If provided, plots on this Axes object.
                                         If None, a new figure and axes are created.
    arrow_width (float, optional): Width of the arrow shaft. Defaults to 0.005.
    ellipse_linewidth (float, optional): Line width for circles and ellipses. Defaults to 1.5.
    ellipse_alpha (float, optional): Alpha (transparency) for circles and ellipses. Defaults to 0.7.
    fig_size (tuple, optional): Figure size if a new figure is created. Defaults to (10, 8).
    title (str, optional): Title for the plot if a new figure is created. Defaults to "Single Field Visualization".
    """
    is_new_plot = False
    if ax is None:
        fig, ax = plt.subplots(figsize=fig_size)
        is_new_plot = True

    # Convert inputs to NumPy arrays for easier vectorized operations
    points_np = np.array(points)
    dir_angle_np = np.array(dir_angle)
    scala_np = np.array(scala)
    ellipticity_np = np.array(ellipticity)
    color_np = np.array(color) # For consistency, though colors are handled per-item

    num_graphics = len(points_np)

    # Validate input list lengths
    if not (len(dir_angle_np) == num_graphics and
            len(scala_np) == num_graphics and
            len(ellipticity_np) == num_graphics and
            len(color_np) == num_graphics):
        raise ValueError("All input lists (points, dir_angle, scala, ellipticity, color) must have the same length.")

    # Initialize lists to collect all plotted coordinates for auto-ranging
    all_x_coords = []
    all_y_coords = []
    # Maximum dimension for auto-ranging calculation for *this field*
    max_graphic_dim_for_range = 0.0

    for i in range(num_graphics):
        x, y = points_np[i]
        current_dir_angle = dir_angle_np[i]
        current_scala = scala_np[i]
        current_ellipticity = ellipticity_np[i]
        current_color = color_np[i]

        all_x_coords.append(x)
        all_y_coords.append(y)

        # --- Plotting Logic based on ellipticity ---
        if current_ellipticity == 0:  # Plot an arrow
            end_x = x + np.cos(current_dir_angle) * current_scala
            end_y = y + np.sin(current_dir_angle) * current_scala
            all_x_coords.append(end_x)
            all_y_coords.append(end_y)

            ax.plot(
                [x, end_x], # X-coordinates of start and end points
                [y, end_y], # Y-coordinates of start and end points
                color=current_color,
                linewidth=arrow_width * 100, # Use arrow_width for line thickness, scaled up for visibility
                zorder=2 # Ensure lines are on top
            )
            max_graphic_dim_for_range = max(max_graphic_dim_for_range, current_scala)

        else:
            width_to_plot = current_scala # User wants major axis length to be 'scala'
            height_to_plot = width_to_plot * abs(current_ellipticity) # Minor axis is major_axis * ellipticity

            # Ellipse angle is in degrees
            ellipse_angle_degrees = np.degrees(current_dir_angle)

            ellipse = Ellipse(
                xy=(x, y),
                width=width_to_plot,
                height=height_to_plot,
                angle=ellipse_angle_degrees,
                facecolor='none', # Empty ellipse
                edgecolor=current_color,
                linewidth=ellipse_linewidth,
                alpha=ellipse_alpha,
                zorder=1 # Ellipses can be below arrows
            )
            ax.add_patch(ellipse)
            max_graphic_dim_for_range = max(max_graphic_dim_for_range, width_to_plot) # Major axis

    # --- Plot Layout and Display (only if new plot created) ---
    if is_new_plot:
        ax.set_xlabel("simga X")
        ax.set_ylabel("sigma Y")
        ax.set_title(title)
        # ax.grid(True, linestyle='--', alpha=0.7)
        ax.grid(False)
        ax.axhline(0, color='gray', linewidth=0.8, linestyle=':')
        ax.axvline(0, color='gray', linewidth=0.8, linestyle=':')
        ax.set_aspect('equal', adjustable='box') # Maintain aspect ratio

        # Auto-adjust axis limits based on all plotted points and max graphic size
        if all_x_coords and all_y_coords:
            min_x, max_x = np.min(all_x_coords), np.max(all_x_coords)
            min_y, max_y = np.min(all_y_coords), np.max(all_y_coords)

            # Add padding based on the maximum graphic dimension to ensure visibility
            # A base padding of 0.5 is added even if max_graphic_dim_for_range is small
            padding = max(max_graphic_dim_for_range * 0.6, 0.5) # A bit more padding for circles/ellipses

            ax.set_xlim(min_x - padding, max_x + padding)
            ax.set_ylim(min_y - padding, max_y + padding)
        else: # Handle empty data
            ax.set_xlim(-1, 1)
            ax.set_ylim(-1, 1)

        plt.show()


if __name__ == "__main__":
    # --- Test Cases for plot_source_field ---

    print("--- Test: Arrows (scala=1 -> length=1) ---")
    plot_source_field(
        points=[[0, 0], [1, 1], [2, 0]],
        dir_angle=[np.pi/4, np.pi/2, np.pi * 7 / 4], # Radians
        scala=[1.0, 1.0, 1.0], # All arrows should have length 1
        ellipticity=[0, 0, 0],
        color=['red', 'blue', 'green'],
        title="Arrows: Scala=1 -> Length=1"
    )

    print("\n--- Test: Circles (scala=1 -> diameter=1) ---")
    plot_source_field(
        points=[[0, 0], [1, 1], [2, 0]],
        dir_angle=[0, 0, 0], # Not used for circles
        scala=[1.0, 1.0, 1.0], # All circles should have diameter 1
        ellipticity=[1, 1, 1],
        color=['orange', 'purple', 'cyan'],
        title="Circles: Scala=1 -> Diameter=1"
    )

    print("\n--- Test: Ellipses (scala=1 -> major axis=1, various ellipticity) ---")
    plot_source_field(
        points=[[0, 0], [1.5, 1.5], [3, 0]],
        dir_angle=[np.pi/4, np.pi/2, np.pi * 3 / 4], # Major axis direction in radians
        scala=[1.0, 1.0, 1.0], # All ellipses should have major axis length 1
        ellipticity=[0.2, 0.5, 0.8], # Varying minor/major axis ratio
        color=['darkgreen', 'darkred', 'darkblue'],
        title="Ellipses: Scala=1 -> Major Axis=1"
    )

    print("\n--- Test: Mixed Types with varying scala ---")
    plot_source_field(
        points=[[0, 0], [1.5, 0], [3, 0], [4.5, 0]],
        dir_angle=[np.pi/4, 0, np.pi/2, np.pi],
        scala=[1,1,1,1], # Varying scales
        ellipticity=[0, 1, 0.5, 0], # Arrow, Circle, Ellipse, Arrow
        color=['red', 'blue', 'green', 'purple'],
        title="Mixed Types with Varying Scala"
    )