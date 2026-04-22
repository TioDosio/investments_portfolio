import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt


def get_investment_growth(ticker_symbol, share_volume, purchase_price, period="1y"):
    """
    Calculates returns and plots growth for a given stock/ETF.
    Periods: '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'
    """
    # 1. Download Historical Data
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period=period)
    
    if df.empty:
        print(f"No data found for {ticker_symbol}. Check the ticker symbol.")
        return None

    # 2. Calculate Value and Returns
    current_price = df['Close'].iloc[-1]
    initial_investment = share_volume * purchase_price
    current_value = share_volume * current_price
    total_return = current_value - initial_investment
    percent_return = (total_return / initial_investment) * 100

    # Create a 'Growth' column based on the volume held
    df['Portfolio_Value'] = df['Close'] * share_volume
    
    # 3. Print Summary
    print(f"--- {ticker_symbol} Summary ---")
    print(f"Current Price: ${current_price:.2f}")
    print(f"Total Return: ${total_return:.2f} ({percent_return:.2f}%)")
    print(f"Current Portfolio Value: ${current_value:.2f}")

    return {
        "ticker_symbol": ticker_symbol,
        "period": period,
        "history": df,
    }

def print_chart(results):
    """
    Plots the growth of the investment over time.
    """
    plt.figure(figsize=(12, 6))
    for result in results:
        ticker_symbol = result["ticker_symbol"]
        period = result["period"]
        df_history = result["history"]
        plt.plot(df_history.index, df_history["Portfolio_Value"], linewidth=2, label=f"{ticker_symbol} ({period})")

    plt.title("Investment Growth Comparison")
    plt.xlabel("Date")
    plt.ylabel("Value (EUR)")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()


def print_price_growth_chart(results):
    """
    Plots each ETF close-price growth (%) for the last year and the average growth line.
    """
    growth_series = []

    plt.figure(figsize=(12, 6))
    for result in results:
        ticker_symbol = result["ticker_symbol"]
        df_history = result["history"]

        if df_history.empty:
            continue

        last_date = df_history.index.max()
        one_year_ago = last_date - pd.Timedelta(days=365)
        df_last_year = df_history[df_history.index >= one_year_ago]

        if df_last_year.empty:
            continue

        price_growth = (df_last_year["Close"] / df_last_year["Close"].iloc[0] - 1) * 100
        growth_series.append(price_growth.rename(ticker_symbol))
        plt.plot(price_growth.index, price_growth.values, linewidth=1.8, label=ticker_symbol)

    if not growth_series:
        print("No valid ETF price data available to plot growth chart.")
        return

    growth_df = pd.concat(growth_series, axis=1)
    average_growth = growth_df.mean(axis=1, skipna=True)
    plt.plot(
        average_growth.index,
        average_growth.values,
        color="black",
        linewidth=2.8,
        linestyle="--",
        label="Average Growth",
    )

    plt.title("ETF Price Growth (Last Year)")
    plt.xlabel("Date")
    plt.ylabel("Growth (%)")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()

def main(csv_path="etfs.csv"):
    """
    Loads ETF positions from CSV and runs calculations for each row.
    Required columns: ticker_symbol, share_volume, purchase_price
    """
    df_input = pd.read_csv(csv_path)

    required_columns = {"ticker_symbol", "share_volume", "purchase_price"}
    missing_columns = required_columns - set(df_input.columns)
    if missing_columns:
        raise ValueError(f"Missing required column(s): {', '.join(sorted(missing_columns))}")

    results = []

    for _, row in df_input.iterrows():
        ticker_symbol = str(row["ticker_symbol"]).strip()
        share_volume = float(row["share_volume"])
        purchase_price = float(row["purchase_price"])
        period = str("1y").strip()

        result = get_investment_growth(
            ticker_symbol=ticker_symbol,
            share_volume=share_volume,
            purchase_price=purchase_price,
            period=period,
        )

        if result is not None:
            results.append(result)

    if not results:
        print("No valid ETF data available to plot.")
        return

    print_chart(results)
    print_price_growth_chart(results)
    

if __name__ == "__main__":
    main()