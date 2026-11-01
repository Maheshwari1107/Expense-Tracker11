import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
import math

DB_NAME = "expenses.db"


class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("1120x760")
        self.root.minsize(950, 650)
        self.root.configure(bg="#f6f1ff")

        self.conn = sqlite3.connect(DB_NAME)
        self.create_table()

        self.setup_style()
        self.build_ui()
        self.refresh_data()

        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

    def create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                expense_date TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Treeview",
            background="white",
            foreground="#302743",
            rowheight=29,
            fieldbackground="white",
            font=("Arial", 10)
        )
        style.configure(
            "Treeview.Heading",
            background="#e7dcff",
            foreground="#302743",
            font=("Arial", 10, "bold")
        )
        style.map("Treeview", background=[("selected", "#d9c7ff")])

    def build_ui(self):
        header = tk.Frame(self.root, bg="#7652b5", height=76)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="EXPENSE TRACKER", bg="#7652b5", fg="white",
            font=("Arial", 22, "bold")
        ).pack(side="left", padx=25, pady=18)

        tk.Label(
            header, text="Manage your money wisely", bg="#7652b5", fg="#f1eaff",
            font=("Arial", 11)
        ).pack(side="right", padx=25)

        dashboard = tk.Frame(self.root, bg="#f6f1ff")
        dashboard.pack(fill="x", padx=20, pady=(18, 10))

        self.total_value = self.make_stat_card(dashboard, "TOTAL EXPENSES", "₹0", 0)
        self.month_value = self.make_stat_card(dashboard, "THIS MONTH", "₹0", 1)
        self.count_value = self.make_stat_card(dashboard, "TRANSACTIONS", "0", 2)

        content = tk.Frame(self.root, bg="#f6f1ff")
        content.pack(fill="both", expand=True, padx=20, pady=8)

        left = tk.Frame(content, bg="white", highlightbackground="#e5dcf3", highlightthickness=1)
        left.pack(side="left", fill="y", padx=(0, 12), ipadx=12, ipady=10)

        tk.Label(left, text="Add New Expense", bg="white", fg="#4b3472",
                 font=("Arial", 15, "bold")).pack(anchor="w", padx=16, pady=(14, 12))

        self.title_var = tk.StringVar()
        self.amount_var = tk.StringVar()
        self.category_var = tk.StringVar(value="Food")
        self.date_var = tk.StringVar(value=date.today().isoformat())

        self.add_field(left, "Expense title", self.title_var)
        self.add_field(left, "Amount (₹)", self.amount_var)

        tk.Label(left, text="Category", bg="white", fg="#514761",
                 font=("Arial", 10, "bold")).pack(anchor="w", padx=16, pady=(10, 4))
        categories = ["Food", "Travel", "Shopping", "Education", "Bills", "Health", "Other"]
        category_box = ttk.Combobox(
            left, textvariable=self.category_var, values=categories,
            state="readonly", width=23
        )
        category_box.pack(anchor="w", padx=16)

        tk.Label(left, text="Date (YYYY-MM-DD)", bg="white", fg="#514761",
                 font=("Arial", 10, "bold")).pack(anchor="w", padx=16, pady=(12, 4))
        tk.Entry(left, textvariable=self.date_var, width=26, font=("Arial", 10),
                 relief="solid", bd=1).pack(anchor="w", padx=16)

        tk.Button(
            left, text="＋  Add Expense", command=self.add_expense,
            bg="#7652b5", fg="white", activebackground="#62419b",
            activeforeground="white", font=("Arial", 11, "bold"),
            relief="flat", padx=14, pady=9, cursor="hand2"
        ).pack(fill="x", padx=16, pady=(20, 8))

        tk.Button(
            left, text="Delete Selected", command=self.delete_expense,
            bg="#f3eafa", fg="#68459b", activebackground="#e8d9f7",
            font=("Arial", 10, "bold"), relief="flat", pady=8, cursor="hand2"
        ).pack(fill="x", padx=16, pady=4)

        tk.Button(
            left, text="Clear Search", command=self.clear_search,
            bg="#f7f4fb", fg="#514761", relief="flat", pady=7, cursor="hand2"
        ).pack(fill="x", padx=16, pady=4)

        right = tk.Frame(content, bg="#f6f1ff")
        right.pack(side="left", fill="both", expand=True)

        search_frame = tk.Frame(right, bg="white", padx=12, pady=10)
        search_frame.pack(fill="x", pady=(0, 10))

        tk.Label(search_frame, text="Search:", bg="white", fg="#514761",
                 font=("Arial", 10, "bold")).pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                font=("Arial", 10), relief="solid", bd=1)
        search_entry.pack(side="left", fill="x", expand=True, padx=10, ipady=5)
        search_entry.bind("<KeyRelease>", lambda event: self.refresh_data())

        table_frame = tk.Frame(right, bg="white", padx=10, pady=10)
        table_frame.pack(fill="both", expand=True)

        tk.Label(table_frame, text="Recent Transactions", bg="white", fg="#4b3472",
                 font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 8))

        columns = ("id", "title", "amount", "category", "date")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=9)
        headings = {
            "id": "ID", "title": "Title", "amount": "Amount (₹)",
            "category": "Category", "date": "Date"
        }
        widths = {"id": 45, "title": 180, "amount": 100, "category": 115, "date": 110}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")
        self.tree.pack(fill="both", expand=True)

        charts = tk.Frame(right, bg="#f6f1ff")
        charts.pack(fill="both", expand=True, pady=(10, 0))

        pie_card = tk.Frame(charts, bg="white", padx=10, pady=8)
        pie_card.pack(side="left", fill="both", expand=True, padx=(0, 6))
        bar_card = tk.Frame(charts, bg="white", padx=10, pady=8)
        bar_card.pack(side="left", fill="both", expand=True, padx=(6, 0))

        tk.Label(pie_card, text="Expenses by Category", bg="white", fg="#4b3472",
                 font=("Arial", 12, "bold")).pack(anchor="w")
        tk.Label(bar_card, text="Category Comparison", bg="white", fg="#4b3472",
                 font=("Arial", 12, "bold")).pack(anchor="w")

        self.pie_canvas = tk.Canvas(pie_card, bg="white", height=205, highlightthickness=0)
        self.pie_canvas.pack(fill="both", expand=True)
        self.bar_canvas = tk.Canvas(bar_card, bg="white", height=205, highlightthickness=0)
        self.bar_canvas.pack(fill="both", expand=True)

    def make_stat_card(self, parent, label, value, column):
        card = tk.Frame(parent, bg="white", highlightbackground="#e5dcf3", highlightthickness=1)
        card.grid(row=0, column=column, sticky="ew", padx=6)
        parent.grid_columnconfigure(column, weight=1)
        tk.Label(card, text=label, bg="white", fg="#81748f",
                 font=("Arial", 9, "bold")).pack(anchor="w", padx=16, pady=(12, 3))
        value_label = tk.Label(card, text=value, bg="white", fg="#68459b",
                               font=("Arial", 19, "bold"))
        value_label.pack(anchor="w", padx=16, pady=(0, 12))
        return value_label

    def add_field(self, parent, label, variable):
        tk.Label(parent, text=label, bg="white", fg="#514761",
                 font=("Arial", 10, "bold")).pack(anchor="w", padx=16, pady=(4, 4))
        tk.Entry(parent, textvariable=variable, width=26, font=("Arial", 10),
                 relief="solid", bd=1).pack(anchor="w", padx=16, ipady=5)

    def add_expense(self):
        title = self.title_var.get().strip()
        amount_text = self.amount_var.get().strip()
        category = self.category_var.get()
        expense_date = self.date_var.get().strip()

        if not title or not amount_text or not expense_date:
            messagebox.showwarning("Missing details", "Please fill in all fields.")
            return

        try:
            amount = float(amount_text)
            if not math.isfinite(amount) or amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid amount", "Enter a valid amount greater than 0.")
            return

        try:
            datetime.strptime(expense_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid date", "Use date format YYYY-MM-DD.")
            return

        self.conn.execute(
            "INSERT INTO expenses (title, amount, category, expense_date) VALUES (?, ?, ?, ?)",
            (title, amount, category, expense_date)
        )
        self.conn.commit()

        self.title_var.set("")
        self.amount_var.set("")
        self.date_var.set(date.today().isoformat())
        self.refresh_data()
        messagebox.showinfo("Success", "Expense added successfully!")

    def delete_expense(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select expense", "Please select a transaction to delete.")
            return

        item = self.tree.item(selected[0])
        expense_id = item["values"][0]
        if messagebox.askyesno("Confirm delete", "Delete the selected expense?"):
            self.conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            self.conn.commit()
            self.refresh_data()

    def clear_search(self):
        self.search_var.set("")
        self.refresh_data()

    def get_expenses(self):
        search_text = self.search_var.get().strip()
        if search_text:
            return self.conn.execute("""
                SELECT id, title, amount, category, expense_date
                FROM expenses
                WHERE title LIKE ? OR category LIKE ?
                ORDER BY expense_date DESC, id DESC
            """, (f"%{search_text}%", f"%{search_text}%")).fetchall()

        return self.conn.execute("""
            SELECT id, title, amount, category, expense_date
            FROM expenses
            ORDER BY expense_date DESC, id DESC
        """).fetchall()

    def refresh_data(self):
        rows = self.get_expenses()

        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in rows:
            self.tree.insert("", "end", values=(
                row[0], row[1], f"{row[2]:,.2f}", row[3], row[4]
            ))

        # Dashboard and charts use all saved expenses, not only search results.
        all_rows = self.conn.execute("""
            SELECT amount, category, expense_date FROM expenses
        """).fetchall()

        total = sum(row[0] for row in all_rows)
        today = date.today()
        month_total = sum(
            row[0] for row in all_rows
            if row[2][:7] == today.strftime("%Y-%m")
        )

        self.total_value.config(text=f"₹{total:,.2f}")
        self.month_value.config(text=f"₹{month_total:,.2f}")
        self.count_value.config(text=str(len(all_rows)))

        category_totals = {}
        for amount, category, _ in all_rows:
            category_totals[category] = category_totals.get(category, 0) + amount

        self.draw_pie_chart(category_totals)
        self.draw_bar_chart(category_totals)

    def draw_pie_chart(self, data):
        canvas = self.pie_canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 300)
        height = max(canvas.winfo_height(), 190)

        if not data or sum(data.values()) == 0:
            canvas.create_text(width / 2, height / 2, text="No expenses yet",
                               fill="#91869e", font=("Arial", 11))
            return

        colors = ["#7652b5", "#a88bd8", "#d2b9f0", "#f0a6ca",
                  "#8fc7bd", "#f2c879", "#91a8df"]
        total = sum(data.values())
        center_x, center_y = width * 0.34, height * 0.52
        radius = min(72, height * 0.37)
        start_angle = 0

        for index, (category, amount) in enumerate(sorted(data.items())):
            extent = amount / total * 360
            color = colors[index % len(colors)]
            canvas.create_arc(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                start=start_angle, extent=extent,
                fill=color, outline="white", width=2
            )
            start_angle += extent

        legend_x = width * 0.62
        legend_y = max(18, height * 0.18)
        for index, (category, amount) in enumerate(sorted(data.items())):
            y = legend_y + index * 23
            color = colors[index % len(colors)]
            canvas.create_rectangle(legend_x, y, legend_x + 11, y + 11,
                                    fill=color, outline=color)
            percent = amount / total * 100
            canvas.create_text(
                legend_x + 17, y + 5, anchor="w",
                text=f"{category} {percent:.0f}%",
                fill="#514761", font=("Arial", 8)
            )

    def draw_bar_chart(self, data):
        canvas = self.bar_canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 300)
        height = max(canvas.winfo_height(), 190)

        if not data:
            canvas.create_text(width / 2, height / 2, text="No expenses yet",
                               fill="#91869e", font=("Arial", 11))
            return

        items = sorted(data.items(), key=lambda item: item[1], reverse=True)
        max_value = max(value for _, value in items) or 1
        left, right = 38, width - 12
        top, bottom = 18, height - 30
        chart_height = bottom - top
        bar_gap = 9
        bar_width = max(12, (right - left - bar_gap * len(items)) / len(items))
        colors = ["#7652b5", "#a88bd8", "#d2b9f0", "#f0a6ca",
                  "#8fc7bd", "#f2c879", "#91a8df"]

        canvas.create_line(left, top, left, bottom, fill="#cfc5dc")
        canvas.create_line(left, bottom, right, bottom, fill="#cfc5dc")

        for index, (category, amount) in enumerate(items):
            x1 = left + index * (bar_width + bar_gap) + 4
            x2 = x1 + bar_width
            bar_height = amount / max_value * (chart_height - 18)
            y1 = bottom - bar_height
            color = colors[index % len(colors)]
            canvas.create_rectangle(x1, y1, x2, bottom, fill=color, outline="")
            canvas.create_text((x1 + x2) / 2, max(top + 5, y1 - 8),
                               text=f"{amount:.0f}", fill="#514761",
                               font=("Arial", 7))
            label = category if len(category) <= 8 else category[:7] + "…"
            canvas.create_text((x1 + x2) / 2, bottom + 12,
                               text=label, fill="#514761",
                               font=("Arial", 7))

    def close_app(self):
        self.conn.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()