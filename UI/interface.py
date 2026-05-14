import tkinter as tk
from tkinter import scrolledtext


class ChefBonoUI:
    # ── Professional Color Palette ──
    BG = "#FFFAF5"  # warm off-white
    BG_CARD = "#FFFFFF"
    BG_INPUT = "#FFF7F0"
    BG_CHAT = "#FFFBF7"
    ORANGE = "#F4845F"  # primary accent
    ORANGE_DARK = "#E06B44"
    ORANGE_LIGHT = "#FFF0E8"
    GREEN = "#34C77B"
    GREEN_BG = "#EAFAF2"
    RED = "#EF6461"
    RED_BG = "#FDECEC"
    DARK = "#1A1A2E"  # near-black text
    TEXT = "#2D2D3F"
    TEXT_SEC = "#6B7280"
    TEXT_MUTED = "#9CA3AF"
    BORDER = "#F0E6DB"
    BORDER_LIGHT = "#F5EDE4"
    SHADOW_BG = "#FDF3EB"

    FONT = "Segoe UI"
    FONT_TITLE = "Segoe UI"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chef Bono — AI Cooking Assistant")
        self.root.geometry("1150x720")
        self.root.configure(bg=self.BG)
        self.root.resizable(False, False)

        self.current_recipe = "No recipe selected"
        self.current_step = 0
        self.is_running = False

        self.recipes = {
            "Chicken Curry": [
                "Chop the onions.",
                "Heat oil in the pan.",
                "Add onions and sauté until golden.",
                "Add spices and chicken.",
                "Cook until the chicken is ready.",
                "Serve hot.",
            ],
            "Tomato Pasta": [
                "Boil the pasta.",
                "Prepare tomato sauce.",
                "Mix pasta with sauce.",
                "Add seasoning.",
                "Serve warm.",
            ],
            "Vegetable Soup": [
                "Chop the vegetables.",
                "Boil water.",
                "Add vegetables.",
                "Cook until soft.",
                "Serve warm.",
            ],
        }
        self.steps = []

        self.container = tk.Frame(self.root, bg=self.BG)
        self.container.pack(fill="both", expand=True)

        self.show_home()

    def clear(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    # ── Pill-style button ──
    def pill_btn(
        self,
        parent,
        text,
        command,
        bg=None,
        fg="white",
        width=20,
        font_size=12,
        icon="",
    ):
        if bg is None:
            bg = self.ORANGE
        display = f"{icon}  {text}" if icon else text
        btn = tk.Button(
            parent,
            text=display,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=bg,
            activeforeground=fg,
            font=(self.FONT, font_size, "bold"),
            relief="flat",
            bd=0,
            width=width,
            pady=11,
            padx=16,
            cursor="hand2",
            highlightthickness=0,
        )
        return btn

    # ── Section header ──
    def heading(self, parent, text, size=20, color=None, bg=None):
        if color is None:
            color = self.DARK
        if bg is None:
            bg = self.BG
        return tk.Label(
            parent, text=text, font=(self.FONT_TITLE, size, "bold"), fg=color, bg=bg
        )

    # ── Subtle badge / tag ──
    def badge(self, parent, text, bg=None, fg=None):
        if bg is None:
            bg = self.ORANGE_LIGHT
        if fg is None:
            fg = self.ORANGE
        lbl = tk.Label(
            parent,
            text=f"  {text}  ",
            font=(self.FONT, 10, "bold"),
            fg=fg,
            bg=bg,
            pady=4,
            padx=8,
        )
        return lbl

    # ══════════════════════════════════════════
    #  HOME SCREEN
    # ══════════════════════════════════════════
    def show_home(self):
        self.clear()
        self.is_running = False

        # ── Navbar ──
        nav = tk.Frame(self.container, bg=self.BG, height=56)
        nav.pack(fill="x", padx=40, pady=(20, 0))
        nav.pack_propagate(False)

        tk.Label(
            nav,
            text="🍳 Chef Bono",
            font=(self.FONT_TITLE, 18, "bold"),
            fg=self.DARK,
            bg=self.BG,
        ).pack(side="left")

        tk.Label(
            nav,
            text="AI-Powered Cooking Assistant",
            font=(self.FONT, 11),
            fg=self.TEXT_MUTED,
            bg=self.BG,
        ).pack(side="left", padx=20)

        # version badge
        self.badge(nav, "v1.0").pack(side="right")

        # ── Divider ──
        tk.Frame(self.container, bg=self.BORDER, height=1).pack(
            fill="x", padx=40, pady=(8, 0)
        )

        # ── Hero section ──
        hero = tk.Frame(self.container, bg=self.BG)
        hero.pack(expand=True, fill="both", padx=60)

        # Left content
        left = tk.Frame(hero, bg=self.BG)
        left.pack(side="left", fill="both", expand=True, pady=30)

        self.badge(left, "✦  AI-Powered Voice Assistant").pack(
            anchor="w", pady=(20, 18)
        )

        # Title
        tk.Label(
            left,
            text="Your Personal",
            font=(self.FONT_TITLE, 36, "bold"),
            fg=self.DARK,
            bg=self.BG,
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            left,
            text="Chef Assistant",
            font=(self.FONT_TITLE, 36, "bold"),
            fg=self.ORANGE,
            bg=self.BG,
            anchor="w",
        ).pack(anchor="w", pady=(0, 15))

        tk.Label(
            left,
            text="Talk with Bono and get step-by-step cooking guidance.\n"
            "Voice-controlled, AI-powered, and always ready to help\n"
            "you create delicious meals effortlessly.",
            font=(self.FONT, 13),
            fg=self.TEXT_SEC,
            bg=self.BG,
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(0, 30))

        # Stats row
        stats = tk.Frame(left, bg=self.BG)
        stats.pack(anchor="w", pady=(0, 30))
        self._stat_item(stats, "🍽", "50+", "Recipes", 0)
        self._stat_item(stats, "🎤", "Voice", "Controlled", 1)
        self._stat_item(stats, "⚡", "Real-time", "AI Feedback", 2)

        # CTA buttons
        btn_row = tk.Frame(left, bg=self.BG)
        btn_row.pack(anchor="w")

        self.pill_btn(
            btn_row,
            "Start Cooking",
            self.start_and_go,
            bg=self.ORANGE,
            width=18,
            icon="▶",
        ).pack(side="left", padx=(0, 12))
        self.pill_btn(
            btn_row,
            "Exit",
            self.root.quit,
            bg=self.BG_CARD,
            fg=self.TEXT_SEC,
            width=12,
            icon="✕",
        ).pack(side="left")

        # Right side – decorative card
        right = tk.Frame(hero, bg=self.BG, width=400)
        right.pack(side="right", fill="y", padx=(30, 0), pady=30)
        right.pack_propagate(False)

        card = tk.Frame(
            right,
            bg=self.SHADOW_BG,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        card.pack(expand=True, fill="both", padx=10, pady=10)

        tk.Label(card, text="🧑‍🍳", font=(self.FONT, 52), bg=self.SHADOW_BG).pack(
            pady=(40, 10)
        )
        tk.Label(
            card,
            text="Chef Bono",
            font=(self.FONT_TITLE, 22, "bold"),
            fg=self.DARK,
            bg=self.SHADOW_BG,
        ).pack()
        tk.Label(
            card,
            text="Ready to assist you",
            font=(self.FONT, 12),
            fg=self.TEXT_MUTED,
            bg=self.SHADOW_BG,
        ).pack(pady=(4, 15))

        # Feature pills inside card
        for feat in ["Voice Recognition", "Smart Recipes", "Step Guidance"]:
            f = tk.Frame(
                card,
                bg=self.BG_CARD,
                highlightbackground=self.BORDER,
                highlightthickness=1,
            )
            f.pack(pady=4, padx=40, fill="x")
            tk.Label(
                f,
                text=f"  ✓  {feat}",
                font=(self.FONT, 11),
                fg=self.TEXT,
                bg=self.BG_CARD,
                anchor="w",
                pady=8,
                padx=8,
            ).pack(fill="x")

        # ── Bottom bar ──
        bottom = tk.Frame(self.container, bg=self.BG, height=40)
        bottom.pack(fill="x", padx=40, pady=(0, 10))
        tk.Label(
            bottom,
            text="© 2026 Chef Bono — Built with AI",
            font=(self.FONT, 9),
            fg=self.TEXT_MUTED,
            bg=self.BG,
        ).pack(side="left")

    def _stat_item(self, parent, icon, value, label, col):
        f = tk.Frame(parent, bg=self.BG)
        f.pack(side="left", padx=(0, 35))
        tk.Label(f, text=icon, font=(self.FONT, 16), fg=self.ORANGE, bg=self.BG).pack()
        tk.Label(
            f, text=value, font=(self.FONT_TITLE, 18, "bold"), fg=self.DARK, bg=self.BG
        ).pack()
        tk.Label(
            f, text=label, font=(self.FONT, 10), fg=self.TEXT_MUTED, bg=self.BG
        ).pack()

    def start_and_go(self):
        self.is_running = True
        self.show_chat_screen()

    # ══════════════════════════════════════════
    #  CHAT SCREEN
    # ══════════════════════════════════════════
    def show_chat_screen(self):
        self.clear()

        # ── Navbar ──
        nav = tk.Frame(self.container, bg=self.BG, height=50)
        nav.pack(fill="x", padx=30, pady=(15, 0))
        nav.pack_propagate(False)

        tk.Label(
            nav,
            text="🍳 Chef Bono",
            font=(self.FONT_TITLE, 16, "bold"),
            fg=self.DARK,
            bg=self.BG,
        ).pack(side="left")

        self.pill_btn(
            nav, "Stop", self.stop_bono, bg=self.RED, width=10, font_size=10, icon="⏹"
        ).pack(side="right")

        # Status
        status_f = tk.Frame(nav, bg=self.GREEN_BG, padx=10, pady=3)
        status_f.pack(side="right", padx=12)
        tk.Label(
            status_f,
            text="● Active",
            font=(self.FONT, 10, "bold"),
            fg=self.GREEN,
            bg=self.GREEN_BG,
        ).pack()

        self.badge(nav, "Chat Mode").pack(side="right", padx=8)

        tk.Frame(self.container, bg=self.BORDER, height=1).pack(
            fill="x", padx=30, pady=(8, 0)
        )

        # ── Chat card ──
        chat_card = tk.Frame(
            self.container,
            bg=self.BG_CARD,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        chat_card.pack(fill="both", expand=True, padx=30, pady=(12, 15))

        # Header
        hdr = tk.Frame(chat_card, bg=self.BG_CARD)
        hdr.pack(fill="x", padx=25, pady=(18, 0))

        tk.Label(hdr, text="💬", font=(self.FONT, 20), bg=self.BG_CARD).pack(
            side="left"
        )
        hdr_text = tk.Frame(hdr, bg=self.BG_CARD)
        hdr_text.pack(side="left", padx=10)
        tk.Label(
            hdr_text,
            text="Conversation with Bono",
            font=(self.FONT_TITLE, 15, "bold"),
            fg=self.DARK,
            bg=self.BG_CARD,
        ).pack(anchor="w")
        tk.Label(
            hdr_text,
            text="Ask anything about cooking — Bono is here to help.",
            font=(self.FONT, 10),
            fg=self.TEXT_MUTED,
            bg=self.BG_CARD,
        ).pack(anchor="w")

        tk.Frame(chat_card, bg=self.BORDER, height=1).pack(
            fill="x", padx=25, pady=(12, 0)
        )

        # Chat area
        self.chat_area = scrolledtext.ScrolledText(
            chat_card,
            height=18,
            bg=self.BG_CHAT,
            fg=self.TEXT,
            font=(self.FONT, 12),
            relief="flat",
            wrap="word",
            highlightbackground=self.BORDER_LIGHT,
            highlightthickness=1,
            padx=14,
            pady=12,
            selectbackground=self.ORANGE_LIGHT,
            selectforeground=self.TEXT,
        )
        self.chat_area.pack(fill="both", expand=True, padx=25, pady=(12, 8))
        self.chat_area.insert(
            tk.END, "🧑‍🍳 Bono:  Hi! What would you like to cook today?\n"
        )
        self.chat_area.config(state="disabled")

        # Input row
        input_row = tk.Frame(chat_card, bg=self.BG_CARD)
        input_row.pack(fill="x", padx=25, pady=(0, 6))

        self.chat_entry = tk.Entry(
            input_row,
            font=(self.FONT, 13),
            bg=self.BG_INPUT,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.BORDER,
        )
        self.chat_entry.pack(side="left", fill="x", expand=True, ipady=10)
        self.chat_entry.bind("<Return>", lambda e: self.send_chat_message())

        send = self.pill_btn(
            input_row,
            "Send",
            self.send_chat_message,
            bg=self.ORANGE,
            width=6,
            font_size=11,
            icon="➤",
        )
        send.pack(side="right", padx=(8, 0))

        # Bottom actions
        actions = tk.Frame(chat_card, bg=self.BG_CARD)
        actions.pack(pady=(0, 14))

        self.pill_btn(
            actions,
            "Talk to Bono",
            self.simulate_voice_choice,
            bg=self.ORANGE_LIGHT,
            fg=self.ORANGE,
            width=16,
            font_size=11,
            icon="🎤",
        ).pack(side="left", padx=5)
        self.pill_btn(
            actions,
            "Back",
            self.show_home,
            bg=self.BG_INPUT,
            fg=self.TEXT_SEC,
            width=10,
            font_size=11,
            icon="←",
        ).pack(side="left", padx=5)

    # ── Chat helpers ──
    def add_chat(self, sender, message):
        self.chat_area.config(state="normal")
        prefix = "🧑‍🍳 " if sender == "Bono" else "🙋 "
        self.chat_area.insert(tk.END, f"{prefix}{sender}:  {message}\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state="disabled")

    def send_chat_message(self):
        message = self.chat_entry.get().strip()
        if not message:
            return
        self.add_chat("You", message)
        self.chat_entry.delete(0, tk.END)

        lower = message.lower()
        if "chicken" in lower:
            self.add_chat("Bono", "Great choice! I selected Chicken Curry for you.")
        elif "pasta" in lower:
            self.add_chat("Bono", "Nice! I selected Tomato Pasta for you.")
        elif "soup" in lower:
            self.add_chat("Bono", "Healthy choice! I selected Vegetable Soup for you.")
        else:
            self.add_chat(
                "Bono",
                "I can help you choose Chicken Curry, Tomato Pasta, or Vegetable Soup.",
            )

    def simulate_voice_choice(self):
        self.add_chat("You", "[voice input detected]")
        self.add_chat("Bono", "Based on your voice request, I suggest Chicken Curry.")

    def stop_bono(self):
        self.is_running = False
        self.show_home()

    #  COOKING SCREEN

    def show_cooking_screen(self):
        self.clear()

        # Navbar
        nav = tk.Frame(self.container, bg=self.BG, height=50)
        nav.pack(fill="x", padx=30, pady=(15, 0))
        nav.pack_propagate(False)

        tk.Label(
            nav,
            text="🍳 Chef Bono",
            font=(self.FONT_TITLE, 16, "bold"),
            fg=self.DARK,
            bg=self.BG,
        ).pack(side="left")

        self.pill_btn(
            nav, "Stop", self.stop_bono, bg=self.RED, width=10, font_size=10, icon="⏹"
        ).pack(side="right")

        tk.Frame(self.container, bg=self.BORDER, height=1).pack(
            fill="x", padx=30, pady=(8, 0)
        )

        # Recipe title
        title_bar = tk.Frame(self.container, bg=self.BG)
        title_bar.pack(fill="x", padx=35, pady=(10, 5))
        self.heading(title_bar, "Cooking Assistant", 20).pack(side="left")
        self.badge(
            title_bar,
            f"📋  {self.current_recipe}",
            bg=self.ORANGE_LIGHT,
            fg=self.ORANGE,
        ).pack(side="left", padx=15)

        main = tk.Frame(self.container, bg=self.BG)
        main.pack(fill="both", expand=True, padx=30, pady=(5, 15))

        # Camera panel
        cam = tk.Frame(
            main,
            bg=self.BG_CARD,
            width=390,
            height=460,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        cam.pack(side="left", fill="y", padx=(0, 12))
        cam.pack_propagate(False)

        self.heading(cam, "📷  Camera", 16, bg=self.BG_CARD).pack(pady=(18, 10))

        cam_box = tk.Frame(
            cam,
            bg=self.BG_INPUT,
            width=330,
            height=220,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        cam_box.pack(pady=8)
        cam_box.pack_propagate(False)
        tk.Label(
            cam_box,
            text="[ Camera preview ]\n\nBono captures a frame\nwhen you speak.",
            font=(self.FONT, 11),
            fg=self.TEXT_MUTED,
            bg=self.BG_INPUT,
            justify="center",
        ).pack(expand=True)

        self.camera_status = tk.Label(
            cam,
            text="📡  Waiting for voice input...",
            font=(self.FONT, 11),
            fg=self.ORANGE,
            bg=self.BG_CARD,
            wraplength=320,
            justify="left",
        )
        self.camera_status.pack(padx=20, pady=12)

        self.pill_btn(
            cam,
            "Ask Bono",
            self.ask_bono_during_cooking,
            bg=self.ORANGE,
            width=18,
            icon="🎤",
        ).pack(pady=8)

        # Instructions panel
        inst = tk.Frame(
            main,
            bg=self.BG_CARD,
            width=690,
            height=460,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        inst.pack(side="left", fill="both", expand=True)
        inst.pack_propagate(False)

        self.heading(inst, "Step-by-Step Instructions", 16, bg=self.BG_CARD).pack(
            anchor="w", padx=25, pady=(18, 10)
        )

        self.step_label = tk.Label(
            inst,
            text=self.get_step_text(),
            font=(self.FONT_TITLE, 16, "bold"),
            fg=self.TEXT,
            bg=self.BG_INPUT,
            wraplength=540,
            justify="left",
            width=42,
            height=4,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        self.step_label.pack(padx=25, pady=8)

        controls = tk.Frame(inst, bg=self.BG_CARD)
        controls.pack(anchor="w", padx=25, pady=6)
        self.pill_btn(
            controls,
            "Next",
            self.next_step,
            bg=self.GREEN,
            width=11,
            font_size=11,
            icon="→",
        ).pack(side="left", padx=(0, 8))
        self.pill_btn(
            controls,
            "Repeat",
            self.repeat_step,
            bg=self.BG_INPUT,
            fg=self.TEXT_SEC,
            width=11,
            font_size=11,
            icon="🔁",
        ).pack(side="left", padx=(0, 8))
        self.pill_btn(
            controls,
            "Finish",
            self.finish_cooking,
            bg=self.RED,
            width=11,
            font_size=11,
            icon="✓",
        ).pack(side="left")

        # Feedback section
        tk.Frame(inst, bg=self.BORDER, height=1).pack(fill="x", padx=25, pady=(12, 8))

        self.heading(
            inst, "💬  Bono Feedback", 14, bg=self.BG_CARD, color=self.ORANGE
        ).pack(anchor="w", padx=25, pady=(0, 5))

        self.feedback_label = tk.Label(
            inst,
            text="🧑‍🍳 Bono:  I am ready. Ask me anything while cooking.",
            font=(self.FONT, 12),
            fg=self.TEXT_SEC,
            bg=self.BG_INPUT,
            wraplength=540,
            justify="left",
            width=50,
            height=3,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        self.feedback_label.pack(padx=25, pady=6)

        self.pill_btn(
            inst,
            "Back to Chat",
            self.show_chat_screen,
            bg=self.BG_INPUT,
            fg=self.TEXT_SEC,
            width=16,
            font_size=11,
            icon="←",
        ).pack(anchor="w", padx=25, pady=8)

    def get_step_text(self):
        return f"Step {self.current_step + 1}:  {self.steps[self.current_step]}"

    def next_step(self):
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.step_label.config(text=self.get_step_text())
            self.feedback_label.config(
                text="🧑‍🍳 Bono:  Good. Let's continue with the next step."
            )
        else:
            self.feedback_label.config(
                text="🧑‍🍳 Bono:  This is the last step. Your meal is almost ready."
            )

    def repeat_step(self):
        self.feedback_label.config(
            text=f"🧑‍🍳 Bono:  Sure. {self.steps[self.current_step]}"
        )

    def ask_bono_during_cooking(self):
        self.camera_status.config(text="📡  Frame captured after voice input.")
        self.feedback_label.config(
            text="🧑‍🍳 Bono:  I checked the camera frame. Everything looks good — keep watching the heat."
        )

    #  FINISH SCREEN

    def finish_cooking(self):
        self.clear()
        self.is_running = False

        frame = tk.Frame(self.container, bg=self.BG)
        frame.pack(expand=True)

        # Success icon
        tk.Label(
            frame, text="✓", font=(self.FONT, 52, "bold"), fg=self.GREEN, bg=self.BG
        ).pack(pady=(0, 5))

        self.heading(frame, "Dish is Ready!", 30, color=self.DARK).pack(pady=(0, 8))

        tk.Label(
            frame,
            text=f"{self.current_recipe} is complete.",
            font=(self.FONT, 16),
            fg=self.TEXT,
            bg=self.BG,
        ).pack(pady=(0, 5))

        tk.Label(
            frame,
            text="🧑‍🍳 Bono says: Don't forget to clean the counter and cutting board.",
            font=(self.FONT, 13),
            fg=self.TEXT_SEC,
            bg=self.BG,
        ).pack(pady=(0, 30))

        self.pill_btn(
            frame, "Back to Home", self.show_home, bg=self.ORANGE, width=20, icon="←"
        ).pack(pady=6)
        self.pill_btn(
            frame,
            "Exit",
            self.root.quit,
            bg=self.BG_CARD,
            fg=self.TEXT_SEC,
            width=14,
            icon="✕",
        ).pack(pady=6)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ChefBonoUI()
    app.run()
