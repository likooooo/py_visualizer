import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.widgets import TextBox, Button
import os

def add_input_widget(im):
    return
    fig = im.figure  # Get the figure from the image
    # Ensure the axes for widgets don't overlap with the image
    ax_textbox = fig.add_axes([0.1, 0.01, 0.8, 0.05])  # Position for the TextBox
    ax_button = fig.add_axes([0.9, 0.01, 0.1, 0.05])  # Position for the Button

    # TextBox widget for inputting file path
    text_box = TextBox(ax_textbox, 'Enter file path: ', initial='')

    # Button widget for submitting the path
    button = Button(ax_button, 'Load File')

    # Define the button callback function to load and display the image
    def on_button_click(event):
        file_path = text_box.text
        if os.path.exists(file_path):
            try:
                # Load the new image data (you can replace this with any image reading method)
                data = np.load(file_path)  # Assuming the file is a numpy array (.npy)
                im.set_data(data)
                fig.canvas.draw()  # Redraw the image with the new data
            except Exception as e:
                print(f"Error loading file: {e}")
        else:
            print(f"Invalid file path: {file_path}")

    # Connect the button's click event to the function
    button.on_clicked(on_button_click)

    # Optional: you can also link the textbox value to some other behavior, like validation
    # For example, display the entered path when the user modifies the text box
    def on_text_change(text):
        print(f"Path entered: {text}")
        
    text_box.on_text_change(on_text_change)

# display image in intercation mode
im = None
ax = None
cb = None
text = None
frame_index = 0
update_count = 0
def try_init(data):
    global im, ax, cb, text
    if ax is not None:
        return
    plt.ion()
    ax = plt.gca()
    shape = data.shape
    if len(shape) == 2 and 1 == shape[1]:
        [im,] = ax.plot(range(shape[0]), data)
        ax.set_ylim([np.min(data), np.max(data)])
    else:
        norm = Normalize(vmin=np.min(data), vmax=np.max(data))
        im = ax.imshow(data, aspect='auto', cmap='viridis', norm = norm)
        ax.xaxis.set_ticks_position('bottom')
        ax.invert_yaxis()
        cb = plt.colorbar(im, ax=ax)
        cb.set_label('Intensity')  # 设置 colorbar 标签
    # text = ax.text(0.05, 0.95, '', transform=ax.transAxes, verticalalignment='top', bbox=dict(facecolor='red', alpha=0.5))
    text = ax.text(0.5, -0.1, '', transform=ax.transAxes,
               horizontalalignment='center',
               verticalalignment='top',
               bbox=dict(facecolor='red', alpha=0.5))
    add_input_widget(im)
def update(data, sync_mode=False):
    global frame_index, update_count, text
    update_count = update_count + 1
    [xsize, ysize] = data.shape
    lb, ub = np.min(data), np.max(data)
    
    # Update the image data (use a 1D slice of the matrix for simplicity)
    # data = data[xsize // 2]
    # ysize = 1
    
    try_init(data)
    text.set_text(f"frame-{frame_index} range:({lb:.2f},{ub:.2f}) sum:{np.sum(data):.2f}")
    frame_index = frame_index + 1
    
    if ysize == 1: 
        im.set_ydata(data)
    else:
        # data = (data - lb)/(ub -lb)
        im.set_array(data)
    
    # im.norm = Normalize(vmin=lb, vmax=ub)
    # cb.update_normal(im) 
    plt.draw()
    
    if sync_mode:
        plt.ioff()
        plt.show(block=True)
    else:
        plt.pause(0.1)

# Function to clean up and close the plot
def close_plot():
    plt.close()

# regist event
mouse_pressed = False
start_x, start_y = None, None
move_x, move_y= None, None
def regist_click_and_motion(click = None, motion = None):
    def clamp(value, min_value, max_value):
        return max(min_value, min(value, max_value))
    def to_data_coord(px, py):
        data_x, data_y = ax.transData.inverted().transform((px, py))
        data_x = clamp(data_x, ax.viewLim.x0, ax.viewLim.x1)
        data_y = clamp(data_y, ax.viewLim.y0, ax.viewLim.y1)
        move_x, move_y = data_x, data_y
        return data_x, data_y   
    def on_button_press(event):
        if not event.inaxes: return 
        global mouse_pressed, start_x, start_y, move_x, move_y
        mouse_pressed = True
        start_x, start_y = event.xdata, event.ydata
        move_x, move_y = start_x, start_y 
        if None != click : 
            click(int(event.button), int(0), float(start_x), float(start_y))
        else:
            print(f'press   from point ({start_x:.2f}, {start_y:.2f})')
    def on_button_release(event):
        global mouse_pressed, start_x, start_y, move_x, move_y
        if not mouse_pressed: return
        data_x, data_y = to_data_coord(event.x, event.y)
        if None != click : 
            click(int(event.button), int(1), float(data_x), float(data_y))
        else:
            print(f'release from point ({data_x:.2f}, {data_y:.2f})')
        mouse_pressed = False
        start_x, start_y = None, None
        move_x, move_y = None,None
    def on_motion(event):
        global move_x, move_y
        if not mouse_pressed or not event.inaxes: return 
        dx = event.xdata - move_x
        dy = event.ydata - move_y
        if None != motion : 
            motion(float(move_x), float(move_y), float(dx), float(dy))
        else : 
            print(f'move    from point ({move_x:.2f}, {move_y:.2f}) \t dir ({dx:.2f}, {dy:.2f}) ')
        move_x, move_y = event.xdata, event.ydata
        
    ax.figure.canvas.mpl_connect('button_press_event', on_button_press)
    ax.figure.canvas.mpl_connect('motion_notify_event', on_motion)
    ax.figure.canvas.mpl_connect('button_release_event', on_button_release) 
def regist_on_close(callback_on_close):
    cid = ax.figure.canvas.mpl_connect('close_event', callback_on_close)
def regist_mouse_event(click, motion):
    regist_click_and_motion(click, motion)

def display_image(matrix):
    """
    显示一个 NumPy 矩阵作为图像或曲线。
    
    参数:
        matrix (numpy.ndarray): 输入的矩阵，可以是灰度图像 (2D)、彩色图像 (3D) 或Nx1/一维数据。
    """
    if not isinstance(matrix, np.ndarray):
        raise TypeError("Input must be a NumPy array.")

    plt.figure()  # 创建新图表

    # 检查是否为Nx1或一维数据
    if matrix.ndim == 1 or (matrix.ndim == 2 and matrix.shape[1] == 1):
        # 绘制曲线
        data = matrix.squeeze()  # 确保数据为一维
        plt.plot(data)
        plt.xlabel('Index')
        plt.ylabel('Value')
        plt.title('Curve Plot')
    else:
        # 显示图像
        ax = plt.gca()
        im = ax.imshow(matrix, aspect='auto', cmap='viridis')
        ax.xaxis.set_ticks_position('bottom')
        ax.invert_yaxis()  # 图像坐标系反向
        
        # 动态计算刻度间隔（保持原逻辑）
        NX = int(matrix.shape[1] / 10)
        NY = int(matrix.shape[0] / 10)
        interval = max(1, min(NX, NY))  # 确保最小间隔为1
        ax.set_xticks(np.arange(0, matrix.shape[1], interval))
        ax.set_yticks(np.arange(0, matrix.shape[0], interval))
        
        # 添加颜色条
        cb = plt.colorbar(im, ax=ax)
        cb.set_label('Intensity')
        add_input_widget(im)  # 保持原有交互功能

    plt.show()

def plot_curves(lines, start_x=None, step_x=None, legends=None, types=None, sample_rate=1.0):
    """
    绘制曲线。

    参数：
        lines (list of list): 曲线数据的列表，其中每个子列表表示一条曲线。
        start_x (list, optional): 长度为 n 的列表，表示每条曲线的起始点 x。默认为 None。
        step_x (list, optional): 长度为 n 的列表，表示每条曲线的 x 步长。默认为 None。
        legends (list, optional): 长度为 n 的列表，表示每条曲线的图例。默认为 None。
        types (list, optional): 长度为 n 的列表，表示每条曲线的绘制方式。默认为 None。
        sample_rate (float, optional): 0-1 之间的浮点数，表示采样率。默认为 1.0 (不采样)。
    """

    n = len(lines)  # 曲线的数量

    if start_x is None:
        start_x = [0] * n
    if step_x is None:
        step_x = [1] * n
    if legends is None:
        legends = [f'Curve {i}' for i in range(n)]
    if types is None:
        types = ['-'] * n

    for i in range(n):
        y = np.array(lines[i])  # 将list转化为numpy array
        m = len(y) # 获取当前曲线的点数
        x = np.array([start_x[i] + j * step_x[i] for j in range(m)])

        if sample_rate < 1.0:
            sample_size = int(m * sample_rate)
            if sample_size < 2:
                sample_size = 2  # 确保采样后的点数至少为 2
            sample_indices = np.random.choice(m, size=sample_size, replace=False)
            sample_indices.sort()
            x = x[sample_indices]
            y = y[sample_indices]

        plt.plot(x, y, types[i], label=legends[i])

    plt.legend(loc='upper right')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Curves')
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    def load_image_from_cmd():
        import argparse
        parser = argparse.ArgumentParser(description="image visualizer")
        parser.add_argument("--path", type=str, required=True)
        parser.add_argument("--shape",type=str, nargs="+", default= [])
        parser.add_argument("--type", type=str, default="")
        args = parser.parse_args() 
        assert(os.path.exists(args.path))

        def to_np_type(s):
            dtype_map = {
                'c': np.complex64,
                'z': np.complex128,
                'f': np.float32,
                'd': np.float64,
                'n': np.int32,
                '' : np.float32
            }
            return dtype_map[s]
        def auto_args_if_need(args):
            default_type = {
                4 : 'f',
                8 : 'c',
                16: 'z'
            }
            import math
            stats = os.stat(args.path)
            n = stats.st_size
            # auto shape
            if '' != args.type and 0 == len(args.shape):
                n1 = int(n / np.dtype(to_np_type(args.type)).itemsize)
                # single image
                w = int(math.sqrt(n1))
                if w * w == n1:
                    args.shape = [w, w]
                    return
                # image stack
                # n = a * w * h
                for a in range(2, 16):
                    if 0 == n1 % a:
                        n1 = int(n1/a)
                        w = int(math.sqrt(n1))
                        if w * w == n1:
                            args.shape = [w *a, w]
                            return
                raise RuntimeError("declshape failed")
            # auto type
            if '' == args.type and 0 != len(args.shape):
                i = int(n / np.prod(args.shape))
                assert(i * np.prod(args.shape) == n)
                if i in default_type:
                    args.type = default_type[i]
                    return
                raise RuntimeError("decltype failed")
            # auto shape & type
            if '' == args.type and 0 == len(args.shape):
                # single image 
                # n = t * w * h
                for t in default_type.keys():
                    n1 = int(n/t)
                    w = int(math.sqrt(n1))
                    if w * w == n1:
                        args.type = default_type[t]
                        args.shape = [w, w]
                        return
                raise RuntimeError("decltype&shape failed")
        auto_args_if_need(args)
        def print_image_info(args):
            print("* image visualizer")
            print("    path =", args.path)
            print("    shape=", args.shape)
            print("    type =", args.type)
        print_image_info(args)
        data = np.fromfile(args.path, dtype=to_np_type(args.type))
        data = np.reshape(data, args.shape)
        if args.type in ['c', 'z']:
            print("    origin=")
            print(data)
            data = np.abs(data)
        return data
    display_image(load_image_from_cmd())
        

    # 显示图像
    plt.show()

def plot_surface(x, y, matrix):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    surf = ax.plot_surface(x, y, matrix, cmap='viridis')
    fig.colorbar(surf)
    ax.set_xlabel('$x$')
    ax.set_ylabel('$y$')
    ax.set_zlabel('$z$')
    plt.show()
