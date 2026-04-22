import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import portfolio_logic
import sheets_api
from datetime import datetime

class PortfolioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Investment Portfolio Helper")
        self.root.geometry("1200x800")
        
        self.assets = []
        self.portfolio_data = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Top Control Panel
        control_frame = ttk.LabelFrame(self.root, text="Step 1: Input & Import", padding=10)
        control_frame.pack(side="top", fill="x", padx=10, pady=5)
        
        # Input fields
        input_inner = ttk.Frame(control_frame)
        input_inner.pack(side="left", fill="x", expand=True)
        
        ttk.Label(input_inner, text="Ticker:").grid(row=0, column=0, padx=5)
        self.ticker_entry = ttk.Entry(input_inner, width=10)
        self.ticker_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(input_inner, text="Volume:").grid(row=0, column=2, padx=5)
        self.volume_entry = ttk.Entry(input_inner, width=10)
        self.volume_entry.grid(row=0, column=3, padx=5)
        
        ttk.Label(input_inner, text="Avg Price:").grid(row=0, column=4, padx=5)
        self.price_entry = ttk.Entry(input_inner, width=10)
        self.price_entry.grid(row=0, column=5, padx=5)
        
        ttk.Button(input_inner, text="Add Asset", command=self.add_asset).grid(row=0, column=6, padx=10)
        
        # Import and Sheets Buttons
        action_inner = ttk.Frame(control_frame)
        action_inner.pack(side="right")
        
        ttk.Button(action_inner, text="Import CSV", command=self.import_csv).pack(side="left", padx=5)
        ttk.Button(action_inner, text="Run Analysis", command=self.run_analysis).pack(side="left", padx=5)
        ttk.Button(action_inner, text="Push to Sheets", command=self.push_to_sheets).pack(side="left", padx=5)
        
        # Main Display Area
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(side="top", fill="both", expand=True, padx=10, pady=5)
        
        # Tab 1: Summary Table
        self.summary_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_tab, text="Summary")
        self.tree = ttk.Treeview(self.summary_tab, columns=("Ticker", "Current Price", "Avg Price", "Profit ($)", "Profit (%)", "Value ($)"), show='headings')
        for col in self.tree['columns']:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(fill="both", expand=True)
        
        # Tab 2: Growth Chart
        self.chart_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.chart_tab, text="Growth Charts")
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_tab)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Tab 3: Predictions
        self.pred_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.pred_tab, text="Future Predictions")
        
        pred_control = ttk.Frame(self.pred_tab)
        pred_control.pack(side="top", fill="x", pady=5)
        ttk.Label(pred_control, text="Monthly Top-up ($):").pack(side="left", padx=5)
        self.topup_entry = ttk.Entry(pred_control, width=10)
        self.topup_entry.insert(0, "0")
        self.topup_entry.pack(side="left", padx=5)
        ttk.Button(pred_control, text="Predict", command=self.update_prediction).pack(side="left", padx=10)
        
        self.fig_pred, self.ax_pred = plt.subplots(figsize=(10, 6))
        self.canvas_pred = FigureCanvasTkAgg(self.fig_pred, master=self.pred_tab)
        self.canvas_pred.get_tk_widget().pack(fill="both", expand=True)

    def add_asset(self):
        try:
            ticker = self.ticker_entry.get().upper()
            volume = float(self.volume_entry.get())
            price = float(self.price_entry.get())
            self.assets.append({'ticker': ticker, 'volume': volume, 'avg_price': price})
            messagebox.showinfo("Success", f"Added {ticker}")
        except ValueError:
            messagebox.showerror("Error", "Invalid volume or price")

    def import_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                df = pd.read_csv(file_path)
                for _, row in df.iterrows():
                    self.assets.append({
                        'ticker': str(row['ticker_symbol']).upper(),
                        'volume': float(row['share_volume']),
                        'avg_price': float(row['purchase_price'])
                    })
                messagebox.showinfo("Success", f"Imported {len(df)} assets")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import: {e}")

    def run_analysis(self):
        if not self.assets:
            messagebox.showwarning("Warning", "No assets added yet")
            return
            
        self.portfolio_data = portfolio_logic.get_portfolio_data(self.assets)
        self.update_summary()
        self.update_charts()
        
    def update_summary(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for res in self.portfolio_data['individual']:
            self.tree.insert("", "end", values=(
                res['ticker'], 
                f"{res['current_price']:.2f}", 
                f"{res['avg_price']:.2f}", 
                f"{res['profit_abs']:.2f}", 
                f"{res['profit_pct']:.2f}%", 
                f"{res['current_value']:.2f}"
            ))
            
    def update_charts(self):
        self.ax.clear()
        data = self.portfolio_data
        self.ax.plot(data['normalized'].index, data['normalized'].values, label="Portfolio")
        self.ax.plot(data['sp500_normalized'].index, data['sp500_normalized'].values, label="S&P 500", linestyle="--")
        self.ax.set_title("Portfolio vs S&P 500 (Normalized)")
        self.ax.legend()
        self.canvas.draw()
        
    def update_prediction(self):
        if self.portfolio_data is None:
            return
            
        try:
            topup = float(self.topup_entry.get())
        except ValueError:
            topup = 0
            
        pred = portfolio_logic.make_predictions(self.portfolio_data['history'], monthly_topup=topup)
        if pred is not None:
            self.ax_pred.clear()
            hist = self.portfolio_data['history']['Total']
            self.ax_pred.plot(hist.index, hist.values, label="Historical")
            self.ax_pred.plot(pred.index, pred.values, label="Predicted", linestyle=":")
            self.ax_pred.set_title("Future Portfolio Prediction")
            self.ax_pred.legend()
            self.canvas_pred.draw()

    def push_to_sheets(self):
        if not self.portfolio_data:
            messagebox.showwarning("Warning", "Run analysis first")
            return
            
        success = sheets_api.push_to_sheets(self.portfolio_data['individual'], "Portfolio_Summary")
        if success:
            messagebox.showinfo("Success", "Data pushed to Google Sheets")
        else:
            messagebox.showerror("Error", "Failed to push to Sheets. Check credentials.json")

if __name__ == "__main__":
    root = tk.Tk()
    app = PortfolioApp(root)
    root.mainloop()
