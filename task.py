import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import psutil
import ttkbootstrap.style
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
from matplotlib import rcParams
import tkinter.font as tkFont

# 设置中文字体，防止中文显示乱码
rcParams['font.sans-serif'] = ['SimHei']  # 黑体
rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


def update_process_list(search_term=""):
    # 更新进程列表。可选地根据 search_term 过滤进程名称。
    process_listbox.delete(0, tk.END)
    for process in psutil.process_iter(['pid', 'name']):
        try:
            process_name = process.info['name']
            pid = process.info['pid']
            if search_term.lower() in process_name.lower():
                process_listbox.insert(tk.END, f"{process_name} (PID: {pid})")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass  # 跳过无法访问的进程


def close_selected_process():
    # 关闭选定的进程。
    try:
        selected_process = process_listbox.get(process_listbox.curselection())
        pid = int(selected_process.split("(PID: ")[1].rstrip(")"))
        process = psutil.Process(pid)
        process.kill()
        messagebox.showinfo("提示", f"{process.name()} 已关闭")
        update_process_list(search_entry.get())
    except Exception as e:
        messagebox.showwarning("警告", f"无法关闭进程：{e}")


def on_process_double_click(event):
    # 处理进程双击事件，显示详细信息。
    try:
        selected_process = process_listbox.get(process_listbox.curselection())
        pid = int(selected_process.split("(PID: ")[1].rstrip(")"))
        process_name = selected_process.split(" (PID: ")[0]
        show_process_details(pid, process_name)
    except Exception as e:
        messagebox.showwarning("警告", f"无法获取进程信息：{e}")


def show_process_details(pid, process_name):
    # 显示选定进程的详细信息，包括 PID、CPU 和内存使用率的实时曲线图。
    try:
        process = psutil.Process(pid)
    except psutil.NoSuchProcess:
        messagebox.showwarning("警告", "该进程不存在。")
        update_process_list(search_entry.get())
        return
    except psutil.AccessDenied:
        messagebox.showwarning("警告", "没有权限访问该进程的信息。")
        return

    # 创建新窗口
    detail_window = tk.Toplevel(root)
    detail_window.title(f"{process_name} (PID: {pid}) 的详细信息")
    detail_window.geometry("600x500")

    # 显示 PID
    pid_label = ttk.Label(detail_window, text=f"PID: {pid}", font=("Arial", 16))
    pid_label.pack(pady=10)

    # 创建图形区域
    fig, (ax_cpu, ax_mem) = plt.subplots(2, 1, figsize=(6, 4))
    fig.tight_layout(pad=3.0)

    # 初始化数据
    cpu_data = []
    mem_data = []
    time_data = []
    start_time = time.time()

    # 绘制初始曲线
    ax_cpu.set_title("CPU 占用率 (%)")
    ax_cpu.set_xlabel("时间 (秒)")
    ax_cpu.set_ylabel("CPU %")
    cpu_line, = ax_cpu.plot([], [], 'r-')

    ax_mem.set_title("内存占用率 (%)")
    ax_mem.set_xlabel("时间 (秒)")
    ax_mem.set_ylabel("内存 %")
    mem_line, = ax_mem.plot([], [], 'b-')

    # 嵌入 matplotlib 图形到 Tkinter
    canvas = FigureCanvasTkAgg(fig, master=detail_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # 更新图形的函数S
    def update_graph():
        try:
            current_time = time.time() - start_time
            cpu = process.cpu_percent(interval=None)  # 非阻塞
            mem = process.memory_percent()

            time_data.append(current_time)
            cpu_data.append(cpu)
            mem_data.append(mem)

            # 保持数据点数量，避免无限增长
            if len(time_data) > 1000:
                time_data.pop(0)
                cpu_data.pop(0)
                mem_data.pop(0)

            cpu_line.set_data(time_data, cpu_data)
            mem_line.set_data(time_data, mem_data)

            # 更新 X 轴范围
            if current_time < 5:
                ax_cpu.set_xlim(0, 5)
                ax_mem.set_xlim(0, 5)
            else:
                ax_cpu.set_xlim(current_time - 5, current_time)
                ax_mem.set_xlim(current_time - 5, current_time)

            # 设置 Y 轴范围
            ax_cpu.set_ylim(0, max(2, max(cpu_data)))
            ax_mem.set_ylim(0, max(2, max(mem_data)))

            # 更新图形
            ax_cpu.relim()
            ax_cpu.autoscale_view()

            ax_mem.relim()
            ax_mem.autoscale_view()

            canvas.draw()

            # 定时再次调用自身
            detail_window.after(10, update_graph)
        except psutil.NoSuchProcess:
            messagebox.showinfo("提示", "该进程已结束。")
            detail_window.destroy()
        except Exception as e:
            messagebox.showwarning("警告", f"获取进程信息时出错：{e}")
            detail_window.destroy()

    # 启动图形更新
    update_graph()


def search_processes():
    # 根据搜索框中的关键词过滤进程列表。
    search_term = search_entry.get()
    update_process_list(search_term)


# 创建主窗口
root = tk.Tk()
root.title("任务管理器")
root.geometry("800x600")  # 调整窗口大小以适应新增的搜索框

bold_font = tkFont.Font(weight="bold")
large_font = tkFont.Font(family="SimHei", size=12, weight="bold")

# 应用样式主题
style = ttkbootstrap.Style(theme='minty')

# 创建搜索框和搜索按钮
search_frame = ttk.Frame(root)
search_frame.pack(pady=10, padx=10, anchor='w')

search_label = ttk.Label(search_frame, text="搜索进程:", font=bold_font)
search_label.pack(side=tk.LEFT, padx=(0, 5))

search_entry = ttk.Entry(search_frame, width=50, font=bold_font)
search_entry.pack(side=tk.LEFT, padx=(0, 5))

search_button = ttk.Button(search_frame, text="搜索", command=search_processes, style='primary.TButton')
search_button.pack(side=tk.LEFT, padx=(0, 5))

listbox_frame = ttk.Frame(root)
listbox_frame.pack(padx=10, pady=(0, 10), fill=tk.BOTH, expand=True)

# 创建进程列表框
process_listbox = tk.Listbox(listbox_frame, width=100, height=20, bd=5, selectmode='extended', selectbackground='red')
process_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# 创建滚动条并绑定到 Listbox
scrollbar_v = tk.Scrollbar(listbox_frame, orient='vertical', command=process_listbox.yview)
scrollbar_v.pack(side=tk.RIGHT, fill='y')

process_listbox.config(yscrollcommand=scrollbar_v.set)

# 绑定双击事件
process_listbox.bind('<Double-Button-1>', on_process_double_click)

# 创建按钮框架
button_frame = ttk.Frame(root)
button_frame.pack(pady=10)

refresh_button = ttk.Button(button_frame, text="刷新进程列表", command=lambda: update_process_list(search_entry.get()),
                            width=15)
refresh_button.pack(side=tk.LEFT, padx=5)

close_button = ttk.Button(button_frame, text="关闭选定进程", command=close_selected_process, width=15)
close_button.pack(side=tk.LEFT, padx=5)

exit_button = ttk.Button(button_frame, text="退出该程序", command=root.destroy, width=15)
exit_button.pack(side=tk.LEFT, padx=5)

# 初始化进程列表
update_process_list()

# 启动主循环
root.mainloop()
