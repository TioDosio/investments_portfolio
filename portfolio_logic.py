import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_portfolio_data(assets, period="5y"):
    """
    assets: list of dicts with {'ticker': str, 'volume': float, 'avg_price': float}
    """
    portfolio_history = pd.DataFrame()
    individual_results = []
    
    # Get S&P 500 for comparison
    sp500 = yf.Ticker("^GSPC").history(period=period)['Close']
    sp500_normalized = sp500 / sp500.iloc[0] * 100

    for asset in assets:
        ticker = asset['ticker']
        volume = asset['volume']
        avg_price = asset['avg_price']
        
        data = yf.Ticker(ticker).history(period=period)
        if data.empty:
            continue
            
        current_price = data['Close'].iloc[-1]
        current_value = volume * current_price
        initial_investment = volume * avg_price
        profit_abs = current_value - initial_investment
        profit_pct = (profit_abs / initial_investment) * 100 if initial_investment != 0 else 0
        
        # Historical growth of this asset in the portfolio
        asset_history = data['Close'] * volume
        if portfolio_history.empty:
            portfolio_history = asset_history.to_frame(name=ticker)
        else:
            portfolio_history[ticker] = asset_history

        individual_results.append({
            'ticker': ticker,
            'current_price': current_price,
            'avg_price': avg_price,
            'profit_abs': profit_abs,
            'profit_pct': profit_pct,
            'current_value': current_value
        })

    portfolio_history['Total'] = portfolio_history.sum(axis=1)
    portfolio_normalized = portfolio_history['Total'] / portfolio_history['Total'].iloc[0] * 100
    
    return {
        'individual': individual_results,
        'history': portfolio_history,
        'normalized': portfolio_normalized,
        'sp500_normalized': sp500_normalized
    }

def make_predictions(portfolio_history, years=5, monthly_topup=0):
    """
    Simple prediction based on historical CAGR
    """
    if portfolio_history.empty or 'Total' not in portfolio_history.columns:
        return None
        
    total_series = portfolio_history['Total']
    start_val = total_series.iloc[0]
    end_val = total_series.iloc[-1]
    n_years = (total_series.index[-1] - total_series.index[0]).days / 365.25
    
    if n_years <= 0:
        cagr = 0
    else:
        cagr = (end_val / start_val) ** (1 / n_years) - 1
    
    # Daily rate for simulation
    daily_rate = (1 + cagr) ** (1/365.25) - 1
    
    last_date = total_series.index[-1]
    prediction_dates = [last_date + timedelta(days=i) for i in range(1, int(years * 365.25) + 1)]
    
    predicted_values = []
    current_val = end_val
    
    for i, date in enumerate(prediction_dates):
        current_val *= (1 + daily_rate)
        # Add monthly top-up (approximate every 30 days)
        if i > 0 and i % 30 == 0:
            current_val += monthly_topup
        predicted_values.append(current_val)
        
    return pd.Series(predicted_values, index=prediction_dates)
