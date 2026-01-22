import tkinter as tk


class BasicInterface:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chef Bono")
        self.root.geometry("400x400")  # Make the window bigger
        self.root.configure(bg="black")  # Set background color to pitch black

        # Title Label
        self.title_label = tk.Label(
            self.root,
            text="Chef Bono",
            font=("Arial", 24, "bold"),
            fg="white",
            bg="black",
        )
        self.title_label.pack(pady=30)

        # Frame for buttons (centered)
        self.button_frame = tk.Frame(self.root, bg="black")
        self.button_frame.pack(expand=True)

        # Continue Button
        self.continue_btn = tk.Button(
            self.button_frame,
            text="Continue",
            command=self.on_continue,
            width=15,
            font=("Arial", 14),
            bg="gray20",
            fg="black",
        )
        self.continue_btn.pack(pady=10)

        # Stop Button
        self.stop_btn = tk.Button(
            self.button_frame,
            text="Stop",
            command=self.on_stop,
            width=15,
            font=("Arial", 14),
            bg="gray20",
            fg="black",
        )
        self.stop_btn.pack(pady=10)

        # Restart Button
        self.restart_btn = tk.Button(
            self.button_frame,
            text="Restart",
            command=self.on_restart,
            width=15,
            font=("Arial", 14),
            bg="gray20",
            fg="black",
        )
        self.restart_btn.pack(pady=10)

        # Exit Button
        self.exit_btn = tk.Button(
            self.button_frame,
            text="Exit",
            command=self.on_exit,
            width=15,
            font=("Arial", 14),
            bg="gray20",
            fg="black",
        )
        self.exit_btn.pack(pady=10)

    def on_continue(self):
        print("Continue pressed")

    def on_stop(self):
        print("Stop pressed")

    def on_restart(self):
        print("Restart pressed")
        self.root.destroy()
        self.__init__()
        self.run()

    def on_exit(self):
        print("Exit pressed")
        self.root.quit()=

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = BasicInterface()
    app.run()
