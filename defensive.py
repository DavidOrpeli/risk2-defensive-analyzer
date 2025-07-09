import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# PDF and Email libraries
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import base64
import io
from datetime import datetime
import os

# הגדרת הדף
st.set_page_config(
    page_title="מנתח נכסים דפנסיביים",
    page_icon="🛡️",
    layout="wide"
)

# CSS עיצוב
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 30px;
    }
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #2a5298;
    }
    
    .rule-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 3px solid #2a5298;
    }
    
    .sector-header {
        background: linear-gradient(135deg, #2a5298 0%, #3a6aa8 100%);
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0 10px 0;
        text-align: center;
        font-weight: bold;
    }
    
    .score-high { color: #28a745; font-weight: bold; }
    .score-medium { color: #ffc107; font-weight: bold; }
    .score-low { color: #dc3545; font-weight: bold; }
    
    .stSelectbox > div > div {
        background-color: white;
        border: 2px solid #2a5298;
    }
    
    .sector-checkbox {
        background: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        border-left: 3px solid #2a5298;
    }
</style>
""", unsafe_allow_html=True)

class DefensiveAssetAnalyzer:
    def __init__(self, benchmark_symbol='SPY'):
        self.benchmark_symbol = benchmark_symbol
        self.vix_symbol = '^VIX'
        
        # רשימת מניות מאורגנת לפי סקטורים
        self.sectors_data = {
            'Technology': [
                'NVDA', 'MSFT', 'AAPL', 'AVGO', 'ORCL', 'PLTR', 'CSCO', 'IBM', 'CRM', 
                'AMD', 'INTU', 'NOW', 'TXN', 'RTX', 'ACN', 'QCOM', 'ADBE', 'AMAT', 
                'MU', 'PANW', 'LRCX', 'CRWD', 'KLAC', 'ADI', 'ANET', 'INTC', 'CDNS', 
                'SNPS', 'MSI', 'FTNT', 'ADSK', 'ROP', 'NXPI', 'WDAY', 'GLW', 'MCHP', 
                'CTSH', 'DELL', 'MPWR', 'GRMN', 'ANSS', 'IT', 'STX', 'HPE', 'TYL', 
                'SMCI', 'TDY', 'ON', 'JBL', 'CDW', 'NTAP', 'PTC', 'LDOS', 'FFIV', 
                'ZBRA', 'GEN', 'TER', 'AKAM', 'PAYC', 'EPAM', 'DAY'
            ],
            'Health Care': [
                'LLY', 'JNJ', 'ABBV', 'UNH', 'ABT', 'ISRG', 'MRK', 'TMO', 'AMGN', 
                'BSX', 'PFE', 'GILD', 'SYK', 'DHR', 'VRTX', 'MDT', 'BMY', 'MCK', 
                'CVS', 'CI', 'ELV', 'ZTS', 'HCA', 'REGN', 'COR', 'BDX', 'EW', 
                'IDXX', 'RMD', 'A', 'GEHC', 'DXCM', 'IQV', 'MTD', 'STE', 'LH', 
                'WAT', 'DGX', 'PODD', 'ZBH', 'CNC', 'WST', 'BAX', 'COO', 'HOLX', 
                'ALGN', 'MOH', 'RVTY', 'INCY', 'UHS', 'MRNA', 'VTRS', 'SOLV', 
                'HSIC', 'TECH', 'CRL', 'DVA'
            ],
            'Financials': [
                'BRK-B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'GS', 'AXP', 'MS', 'SPGI', 
                'C', 'SCHW', 'BLK', 'PGR', 'COF', 'BX', 'MMC', 'CB', 'ICE', 'CME', 
                'FI', 'KKR', 'PNC', 'AJG', 'MCO', 'AON', 'COIN', 'BK', 'APO', 'TFC', 
                'TRV', 'AMP', 'AFL', 'AIG', 'MET', 'MSCI', 'VRSK', 'FIS', 'FICO', 
                'PRU', 'NDAQ', 'ACGL', 'MTB', 'EFX', 'STT', 'WTW', 'BRO', 'RJF', 
                'BR', 'SYF', 'HBAN', 'NTRS', 'CBOE', 'CPAY', 'CINF', 'TROW', 'WRB', 
                'CFG', 'GPN', 'KEY', 'FDS', 'PFG', 'L', 'EG', 'JKHY', 'GL', 'MKTX', 
                'BEN', 'IVZ'
            ],
            'Consumer Discretionary': [
                'AMZN', 'TSLA', 'HD', 'MCD', 'BKNG', 'TJX', 'LOW', 'SBUX', 'RCL', 
                'ORLY', 'CMG', 'HLT', 'AZO', 'GM', 'F', 'CPRT', 'YUM', 'DHI', 'CCL', 
                'TSCO', 'LULU', 'LEN', 'DRI', 'LYV', 'NVR', 'PHM', 'ULTA', 'WSM', 
                'TPR', 'LVS', 'DECK', 'DPZ', 'APTV', 'BLDR', 'BBY', 'MAS', 'POOL', 
                'TKO', 'RL', 'KMX', 'HAS', 'LKQ', 'WYNN', 'NCLH', 'MGM', 'CZR', 'MHK'
            ],
            'Communications': [
                'META', 'GOOGL', 'GOOG', 'NFLX', 'DIS', 'UBER', 'T', 'VZ', 'CMCSA', 
                'TMUS', 'DASH', 'ABNB', 'TTWO', 'CHTR', 'EA', 'WBD', 'GDDY', 'VRSN', 
                'EXPE', 'OMC', 'FOXA', 'NWSA', 'MTCH', 'PARA', 'FOX', 'NWS', 'IPG'
            ],
            'Consumer Staples': [
                'COST', 'WMT', 'PM', 'KO', 'PEP', 'MO', 'MDLZ', 'CL', 'TGT', 'KDP', 
                'KMB', 'MNST', 'KR', 'KVUE', 'SYY', 'GIS', 'ADM', 'STZ', 'HSY', 'DG', 
                'CHD', 'KHC', 'K', 'EL', 'MKC', 'TSN', 'CLX', 'SJM', 'BG', 'CAG', 
                'WBA', 'HRL', 'TAP', 'LW', 'CPB', 'BF-B'
            ],
            'Industrials': [
                'GE', 'CAT', 'RTX', 'BA', 'HON', 'UNP', 'ETN', 'DE', 'ADP', 'APH', 
                'LMT', 'TT', 'PH', 'TDG', 'MMM', 'WM', 'EMR', 'UPS', 'GD', 'CTAS', 
                'HWM', 'JCI', 'ITW', 'NOC', 'CARR', 'CSX', 'NSC', 'AXON', 'PWR', 
                'PCAR', 'URI', 'TEL', 'FAST', 'RSG', 'LHX', 'PAYX', 'CMI', 'GWW', 
                'AME', 'OTIS', 'ROK', 'WAB', 'IR', 'ODFL', 'DAL', 'XYL', 'DOV', 
                'VLTO', 'UAL', 'LUV', 'TRMB', 'EXPD', 'J', 'ROL', 'IEX', 'ALLE', 
                'NDSN', 'JBHT', 'CHRW', 'SWK', 'HII', 'GNRC', 'AOS', 'RAL'
            ],
            'Energy': [
                'XOM', 'CVX', 'COP', 'EOG', 'MPC', 'KMI', 'PSX', 'SLB', 'VLO', 'HES', 
                'BKR', 'TRGP', 'EQT', 'OXY', 'FANG', 'DVN', 'EXE', 'TPL', 'CTRA', 
                'HAL', 'FSLR', 'APA', 'ENPH'
            ],
            'Materials': [
                'LIN', 'APD', 'SHW', 'ECL', 'FCX', 'NEM', 'CTVA', 'VMC', 'MLM', 'NUE', 
                'DD', 'IP', 'PPG', 'SW', 'AMCR', 'DOW', 'IFF', 'STLD', 'PKG', 'LYB', 
                'BALL', 'CF', 'AVY', 'MOS', 'EMN', 'ALB'
            ],
            'Real Estate': [
                'AMT', 'PLD', 'WELL', 'DLR', 'O', 'SPG', 'PSA', 'CCI', 'CBRE', 'EQIX', 
                'VICI', 'CSGP', 'EXR', 'AVB', 'VTR', 'SBAC', 'EQR', 'WY', 'INVH', 
                'MAA', 'REG', 'HST', 'BXP', 'FRT', 'IRM', 'ESS', 'KIM', 'DOC', 'UDR', 
                'CPT', 'ARE'
            ],
            'Utilities': [
                'NEE', 'SO', 'DUK', 'CEG', 'AEP', 'SRE', 'D', 'EXC', 'PEG', 'XEL', 
                'ETR', 'WEC', 'ED', 'PCG', 'NRG', 'AWK', 'DTE', 'AEE', 'PPL', 'ATO', 
                'ES', 'CNP', 'CMS', 'FE', 'EIX', 'NI', 'LNT', 'EVRG', 'PNW', 'AES'
            ]
        }
        
        # התאמות סימבולים ל-yfinance
        self.symbol_adjustments = {
            'BRK/B': 'BRK-B',
            'BF/B': 'BF-B'
        }
    
    def adjust_symbol_for_yfinance(self, symbol):
        """התאמת סימבול ל-yfinance"""
        return self.symbol_adjustments.get(symbol, symbol)
    
    def get_selected_symbols(self, selected_sectors):
        """קבלת רשימת סימבולים לפי סקטורים נבחרים"""
        symbols = []
        for sector in selected_sectors:
            if sector in self.sectors_data:
                sector_symbols = [self.adjust_symbol_for_yfinance(sym) for sym in self.sectors_data[sector]]
                symbols.extend(sector_symbols)
        return list(set(symbols))  # הסרת כפילויות
        
    def fetch_data(self, symbols, period='3y'):
        """שליפת נתונים מ-yfinance"""
        data = {}
        progress_bar = st.progress(0)
        
        for i, symbol in enumerate(symbols):
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                if len(hist) > 0:
                    data[symbol] = hist
                progress_bar.progress((i + 1) / len(symbols))
            except Exception as e:
                st.warning(f"לא ניתן לשלוף נתונים עבור {symbol}: {e}")
        
        # שליפת נתוני בנצ'מארק
        try:
            benchmark = yf.Ticker(self.benchmark_symbol)
            data['BENCHMARK'] = benchmark.history(period=period)
        except Exception as e:
            st.error(f"לא ניתן לשלוף נתוני בנצ'מארק: {e}")
            
        return data

    def calculate_beta(self, stock_returns, benchmark_returns):
        """חישוב בטא"""
        try:
            covariance = np.cov(stock_returns, benchmark_returns)[0][1]
            benchmark_variance = np.var(benchmark_returns)
            return covariance / benchmark_variance if benchmark_variance != 0 else 0
        except:
            return 0
    
    def calculate_correlation(self, stock_returns, benchmark_returns):
        """חישוב מתאם"""
        try:
            return np.corrcoef(stock_returns, benchmark_returns)[0][1]
        except:
            return 0
    
    def calculate_max_drawdown(self, prices):
        """חישוב מקסימום דראודאון"""
        try:
            peak = prices.expanding().max()
            drawdown = (prices - peak) / peak
            return drawdown.min()
        except:
            return 0
    
    def calculate_volatility(self, returns):
        """חישוב תנודתיות שנתית"""
        try:
            return returns.std() * np.sqrt(252)
        except:
            return 0
    
    def analyze_rule_1_beta(self, data, symbol):
        """כלל 1: בטא 0.6-0.85"""
        try:
            stock_returns = data[symbol]['Close'].pct_change().dropna()
            benchmark_returns = data['BENCHMARK']['Close'].pct_change().dropna()
            
            # יישור תאריכים
            common_dates = stock_returns.index.intersection(benchmark_returns.index)
            stock_returns = stock_returns.loc[common_dates]
            benchmark_returns = benchmark_returns.loc[common_dates]
            
            beta = self.calculate_beta(stock_returns, benchmark_returns)
            
            if 0.6 <= beta <= 0.85:
                score = 10
            elif 0.5 <= beta < 0.6 or 0.85 < beta <= 0.9:
                score = 7
            elif 0.4 <= beta < 0.5 or 0.9 < beta <= 1.0:
                score = 5
            else:
                score = 2
                
            return {
                'score': score,
                'value': beta,
                'description': f'בטא: {beta:.2f}',
                'status': 'מצוין' if score >= 8 else 'טוב' if score >= 6 else 'חלש'
            }
        except Exception as e:
            return {'score': 0, 'value': 0, 'description': 'שגיאה בחישוב', 'status': 'שגיאה'}
    
    def analyze_rule_2_drawdown(self, data, symbol):
        """כלל 2: עמידות במשבר"""
        try:
            stock_prices = data[symbol]['Close']
            benchmark_prices = data['BENCHMARK']['Close']
            
            stock_dd = self.calculate_max_drawdown(stock_prices)
            benchmark_dd = self.calculate_max_drawdown(benchmark_prices)
            
            relative_dd = abs(stock_dd / benchmark_dd) if benchmark_dd != 0 else 0
            
            if relative_dd <= 0.7:
                score = 10
            elif relative_dd <= 0.8:
                score = 8
            elif relative_dd <= 0.9:
                score = 6
            elif relative_dd <= 1.0:
                score = 4
            else:
                score = 2
                
            return {
                'score': score,
                'value': relative_dd,
                'description': f'יחס דראודאון: {relative_dd:.1%}',
                'status': 'מצוין' if score >= 8 else 'טוב' if score >= 6 else 'חלש'
            }
        except Exception as e:
            return {'score': 0, 'value': 0, 'description': 'שגיאה בחישוב', 'status': 'שגיאה'}
    
    def analyze_rule_3_correlation(self, data, symbol):
        """כלל 3: מתאם יציב"""
        try:
            stock_returns = data[symbol]['Close'].pct_change().dropna()
            benchmark_returns = data['BENCHMARK']['Close'].pct_change().dropna()
            
            # יישור תאריכים
            common_dates = stock_returns.index.intersection(benchmark_returns.index)
            stock_returns = stock_returns.loc[common_dates]
            benchmark_returns = benchmark_returns.loc[common_dates]
            
            correlation = self.calculate_correlation(stock_returns, benchmark_returns)
            
            if 0.5 <= correlation <= 0.8:
                score = 10
            elif 0.4 <= correlation < 0.5 or 0.8 < correlation <= 0.9:
                score = 7
            elif 0.3 <= correlation < 0.4 or 0.9 < correlation <= 1.0:
                score = 5
            else:
                score = 2
                
            return {
                'score': score,
                'value': correlation,
                'description': f'מתאם: {correlation:.2f}',
                'status': 'מצוין' if score >= 8 else 'טוב' if score >= 6 else 'חלש'
            }
        except Exception as e:
            return {'score': 0, 'value': 0, 'description': 'שגיאה בחישוב', 'status': 'שגיאה'}
    
    def analyze_rule_4_volatility(self, data, symbol):
        """כלל 4: תנודתיות יחסית"""
        try:
            stock_returns = data[symbol]['Close'].pct_change().dropna()
            benchmark_returns = data['BENCHMARK']['Close'].pct_change().dropna()
            
            stock_vol = self.calculate_volatility(stock_returns)
            benchmark_vol = self.calculate_volatility(benchmark_returns)
            
            relative_vol = stock_vol / benchmark_vol if benchmark_vol != 0 else 0
            
            if relative_vol <= 0.8:
                score = 10
            elif relative_vol <= 0.9:
                score = 8
            elif relative_vol <= 1.0:
                score = 6
            elif relative_vol <= 1.2:
                score = 4
            else:
                score = 2
                
            return {
                'score': score,
                'value': relative_vol,
                'description': f'תנודתיות יחסית: {relative_vol:.1f}',
                'status': 'מצוין' if score >= 8 else 'טוב' if score >= 6 else 'חלש'
            }
        except Exception as e:
            return {'score': 0, 'value': 0, 'description': 'שגיאה בחישוב', 'status': 'שגיאה'}
    
    def analyze_rule_5_trend_stability(self, data, symbol):
        """כלל 5: יציבות מגמה"""
        try:
            prices = data[symbol]['Close']
            ma_200 = prices.rolling(window=200).mean()
            
            above_ma = (prices > ma_200).sum()
            total_days = len(prices.dropna())
            
            pct_above_ma = above_ma / total_days if total_days > 0 else 0
            
            if pct_above_ma >= 0.7:
                score = 10
            elif pct_above_ma >= 0.6:
                score = 8
            elif pct_above_ma >= 0.5:
                score = 6
            elif pct_above_ma >= 0.4:
                score = 4
            else:
                score = 2
                
            return {
                'score': score,
                'value': pct_above_ma,
                'description': f'זמן מעל MA-200: {pct_above_ma:.1%}',
                'status': 'מצוין' if score >= 8 else 'טוב' if score >= 6 else 'חלש'
            }
        except Exception as e:
            return {'score': 0, 'value': 0, 'description': 'שגיאה בחישוב', 'status': 'שגיאה'}
    
    def get_sector_for_symbol(self, symbol):
        """מציאת הסקטור של מניה"""
        for sector, symbols in self.sectors_data.items():
            if symbol in [self.adjust_symbol_for_yfinance(sym) for sym in symbols]:
                return sector
        return 'Unknown'

    def fetch_fundamental_data(self, symbol):
        """שליפת נתונים פונדמנטליים מ-yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # נתונים פונדמנטליים נוכחיים - ודוא שהם ערכים חוקיים
            current_pe = info.get('trailingPE', None)
            current_pb = info.get('priceToBook', None)
            current_ev_ebitda = info.get('enterpriseToEbitda', None)
            current_ps = info.get('priceToSalesTrailing12Months', None)
            
            # נקה ערכים לא תקינים
            def clean_value(value):
                if value is None:
                    return None
                try:
                    value = float(value)
                    if value <= 0 or value > 1000:  # ערכים קיצוניים
                        return None
                    return value
                except:
                    return None
            
            return {
                'current_pe': clean_value(current_pe),
                'current_pb': clean_value(current_pb),
                'current_ev_ebitda': clean_value(current_ev_ebitda),
                'current_ps': clean_value(current_ps)
            }
        except Exception as e:
            return {}

    def calculate_historical_valuation_percentile(self, symbol, metric_type='pe'):
        """חישוב percentile של המכפיל הנוכחי יחסית להיסטוריה של 3 שנים"""
        try:
            ticker = yf.Ticker(symbol)
            
            # קבלת המכפיל הנוכחי
            info = ticker.info
            if metric_type == 'pe':
                current_multiple = info.get('trailingPE', None)
            elif metric_type == 'pb':
                current_multiple = info.get('priceToBook', None)
            else:
                return None, None
            
            # אם אין מכפיל נוכחי תקין
            if current_multiple is None or current_multiple <= 0:
                return None, current_multiple
            
            # שליפת נתונים היסטוריים של 3 שנים
            hist_data = ticker.history(period='3y')
            if len(hist_data) < 100:  # צריך לפחות 100 ימים
                return None, current_multiple
            
            # גישה פשוטה: נשתמש במחירים היסטוריים עם הנתון הפונדמנטלי הנוכחי
            # זה לא מושלם אבל יעבוד ברוב המקרים
            historical_prices = hist_data['Close'].values
            current_price = historical_prices[-1]
            
            # חישוב מכפילים היסטוריים בהנחה שהנתון הפונדמנטלי יציב יחסית
            if metric_type == 'pe':
                # נחשב earnings per share נוכחי
                current_eps = current_price / current_multiple if current_multiple > 0 else None
                if current_eps is None or current_eps <= 0:
                    return None, current_multiple
                
                # נחשב P/E היסטורי לכל יום עם EPS הנוכחי
                historical_multiples = historical_prices / current_eps
                
            elif metric_type == 'pb':
                # נחשב book value per share נוכחי
                current_bvps = current_price / current_multiple if current_multiple > 0 else None
                if current_bvps is None or current_bvps <= 0:
                    return None, current_multiple
                
                # נחשב P/B היסטורי לכל יום עם BVPS הנוכחי
                historical_multiples = historical_prices / current_bvps
            
            # סינון ערכים קיצוניים
            if metric_type == 'pe':
                valid_multiples = historical_multiples[(historical_multiples > 5) & (historical_multiples < 200)]
            else:  # pb
                valid_multiples = historical_multiples[(historical_multiples > 0.1) & (historical_multiples < 20)]
            
            # צריך לפחות 50 נתונים תקינים
            if len(valid_multiples) < 50:
                return None, current_multiple
            
            # חישוב percentile
            percentile = (np.sum(valid_multiples <= current_multiple) / len(valid_multiples)) * 100
            
            return percentile, current_multiple
            
        except Exception as e:
            print(f"Error calculating percentile for {symbol}: {e}")
            return None, None

    def analyze_rule_6_valuation(self, data, symbol):
        """כלל 6: ניתוח תמחור לפי סקטור - על בסיס percentile היסטורי"""
        try:
            sector = self.get_sector_for_symbol(symbol)
            
            # בחירת המכפיל המתאים לפי סקטור
            sector_metrics = {
                'Technology': 'pe',
                'Financials': 'pb',
                'Health Care': 'pe',
                'Consumer Staples': 'pe',
                'Consumer Discretionary': 'pe',
                'Utilities': 'pe',
                'Energy': 'pe',
                'Materials': 'pe',
                'Real Estate': 'pb',
                'Communications': 'pe',
                'Industrials': 'pe'
            }
            
            primary_metric = sector_metrics.get(sector, 'pe')
            
            # חישוב percentile היסטורי
            percentile, current_value = self.calculate_historical_valuation_percentile(symbol, primary_metric)
            
            # אם לא הצלחנו לחשב percentile, ננסה המכפיל השני
            if percentile is None and primary_metric == 'pe':
                percentile, current_value = self.calculate_historical_valuation_percentile(symbol, 'pb')
                primary_metric = 'pb'
            elif percentile is None and primary_metric == 'pb':
                percentile, current_value = self.calculate_historical_valuation_percentile(symbol, 'pe')
                primary_metric = 'pe'
            
            # אם עדיין אין נתונים, השתמש בנתון נוכחי בלבד
            if percentile is None:
                if current_value is None or current_value <= 0:
                    # נסה לקבל את הנתון הנוכחי ישירות
                    fundamentals = self.fetch_fundamental_data(symbol)
                    current_value = fundamentals.get(f'current_{primary_metric}', None)
                    
                if current_value is None or current_value <= 0:
                    return {
                        'score': 5,
                        'value': 'N/A',
                        'description': 'נתוני תמחור לא זמינים',
                        'status': 'לא זמין',
                        'metric_used': 'N/A',
                        'percentile': None
                    }
                
                # ציון ברירת מחדל כאשר אין נתונים היסטוריים
                score = 5
                status = 'לא זמין היסטוריה'
                percentile_desc = 'N/A'
            else:
                # חישוב ציון על בסיס percentile
                # percentile נמוך = תמחור נמוך ביחס להיסטוריה = ציון גבוה
                if percentile <= 10:
                    score = 10
                    status = 'זול מאוד'
                elif percentile <= 25:
                    score = 9
                    status = 'זול'
                elif percentile <= 40:
                    score = 8
                    status = 'מתחת לממוצע'
                elif percentile <= 60:
                    score = 6
                    status = 'ממוצע'
                elif percentile <= 75:
                    score = 4
                    status = 'מעל הממוצע'
                elif percentile <= 90:
                    score = 2
                    status = 'יקר'
                else:
                    score = 1
                    status = 'יקר מאוד'
                
                percentile_desc = f'(P{percentile:.0f})'
            
            # תרגום שם המטריקה לעברית
            metric_names = {
                'pe': 'מכפיל רווח',
                'pb': 'מכפיל הון',
                'ps': 'מכפיל מכירות'
            }
            
            metric_display = metric_names.get(primary_metric, primary_metric)
            
            # תיאור מפורט
            if current_value and current_value > 0:
                description = f'{metric_display}: {current_value:.1f} {percentile_desc}'
            else:
                description = 'נתונים לא זמינים'
            
            # המרת percentile למספר רגיל
            if percentile is not None:
                percentile = float(percentile)
            
            return {
                'score': score,
                'value': current_value if current_value else 'N/A',
                'description': description,
                'status': status,
                'metric_used': primary_metric,
                'sector': sector,
                'percentile': percentile
            }
            
        except Exception as e:
            return {
                'score': 5, 
                'value': 0, 
                'description': f'שגיאה בניתוח תמחור: {str(e)[:50]}',
                'status': 'שגיאה',
                'metric_used': 'N/A',
                'percentile': None
            }
    
    def analyze_symbol(self, data, symbol):
        """ניתוח מקיף של סימבול"""
        rules = {
            'בטא יציבה': self.analyze_rule_1_beta(data, symbol),
            'עמידות במשבר': self.analyze_rule_2_drawdown(data, symbol),
            'מתאם יציב': self.analyze_rule_3_correlation(data, symbol),
            'תנודתיות נמוכה': self.analyze_rule_4_volatility(data, symbol),
            'יציבות מגמה': self.analyze_rule_5_trend_stability(data, symbol),
            'תמחור סביר': self.analyze_rule_6_valuation(data, symbol)
        }
        
        # חישוב ציון כולל
        total_score = sum([rule['score'] for rule in rules.values()])
        avg_score = total_score / len(rules)
        
        # קביעת דירוג
        if avg_score >= 8:
            rating = 'נכס דפנסיבי מצוין'
            color = '#28a745'
        elif avg_score >= 6:
            rating = 'נכס דפנסיבי טוב'
            color = '#ffc107'
        elif avg_score >= 4:
            rating = 'נכס דפנסיבי חלש'
            color = '#fd7e14'
        else:
            rating = 'לא מתאים כנכס דפנסיבי'
            color = '#dc3545'
            
        return {
            'symbol': symbol,
            'rules': rules,
            'total_score': avg_score,
            'rating': rating,
            'color': color
        }

def create_pdf_report(all_results, selected_sectors, sector_results):
    """יצירת דוח PDF מפורט"""
    
    # יצירת buffer לPDF
    buffer = io.BytesIO()
    
    # יצירת מסמך PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
    
    # קבלת סטיילים
    styles = getSampleStyleSheet()
    
    # יצירת סטיילים מותאמים אישית
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2a5298')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=20,
        textColor=colors.HexColor('#2a5298')
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    
    # תוכן הדוח
    story = []
    
    # כותרת ראשית
    story.append(Paragraph("🛡️ דוח ניתוח נכסים דפנסיביים", title_style))
    story.append(Spacer(1, 20))
    
    # מידע כללי
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
    story.append(Paragraph(f"<b>תאריך הדוח:</b> {current_time}", normal_style))
    story.append(Paragraph(f"<b>סקטורים שנותחו:</b> {', '.join(selected_sectors)}", normal_style))
    story.append(Paragraph(f"<b>סך כל מניות:</b> {len(all_results)}", normal_style))
    story.append(Spacer(1, 20))
    
    # סיכום מהיר
    story.append(Paragraph("📈 סיכום ביצועים", heading_style))
    
    excellent_count = len([r for r in all_results if r['total_score'] >= 8])
    good_count = len([r for r in all_results if 6 <= r['total_score'] < 8])
    weak_count = len([r for r in all_results if 4 <= r['total_score'] < 6])
    poor_count = len([r for r in all_results if r['total_score'] < 4])
    avg_score = np.mean([r['total_score'] for r in all_results])
    
    summary_data = [
        ['קטגוריה', 'מספר מניות', 'אחוז'],
        ['נכסים מצוינים (8-10)', str(excellent_count), f"{excellent_count/len(all_results)*100:.1f}%"],
        ['נכסים טובים (6-8)', str(good_count), f"{good_count/len(all_results)*100:.1f}%"],
        ['נכסים חלשים (4-6)', str(weak_count), f"{weak_count/len(all_results)*100:.1f}%"],
        ['לא מתאים (0-4)', str(poor_count), f"{poor_count/len(all_results)*100:.1f}%"],
        ['', '', ''],
        ['ציון ממוצע כללי', f"{avg_score:.2f}", '']
    ]
    
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a5298')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 30))
    
    # ביצועים לפי סקטורים
    story.append(Paragraph("🎯 ביצועים לפי סקטורים", heading_style))
    
    sector_data = [['סקטור', 'מספר מניות', 'ציון ממוצע', 'דירוג']]
    
    for sector in selected_sectors:
        if sector in sector_results and sector_results[sector]:
            results = sector_results[sector]
            avg_score = np.mean([r['total_score'] for r in results])
            
            if avg_score >= 8:
                rating = 'מצוין 🌟'
            elif avg_score >= 6:
                rating = 'טוב 👍'
            elif avg_score >= 4:
                rating = 'חלש ⚠️'
            else:
                rating = 'לא מתאים ❌'
            
            sector_data.append([
                sector,
                str(len(results)),
                f"{avg_score:.2f}",
                rating
            ])
    
    sector_table = Table(sector_data)
    sector_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a5298')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    story.append(sector_table)
    story.append(PageBreak())
    
    # המניות הטובות ביותר
    story.append(Paragraph("🌟 המניות הדפנסיביות הטובות ביותר", heading_style))
    
    # מיון לפי ציון
    sorted_results = sorted(all_results, key=lambda x: x['total_score'], reverse=True)
    top_stocks = sorted_results[:20]  # 20 הראשונות
    
    stock_data = [['מניה', 'ציון כולל', 'דירוג', 'בטא', 'מתאם', 'סקטור']]
    
    for result in top_stocks:
        sector = next((sector for sector, results in sector_results.items() if result in results), 'Unknown')
        stock_data.append([
            result['symbol'],
            f"{result['total_score']:.2f}",
            result['rating'],
            f"{result['rules']['בטא יציבה']['value']:.2f}",
            f"{result['rules']['מתאם יציב']['value']:.2f}",
            sector
        ])
    
    stock_table = Table(stock_data)
    stock_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a5298')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    story.append(stock_table)
    story.append(PageBreak())
    
    # הסבר מתודולוגיה
    story.append(Paragraph("📋 מתודולוגיית הניתוח", heading_style))
    
    methodology_text = """
    <b>המערכת בוחנת 5 כללים עיקריים לקביעת דפנסיביות של נכס:</b><br/><br/>
    
    <b>1. בטא יציבה (0.6-0.85):</b> מודדת רגישות המניה לשינויים במדד S&P 500. 
    בטא נמוכה יותר מ-1 מעידה על תנודתיות מופחתת.<br/><br/>
    
    <b>2. עמידות במשבר:</b> יכולת המניה לעמוד טוב יותר מהמדד בתקופות ירידה. 
    נמדדת על ידי השוואת מקסימום דראודאון.<br/><br/>
    
    <b>3. מתאם יציב (0.5-0.8):</b> רמת המתאם האידיאלית עם המדד - לא גבוה מדי ולא נמוך מדי 
    כדי לאפשר גיוון פורטפוליו.<br/><br/>
    
    <b>4. תנודתיות נמוכה:</b> תנודתיות שנתית נמוכה יותר מהמדד, המעידה על יציבות מחירים.<br/><br/>
    
    <b>5. יציבות מגמה:</b> אחוז הזמן שהמניה נמצאת מעל הממוצע הנע 200 יום, 
    המעיד על עקביות המגמה החיובית.<br/><br/>
    
    <b>ציון סופי:</b> ממוצע משוקלל של כל הכללים, בטווח 0-10.<br/>
    8-10: מצוין | 6-8: טוב | 4-6: חלש | 0-4: לא מתאים<br/><br/>
    
    <b>מקור נתונים:</b> Yahoo Finance | <b>תקופת ניתוח:</b> 3 שנים אחרונות
    """
    
    story.append(Paragraph(methodology_text, normal_style))
    
    # בניית הPDF
    doc.build(story)
    
    # החזרת הbuffer
    buffer.seek(0)
    return buffer

def send_email_with_pdf(pdf_buffer, selected_sectors, recipient_email="dudio@amitim.com"):
    """שליחת מייל עם קובץ PDF מצורף"""
    
    try:
        # הגדרות מייל (להתאמה לפי הספק המייל שלך)
        smtp_server = "smtp.gmail.com"  # לדוגמה - Gmail
        smtp_port = 587
        sender_email = "your-email@gmail.com"  # יש להחליף
        sender_password = "your-app-password"  # יש להחליף לapp password
        
        # יצירת הודעת מייל
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"דוח ניתוח נכסים דפנסיביים - {', '.join(selected_sectors)}"
        
        # תוכן המייל
        body = f"""
        שלום,
        
        מצורף דוח ניתוח נכסים דפנסיביים עבור הסקטורים הבאים:
        {', '.join(selected_sectors)}
        
        הדוח נוצר אוטומטית על ידי מערכת ניתוח נכסים דפנסיביים.
        תאריך יצירה: {datetime.now().strftime("%d/%m/%Y %H:%M")}
        
        בברכה,
        מערכת ניתוח נכסים דפנסיביים
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # צירוף קובץ PDF
        pdf_data = pdf_buffer.getvalue()
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(pdf_data)
        encoders.encode_base64(attachment)
        
        filename = f"defensive_assets_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        attachment.add_header(
            'Content-Disposition',
            f'attachment; filename= {filename}'
        )
        
        msg.attach(attachment)
        
        # שליחת המייל
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        return True, "המייל נשלח בהצלחה!"
        
    except Exception as e:
        return False, f"שגיאה בשליחת המייל: {str(e)}"

def main():
    st.markdown("""
    <div class="main-header">
        <h1>🛡️ מנתח נכסים דפנסיביים</h1>
        <p>כלי מתקדם לניתוח וזיהוי נכסים דפנסיביים בשוק ההון</p>
    </div>
    """, unsafe_allow_html=True)
    
    # יצירת מנתח
    analyzer = DefensiveAssetAnalyzer()
    
    # סייד בר להגדרות
    st.sidebar.header("🔧 הגדרות")
    
    # בחירת סקטורים
    st.sidebar.subheader("📊 בחירת סקטורים")
    
    sector_icons = {
        'Technology': '💻',
        'Health Care': '🏥',
        'Financials': '🏦',
        'Consumer Discretionary': '🛒',
        'Communications': '📡',
        'Consumer Staples': '🍕',
        'Industrials': '🏭',
        'Energy': '⚡',
        'Materials': '🏗️',
        'Real Estate': '🏠',
        'Utilities': '🔌'
    }
    
    selected_sectors = []
    
    # אתחול session state למפתחות הכפתורים
    if 'select_all_clicked' not in st.session_state:
        st.session_state.select_all_clicked = False
    if 'clear_all_clicked' not in st.session_state:
        st.session_state.clear_all_clicked = False
    
    # כפתור לבחירת כל הסקטורים
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("✅ בחר הכל", key="select_all_btn"):
            st.session_state.select_all_clicked = True
            st.session_state.clear_all_clicked = False
    
    with col2:
        if st.button("❌ נקה הכל", key="clear_all_btn"):
            st.session_state.clear_all_clicked = True
            st.session_state.select_all_clicked = False
    
    # יצירת checkboxes לכל סקטור
    st.sidebar.markdown("**בחר סקטורים לניתוח:**")
    
    for sector in analyzer.sectors_data.keys():
        icon = sector_icons.get(sector, '📈')
        stocks_count = len(analyzer.sectors_data[sector])
        
        # קביעת הערך בהתאם לכפתורים שנלחצו
        default_value = False
        if st.session_state.select_all_clicked:
            default_value = True
        elif st.session_state.clear_all_clicked:
            default_value = False
        else:
            # שמירה על הערך הקיים אם לא נלחץ כפתור
            default_value = st.session_state.get(f"sector_{sector}", False)
        
        if st.sidebar.checkbox(
            f"{icon} {sector} ({stocks_count} מניות)",
            value=default_value,
            key=f"sector_{sector}"
        ):
            selected_sectors.append(sector)
    
    # איפוס הכפתורים אחרי העדכון
    if st.session_state.select_all_clicked or st.session_state.clear_all_clicked:
        st.session_state.select_all_clicked = False
        st.session_state.clear_all_clicked = False
    
    # הצגת סיכום הבחירה
    if selected_sectors:
        total_stocks = len(analyzer.get_selected_symbols(selected_sectors))
        st.sidebar.success(f"נבחרו {len(selected_sectors)} סקטורים עם {total_stocks} מניות")
    else:
        st.sidebar.warning("אנא בחר לפחות סקטור אחד")
    
    # כפתור להפעלת הניתוח
    if st.sidebar.button("🚀 הפעל ניתוח", type="primary", disabled=len(selected_sectors) == 0):
        symbols = analyzer.get_selected_symbols(selected_sectors)
        
        with st.spinner("שולף נתונים וחושב..."):
            data = analyzer.fetch_data(symbols)
            
            if data:
                # ניתוח כל הסימבולים
                all_results = []
                for symbol in symbols:
                    if symbol in data:
                        result = analyzer.analyze_symbol(data, symbol)
                        all_results.append(result)
                
                # ארגון תוצאות לפי סקטורים
                sector_results = {}
                for sector in selected_sectors:
                    sector_symbols = [analyzer.adjust_symbol_for_yfinance(sym) for sym in analyzer.sectors_data[sector]]
                    sector_results[sector] = [r for r in all_results if r['symbol'] in sector_symbols]
                
                # תצוגת תוצאות כלליות
                st.header("📈 תוצאות הניתוח")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    excellent_count = len([r for r in all_results if r['total_score'] >= 8])
                    st.metric("🌟 נכסים מצוינים", excellent_count)
                
                with col2:
                    good_count = len([r for r in all_results if 6 <= r['total_score'] < 8])
                    st.metric("👍 נכסים טובים", good_count)
                
                with col3:
                    avg_score = np.mean([r['total_score'] for r in all_results])
                    st.metric("📊 ציון ממוצע", f"{avg_score:.1f}")
                
                with col4:
                    st.metric("🎯 סקטורים נבחרים", len(selected_sectors))
                
                # תרשים תוצאות לפי סקטורים
                st.subheader("🎯 ביצועים לפי סקטורים")
                
                sector_avg_scores = {}
                sector_counts = {}
                
                for sector, results in sector_results.items():
                    if results:
                        sector_avg_scores[sector] = np.mean([r['total_score'] for r in results])
                        sector_counts[sector] = len(results)
                
                if sector_avg_scores:
                    df_sectors = pd.DataFrame([
                        {
                            'Sector': sector,
                            'Average Score': score,
                            'Count': sector_counts[sector],
                            'Icon': sector_icons.get(sector, '📈')
                        }
                        for sector, score in sector_avg_scores.items()
                    ])
                    
                    fig_sectors = px.bar(
                        df_sectors,
                        x='Average Score',
                        y='Sector',
                        orientation='h',
                        color='Average Score',
                        color_continuous_scale='RdYlGn',
                        title='ציון ממוצע דפנסיביות לפי סקטור',
                        hover_data=['Count']
                    )
                    
                    fig_sectors.update_layout(
                        height=max(400, len(df_sectors) * 50),
                        plot_bgcolor='white',
                        paper_bgcolor='white'
                    )
                    
                    st.plotly_chart(fig_sectors, use_container_width=True)
                
                # יצירת DataFrame כללי לתוצאות
                df_results = pd.DataFrame([
                    {
                        'Symbol': r['symbol'],
                        'Sector': next((sector for sector, results in sector_results.items() if r in results), 'Unknown'),
                        'Score': r['total_score'],
                        'Rating': r['rating'],
                        'Beta': r['rules']['בטא יציבה']['value'],
                        'Correlation': r['rules']['מתאם יציב']['value'],
                        'Volatility': r['rules']['תנודתיות נמוכה']['value'],
                        'Valuation': r['rules']['תמחור סביר']['description'],
                        'Valuation_Score': r['rules']['תמחור סביר']['score']
                    }
                    for r in all_results
                ])
                
                # תרשים פיזור כללי
                st.subheader("🎯 מפת נכסים דפנסיביים")
                
                fig_scatter = px.scatter(
                    df_results,
                    x='Beta',
                    y='Correlation',
                    size='Score',
                    color='Sector',
                    hover_name='Symbol',
                    title='מיפוי נכסים דפנסיביים - בטא מול מתאם',
                    labels={'Beta': 'בטא', 'Correlation': 'מתאם עם המדד'}
                )
                
                # הוספת קווי היעד
                fig_scatter.add_hline(y=0.5, line_dash="dash", line_color="blue", 
                                    annotation_text="מתאם מינימלי")
                fig_scatter.add_hline(y=0.8, line_dash="dash", line_color="blue", 
                                    annotation_text="מתאם מקסימלי")
                fig_scatter.add_vline(x=0.6, line_dash="dash", line_color="red", 
                                    annotation_text="בטא מינימלי")
                fig_scatter.add_vline(x=0.85, line_dash="dash", line_color="red", 
                                    annotation_text="בטא מקסימלי")
                
                # הוספת רקטנגל היעד
                fig_scatter.add_shape(
                    type="rect",
                    x0=0.6, y0=0.5, x1=0.85, y1=0.8,
                    line=dict(color="green", width=2),
                    fillcolor="green",
                    opacity=0.1,
                )
                
                fig_scatter.update_layout(
                    height=600,
                    plot_bgcolor='white',
                    paper_bgcolor='white'
                )
                
                st.plotly_chart(fig_scatter, use_container_width=True)
                
                # פירוט לפי סקטורים
                st.subheader("📋 פירוט מפורט לפי סקטורים")
                
                for sector in selected_sectors:
                    if sector in sector_results and sector_results[sector]:
                        results = sector_results[sector]
                        icon = sector_icons.get(sector, '📈')
                        avg_score = np.mean([r['total_score'] for r in results])
                        
                        st.markdown(f"""
                        <div class="sector-header">
                            {icon} {sector} - ציון ממוצע: {avg_score:.1f} ({len(results)} מניות)
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # מיון המניות בסקטור לפי ציון
                        sorted_results = sorted(results, key=lambda x: x['total_score'], reverse=True)
                        
                        # תצוגה בעמודות
                        cols = st.columns(min(3, len(sorted_results)))
                        
                        for i, result in enumerate(sorted_results[:9]):  # מגביל ל-9 מניות בשורה
                            col_idx = i % 3
                            with cols[col_idx]:
                                score_color = 'score-high' if result['total_score'] >= 8 else 'score-medium' if result['total_score'] >= 6 else 'score-low'
                                
                                st.markdown(f"""
                                <div class="metric-card">
                                    <h4>{result['symbol']}</h4>
                                    <span class="{score_color}">ציון: {result['total_score']:.1f}</span><br>
                                    <small>{result['rating']}</small>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # אם יש יותר מ-9 מניות, הצג טבלה
                        if len(sorted_results) > 9:
                            with st.expander(f"הצג את כל {len(sorted_results)} המניות ב{sector}"):
                                sector_df = pd.DataFrame([
                                    {
                                        'Symbol': r['symbol'],
                                        'Score': r['total_score'],
                                        'Rating': r['rating'],
                                        'Beta': r['rules']['בטא יציבה']['value'],
                                        'Correlation': r['rules']['מתאם יציב']['value'],
                                        'Valuation': r['rules']['תמחור סביר']['description']
                                    }
                                    for r in sorted_results
                                ])
                                
                                st.dataframe(
                                    sector_df.style.format({
                                        'Score': '{:.1f}',
                                        'Beta': '{:.2f}',
                                        'Correlation': '{:.2f}'
                                    }),
                                    use_container_width=True
                                )
                
                # טבלת תוצאות מלאה
                st.subheader("📊 טבלת תוצאות מלאה")
                
                # מיון לפי ציון
                df_sorted = df_results.sort_values('Score', ascending=False)
                
                st.dataframe(
                    df_sorted.style.format({
                        'Score': '{:.1f}',
                        'Beta': '{:.2f}',
                        'Correlation': '{:.2f}',
                        'Volatility': '{:.1f}',
                        'Valuation_Score': '{:.1f}'
                    }),
                    use_container_width=True
                )
                
                # אפשרויות הורדה ושליחה
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    csv = df_sorted.to_csv(index=False)
                    st.download_button(
                        label="💾 הורד תוצאות כ-CSV",
                        data=csv,
                        file_name=f'defensive_assets_analysis_{"-".join(selected_sectors)}.csv',
                        mime='text/csv'
                    )
                
                with col2:
                    if st.button("📄 יצר דוח PDF", type="secondary"):
                        with st.spinner("יוצר דוח PDF..."):
                            try:
                                pdf_buffer = create_pdf_report(all_results, selected_sectors, sector_results)
                                
                                st.download_button(
                                    label="⬇️ הורד דוח PDF",
                                    data=pdf_buffer.getvalue(),
                                    file_name=f'defensive_assets_report_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf',
                                    mime='application/pdf'
                                )
                                st.success("✅ דוח PDF נוצר בהצלחה!")
                                
                            except Exception as e:
                                st.error(f"❌ שגיאה ביצירת PDF: {str(e)}")
                
                with col3:
                    if st.button("📧 שלח דוח למייל", type="primary"):
                        with st.spinner("שולח דוח למייל..."):
                            try:
                                pdf_buffer = create_pdf_report(all_results, selected_sectors, sector_results)
                                success, message = send_email_with_pdf(pdf_buffer, selected_sectors)
                                
                                if success:
                                    st.success(f"✅ {message}")
                                    st.balloons()
                                else:
                                    st.error(f"❌ {message}")
                                    st.info("💡 **הערה:** לשליחת מייל יש צורך בהגדרת פרטי SMTP. אנא עדכן את פרטי המייל בקוד.")
                                    
                            except Exception as e:
                                st.error(f"❌ שגיאה בשליחת המייל: {str(e)}")
                                st.info("💡 **הערה:** לשליחת מייל יש צורך בהגדרת פרטי SMTP. אנא עדכן את פרטי המייל בקוד.")
                
                # הסבר על שליחת מייל
                with st.expander("⚙️ הגדרת שליחת מייל"):
                    st.markdown("""
                    **להפעלת שליחת המייל יש לערוך את הפונקציה `send_email_with_pdf`:**
                    
                    1. **Gmail:** החלף את `your-email@gmail.com` במייל שלך
                    2. **App Password:** צור App Password ב-Gmail והחלף את `your-app-password`
                    3. **SMTP אחר:** עדכן את `smtp_server` ו-`smtp_port` לספק המייל שלך
                    
                    **הדוח יישלח אוטומטית ל:** `dudio@amitim.com`
                    
                    **תוכן הדוח PDF:**
                    - 📊 סיכום ביצועים כללי
                    - 🎯 ביצועים לפי סקטורים 
                    - 🌟 רשימת המניות הטובות ביותר
                    - 📋 הסבר מפורט על המתודולוגיה
                    """)
    
    # מידע נוסף
    with st.expander("ℹ️ מידע על הכללים והסקטורים"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **כללי הניתוח:**
            
            1. **בטא יציבה (0.6-0.85)**: מודדת רגישות המניה לשינויים במדד
            2. **עמידות במשבר**: יכולת המניה לעמוד טוב יותר מהמדד בתקופות קשות
            3. **מתאם יציב (0.5-0.8)**: רמת המתאם האידיאלית עם המדד
            4. **תנודתיות נמוכה**: תנודתיות נמוכה יותר מהמדד
            5. **יציבות מגמה**: זמן שהמניה נמצאת מעל הממוצע הנע
            6. **תמחור סביר**: מכפילים סבירים לפי סקטור (P/E, P/B, EV/EBITDA)
            
            **מדרג הציונים:**
            - 8-10: נכס דפנסיבי מצוין 🌟
            - 6-8: נכס דפנסיבי טוב 👍
            - 4-6: נכס דפנסיבי חלש ⚠️
            - 0-4: לא מתאים כנכס דפנסיבי ❌
            """)
        
        with col2:
            st.markdown("""
            **הסקטורים הזמינים:**
            
            💻 **Technology** - חברות טכנולוגיה  
            🏥 **Health Care** - חברות בריאות ותרופות  
            🏦 **Financials** - בנקים וביטוח  
            🛒 **Consumer Discretionary** - צריכה בררנית  
            📡 **Communications** - תקשורת ומדיה  
            🍕 **Consumer Staples** - צריכה בסיסית  
            🏭 **Industrials** - תעשייה וייצור  
            ⚡ **Energy** - אנרגיה ונפט  
            🏗️ **Materials** - חומרי גלם  
            🏠 **Real Estate** - נדל"ן  
            🔌 **Utilities** - שירותים ציבוריים  
            
            **סך הכל: {} מניות מ-{} סקטורים**
            """.format(
                sum(len(symbols) for symbols in analyzer.sectors_data.values()),
                len(analyzer.sectors_data)
            ))
    
    # הסבר מפורט על החישובים
    with st.expander("🧮 הסבר מפורט על החישובים המתמטיים"):
        st.markdown("""
        ## 📊 **כלל 1: בטא יציבה (Beta Analysis)**
        
        **מה זה בטא?**  
        בטא מודדת את הרגישות של מניה לשינויים בשוק הכללי (S&P 500).
        
        **הפורמולה:**
        ```
        Beta = Covariance(Stock_Returns, Market_Returns) / Variance(Market_Returns)
        ```
        
        **תהליך החישוב:**
        1. שליפת מחירי סגירה של 3 שנים
        2. חישוב תשואות יומיות: `(Price_today - Price_yesterday) / Price_yesterday`
        3. יישור תאריכים - וידוא שיש נתונים לאותם תאריכים
        4. חישוב קובריאנס: `np.cov(stock_returns, benchmark_returns)[0][1]`
        5. חישוב שונות השוק: `np.var(benchmark_returns)`
        6. חישוב בטא: חלוקה של קובריאנס בשונות
        
        **מדרג הציונים:**
        - **10 נקודות:** 0.6 ≤ בטא ≤ 0.85 (טווח דפנסיבי אידיאלי)
        - **7 נקודות:** 0.5 ≤ בטא < 0.6 או 0.85 < בטא ≤ 0.9 (קרוב לאידיאלי)
        - **5 נקודות:** 0.4 ≤ בטא < 0.5 או 0.9 < בטא ≤ 1.0 (מקבל)
        - **2 נקודות:** מחוץ לטווח הדפנסיבי
        
        **הרציונל:** בטא של 0.6-0.85 אומרת שהמניה נעה עם השוק אבל בעוצמה מופחתת, מה שמקנה יציבות.
        
        ---
        
        ## 📉 **כלל 2: עמידות במשבר (Drawdown Analysis)**
        
        **מה זה מקסימום דראודאון?**  
        הירידה הגדולה ביותר מפסגה לשפל בתקופה מסוימת.
        
        **הפורמולה:**
        ```
        Peak = מחיר המקסימום עד היום
        Drawdown = (Current_Price - Peak) / Peak
        Max_Drawdown = Min(Drawdown)
        Relative_Drawdown = Stock_Drawdown / Benchmark_Drawdown
        ```
        
        **תהליך החישוב:**
        1. חישוב פסגות מתגלגלות: `prices.expanding().max()`
        2. חישוב דראודאון לכל יום: `(prices - peak) / peak`
        3. מציאת המקסימום: `drawdown.min()` (המספר השלילי הגדול ביותר)
        4. חישוב יחסי: `stock_dd / benchmark_dd`
        
        **מדרג הציונים:**
        - **10 נקודות:** ≤ 70% מהדראודאון של השוק
        - **8 נקודות:** ≤ 80% מהדראודאון של השוק
        - **6 נקודות:** ≤ 90% מהדראודאון של השוק
        - **4 נקודות:** בדיוק כמו השוק
        - **2 נקודות:** גרוע מהשוק
        
        **הרציונל:** נכס דפנסיבי צריך לרדת פחות מהשוק בתקופות משבר.
        
        ---
        
        ## 🔗 **כלל 3: מתאם יציב (Correlation Analysis)**
        
        **מה זה מתאם?**  
        מדד לחוזק הקשר הליניארי בין תנועות המניה לשוק (טווח: -1 עד +1).
        
        **הפורמולה:**
        ```
        Correlation = Covariance(Stock, Market) / (Std(Stock) * Std(Market))
        ```
        
        **תהליך החישוב:**
        1. שימוש בפונקציה: `np.corrcoef(stock_returns, benchmark_returns)[0][1]`
        2. +1 = מתאם מושלם חיובי
        3. 0 = אין מתאם
        4. -1 = מתאם מושלם שלילי
        
        **מדרג הציונים:**
        - **10 נקודות:** 0.5 ≤ מתאם ≤ 0.8 (מתאם מאוזן)
        - **7 נקודות:** 0.4 ≤ מתאם < 0.5 או 0.8 < מתאם ≤ 0.9 (קרוב לאידיאלי)
        - **5 נקודות:** 0.3 ≤ מתאם < 0.4 או 0.9 < מתאם ≤ 1.0 (מקבל)
        - **2 נקודות:** מתאם חלש מדי או חזק מדי
        
        **הרציונל:** מתאם של 0.5-0.8 מבטיח שהנכס יועיל לגיוון אבל לא מנותק מהשוק.
        
        ---
        
        ## 📊 **כלל 4: תנודתיות יחסית (Volatility Analysis)**
        
        **מה זה תנודתיות?**  
        מדד לגודל השינויים במחיר הנכס לאורך זמן.
        
        **הפורמולה:**
        ```
        Daily_Returns = (Price_today - Price_yesterday) / Price_yesterday
        Volatility = Std(Daily_Returns) * sqrt(252)  # אנואליזציה
        Relative_Volatility = Stock_Volatility / Benchmark_Volatility
        ```
        
        **תהליך החישוב:**
        1. חישוב תשואות יומיות לכל נכס
        2. חישוב סטיית תקן יומית: `returns.std()`
        3. אנואליזציה: הכפלה ב-√252 (מספר ימי מסחר בשנה)
        4. חישוב יחסי: חלוקה בתנודתיות השוק
        
        **מדרג הציונים:**
        - **10 נקודות:** ≤ 80% מתנודתיות השוק
        - **8 נקודות:** ≤ 90% מתנודתיות השוק
        - **6 נקודות:** בדיוק כמו השוק
        - **4 נקודות:** ≤ 120% מתנודתיות השוק
        - **2 נקודות:** תנודתיות גבוהה מדי
        
        **הרציונל:** נכס דפנסיבי צריך להיות פחות תנודתי מהשוק הכללי.
        
        ---
        
        ## 📈 **כלל 5: יציבות מגמה (Trend Stability)**
        
        **מה זה יציבות מגמה?**  
        אחוז הזמן שהמניה נמצאת מעל הממוצע הנע 200 יום.
        
        **הפורמולה:**
        ```
        MA_200 = Moving_Average(Prices, 200_days)
        Days_Above_MA = Count(Price > MA_200)
        Percentage = Days_Above_MA / Total_Days
        ```
        
        **תהליך החישוב:**
        1. חישוב ממוצע נע: `prices.rolling(window=200).mean()`
        2. בדיקה יומית: `prices > ma_200` (מחזיר True/False)
        3. ספירת ימים: `(prices > ma_200).sum()`
        4. חישוב אחוז: חלוקה במספר הימים הכולל
        
        **מדרג הציונים:**
        - **10 נקודות:** ≥ 70% מהזמן מעל הממוצע
        - **8 נקודות:** ≥ 60% מהזמן
        - **6 נקודות:** ≥ 50% מהזמן
        - **4 נקודות:** ≥ 40% מהזמן
        - **2 נקודות:** < 40% מהזמן
        
        **הרציונל:** נכס דפנסיבי צריך להיות במגמת עלייה רוב הזמן.
        
        ---
        
        ## 💰 **כלל 6: תמחור סביר - ניתוח היסטורי (Valuation Analysis)**
        
        **מה זה ניתוח תמחור יחסי?**  
        במקום ספים קבועים, המערכת בוחנת את המכפיל הנוכחי יחסית להיסטוריה של 3 השנים האחרונות של אותה מניה.
        
        **המכפילים הנבחנים לפי סקטור:**
        ```
        טכנולוגיה: P/E (Price-to-Earnings)
        בנקים וביטוח: P/B (Price-to-Book)  
        בריאות: P/E
        צריכה בסיסית: P/E
        צריכה בררנית: P/E
        שירותים ציבוריים: P/E
        אנרגיה: P/E
        חומרי גלם: P/E
        נדל"ן: P/B
        תקשורת: P/E
        תעשייה: P/E
        ```
        
        **תהליך החישוב המתקדם:**
        1. **זיהוי סקטור:** קביעת המכפיל המתאים
        2. **שליפת נתונים היסטוריים:** 3 שנים של נתונים פיננסיים רבעוניים
        3. **חישוב מכפילים היסטוריים:** חישוב P/E או P/B לכל רבעון
        4. **סינון ערכים קיצוניים:** הסרת ערכים לא הגיוניים
        5. **חישוב Percentile:** מיקום המכפיל הנוכחי בהתפלגות ההיסטורית
        
        **נוסחאת Percentile:**
        ```python
        historical_multiples = [רשימת_מכפילים_של_3_שנים]
        percentile = (מספר_ערכים_קטנים_או_שווים / כל_הערכים) * 100
        ```
        
        **מערכת ציונים מבוססת Percentile:**
        - **10 נקודות:** Percentile ≤ 10% (זול מאוד - 10% הזול ביותר)
        - **9 נקודות:** Percentile ≤ 25% (זול - רבעון תחתון)
        - **8 נקודות:** Percentile ≤ 40% (מתחת לממוצע)
        - **6 נקודות:** Percentile 40-60% (ממוצע)
        - **4 נקודות:** Percentile 60-75% (מעל הממוצע)
        - **2 נקודות:** Percentile 75-90% (יקר)
        - **1 נקודה:** Percentile > 90% (יקר מאוד - 10% היקר ביותר)
        
        **דוגמה מעשית - מניית COST:**
        ```
        P/E נוכחי: 52
        P/E היסטורי של 3 שנים: [38, 41, 35, 45, 42, 47, 39, 44, 52, 48, 36, 43]
        Percentile: 92% (רק ב-8% מהזמן המניה הייתה יקרה יותר)
        ציון: 1 נקודה (יקר מאוד)
        סטטוס: "מכפיל רווח: 52.0 (P92)"
        ```
        
        **יתרונות הגישה החדשה:**
        - **התאמה אישית:** כל מניה נבחנת יחסית לעצמה
        - **דינמיות:** התחשבות בשינויים עסקיים וכלכליים
        - **הגינות:** COST עם P/E 52 מקבלת ציון נמוך בגלל שהיא יקרה יחסית להיסטוריה שלה
        - **דיוק מוגבר:** זיהוי מדויק יותר של הזדמנויות ומלכודות
        
        **טיפול בנתונים חסרים:**
        - אם אין מספיק נתונים היסטוריים (< 4 רבעונים) → מעבר למכפיל משני
        - אם אין P/E → מעבר ל-P/B ולהפך
        - אם אין נתונים כלל → ציון 5 (ניטרלי)
        - המערכת מסננת ערכים קיצוניים אוטומטית
        
        ---
        
        ## 🎯 **חישוב הציון הסופי**
        
        **שלב 1: צבירת ציונים**
        ```python
        total_score = sum([rule['score'] for rule in rules.values()])
        avg_score = total_score / 6  # ממוצע של 6 הכללים
        ```
        
        **שלב 2: קביעת דירוג**
        - **8-10:** נכס דפנסיבי מצוין 🌟
        - **6-8:** נכס דפנסיבי טוב 👍
        - **4-6:** נכס דפנסיבי חלש ⚠️
        - **0-4:** לא מתאים כנכס דפנסיבי ❌
        
        ---
        
        ## 🔍 **דוגמה מעשית: השוואת מניות**
        
        **מניית JNJ (נכס דפנסיבי איכותי):**
        ```
        בטא: 0.75 → ציון 10 (בטווח 0.6-0.85)
        דראודאון יחסי: 0.65 → ציון 10 (ירד פחות מהשוק)
        מתאם: 0.72 → ציון 10 (בטווח 0.5-0.8)
        תנודתיות יחסית: 0.85 → ציון 10 (פחות תנודתי)
        זמן מעל MA-200: 68% → ציון 8 (מעל 60%)
        תמחור P/E: 15.2 (P25) → ציון 9 (רבעון תחתון - זול יחסית)
        
        ציון סופי: (10+10+10+10+8+9)/6 = 9.5
        דירוג: נכס דפנסיבי מצוין 🌟
        ```
        
        **מניית COST (איכותית אך יקרה):**
        ```
        בטא: 0.82 → ציון 10 (בטווח דפנסיבי)
        דראודאון יחסי: 0.73 → ציון 10 (עמדה במשבר)
        מתאם: 0.65 → ציון 10 (מתאם מושלם)
        תנודתיות יחסית: 0.88 → ציון 10 (תנודתיות נמוכה)
        זמן מעל MA-200: 75% → ציון 10 (יציבות גבוהה)
        תמחור P/E: 52.0 (P92) → ציון 1 (יקר מאוד יחסית להיסטוריה)
        
        ציון סופי: (10+10+10+10+10+1)/6 = 8.5
        דירוג: נכס דפנסיבי טוב 👍 (נפגע מהתמחור הגבוה)
        ```
        
        ---
        
        ## ⚙️ **טיפול בשגיאות ואמינות הנתונים**
        
        המערכת כוללת מנגנוני הגנה מתקדמים:
        - **try-catch blocks** לכל חישוב מתמטי
        - **בדיקות אפס** למניעת חלוקה באפס
        - **יישור תאריכים** לטיפול בנתונים חסרים
        - **ציון ברירת מחדל:** 0 במקרה של שגיאה חמורה
        - **ולידציה של נתונים** לפני החישובים
        
        **המטרה:** זיהוי נכסים שמשלבים **יציבות, עמידות במשבר, וגיוון פורטפוליו** תוך שמירה על חשיפה סבירה לצמיחת השוק.
        """)
        
        st.info("💡 **טיפ:** כל הפורמולות מבוססות על מחקר אקדמי בתחום הפיננסים והם מקובלים בתעשיית ההשקעות העולמית.")

if __name__ == "__main__":
    main()