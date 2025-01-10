import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches

class BuddySystemGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Buddy Memory Allocation")
        self.buddy_system = None
        self.init_memory_screen()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)


    def init_memory_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        # Close the matplotlib figure if it exists
        if hasattr(self, 'fig'):
            plt.close(self.fig)

        tk.Label(self.root, text="Initialize Memory (in MB)", font=("Arial", 14)).pack(pady=10)

        self.memory_size = tk.IntVar()
        memory_sizes = [2 ** i for i in range(1, 12)]
        self.memory_combobox = ttk.Combobox(self.root, values=memory_sizes, state="readonly")
        self.memory_combobox.pack(pady=5)
        self.memory_combobox.set("Select Memory Size")

        tk.Button(self.root, text="Initialize", command=self.initialize_memory).pack(pady=10)

    def on_close(self):
        """Handle the close event of the Tkinter window."""
        if hasattr(self, 'fig'):
            plt.close(self.fig)  # Close matplotlib figure
        self.root.destroy()  # Properly close the Tkinter mainloop

    def initialize_memory(self):
        try:
            memory = int(self.memory_combobox.get())
            self.buddy_system = BuddySystem(memory)
            self.memory_management_screen()
        except ValueError:
            messagebox.showerror("Error", "Please select a valid memory size.")

    def memory_management_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        # Disconnect matplotlib events if already connected
        if hasattr(self, 'fig') and hasattr(self.fig.canvas, 'mpl_disconnect'):
            self.fig.canvas.mpl_disconnect(self.zoom)

        back_button = tk.Button(self.root, text="Back", command=self.init_memory_screen)
        back_button.pack(anchor="ne", padx=10, pady=10)

        self.fig, self.ax = plt.subplots(figsize=(10, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack()

        self.ax.set_xlim(0, self.buddy_system.total_memory / (1024 * 1024))
        self.ax.set_ylim(0, 1)
        
        # Connect zoom events
        self.zoom_event_id = self.fig.canvas.mpl_connect("scroll_event", self.zoom)

        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)

        tk.Label(control_frame, text="Allocate Memory (MB):").grid(row=0, column=0, padx=5, pady=5)
        self.alloc_size = tk.Entry(control_frame, width=10)
        self.alloc_size.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(control_frame, text="Label:").grid(row=0, column=2, padx=5, pady=5)
        self.alloc_label = tk.Entry(control_frame, width=10)
        self.alloc_label.grid(row=0, column=3, padx=5, pady=5)

        tk.Button(control_frame, text="Allocate", command=self.allocate_memory).grid(row=0, column=4, padx=5, pady=5)

        tk.Label(control_frame, text="Deallocate Memory:").grid(row=1, column=0, padx=5, pady=5)
        self.dealloc_combobox = ttk.Combobox(control_frame, state="readonly")
        self.dealloc_combobox.grid(row=1, column=1, padx=5, pady=5, columnspan=2)

        tk.Button(control_frame, text="Deallocate", command=self.deallocate_memory).grid(row=1, column=3, padx=5, pady=5)

        self.update_dealloc_combobox()
        self.update_plot()


    def zoom(self, event):
        """Zoom in or out on the plot."""
        base_scale = 1.2
        ax = self.ax

        if event.button == 'up':  # Zoom in
            scale_factor = 1 / base_scale
        elif event.button == 'down':  # Zoom out
            scale_factor = base_scale
        else:
            return

        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        x_range = (xlim[1] - xlim[0]) * scale_factor
        y_range = (ylim[1] - ylim[0]) * scale_factor

        x_center = event.xdata
        y_center = event.ydata

        new_xlim = [x_center - x_range / 2, x_center + x_range / 2]
        new_ylim = [y_center - y_range / 2, y_center + y_range / 2]

        # Set new limits ensuring they are within bounds
        ax.set_xlim(max(new_xlim[0], 0), min(new_xlim[1], self.buddy_system.total_memory / (1024 * 1024)))
        ax.set_ylim(max(new_ylim[0], 0), min(new_ylim[1], 1))

        self.canvas.draw()


    def update_plot(self):
        if not self.buddy_system:
            return

        self.ax.clear()
        self.ax.set_xlim(0, self.buddy_system.total_memory / (1024 * 1024))
        self.ax.set_ylim(0, 1)

        for address, (allocated_size, block_size) in self.buddy_system.allocated_blocks.items():
            self.ax.add_patch(
                patches.Rectangle(
                    (address / (1024 * 1024), 0.4), allocated_size / (1024 * 1024), 0.2,
                    edgecolor='black', facecolor='green'
                )
            )
            internal_frag = block_size - allocated_size
            if internal_frag > 0:
                self.ax.add_patch(
                    patches.Rectangle(
                        ((address + allocated_size) / (1024 * 1024), 0.4), internal_frag / (1024 * 1024), 0.2,
                        edgecolor='black', facecolor='lightgreen'
                    )
                )

        for block_size, blocks in self.buddy_system.free_blocks.items():
            for address in blocks:
                self.ax.add_patch(
                    patches.Rectangle(
                        (address / (1024 * 1024), 0.4), block_size / (1024 * 1024), 0.2,
                        edgecolor='black', facecolor='lightgrey'
                    )
                )

        internal, external = self.buddy_system.get_fragmentation()
        self.ax.text(0, 0.8, f"Internal Fragmentation: {internal / (1024 * 1024):.2f} MB", fontsize=10)
        self.ax.text(0, 0.7, f"External Fragmentation: {external / (1024 * 1024):.2f} MB", fontsize=10)

        self.ax.set_xlabel('Memory Address (MB)')
        self.ax.set_title('Buddy System Memory Allocation')

        self.canvas.draw()

    def update_dealloc_combobox(self):
        labels = list(self.buddy_system.label_to_address.keys())
        self.dealloc_combobox['values'] = labels
        if labels:
            self.dealloc_combobox.set(labels[0])

    def allocate_memory(self):
        try:
            size = int(self.alloc_size.get())
            label = self.alloc_label.get().strip()

            if not label:
                messagebox.showerror("Error", "Label cannot be empty.")
                return

            if label in self.buddy_system.label_to_address:
                messagebox.showerror("Error", "Label already in use.")
                return

            address = self.buddy_system.allocate(size, label)
            if address is not None:
                messagebox.showinfo("Success", f"Memory allocated with label '{label}'.")
                self.update_dealloc_combobox()
                self.update_plot()
            else:
                messagebox.showerror("Error", "Memory allocation failed.")
        except ValueError:
            messagebox.showerror("Error", "Invalid input for memory allocation.")

    def deallocate_memory(self):
        label = self.dealloc_combobox.get()
        if not label:
            messagebox.showerror("Error", "No label selected for deallocation.")
            return

        success = self.buddy_system.deallocate(label)
        if success:
            messagebox.showinfo("Success", f"Memory deallocated for label '{label}'.")
            self.update_dealloc_combobox()
            self.update_plot()
        else:
            messagebox.showerror("Error", f"Failed to deallocate memory for label '{label}'.")

class BuddySystem:
    def __init__(self, total_memory):
        self.total_memory = total_memory * 1024 * 1024
        self.free_blocks = {self.total_memory: [0]}
        self.allocated_blocks = {}
        self.label_to_address = {}

    def allocate(self, size, label):
        size = size * 1024 * 1024
        required_size = 2 ** math.ceil(math.log2(size))

        for block_size in sorted(self.free_blocks.keys()):
            if block_size >= required_size and self.free_blocks[block_size]:
                address = self.free_blocks[block_size].pop(0)
                while block_size > required_size:
                    block_size //= 2
                    buddy_address = address + block_size
                    self.free_blocks.setdefault(block_size, []).append(buddy_address)

                self.allocated_blocks[address] = (size, required_size)
                self.label_to_address[label] = address
                return address
        return None

    def deallocate(self, label):
        if label not in self.label_to_address:
            return False

        address = self.label_to_address.pop(label)
        if address not in self.allocated_blocks:
            return False

        size, block_size = self.allocated_blocks.pop(address)
        while True:
            buddy_address = address ^ block_size
            if buddy_address in self.free_blocks.get(block_size, []):
                self.free_blocks[block_size].remove(buddy_address)
                address = min(address, buddy_address)
                block_size *= 2
            else:
                break
        self.free_blocks.setdefault(block_size, []).append(address)
        return True

    def get_fragmentation(self):
        internal = 0
        external = 0
        for _, (size, block_size) in self.allocated_blocks.items():
            internal += block_size - size
        for block_size, blocks in self.free_blocks.items():
            external += len(blocks) * block_size
        return internal, external

if __name__ == "__main__":
    root = tk.Tk()
    app = BuddySystemGUI(root)
    root.mainloop()
