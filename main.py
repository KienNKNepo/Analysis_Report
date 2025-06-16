from vnstock import Quote
import pandas_ta as ta
import pandas as pd
import json
import google.generativeai as genai 
symbol = "DBD"

# Thay đổi mã cổ phiéu
# Lấy dữ liệu lịch sử giá của cổ phiếu từ Vnstock
quote = Quote(symbol, source='VCI')
df = quote.history(start='2024-01-01', end='2024-12-31', interval='1D')
# Lấy dữ liệu VNINDEX
stock_vnindex = Quote(symbol="VNINDEX", source="VCI")
df_vnindex = stock_vnindex.history(start="2024-01-01", end="2024-12-31", interval='1D')
# Đọc dữ liệu từ file Excel
    #Đọc thông tin các mã cổ phiếu
df_infor = pd.read_excel("C:/Users/HUU KIEN/OneDrive/Máy tính/Học tập/HK8/Gói 1/BTCK/Data_MSSV_Le/Infor.xlsx")
    #Đọc dữ liệu về vốn hóa thị trường
df_mkc = pd.read_excel("C:/Users/HUU KIEN/OneDrive/Máy tính/Học tập/HK8/Gói 1/BTCK/Data_MSSV_Le/Vietnam_Marketcap.xlsx")
    #Đọc dữ liệu về bảng cân đối kế toán
df_balance_sheet = pd.read_excel("C:/Users/HUU KIEN/OneDrive/Máy tính/Học tập/HK8/Gói 1/BTCK/Data_MSSV_Chan/balance_sheet.xlsx")
    #Đọc dữ liệu về kết quả kinh doanh
df_income_statement = pd.read_excel("C:/Users/HUU KIEN/OneDrive/Máy tính/Học tập/HK8/Gói 1/BTCK/Data_MSSV_Chan/income_statement.xlsx")
    #Đọc dữ liệu về giá
df_price = pd.read_excel("C:/Users/HUU KIEN/OneDrive/Máy tính/Học tập/HK8/Gói 1/BTCK/Data_MSSV_Le/Vietnam_Price.xlsx")
    #Đọc dữ liệu về dòng tiền
df_waterfall = pd.read_excel("C:/Users/HUU KIEN/OneDrive/Máy tính/Học tập/HK8/Gói 1/BTCK/Data_MSSV_Le/Khop_lenh_Thoa_thuan.xlsx")
    #Đọc dữ liệu về lưu chuyển tiền tệ
df_money_flow = pd.read_excel("C:/Users/HUU KIEN/OneDrive/Máy tính/Học tập/HK8/Gói 1/BTCK/Data_MSSV_Chan/money_flow.xlsx")

#Hàm lấy thông tin mã cổ phiếu
def get_infor(symbol, df_infor):
    stock_inf = df_infor[df_infor["Symbol"] == f"VT:{symbol}"]
    data_infor = {
        "Tên": stock_inf["Full Name"].values[0],
        "Ngày niêm yết": stock_inf["Start Date"].values[0],
        "Mã cổ phiếu": stock_inf["Symbol"].values[0][3:],
        "Sàn": stock_inf["Exchange"].values[0],
        "Ngành": stock_inf["Sector"].values[0]
    }
    return data_infor

#Hàm phân tích cổ phiếu và đưa ra khuyến nghị
def analyze_stock_data(symbol, df):
    quote = Quote(symbol, source='VCI')
    df = quote.history(start='2024-01-01', end='2024-12-31', interval='1D')
    """
    Phân tích dữ liệu giá và tính các chỉ báo kỹ thuật
    """
    current_price = df.iloc[-1]["close"]
    # Tính MA
    df['MA10'] = df['close'].rolling(window=10).mean()
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['MA50'] = df['close'].rolling(window=50).mean()

    # Tính Bollinger Bands (BB)
    middle_bb = df['close'].rolling(window=20).mean().iloc[-1]
    std_dev = df['close'].rolling(window=20).std().iloc[-1]
    df['Middle_BB'] = middle_bb
    df['Upper_BB'] = middle_bb + 2 * std_dev
    df['lower_BB'] = middle_bb - 2 * std_dev

    # Tính RSI
    df['RSI'] = ta.rsi(close=df['close'], length=14)

    # Tính MACD
    df['MACD'] = df['close'].ewm(span=12, adjust=False).mean() - df['close'].ewm(span=26, adjust=False).mean()
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # Tính MFI
    df['Typical_Price'] = (df['high'] + df['low'] + df['close']) / 3
    df['Raw_Money_Flow'] = df['Typical_Price'] * df['volume']
    df['Positive_Flow'] = df['Raw_Money_Flow'].where(df['Typical_Price'] > df['Typical_Price'].shift(1), 0)
    df['Negative_Flow'] = df['Raw_Money_Flow'].where(df['Typical_Price'] < df['Typical_Price'].shift(1), 0)
    df['Positive_Flow_Sum'] = df['Positive_Flow'].rolling(window=14).sum()
    df['Negative_Flow_Sum'] = df['Negative_Flow'].rolling(window=14).sum()
    df['Money_Flow_Ratio'] = df['Positive_Flow_Sum'] / df['Negative_Flow_Sum']
    df['MFI'] = 100 - (100 / (1 + df['Money_Flow_Ratio']))

    # Tính khối lượng trung bình
    df['volume_avg'] = df['volume'].rolling(window=20).mean()

    # Lấy dữ liệu ngày hiện tại (dòng cuối)
    last_index = df.last_valid_index()

    # Đưa ra tín hiệu giao dịch dựa trên các chỉ báo
    buy_criteria = [
        df.loc[last_index, 'MA10'] > df.loc[last_index, 'MA20'],
        df.loc[last_index, 'MA10'] > df.loc[last_index, 'MA50'],
        df.loc[last_index, 'RSI'] < 20,
        df.loc[last_index, 'MACD'] > df.loc[last_index, 'Signal'],
        df.loc[last_index, 'close'] < df.loc[last_index, 'lower_BB'],
        df.loc[last_index, 'MFI'] < 20,
        df.loc[last_index, 'volume'] > df.loc[last_index, 'volume_avg']
    ]
    sell_criteria = [
        df.loc[last_index, 'MA10'] < df.loc[last_index, 'MA20'],
        df.loc[last_index, 'MA10'] < df.loc[last_index, 'MA50'],
        df.loc[last_index, 'RSI'] > 80,
        df.loc[last_index, 'MACD'] < df.loc[last_index, 'Signal'],
        df.loc[last_index, 'close'] > df.loc[last_index, 'Upper_BB'],
        df.loc[last_index, 'MFI'] > 80,
        df.loc[last_index, 'volume'] < df.loc[last_index, 'volume_avg']
    ]
    hold_criteria = [
        df.loc[last_index, 'MA10'] == df.loc[last_index, 'MA20'],
        (df.loc[last_index, 'RSI'] > 30 and df.loc[last_index, 'RSI'] < 70),
        df.loc[last_index, 'MACD'] == df.loc[last_index, 'Signal'],
        (df.loc[last_index, 'close'] > df.loc[last_index, 'lower_BB'] and df.loc[last_index, 'close'] < df.loc[last_index, 'Upper_BB']),
        (df.loc[last_index, 'MFI'] > 30 and df.loc[last_index, 'MFI'] < 70)
    ]

    buy = sum(buy_criteria)
    sell = sum(sell_criteria)
    hold = sum(hold_criteria)

    if buy > sell and buy > hold:
        signal = "Buy"
    elif sell > buy and sell > hold:
        signal = "Sell"
    elif hold > sell and hold > buy:
        signal = "Hold"
    else:
        signal = "Unclear signal"

    data_recommend = {
        "Giá hiện tại": current_price,
        "Mua": int(buy),
        "Nắm giữ": int(hold),
        "Bán": int(sell),
        "Khuyến nghị": signal
    }
    return data_recommend

#Hàm lấy các chỉ số tài chỉnh đầu trang
def financial_index(symbol, df, df_mkc, df_balance_sheet, df_income_statement):
    quote = Quote(symbol, source='VCI')
    df = quote.history(start='2024-01-01', end='2024-12-31', interval='1D')
    col_date = pd.Timestamp("2024-12-31")
    current_price = df.iloc[-1]["close"]
    mkc = df_mkc.loc[df_mkc["Code"] == f"VT:{symbol}(MV)", col_date].iloc[0]
    quantity = mkc/current_price 
    avg3m = df['volume'].rolling(window=30).mean().iloc[-1]
    # Tính toán EPS
    # Lấy dữ liệu từ Income Statement
    eps = df_income_statement[
        (df_income_statement["Mã"] == symbol) & (df_income_statement["Năm"] == 2024)
    ]["Lợi nhuận sau thuế thu nhập doanh nghiệp"].iloc[0] / quantity  # Sử dụng iloc[0]

    # Tính BVPS
    total_assets = df_balance_sheet[
        (df_balance_sheet["Mã"] == symbol) & (df_balance_sheet["Năm"] == 2024)
    ]["TỔNG CỘNG TÀI SẢN"].iloc[0]  # Sử dụng iloc[0]
    
    total_liabilities = df_balance_sheet[
        (df_balance_sheet["Mã"] == symbol) & (df_balance_sheet["Năm"] == 2024)
    ]["NỢ PHẢI TRẢ"].iloc[0]  # Sử dụng iloc[0]

    equity = df_balance_sheet[
        (df_balance_sheet["Mã"] == symbol) & (df_balance_sheet["Năm"] == 2024)
    ]["VỐN CHỦ SỞ HỮU"].iloc[0]  # Sử dụng iloc[0]

    bvps = (total_assets - total_liabilities) / quantity

    # Tính DoE (Debt to Equity Ratio)
    DoE = total_liabilities / equity

    # Tính ROE (Return on Equity)
    roe = df_income_statement[
        (df_income_statement["Mã"] == symbol) & (df_income_statement["Năm"] == 2024)
    ]["Lợi nhuận sau thuế thu nhập doanh nghiệp"].iloc[0] / equity

    # Tính ROA (Return on Assets)
    roa = df_income_statement[
        (df_income_statement["Mã"] == symbol) & (df_income_statement["Năm"] == 2024)
    ]["Lợi nhuận sau thuế thu nhập doanh nghiệp"].iloc[0] / total_assets

    # Tính P/E và P/B
    pe = current_price / eps
    pb = current_price / bvps
    
    data_finance ={
        "Cổ phiếu đang lưu hành": round(quantity, 2),
        "Vốn hóa": round(mkc, 2),
        "Khối lượng giao dịch trung bình 3 tháng": round(avg3m, 2),
        "EPS": eps,
        "BVPS": round(bvps, 2),
        "DoE": round(DoE, 4),
        "ROA": round(roa, 4),
        "ROE": round(roe, 4),
        "P/E": round(pe, 2),
        "P/B": round(pb, 2)
    }

    return data_finance

#Hàm lấy data vẽ chart xu hướng biến động
def get_market_data(symbol, df_vnindex, df):
    # Chuyển cột 'time' thành datetime, đặt làm index, sắp xếp cho cả 2 DataFrame
    quote = Quote(symbol, source='VCI')
    df = quote.history(start='2024-01-01', end='2024-12-31', interval='1D')
    for df_ in [df_vnindex, df]:
        df_['time'] = pd.to_datetime(df_['time'])
        df_.set_index('time', inplace=True)
        df_.sort_index(inplace=True)
    
    if df_vnindex.empty or df.empty:
        print("Không có dữ liệu thị trường trong khoảng thời gian yêu cầu!")
        return {}
    
    baseline_vnindex = df_vnindex.iloc[0]["close"]
    baseline_dbd = df.iloc[0]["close"]
    
    market_data = []
    common_dates = df_vnindex.index.intersection(df.index)
    
    for date in common_dates:
        close_vn = df_vnindex.loc[date, "close"]
        close_dbd = df.loc[date, "close"]
        
        pct_vn = (close_vn - baseline_vnindex) / baseline_vnindex * 100
        pct_dbd = (close_dbd - baseline_dbd) / baseline_dbd * 100
        
        date_str = date.strftime("%Y-%m-%d")
        market_data.append({
            "date": date_str,
            "VNINDEX": round(pct_vn, 2),
            f"{symbol}": round(pct_dbd, 2)
        })
    
    return {"Dữ liệu thị trường": market_data}

#Hàm lấy data vẽ chart biến động giá
def get_stock_price_fluctuation(symbol, df):
    quote = Quote(symbol, source='VCI')
    df = quote.history(start='2024-01-01', end='2024-12-31', interval='1D')
    if df.empty:
        print("⚠️ Không có dữ liệu cổ phiếu trong khoảng thời gian yêu cầu!")
        return {}

    # print("Index của DataFrame:", df.index)

    # Nếu index chưa phải là Datetime, thì chuyển đổi
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    df.sort_index(inplace=True)  # Sắp xếp theo thời gian

    stock_data = []
    for date, row in df.iterrows():
        stock_data.append({
            "Ngày": date.strftime("%Y-%m-%d"),  # Định dạng ngày từ index
            "Giá": row["close"],  # Giá đóng cửa
            "Khối lượng": row["volume"]
        })
    
    return {"Biến động giá": stock_data}






#Hàm lấy data vẽ chart doanh thu và lợi nhuận và tăng trưởng
def chart_finance(df_income_statement, symbol):
    """Tạo dữ liệu tài chính (doanh thu & lợi nhuận) dưới dạng JSON"""
    df_filtered = df_income_statement[df_income_statement["Mã"] == symbol]
    df_filtered = df_filtered.sort_values(by="Năm", ascending=True)

    years = df_filtered["Năm"].astype(int).astype(str).tolist()
    revenues = df_filtered["Doanh thu thuần"].tolist()
    profits = df_filtered["Lợi nhuận sau thuế thu nhập doanh nghiệp"].tolist()

    revenue_data, profit_data = [], []

    for i in range(len(years)):
        revenue_entry = {"year": years[i], "revenue": revenues[i]}
        profit_entry = {"year": years[i], "profit": profits[i]}

        if i == 0:
            revenue_entry["growth"] = 0
            profit_entry["growth"] = 0
        else:
            revenue_entry["growth"] = round((revenues[i] - revenues[i - 1]) / revenues[i - 1] * 100, 2) if revenues[i - 1] != 0 else None
            profit_entry["growth"] = round((profits[i] - profits[i - 1]) / profits[i - 1] * 100, 2) if profits[i - 1] != 0 else None
        
        revenue_data.append(revenue_entry)
        profit_data.append(profit_entry)

    return {
        "Doanh thu thuần": revenue_data,
        "Lợi nhuận sau thuế": profit_data
    }

#Hàm lấy data vẽ chart liên quan đến tài chính
def compute_financial_indicators(symbol, df_income_statement, df_balance_sheet):
    # --- 1) Lọc dữ liệu doanh nghiệp mục tiêu ---
    df_target = df_income_statement[df_income_statement["Mã"] == symbol].sort_values("Năm")
    df_target_last5 = df_target.tail(5)
    target_years = df_target_last5["Năm"].unique().tolist()
    
    target_company_data = []
    for _, row in df_target_last5.iterrows():
        year = int(row["Năm"])
        revenue = row["Doanh thu thuần"]
        gross_profit = row["Lợi nhuận gộp về bán hàng và cung cấp dịch vụ"]
        net_profit = row["Lợi nhuận sau thuế thu nhập doanh nghiệp"]
        # Lấy chi phí bán hàng và chi phí quản lý doanh nghiệp từ df_income_statement
        sales_expense = row.get("Chi phí bán hàng", None)
        # Sửa tên cột: loại bỏ khoảng trắng thừa giữa "doanh" và "nghiệp"
        admin_expense = row.get("Chi phí quản lý doanh nghiệp", None)
        
        # Lấy vốn chủ sở hữu và nợ phải trả từ df_balance_sheet dựa theo năm
        bs_row = df_balance_sheet[(df_balance_sheet["Mã"] == symbol) & (df_balance_sheet["Năm"] == year)]
        if not bs_row.empty:
            bs_row = bs_row.iloc[0]
            equity = bs_row.get("VỐN CHỦ SỞ HỮU", None)
            debt = bs_row.get("NỢ PHẢI TRẢ", None)
        else:
            equity = None
            debt = None
        
        gross_margin = (gross_profit / revenue) * 100 if revenue else None
        net_margin = (net_profit / revenue) * 100 if revenue else None
        
        if revenue and sales_expense is not None and admin_expense is not None:
            sg_a_ratio = ((sales_expense + admin_expense) / revenue) * 100
        else:
            sg_a_ratio = None
        
        if equity and equity != 0:
            roe = (net_profit / equity) * 100
        else:
            roe = None
        
        if equity and equity != 0 and debt is not None:
            debt_to_equity = (debt / equity) * 100
        else:
            debt_to_equity = None
        
        target_company_data.append({
            "year": year,
            "gross_margin": round(gross_margin, 2) if gross_margin is not None else None,
            "net_margin": round(net_margin, 2) if net_margin is not None else None,
            "sg_a_ratio": round(sg_a_ratio, 2) if sg_a_ratio is not None else None,
            "ROE": round(roe, 2) if roe is not None else None,
            "debt_to_equity": round(debt_to_equity, 2) if debt_to_equity is not None else None
        })
    
    # --- 2) Xác định Ngành ICB - cấp 2 của doanh nghiệp mục tiêu ---
    try:
        target_industry = df_balance_sheet[df_balance_sheet["Mã"] == symbol]["Ngành ICB - cấp 2"].iloc[0]
    except IndexError:
        raise ValueError(f"Không tìm thấy 'Ngành ICB - cấp 2' cho mã {symbol} trong df_balance_sheet.")
    
    # --- 3) Lọc các doanh nghiệp cùng ngành, cùng năm (theo target_years) ---
    df_industry = df_balance_sheet[
        (df_balance_sheet["Ngành ICB - cấp 2"] == target_industry) &
        (df_balance_sheet["Năm"].isin(target_years))
    ]
    
    # Tính trung bình TỔNG CỘNG TÀI SẢN của mỗi doanh nghiệp
    peers_avg_assets = df_industry.groupby("Mã")["TỔNG CỘNG TÀI SẢN"].mean().reset_index()
    # Bỏ doanh nghiệp mục tiêu ra
    peers_avg_assets = peers_avg_assets[peers_avg_assets["Mã"] != symbol]
    
    # Top 4 cho margin, SG&A, ROE
    top4_peers = peers_avg_assets.sort_values("TỔNG CỘNG TÀI SẢN", ascending=False).head(4)["Mã"].tolist()
    # Top 9 cho debt_to_equity
    top9_peers = peers_avg_assets.sort_values("TỔNG CỘNG TÀI SẢN", ascending=False).head(9)["Mã"].tolist()
    
    # --- 4) Tính margin, SG&A, ROE cho Top 4 ---
    peers_top4_data = {}
    for peer in top4_peers:
        df_peer_income = df_income_statement[
            (df_income_statement["Mã"] == peer) &
            (df_income_statement["Năm"].isin(target_years))
        ].sort_values("Năm")
        df_peer_bs = df_balance_sheet[
            (df_balance_sheet["Mã"] == peer) &
            (df_balance_sheet["Năm"].isin(target_years))
        ]
        
        peer_data_list = []
        for _, row_inc in df_peer_income.iterrows():
            year = int(row_inc["Năm"])
            revenue = row_inc["Doanh thu thuần"]
            gross_profit = row_inc["Lợi nhuận gộp về bán hàng và cung cấp dịch vụ"]
            net_profit = row_inc["Lợi nhuận sau thuế thu nhập doanh nghiệp"]
            sales_expense = row_inc.get("Chi phí bán hàng", None)
            admin_expense = row_inc.get("Chi phí quản lý doanh nghiệp", None)
            
            row_bs = df_peer_bs[df_peer_bs["Năm"] == year]
            if not row_bs.empty:
                row_bs = row_bs.iloc[0]
                equity = row_bs.get("VỐN CHỦ SỞ HỮU", None)
            else:
                equity = None
            
            gm = (gross_profit / revenue) * 100 if revenue else None
            nm = (net_profit / revenue) * 100 if revenue else None
            if revenue and sales_expense is not None and admin_expense is not None:
                sga = ((sales_expense + admin_expense) / revenue) * 100
            else:
                sga = None
            if equity and equity != 0:
                roe = (net_profit / equity) * 100
            else:
                roe = None
            
            peer_data_list.append({
                "year": year,
                "gross_margin": round(gm, 2) if gm is not None else None,
                "net_margin": round(nm, 2) if nm is not None else None,
                "sg_a_ratio": round(sga, 2) if sga is not None else None,
                "ROE": round(roe, 2) if roe is not None else None
            })
        peers_top4_data[peer] = peer_data_list
    
    # --- 5) Tính debt_to_equity cho Top 9 ---
    peers_top9_debt_data = {}
    for peer in top9_peers:
        df_peer_bs = df_balance_sheet[
            (df_balance_sheet["Mã"] == peer) &
            (df_balance_sheet["Năm"].isin(target_years))
        ]
        peer_debt_list = []
        for _, row_bs in df_peer_bs.iterrows():
            year = int(row_bs["Năm"])
            equity = row_bs.get("VỐN CHỦ SỞ HỮU", None)
            debt = row_bs.get("NỢ PHẢI TRẢ", None)
            if equity and equity != 0 and debt is not None:
                dte = (debt / equity) * 100
            else:
                dte = None
            peer_debt_list.append({
                "year": year,
                "debt_to_equity": round(dte, 2) if dte is not None else None
            })
        peers_top9_debt_data[peer] = peer_debt_list
    
    # Trả về target_company như một dictionary có key là symbol thay vì danh sách
    return {
        symbol: target_company_data,
        "peer_companies": {
            "top4": peers_top4_data,
            "top9_debt": peers_top9_debt_data
        }
    }

#Hàm tóm tắt kết quả kinh doanh
def compute_yearly_summary(symbol, df_income_statement, year=2024):
    # Hàm tính tăng trưởng yoy
    def yoy_growth(current, previous):
        if previous and previous != 0:
            return round((current - previous) / previous * 100, 2)
        else:
            return None

    # Lọc dữ liệu cho công ty, năm hiện tại (year)
    df_current = df_income_statement[
        (df_income_statement["Mã"] == symbol) &
        (df_income_statement["Năm"] == year)
    ]
    # Lọc dữ liệu cho năm trước (year-1)
    df_previous = df_income_statement[
        (df_income_statement["Mã"] == symbol) &
        (df_income_statement["Năm"] == (year - 1))
    ]

    # Giả sử mỗi năm chỉ có 1 dòng báo cáo, lấy dòng đầu tiên
    row_current = df_current.iloc[0] if not df_current.empty else None
    row_previous = df_previous.iloc[0] if not df_previous.empty else None

    # Hàm tiện ích để lấy giá trị cột (nếu không có thì trả về 0)
    def val(row, col):
        return row[col] if (row is not None and col in row) else 0

    # Lấy dữ liệu từ các cột
    current_dtt = val(row_current, "Doanh thu thuần")
    prev_dtt = val(row_previous, "Doanh thu thuần")

    current_gp = val(row_current, "Lợi nhuận gộp về bán hàng và cung cấp dịch vụ")
    prev_gp = val(row_previous, "Lợi nhuận gộp về bán hàng và cung cấp dịch vụ")

    current_sale_exp = val(row_current, "Chi phí bán hàng")
    prev_sale_exp = val(row_previous, "Chi phí bán hàng")

    current_admin_exp = val(row_current, "Chi phí quản lý doanh nghiệp")
    prev_admin_exp = val(row_previous, "Chi phí quản lý doanh nghiệp")

    current_fin_rev = val(row_current, "Doanh thu hoạt động tài chính")
    prev_fin_rev = val(row_previous, "Doanh thu hoạt động tài chính")

    current_fin_exp = val(row_current, "Chi phí tài chính")
    prev_fin_exp = val(row_previous, "Chi phí tài chính")

    current_laivay = val(row_current, "Trong đó: Chi phí lãi vay")
    prev_laivay = val(row_current, "Trong đó: Chi phí lãi vay")

    current_assoc = val(row_current, "Lãi/lỗ từ công ty liên doanh")
    prev_assoc = val(row_previous, "Lãi/lỗ từ công ty liên doanh")

    current_pretax = val(row_current, "Tổng lợi nhuận kế toán trước thuế")
    prev_pretax = val(row_previous, "Tổng lợi nhuận kế toán trước thuế")

    current_lnst_parent = val(row_current, "Cổ đông của Công ty mẹ")
    prev_lnst_parent = val(row_previous, "Cổ đông của Công ty mẹ")

    # Tính các chỉ số
    current_gross_margin = (current_gp / current_dtt * 100) if current_dtt else None
    prev_gross_margin = (prev_gp / prev_dtt * 100) if prev_dtt else None

    current_chiphi_dtt = ((current_sale_exp + current_admin_exp)/current_dtt * 100) if current_dtt else None
    prev_chiphi_dtt = ((prev_admin_exp + prev_sale_exp)/prev_dtt*100) if prev_dtt else None

    current_net_margin = (current_lnst_parent / current_dtt * 100) if current_dtt else None
    prev_net_margin = (prev_lnst_parent / prev_dtt * 100) if prev_dtt else None

    # Tạo cấu trúc kết quả
    return {
        "Doanh thu thuần": {
            "current": current_dtt,
            "previous": prev_dtt,
            "yoy": yoy_growth(current_dtt, prev_dtt)
        },
        "Lợi nhuận gộp": {
            "current": current_gp,
            "previous": prev_gp,
            "yoy": yoy_growth(current_gp, prev_gp)
        },
        "Biên lợi nhuận gộp (%)": {
            "current": round(current_gross_margin, 2) if current_gross_margin is not None else None,
            "previous": round(prev_gross_margin, 2) if prev_gross_margin is not None else None,
            "yoy": yoy_growth(current_gross_margin, prev_gross_margin)
        },
        "Chi phí bán hàng": {
            "current": current_sale_exp,
            "previous": prev_sale_exp,
            "yoy": yoy_growth(current_sale_exp, prev_sale_exp)
        },
        "Chi phí quản lý doanh nghiệp": {
            "current": current_admin_exp,
            "previous": prev_admin_exp,
            "yoy": yoy_growth(current_admin_exp, prev_admin_exp)
        },
        "Chi phí bh&qldn / DTT (%)": {
            "current": round(current_chiphi_dtt, 2) if current_chiphi_dtt is not None else None,
            "previous": round(prev_chiphi_dtt, 2) if prev_chiphi_dtt is not None else None,
            "yoy": yoy_growth(current_chiphi_dtt, prev_chiphi_dtt)
        },
        "Doanh thu hoạt động tài chính": {
            "current": current_fin_rev,
            "previous": prev_fin_rev,
            "yoy": yoy_growth(current_fin_rev, prev_fin_rev)
        },
        "Chi phí tài chính": {
            "current": current_fin_exp,
            "previous": prev_fin_exp,
            "yoy": yoy_growth(current_fin_exp, prev_fin_exp)
        },
        "Chi phí lãi vay":{
            "current": current_laivay,
            "previous": prev_laivay,
            "yoy": yoy_growth(current_laivay, prev_laivay)
        },
        "Lãi/(lỗ) công ty liên kết": {
            "current": current_assoc,
            "previous": prev_assoc,
            "yoy": yoy_growth(current_assoc, prev_assoc)
        },
        "Lợi nhuận trước thuế": {
            "current": current_pretax,
            "previous": prev_pretax,
            "yoy": yoy_growth(current_pretax, prev_pretax)
        },
        "LNST công ty mẹ": {
            "current": current_lnst_parent,
            "previous": prev_lnst_parent,
            "yoy": yoy_growth(current_lnst_parent, prev_lnst_parent)
        },
        "Biên lợi nhuận ròng (%)": {
            "current": round(current_net_margin, 2) if current_net_margin is not None else None,
            "previous": round(prev_net_margin, 2) if prev_net_margin is not None else None,
            "yoy": yoy_growth(current_net_margin, prev_net_margin)
        },
    }

#Hàm tóm tắt ngành
def get_dinh_gia_table(symbol, df_mkc, df_price, df_income_statement, df_balance_sheet, top_n=9):
    # -----------------------------
    # HÀM PHỤ: TÍNH CHỈ SỐ TÀI CHÍNH
    # -----------------------------
    def calc_fin_ratios(sym):
        """
        Tính:
          - P/E, P/B, marketcap tại ngày 12/31/2024
          - Thay đổi giá cổ phiếu (%) so với 02/01/2024
        Dựa trên df_mkc, df_price, df_income_statement, df_balance_sheet.
        """
        # Chọn mốc ngày
        date_1 = pd.Timestamp("2024-02-01")   # ngày so sánh (2/1/2024)
        date_2 = pd.Timestamp("2024-12-31")   # ngày chốt (12/31/2024)

        # Lọc df_mkc
        row_mkc = df_mkc[df_mkc["Code"] == f"VT:{sym}(MV)"]
        if row_mkc.empty or date_2 not in row_mkc.columns:
            return {"pe": None, "pb": None, "marketcap": None, "price_change": None}
        marketcap_2024 = row_mkc[date_2].iloc[0]  # Marketcap tại 12/31/2024

        # Lọc df_price (lưu ý: Code dạng "VT:{symbol}(P)" hay "VT:{symbol}(MV)"?)
        row_price = df_price[df_price["Code"] == f"VT:{sym}(P)"]
        if row_price.empty or (date_2 not in row_price.columns) or (date_1 not in row_price.columns):
            return {"pe": None, "pb": None, "marketcap": marketcap_2024, "price_change": None}
        price2 = row_price[date_2].iloc[0]  # Giá tại 12/31/2024
        price1 = row_price[date_1].iloc[0]  # Giá tại 02/01/2024

        # Thay đổi giá
        if price1 and price1 != 0:
            price_change = (price2 - price1) / price1 * 100
        else:
            price_change = None

        # Tính số cổ phiếu đang lưu hành
        if price2 != 0:
            quantity = marketcap_2024 / price2
        else:
            quantity = None

        # Lợi nhuận 2024
        row_is_2024 = df_income_statement[
            (df_income_statement["Mã"] == sym) & (df_income_statement["Năm"] == 2024)
        ]
        if not row_is_2024.empty:
            net_profit_2024 = row_is_2024["Lợi nhuận sau thuế thu nhập doanh nghiệp"].iloc[0]
        else:
            net_profit_2024 = None

        # EPS
        if quantity and quantity != 0 and net_profit_2024 is not None:
            eps = net_profit_2024 / quantity
        else:
            eps = None

        # BVPS
        row_bs_2024 = df_balance_sheet[
            (df_balance_sheet["Mã"] == sym) & (df_balance_sheet["Năm"] == 2024)
        ]
        if row_bs_2024.empty:
            return {
                "pe": None, "pb": None,
                "marketcap": marketcap_2024,
                "price_change": round(price_change, 2) if price_change else None
            }

        total_assets = row_bs_2024["TỔNG CỘNG TÀI SẢN"].iloc[0]
        total_liab = row_bs_2024["NỢ PHẢI TRẢ"].iloc[0]
        if quantity and quantity != 0:
            bvps = (total_assets - total_liab) / quantity
        else:
            bvps = None

        # Tính P/E, P/B
        if eps and eps != 0:
            pe_val = (price2 / eps)
        else:
            pe_val = None

        if bvps and bvps != 0:
            pb_val = (price2 / bvps)
        else:
            pb_val = None

        return {
            "pe": round(pe_val/1000, 1) if pe_val else None,
            "pb": round(pb_val/1000, 1) if pb_val else None,
            "marketcap": round(marketcap_2024, 2) if marketcap_2024 else None,
            "price_change": round(price_change, 2) if price_change else None
        }

    # -----------------------------
    # BƯỚC 1: XÁC ĐỊNH NGÀNH
    # -----------------------------
    row_is_2024 = df_income_statement[
        (df_income_statement["Mã"] == symbol) & (df_income_statement["Năm"] == 2024)
    ]
    if row_is_2024.empty:
        raise ValueError(f"Không có dữ liệu năm 2024 cho mã {symbol} trong df_income_statement.")
    industry = row_is_2024["Ngành ICB - cấp 2"].iloc[0]

    # -----------------------------
    # BƯỚC 2: LỌC TOP 9 CÙNG NGÀNH
    # -----------------------------
    df_same_industry = df_balance_sheet[
        (df_balance_sheet["Ngành ICB - cấp 2"] == industry) & (df_balance_sheet["Năm"] == 2024)
    ].copy()
    df_same_industry = df_same_industry.sort_values("TỔNG CỘNG TÀI SẢN", ascending=False)
    top9 = df_same_industry["Mã"].head(top_n).tolist()

    all_symbols = [symbol] + top9
    # Loại bỏ trùng
    all_symbols = list(dict.fromkeys(all_symbols))

    # -----------------------------
    # HÀM PHỤ TÍNH CHỈ SỐ CHO 1 MÃ
    # -----------------------------
    def compute_metrics(sym):
        """
        Tính:
          - Mã, Sàn
          - Doanh thu 2024
          - Tăng yoy Doanh thu (%)
          - Lợi nhuận 2024
          - Tăng yoy Lợi nhuận (%)
          - GPM (%)
          - Biên LN ròng (%)
          - ROE (%)
          - P/E, P/B, Vốn hóa, Thay đổi giá
        """
        # Income Statement 2024, 2023
        row_2024 = df_income_statement[
            (df_income_statement["Mã"] == sym) & (df_income_statement["Năm"] == 2024)
        ]
        row_2023 = df_income_statement[
            (df_income_statement["Mã"] == sym) & (df_income_statement["Năm"] == 2023)
        ]
        if row_2024.empty:
            return None

        # Sàn
        exchange = row_2024["Sàn"].iloc[0] if "Sàn" in row_2024.columns else "HOSE"

        # Doanh thu & LN
        rev_2024 = row_2024["Doanh thu thuần"].iloc[0]
        ln_2024 = row_2024["Lợi nhuận sau thuế thu nhập doanh nghiệp"].iloc[0]

        if not row_2023.empty:
            rev_2023 = row_2023["Doanh thu thuần"].iloc[0]
            ln_2023 = row_2023["Lợi nhuận sau thuế thu nhập doanh nghiệp"].iloc[0]
        else:
            rev_2023, ln_2023 = None, None

        yoy_rev = None
        if rev_2023 and rev_2023 != 0:
            yoy_rev = (rev_2024 - rev_2023) / rev_2023 * 100

        yoy_ln = None
        if ln_2023 and ln_2023 != 0:
            yoy_ln = (ln_2024 - ln_2023) / ln_2023 * 100

        # GPM
        gross_2024 = None
        if "Lợi nhuận gộp về bán hàng và cung cấp dịch vụ" in row_2024.columns:
            gross_2024 = row_2024["Lợi nhuận gộp về bán hàng và cung cấp dịch vụ"].iloc[0]

        gpm = None
        if gross_2024 and rev_2024 != 0:
            gpm = (gross_2024 / rev_2024) * 100

        # Biên LN ròng
        net_margin = (ln_2024 / rev_2024) * 100 if rev_2024 != 0 else None

        # Balance Sheet 2024
        row_bs_2024 = df_balance_sheet[
            (df_balance_sheet["Mã"] == sym) & (df_balance_sheet["Năm"] == 2024)
        ]
        if row_bs_2024.empty:
            return None

        debt_2024 = row_bs_2024["NỢ PHẢI TRẢ"].iloc[0]
        equity_2024 = row_bs_2024["VỐN CHỦ SỞ HỮU"].iloc[0]

        roe = None
        if equity_2024 and equity_2024 != 0:
            roe = (ln_2024 / equity_2024) * 100

        de = debt_2024 / equity_2024 if equity_2024 and equity_2024 != 0 else None

        # Gọi hàm phụ tính P/E, P/B, marketcap, price_change
        fin_idx = calc_fin_ratios(sym)
        pe = fin_idx["pe"]
        pb = fin_idx["pb"]
        marketcap = fin_idx["marketcap"]
        price_change = fin_idx["price_change"]

        return {
            "Mã": sym,
            "Sàn": exchange,
            "Doanh thu 2024 (tỷ)": round(rev_2024, 2),   # chia 1e3 => tỷ đồng
            "Tăng yoy Doanh thu (%)": round(yoy_rev, 2) if yoy_rev else None,
            "Lợi nhuận 2024 (tỷ)": round(ln_2024, 2),
            "Tăng yoy Lợi nhuận (%)": round(yoy_ln, 2) if yoy_ln else None,
            "GPM (%)": round(gpm, 2) if gpm else None,
            "Biên LN ròng (%)": round(net_margin, 2) if net_margin else None,
            "ROE (%)": round(roe, 2) if roe else None,
            "P/E": pe,
            "P/B": pb,
            "Vốn hóa (tỷ đồng)": round(marketcap/1000, 2) if marketcap else None,  
            "Thay đổi giá cổ phiếu (%)": price_change
        }

    # -----------------------------
    # BƯỚC 4: TÍNH CHỈ SỐ CHO 10 MÃ
    # -----------------------------
    results = []
    for sym in all_symbols:
        row_data = compute_metrics(sym)
        if row_data:
            results.append(row_data)

    # -----------------------------
    # BƯỚC 5: TÍNH TRUNG BÌNH, TRUNG VỊ
    # -----------------------------
    numeric_keys = [
        "Doanh thu 2024 (tỷ)", "Tăng yoy Doanh thu (%)", 
        "Lợi nhuận 2024 (tỷ)", "Tăng yoy Lợi nhuận (%)",
        "GPM (%)", "Biên LN ròng (%)", "ROE (%)",
        "P/E", "P/B", "Vốn hóa (tỷ đồng)", "Thay đổi giá cổ phiếu (%)"
    ]
    if results:
        df_temp = pd.DataFrame(results)
        mean_vals = {}
        median_vals = {}
        for key in numeric_keys:
            if key in df_temp.columns:
                mean_val = pd.to_numeric(df_temp[key], errors="coerce").mean()
                median_val = pd.to_numeric(df_temp[key], errors="coerce").median()
                mean_vals[key] = round(mean_val, 2) if pd.notnull(mean_val) else None
                median_vals[key] = round(median_val, 2) if pd.notnull(median_val) else None
    else:
        mean_vals = {}
        median_vals = {}

    return {"Summary_sector": results, "mean": mean_vals, "median": median_vals}

#Hàm tính tăng trưởng lợi nhuận sau thuế của 3 nhóm
def calc_profit_growth_by_sector(df_income_statement):
    years = [2020, 2021, 2022, 2023, 2024]
    result = {}

    # Hàm nội bộ tính tăng trưởng dựa trên tổng lợi nhuận theo năm của một nhóm
    def compute_growth(df_group):
        # Tính tổng lợi nhuận sau thuế cho mỗi năm
        profit_by_year = df_group.groupby("Năm")["Lợi nhuận sau thuế thu nhập doanh nghiệp"].sum()
        base = profit_by_year.get(2020, None)
        growth = {}
        for year in years:
            if base is None or base == 0:
                growth[year] = None
            else:
                profit_year = profit_by_year.get(year, None)
                if profit_year is None:
                    growth[year] = None
                else:
                    # Nếu năm 2020 là cơ sở, ta đặt tăng trưởng 0%
                    if year == 2020:
                        growth[year] = 0.0
                    else:
                        growth[year] = round((profit_year - base) / base * 100, 2)
        return growth

    # 1. Toàn thị trường: tất cả các doanh nghiệp từ năm 2020 đến 2024
    df_all = df_income_statement[df_income_statement["Năm"].isin(years)]
    result["Toàn thị trường"] = compute_growth(df_all)

    # 2. Tài chính: chỉ các doanh nghiệp có "Ngành ICB - cấp 1" là "Ngân hàng" hoặc "Tài chính"
    df_financial = df_income_statement[
        df_income_statement["Ngành ICB - cấp 1"].isin(["Ngân hàng", "Tài chính"]) & 
        df_income_statement["Năm"].isin(years)
    ]
    result["Tài chính"] = compute_growth(df_financial)

    # 3. Phi tài chính: các doanh nghiệp không thuộc nhóm tài chính
    df_non_financial = df_income_statement[
        ~df_income_statement["Ngành ICB - cấp 1"].isin(["Ngân hàng", "Tài chính"]) &
        df_income_statement["Năm"].isin(years)
    ]
    result["Phi tài chính"] = compute_growth(df_non_financial)

    return result

#Hàm tính tăng trưởng LNST của các ngành so với thị trường
def calc_yoy_growth_2024_by_icb2(df_income_statement):
    # 1) Lọc dữ liệu năm 2023 và 2024
    df_2023 = df_income_statement[df_income_statement["Năm"] == 2023]
    df_2024 = df_income_statement[df_income_statement["Năm"] == 2024]

    # 2) Tính tổng LNST 2023 và 2024 cho toàn thị trường
    lnst_2023_all = df_2023["Lợi nhuận sau thuế thu nhập doanh nghiệp"].sum()
    lnst_2024_all = df_2024["Lợi nhuận sau thuế thu nhập doanh nghiệp"].sum()

    # Tính YoY cho toàn thị trường
    if lnst_2023_all == 0:
        yoy_all = None
    else:
        yoy_all = round((lnst_2024_all - lnst_2023_all) / lnst_2023_all * 100, 2)

    # 3) Gom theo ngành ICB - cấp 2
    # Tổng LNST mỗi ngành năm 2023
    group_2023 = df_2023.groupby("Ngành ICB - cấp 2")["Lợi nhuận sau thuế thu nhập doanh nghiệp"].sum()
    # Tổng LNST mỗi ngành năm 2024
    group_2024 = df_2024.groupby("Ngành ICB - cấp 2")["Lợi nhuận sau thuế thu nhập doanh nghiệp"].sum()

    # 4) Tạo dictionary kết quả
    result = {}
    # Gán trước "Toàn thị trường"
    result["Toàn thị trường"] = yoy_all

    # Lấy danh sách tất cả ngành (union 2 tập index)
    all_icb2 = set(group_2023.index).union(set(group_2024.index))

    for icb2 in all_icb2:
        val_2023 = group_2023.get(icb2, 0)
        val_2024 = group_2024.get(icb2, 0)
        if val_2023 == 0:
            yoy_icb2 = None
        else:
            yoy_icb2 = round((val_2024 - val_2023) / val_2023 * 100, 2)
        result[icb2] = yoy_icb2

    return result

#Hàm tính % đóng góp LNST của từng ngành
def calc_icb2_profit_share_2023_2024(df_income_statement):
    # Kết quả cuối
    result = {2023: {}, 2024: {}}

    # Lọc dữ liệu cho năm 2023 và 2024
    df_2023 = df_income_statement[df_income_statement["Năm"] == 2023]
    df_2024 = df_income_statement[df_income_statement["Năm"] == 2024]

    # 1) Tính tổng LNST từng ngành năm 2023
    group_2023 = df_2023.groupby("Ngành ICB - cấp 2")["Lợi nhuận sau thuế thu nhập doanh nghiệp"].sum()
    total_2023 = group_2023.sum()  # Tổng LNST toàn thị trường năm 2023

    # 2) Tính tổng LNST từng ngành năm 2024
    group_2024 = df_2024.groupby("Ngành ICB - cấp 2")["Lợi nhuận sau thuế thu nhập doanh nghiệp"].sum()
    total_2024 = group_2024.sum()  # Tổng LNST toàn thị trường năm 2024

    # Lấy union của tất cả ngành ICB - cấp 2 xuất hiện ở 2023 hoặc 2024
    all_icb2 = set(group_2023.index).union(group_2024.index)

    # 3) Tính % cho năm 2023
    for icb2 in all_icb2:
        profit_2023 = group_2023.get(icb2, 0)
        if total_2023 == 0:
            result[2023][icb2] = None
        else:
            result[2023][icb2] = round(profit_2023 / total_2023 * 100, 2)

    # 4) Tính % cho năm 2024
    for icb2 in all_icb2:
        profit_2024 = group_2024.get(icb2, 0)
        if total_2024 == 0:
            result[2024][icb2] = None
        else:
            result[2024][icb2] = round(profit_2024 / total_2024 * 100, 2)

    return result

#Hàm phân loại 4 nhóm ngành
def classify_industry_growth(df_income_statement):
    # Các năm cần tính
    years = [2021, 2022, 2023, 2024]

    # Lọc 5 năm 2020->2024
    df_5years = df_income_statement[df_income_statement["Năm"].isin([2020, 2021, 2022, 2023, 2024])].copy()

    # Loại bỏ các dòng ngành "Ngân hàng" trong "Ngành ICB - cấp 2"
    df_5years = df_5years[df_5years["Ngành ICB - cấp 2"] != "Ngân hàng"]

    # Gom theo Ngành ICB - cấp 2, Năm => sum(Doanh thu), sum(LNST)
    grouped = df_5years.groupby(["Ngành ICB - cấp 2", "Năm"]).agg({
        "Doanh thu thuần": "sum",
        "Lợi nhuận sau thuế thu nhập doanh nghiệp": "sum"
    }).reset_index()

    # Tạo pivot => row=Ngành, col=Năm => sum(Doanh thu), sum(LNST)
    pivot_rev = grouped.pivot(index="Ngành ICB - cấp 2", columns="Năm", values="Doanh thu thuần").fillna(0)
    pivot_lnst = grouped.pivot(index="Ngành ICB - cấp 2", columns="Năm", values="Lợi nhuận sau thuế thu nhập doanh nghiệp").fillna(0)

    # Kết quả "data" => dict
    data_dict = {}

    # Duyệt từng ngành
    for icb2 in pivot_rev.index:
        # Lấy Doanh thu 2020, LNST 2020
        rev_2020 = pivot_rev.loc[icb2, 2020] if 2020 in pivot_rev.columns else 0
        lnst_2020 = pivot_lnst.loc[icb2, 2020] if 2020 in pivot_lnst.columns else 0

        # Tính yoy revenue, yoy lnst
        yoy_rev_dict = {}
        yoy_lnst_dict = {}

        for y in years:
            rev_y = pivot_rev.loc[icb2, y] if y in pivot_rev.columns else 0
            lnst_y = pivot_lnst.loc[icb2, y] if y in pivot_lnst.columns else 0

            if rev_2020 == 0:
                yoy_rev_dict[y] = None
            else:
                yoy_rev_dict[y] = round((rev_y - rev_2020) / rev_2020 * 100, 2)

            if lnst_2020 == 0:
                yoy_lnst_dict[y] = None
            else:
                yoy_lnst_dict[y] = round((lnst_y - lnst_2020) / lnst_2020 * 100, 2)

        data_dict[icb2] = {
            "RevenueGrowth": yoy_rev_dict,
            "LNSTGrowth": yoy_lnst_dict
        }

    # Bắt đầu phân loại
    # Tạo 4 list
    tang_truong = []
    hoi_phuc = []
    tao_day = []
    suy_yeu = []

    # Hàm phụ: Lấy chuỗi yoy LNST
    def get_lnst_seq(icb2):
        return [data_dict[icb2]["LNSTGrowth"][y] for y in years]

    def get_rev_seq(icb2):
        return [data_dict[icb2]["RevenueGrowth"][y] for y in years]

    for icb2 in data_dict.keys():
        lnst_seq = get_lnst_seq(icb2)  # list [2021->2024]
        rev_seq = get_rev_seq(icb2)

        # Kiểm tra logic
        # 1) Tăng trưởng: LN yoy >= 0 cho tất cả, Doanh thu yoy >= 0 cho tất cả
        if all(x is not None and x >= 0 for x in lnst_seq) and all(r is not None and r >= 0 for r in rev_seq):
            tang_truong.append(icb2)
            continue

        # 2) Hồi phục: LN yoy năm 2024 > 0, từng có năm < 0
        #    Doanh thu có thể dao động, miễn 2024 >= 0
        if (lnst_seq[-1] is not None and lnst_seq[-1] > 0) and any(x is not None and x < 0 for x in lnst_seq):
            hoi_phuc.append(icb2)
            continue

        # 3) Tạo đáy: LN yoy năm 2024 vẫn < 0, nhưng giảm âm so với năm 2023
        #    => LNST(2024) < 0 & LNST(2023) < 0 & LNST(2024) > LNST(2023)
        if lnst_seq[-1] is not None and lnst_seq[-2] is not None:
            if lnst_seq[-1] < 0 < lnst_seq[-2]: 
                # => Từ dương sang âm => có thể "suy yếu" thay
                pass
            else:
                # Check
                if (lnst_seq[-1] < 0) and (lnst_seq[-2] < 0) and (lnst_seq[-1] > lnst_seq[-2]):
                    tao_day.append(icb2)
                    continue

        # 4) Suy yếu: 
        #    LN yoy tiếp tục giảm sâu (so sánh 2024 < 2023) hoặc 
        #    chuyển từ dương sang âm
        if lnst_seq[-1] is not None and lnst_seq[-2] is not None:
            # Từ dương sang âm
            if (lnst_seq[-2] > 0) and (lnst_seq[-1] < 0):
                suy_yeu.append(icb2)
                continue
            # Hoặc âm nặng hơn
            if (lnst_seq[-1] < lnst_seq[-2]) and (lnst_seq[-2] < 0):
                suy_yeu.append(icb2)
                continue

        # Nếu không rơi vào logic nào, có thể xếp tạm vào "Suy yếu" 
        # hoặc "Khác" tuỳ ý
        # Ở đây ta xếp tạm vào "Suy yếu"
        suy_yeu.append(icb2)

    return {
        "data": data_dict, 
        "groups": {
            "Tăng trưởng": tang_truong,
            "Hồi phục": hoi_phuc,
            "Tạo đáy": tao_day,
            "Suy yếu": suy_yeu
        }
    }

#Hàm tính % vốn hóa thị trường ngành
def marketcap_by_sector(df_mkc, df_income_statement):
    # Tạo bản sao để không làm thay đổi df_mkc gốc
    df_mkc = df_mkc.copy()
    
    # 1. Từ cột "Code" (ví dụ: "VT:DBD(MV)") lấy phần mã cổ phiếu, ví dụ "DBD"
    df_mkc["Mã"] = df_mkc["Code"].apply(lambda x: x.split(":")[1].split("(")[0] if pd.notnull(x) and ":" in x and "(" in x.split(":")[1] else None)
    
    # 2. Xác định ngày mục tiêu dưới dạng Timestamp
    target_date = pd.Timestamp("2024-12-31")
    if target_date not in df_mkc.columns:
        raise ValueError("Không tìm thấy cột với ngày 12/31/2024 trong df_mkc.")
    
    # 3. Lấy mapping giữa "Mã" và "Ngành ICB - cấp 2" từ df_income_statement
    mapping = df_income_statement.drop_duplicates(subset=["Mã"])[["Mã", "Ngành ICB - cấp 2"]].rename(
        columns={"Ngành ICB - cấp 2": "Sector"}
    )
    
    # 4. Merge df_mkc với mapping theo "Mã"
    df_merged = pd.merge(df_mkc, mapping, on="Mã", how="left")
    
    # 5. Nhóm theo Sector và tính tổng vốn hóa tại ngày target_date
    sector_sum = df_merged.groupby("Sector")[target_date].sum()
    total_marketcap = sector_sum.sum()
    
    # 6. Tính % đóng góp của mỗi ngành
    sector_pct = (sector_sum / total_marketcap * 100).round(2)
    
    return sector_pct.to_dict()

#Hàm vẽ waterfall thôgns kê dòng tiền
def extract_buy_sell_and_net_yearly(df_waterfall):
    df = df_waterfall.copy()

    # 1) Chuyển "Ngày" sang kiểu datetime
    df["Ngày"] = pd.to_datetime(df["Ngày"], format="%m/%d/%Y", errors="coerce")

    # 2) Lọc dữ liệu trong khoảng 01/01/2024 - 12/31/2024
    start_date = pd.Timestamp("2024-01-01")
    end_date   = pd.Timestamp("2024-12-31")
    df_filtered = df[(df["Ngày"] >= start_date) & (df["Ngày"] <= end_date)].copy()

    # 3) Thêm cột "Month" (theo định dạng "YYYY-MM")
    df_filtered["Month"] = df_filtered["Ngày"].dt.to_period("M").astype(str)

    # 4) Nhóm theo Month và tính tổng (chỉ áp dụng với các cột số)
    df_grouped = df_filtered.drop(columns=["Ngày"]).groupby("Month", as_index=False).sum(numeric_only=True)

    # 5) Mapping cột cho 4 nhóm NĐT cho 2 loại giao dịch
    col_map = {
        "CNTN": {
            "Khớp lệnh": {
                "Mua": "CNTN GT mua khớp lệnh (nghìn VND)",
                "Bán": "CNTN GT bán khớp lệnh (nghìn VND)"
            },
            "Thỏa thuận": {
                "Mua": "CNTN GT mua thỏa thuận (nghìn VND)",
                "Bán": "CNTN GT bán thỏa thuận (nghìn VND)"
            }
        },
        "CNNN": {
            "Khớp lệnh": {
                "Mua": "CNNN GT mua khớp lệnh (nghìn VND)",
                "Bán": "CNNN GT bán khớp lệnh (nghìn VND)"
            },
            "Thỏa thuận": {
                "Mua": "CNNN GT mua thỏa thuận (nghìn VND)",
                "Bán": "CNNN GT bán thỏa thuận (nghìn VND)"
            }
        },
        "TCTN": {
            "Khớp lệnh": {
                "Mua": "TCTN GT mua khớp lệnh (nghìn VND)",
                "Bán": "TCTN GT bán khớp lệnh (nghìn VND)"
            },
            "Thỏa thuận": {
                "Mua": "TCTN GT mua thỏa thuận (nghìn VND)",
                "Bán": "TCTN GT bán thỏa thuận (nghìn VND)"
            }
        },
        "TCNN": {
            "Khớp lệnh": {
                "Mua": "TCNN GT mua khớp lệnh (nghìn VND)",
                "Bán": "TCNN GT bán khớp lệnh (nghìn VND)"
            },
            "Thỏa thuận": {
                "Mua": "TCNN GT mua thỏa thuận (nghìn VND)",
                "Bán": "TCNN GT bán thỏa thuận (nghìn VND)"
            }
        }
    }

    # 6) Xây dựng dictionary "monthly" (các giá trị mua, bán theo tháng)
    monthly_dict = {}
    for _, row in df_grouped.iterrows():
        month_str = row["Month"]  # e.g., "2024-01"
        # Chia giá trị cho 1e9 và làm tròn 2 chữ số
        monthly_dict[month_str] = {
            "Khớp lệnh": {},
            "Thỏa thuận": {}
        }
        for group in ["CNTN", "CNNN", "TCTN", "TCNN"]:
            for trade_type in ["Khớp lệnh", "Thỏa thuận"]:
                val_buy = row.get(col_map[group][trade_type]["Mua"], 0)
                val_sell = row.get(col_map[group][trade_type]["Bán"], 0)
                # Chia cho 1e9 và làm tròn 2 chữ số
                monthly_dict[month_str][trade_type][group] = {
                    "Mua": round(val_buy / 1e9, 2) if pd.notnull(val_buy) else None,
                    "Bán": round(val_sell / 1e9, 2) if pd.notnull(val_sell) else None
                }

    # 7) Tính tổng giá trị ròng của cả năm (01/01/2024 - 12/31/2024)
    #    Cộng dồn toàn bộ df_filtered (tất cả các dòng) theo các cột
    df_year_sum = df_filtered.drop(columns=["Ngày", "Month"]).sum(numeric_only=True)

    yearly_net = {}
    for group in ["CNTN", "CNNN", "TCTN", "TCNN"]:
        kl_mua_col = col_map[group]["Khớp lệnh"]["Mua"]
        kl_ban_col = col_map[group]["Khớp lệnh"]["Bán"]
        tt_mua_col = col_map[group]["Thỏa thuận"]["Mua"]
        tt_ban_col = col_map[group]["Thỏa thuận"]["Bán"]

        kl_mua_val = df_year_sum.get(kl_mua_col, 0)
        kl_ban_val = df_year_sum.get(kl_ban_col, 0)
        tt_mua_val = df_year_sum.get(tt_mua_col, 0)
        tt_ban_val = df_year_sum.get(tt_ban_col, 0)

        net_val = (kl_mua_val + tt_mua_val) - (kl_ban_val + tt_ban_val)
        # Chia cho 1e9 và làm tròn 2 chữ số
        yearly_net[group] = round(net_val / 1e9, 2) if pd.notnull(net_val) else None

    return {
        "monthly": monthly_dict,
        "yearly_net": yearly_net
    }

#Hàm trích xuất dữ liệu mục lục
def extract_financial_data(symbol, df_income_statement, df_balance_sheet, df_money_flow):
    """
    Trích xuất dữ liệu của doanh nghiệp có mã {symbol} từ năm 2020 đến 2024.

    Các chỉ tiêu được trích xuất:

    Kết quả kinh doanh (df_income_statement):
      - Doanh thu thuần
      - Giá vốn hàng bán: Doanh thu thuần - Lợi nhuận gộp về bán hàng và cung cấp dịch vụ
      - Lợi nhuận gộp về bán hàng và cung cấp dịch vụ
      - Chi phí bán hàng và QLDN: Chi phí bán hàng + Chi phí quản lý doanh nghiệp
      - Lợi nhuận thuần từ hoạt động kinh doanh
      - Doanh thu hoạt động tài chính
      - Trong đó: Chi phí lãi vay
      - Lãi/lỗ từ công ty liên doanh
      - Lợi nhuận khác
      - Tổng lợi nhuận kế toán trước thuế
      - Lợi nhuận sau thuế thu nhập doanh nghiệp
      - Cổ đông của Công ty mẹ

    Cân đối kế toán (df_balance_sheet):
      - TÀI SẢN NGẮN HẠN: tổng của các cột:
            "Tiền và tương đương tiền", "Đầu tư tài chính ngắn hạn", "Các khoản phải thu ngắn hạn",
            "Hàng tồn kho, ròng", "Tài sản ngắn hạn khác"
      - TÀI SẢN DÀI HẠN: tổng của các cột:
            "Phải thu dài hạn", "Tài sản cố định", "Tài sản dở dang dài hạn", "Đầu tư dài hạn",
            "Tài sản dài hạn khác", "Lợi thế thương mại"
      - TỔNG CỘNG TÀI SẢN: cột "TỔNG CỘNG TÀI SẢN"
      - NỢ PHẢI TRẢ: tổng của các cột "Nợ ngắn hạn", "Nợ dài hạn"
      - VỐN CHỦ SỞ HỮU: tổng của các cột:
            "Vốn góp của chủ sở hữu", "Vốn khác", "Lợi nhuận giữ lại" (với "Lợi nhuận giữ lại" = 
            "LNST chưa phân phối lũy kế đến cuối kỳ trước" + "LNST chưa phân phối kỳ này")
      - TỔNG CỘNG NGUỒN: cột "TỔNG CỘNG NGUỒN VỐN"

    Lưu chuyển tiền tệ (df_money_flow):
      - Lãi trước thuế
      - Khấu hao TSCĐ
      - Lưu chuyển tiền tệ ròng từ các hoạt động sản xuất kinh doanh (TT)
      - Lưu chuyển tiền tệ ròng từ hoạt động đầu tư (TT)
      - Lưu chuyển tiền tệ từ hoạt động tài chính (TT)
      - Lưu chuyển tiền thuần trong kỳ (TT)

    Tất cả giá trị được làm tròn 2 chữ số thập phân.

    Return: Dictionary gồm các key "KQKD", "CDKT", "LCCT".
    """
    years = [2020, 2021, 2022, 2023, 2024]
    
    # Hàm tiện ích: chuyển giá trị về float và làm tròn 2 chữ số
    def to_float_round(val):
        try:
            f = float(val)
            return round(f, 2)
        except:
            return 0.0

    # --- KẾT QUẢ KINH DOANH (KQKD) ---
    kqkd_fields = {
        "Doanh thu thuần": "Doanh thu thuần",
        "Lợi nhuận gộp": "Lợi nhuận gộp về bán hàng và cung cấp dịch vụ",
        "Chi phí bán hàng": "Chi phí bán hàng",
        "Chi phí QLDN": "Chi phí quản lý doanh nghiệp",
        "Lợi nhuận thuần từ HĐKD": "Lợi nhuận thuần từ hoạt động kinh doanh",
        "Doanh thu HĐ tài chính": "Doanh thu hoạt động tài chính",
        "Chi phí lãi vay": "Trong đó: Chi phí lãi vay",
        "Lãi/lỗ từ công ty liên doanh": "Lãi/lỗ từ công ty liên doanh",
        "Lợi nhuận khác": "Lợi nhuận khác",
        "Tổng lợi nhuận kế toán trước thuế": "Tổng lợi nhuận kế toán trước thuế",
        "Lợi nhuận sau thuế": "Lợi nhuận sau thuế thu nhập doanh nghiệp",
        "Cổ đông của Công ty mẹ": "Cổ đông của Công ty mẹ"
    }
    
    def calc_gvhb(row):
        dt = row.get("Doanh thu thuần", 0)
        lg = row.get("Lợi nhuận gộp về bán hàng và cung cấp dịch vụ", 0)
        return to_float_round(dt) - to_float_round(lg)
    
    def calc_chiphi_bh_qldn(row):
        cbh = row.get("Chi phí bán hàng", 0)
        cqldn = row.get("Chi phí quản lý doanh nghiệp", 0)
        return to_float_round(cbh) + to_float_round(cqldn)
    
    KQKD = { field: {} for field in list(kqkd_fields.keys()) }
    KQKD["Giá vốn hàng bán"] = {}
    KQKD["Chi phí bán hàng và QLDN"] = {}

    for year in years:
        df_year = df_income_statement[(df_income_statement["Mã"] == symbol) & (df_income_statement["Năm"] == year)]
        row = df_year.iloc[0] if not df_year.empty else {}
        for field, col in kqkd_fields.items():
            val = row.get(col, 0)
            KQKD[field][year] = to_float_round(val)
        KQKD["Giá vốn hàng bán"][year] = calc_gvhb(row)
        KQKD["Chi phí bán hàng và QLDN"][year] = calc_chiphi_bh_qldn(row)
    
    # --- CÂN ĐỐI KẾ TOÁN (CDKT) ---
    # Các chỉ tiêu cần lấy:
    # "Tài sản ngắn hạn": tổng của các cột ["Tiền và tương đương tiền", "Đầu tư tài chính ngắn hạn",
    # "Các khoản phải thu ngắn hạn", "Hàng tồn kho, ròng", "Tài sản ngắn hạn khác"]
    # "Tài sản dài hạn": tổng của các cột ["Phải thu dài hạn", "Tài sản cố định", "Tài sản dở dang dài hạn",
    # "Đầu tư dài hạn", "Tài sản dài hạn khác", "Lợi thế thương mại"]
    # "Tổng cộng tài sản": "TỔNG CỘNG TÀI SẢN"
    # "Nợ phải trả": tổng của ["Nợ ngắn hạn", "Nợ dài hạn"]
    # "Vốn chủ sở hữu": tổng của ["Vốn góp của chủ sở hữu", "Vốn khác", "Lợi nhuận giữ lại"]
    # Trong đó, "Lợi nhuận giữ lại" được tính = "LNST chưa phân phối lũy kế đến cuối kỳ trước" + "LNST chưa phân phối kỳ này"
    # "Tổng cộng nguồn vốn": "TỔNG CỘNG NGUỒN VỐN"
    cdkt_fields = {
        "Tài sản ngắn hạn": ["Tiền và tương đương tiền", "Đầu tư tài chính ngắn hạn", "Các khoản phải thu ngắn hạn", "Hàng tồn kho, ròng", "Tài sản ngắn hạn khác"],
        "Tài sản dài hạn": ["Phải thu dài hạn", "Tài sản cố định", "Tài sản dở dang dài hạn", "Đầu tư dài hạn", "Tài sản dài hạn khác", "Lợi thế thương mại"],
        "Tổng cộng tài sản": "TỔNG CỘNG TÀI SẢN",
        "Nợ phải trả": ["Nợ ngắn hạn", "Nợ dài hạn"],
        "Vốn chủ sở hữu": ["Vốn góp của chủ sở hữu", "Vốn khác", "Lợi nhuận giữ lại"],
        "Tổng cộng nguồn vốn": "TỔNG CỘNG NGUỒN VỐN"
    }
    
    CDKT = { field: {} for field in cdkt_fields.keys() }
    
    def sum_columns(row, cols):
        total = 0.0
        for c in cols:
            total += to_float_round(row.get(c, 0))
        return total

    for year in years:
        df_year = df_balance_sheet[(df_balance_sheet["Mã"] == symbol) & (df_balance_sheet["Năm"] == year)]
        row = df_year.iloc[0] if not df_year.empty else {}
        for field, col in cdkt_fields.items():
            if isinstance(col, list):
                sub_dict = {}
                total = 0.0
                for c in col:
                    # Nếu là "Lợi nhuận giữ lại", tính bằng 2 cột: 
                    # "LNST chưa phân phối lũy kế đến cuối kỳ trước" + "LNST chưa phân phối kỳ này"
                    if field == "Vốn chủ sở hữu" and c == "Lợi nhuận giữ lại":
                        val = to_float_round(row.get("LNST chưa phân phối lũy kế đến cuối kỳ trước", 0)) + \
                              to_float_round(row.get("LNST chưa phân phối kỳ này", 0))
                    else:
                        val = to_float_round(row.get(c, 0))
                    sub_dict[c] = val
                    total += val
                sub_dict["Tổng"] = round(total, 2)
                CDKT[field][year] = sub_dict
            else:
                CDKT[field][year] = to_float_round(row.get(col, 0))
    
    # --- LƯU CHUYỂN TIỀN TỆ (LCCT) ---
    lcct_fields = {
        "Lãi trước thuế": "Lãi trước thuế",
        "Khấu hao TSCĐ": "Khấu hao TSCĐ",
        "Lưu chuyển tiền tệ ròng từ các hoạt động sản xuất kinh doanh (TT)": "Lưu chuyển tiền tệ ròng từ các hoạt động sản xuất kinh doanh (TT)",
        "Lưu chuyển tiền tệ ròng từ hoạt động đầu tư (TT)": "Lưu chuyển tiền tệ ròng từ hoạt động đầu tư (TT)",
        "Lưu chuyển tiền tệ từ hoạt động tài chính (TT)": "Lưu chuyển tiền tệ từ hoạt động tài chính (TT)",
        "Lưu chuyển tiền thuần trong kỳ (TT)": "Lưu chuyển tiền thuần trong kỳ (TT)"
    }
    
    LCCT = { field: {} for field in lcct_fields.keys() }
    
    for year in years:
        df_year = df_money_flow[(df_money_flow["Mã"] == symbol) & (df_money_flow["Năm"] == year)]
        row = df_year.iloc[0] if not df_year.empty else {}
        for field, col in lcct_fields.items():
            LCCT[field][year] = to_float_round(row.get(col, 0))
    
    return {
        "KQKD": KQKD,
        "CDKT": CDKT,
        "LCCT": LCCT
    }

#Hàm chatbot AI phân tích
def get_chatbotAI(symbol, df_income_statement):
    genai.configure(api_key='AIzaSyAds6_jTjsyhi6ZrTT9dG0YfCkipccpNDY')

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        safety_settings=safety_settings,
        generation_config=generation_config,
        system_instruction="This chatbot will act as a professional stock broker, supporting users in buying and selling stocks and providing information, analysis, and advice on issues related to stock codes and investments...",
    )

    chat_session = model.start_chat(history=[])

    # Phần 1: Tổng quan công ty
    sample_overview = (
        "Binh Dinh Pharmaceutical and Medical Equipment Joint Stock Company (HSX: DBD) was established in 1980, operating in the field of manufacturing, trading pharmaceuticals, medical equipment and promoting scientific research in this field. After 44 years of construction and development, DBD has produced nearly 400 products in 19 treatment groups widely distributed throughout Vietnam with a presence in 99% of hospitals and more than 20,000 pharmacies in the country. The company's 3 main treatment product groups are antibiotics, anti-cancer drugs, and dialysis solutions."
    )
    user_input_overview = f"Bạn hãy cho tôi thông tin tổng quan về công ty có mã cổ phiếu là: {symbol}, chỉ cần làm đoạn văn, không xuống dòng, tiếng Anh, khoảng 70 chữ, theo mẫu như sau: {sample_overview}, bỏ qua câu dẫn mở đầu như là: okay, sure here is the information.. hãy vào trực tiếp yêu cầu của tôi"

    try:
        response_overview = chat_session.send_message(user_input_overview)
        company_overview = response_overview.text
    except Exception as e:
        company_overview = "Không thể lấy dữ liệu tổng quan công ty."

    # Phần 2: Phân tích doanh thu và lợi nhuận
    finance_data = chart_finance(df_income_statement, symbol)
    sample_finance = ("")
    user_input_financial = f"Dựa trên dữ liệu về doanh thu thuần và lợi nhuận sau thuế này: {finance_data} của công ty có mã cổ phiếu là: {symbol}, hãy viết hai đoạn văn phân tích kết quả kinh doanh của doanh nghiệp, đặc biệt là nhấn mạnh vào năm 2024, mỗi đoạn khoảng 150 chữ bằng tiếng Anh, đi thẳng vào câu phân tích, không được có câu dẫn mở đầu như là: oke, here's an analysis of....."

    try:
        response_financial = chat_session.send_message(user_input_financial)
        financial_analysis = response_financial.text
    except Exception as e:
        financial_analysis = "Không thể phân tích doanh thu và lợi nhuận."

    #Phần 3: Điểm nhấn đầu tư
    sample_investment = (
        "Core product portfolio: DBD focuses on three main product groups: antibiotics, oncology drugs and dialysis solutions, accounting for 65% of revenue. The company is the market leader in oncology drugs in the ETC channel and the third in dialysis solutions. High growth potential thanks to large demand, competitive prices and international cooperation with Crearene AG. From 2026, DBD can participate in high-group bidding after the factory achieves EU-GMP."
        "Investing in EU-GMP standard factories: DBD is operating a cancer drug factory at 90% capacity and will upgrade to EU-GMP standard in 2026. In the period of 2024-2028, the company will invest in two new factories in Nhon Hoi that meet EU-GMP standards. Expanding production will help DBD improve its competitiveness and participate in high-level group bidding. The policy of prioritizing domestic drugs also supports DBD to expand its market share sustainably."
        "Vietnam's leading R&D: DBD pioneers the application of technology in drug production and develops nearly 100 new products from 2018–2023. The company continues to strengthen its position and meet market needs through a sustainable R&D strategy."
    )
    user_input_investment = f"Bạn hãy cho tôi 3 thông tin liên quan đến điểm nhấn đầu tư về công ty có mã cổ phiếu là: {symbol}, hãy viết thành 3 đoạn văn ngắn, KHÔNG được phản hồi lại như các từ như: okey, here are three, absolutely!...,, bằng tiếng Anh, mỗi đoạn khoảng 30 chữ, theo mẫu như sau: {sample_investment}"
    try:
        response_investment = chat_session.send_message(user_input_investment)
        company_investment = response_investment.text
    except Exception as e:
        company_investment = "Không thể lấy dữ liệu tổng quan công ty."

    #Phần 4: phân tích chart 3->5
    compute_finance_data = compute_financial_indicators(symbol, df_income_statement, df_balance_sheet)
    sample_finance = ("")
    user_input_compute_financial = f"Dựa trên dữ liệu về Biên lợi nhuận gộp (gross profit margin), Biên lợi nhuận ròng (net profit margin), Tỷ lệ chi phí SG&A trên Doanh thu và ROE như sau: {compute_finance_data} của công ty có mã cổ phiếu là: {symbol} so với top4 đối thủ có tài sản lớn nhất trong ngành, hãy viết một đoạn văn phân tích tình hình tài chính của doanh nghiệp, đặc biệt là nhấn mạnh vào năm 2024, khoảng 120 chữ bằng tiếng Anh, đi thẳng vào câu phân tích, không cần câu dẫn mở đầu."

    try:
        response_compute_financial = chat_session.send_message(user_input_compute_financial)
        compute_financial_analysis = response_compute_financial.text
    except Exception as e:
        compute_financial_analysis = "Không thể phân tích doanh thu và lợi nhuận."

    #Phần 5: Phân tích chart Nợ vay/VCSH
    debt_finance_data = compute_financial_indicators(symbol, df_income_statement, df_balance_sheet)
    sample_finance = ("")
    user_input_debt_financial = f"Dựa trên dữ liệu về Nợ vay/Vốn chủ sở hữu (debt_to_equity) như sau: {debt_finance_data} của công ty có mã cổ phiếu là: {symbol} so với top9 đối thủ có tài sản lớn nhất trong ngành, hãy viết một đoạn văn phân tích tình hình sức khỏe tài chính của doanh nghiệp, đặc biệt là nhấn mạnh vào năm 2024, khoảng 80 chữ bằng tiếng Anh, đi thẳng vào câu phân tích, không cần câu dẫn mở đầu."

    try:
        response_debt_financial = chat_session.send_message(user_input_debt_financial)
        debt_financial_analysis = response_debt_financial.text
    except Exception as e:
        debt_financial_analysis = "Không thể phân tích doanh thu và lợi nhuận."

    # --- Các phần phân tích bổ sung dựa trên compute_yearly_summary ---
    yearly_summary = compute_yearly_summary(symbol, df_income_statement, year=2024)

    # Phần 6: Phân tích các chỉ số về Doanh thu thuần, Chi phí bán hàng và Chi phí quản lý doanh nghiệp / DTT (%)
    user_input_yearly_part1 = f"Dựa trên dữ liệu năm 2024 và 2023 về Doanh thu thuần, Chi phí bán hàng và Chi phí quản lý doanh nghiệp / DTT (%) được tính theo compute_yearly_summary: {yearly_summary.get('Doanh thu thuần', {})}, {yearly_summary.get('Chi phí bán hàng', {})}, {yearly_summary.get('Chi phí quản lý doanh nghiệp / DTT (%)', {})}. Hãy viết một đoạn văn phân tích ngắn, khoảng 80 chữ, bằng tiếng Anh, đi thẳng vào câu phân tích, không có câu mở đầu chung."
    try:
        response_yearly_part1 = chat_session.send_message(user_input_yearly_part1)
        yearly_analysis_part1 = response_yearly_part1.text
    except Exception as e:
        yearly_analysis_part1 = "Không thể phân tích phần 1 năm."

    # Phần 7: Phân tích Lợi nhuận gộp và Biên lợi nhuận gộp (%)
    user_input_yearly_part2 = f"Dựa trên dữ liệu năm 2024 và 2023 về Lợi nhuận gộp và Biên lợi nhuận gộp (%) từ compute_yearly_summary: {yearly_summary.get('Lợi nhuận gộp', {})}, {yearly_summary.get('Biên lợi nhuận gộp (%)', {})}. Hãy viết một đoạn văn phân tích ngắn, khoảng 100 chữ, bằng tiếng Anh, đi thẳng vào câu phân tích."
    try:
        response_yearly_part2 = chat_session.send_message(user_input_yearly_part2)
        yearly_analysis_part2 = response_yearly_part2.text
    except Exception as e:
        yearly_analysis_part2 = "Không thể phân tích phần 2 năm."

    # Phần 8: Phân tích Doanh thu hoạt động tài chính, Chi phí tài chính và Chi phí lãi vay
    # (Giả sử dữ liệu "Trong đó: Chi phí lãi vay" có trong df_income_statement, nếu không có thì hệ thống sẽ trả về 0)
    user_input_yearly_part3 = f"Dựa trên dữ liệu năm 2024 và 2023 về Doanh thu hoạt động tài chính, Chi phí tài chính và 'Trong đó: Chi phí lãi vay' từ compute_yearly_summary: {yearly_summary.get('Doanh thu hoạt động tài chính', {})}, {yearly_summary.get('Chi phí tài chính', {})}, {yearly_summary.get('Trong đó: Chi phí lãi vay', 'N/A')}. Hãy viết một đoạn văn phân tích ngắn, khoảng 80 chữ, bằng tiếng Anh, đi thẳng vào câu phân tích."
    try:
        response_yearly_part3 = chat_session.send_message(user_input_yearly_part3)
        yearly_analysis_part3 = response_yearly_part3.text
    except Exception as e:
        yearly_analysis_part3 = "Không thể phân tích phần 3 năm."

    # Phần 9: Phân tích Lãi/(lỗ) công ty liên doanh, LNST công ty mẹ và Biên lợi nhuận ròng (%)
    user_input_yearly_part4 = f"Dựa trên dữ liệu năm 2024 và 2023 về Lãi/(lỗ) công ty liên doanh, LNST công ty mẹ và Biên lợi nhuận ròng (%) từ compute_yearly_summary: {yearly_summary.get('Lãi/(lỗ) công ty liên doanh', {})}, {yearly_summary.get('LNST công ty mẹ', {})}, {yearly_summary.get('Biên lợi nhuận ròng (%)', {})}. Hãy viết một đoạn văn phân tích ngắn, khoảng 80 chữ, bằng tiếng Anh, đi thẳng vào câu phân tích."
    try:
        response_yearly_part4 = chat_session.send_message(user_input_yearly_part4)
        yearly_analysis_part4 = response_yearly_part4.text
    except Exception as e:
        yearly_analysis_part4 = "Không thể phân tích phần 4 năm."

    # Phần 10: Phân tích lợi nhuận tăng trưởng của 3 nhóm và đóng góp vào vốn hóa
    finance_data_1 = calc_profit_growth_by_sector(df_income_statement)
    finance_data_11 = marketcap_by_sector(df_mkc, df_income_statement)
    sample_finance_1 = ("Tổng LNST toàn thị trường tăng +26% so với cùng kỳ với động lực tăng trưởng từ nhóm Phi tài chính (+32,9%) nhờ đóng góp đáng kể từ nhóm có câu chuyện hồi phục (bao gồm Thép, Hàng  không, Viễn thông, Phân bón, Bán lẻ) và Bất động sản (phần lớn nhờ bán buôn dự án và ghi nhận thu nhập từ hoạt động tài chính). Ở nhóm Tài chính, LNST tăng +20,6% so với cùng kỳ. Ngân hàng tiếp tục là trụ cột tăng trưởng chính (+21,6% YoY và 6% QoQ) trong khi Chứng khoán không còn tăng trưởng đột biến do hiệu ứng nền so sánh thấp đã hết")
    user_input_financial_1 = f"Dựa trên dữ liệu về phần trăm tăng trưởng lợi nhuận sau thuế của 3 nhóm: Toàn thị trường, Tài chính và Phi tài chính như sau: {finance_data_1} và dữ liệu về phần trăm đóng góp vào vốn hóa thị trường của từng nhóm ngành như sau: {finance_data_11}, kết hợp với cách phân tích của đoạn văn mẫu {sample_finance_1}, hãy viết 2 đoạn văn phân tích về thị trường, đặc biệt là nhấn mạnh vào năm 2024, mỗi đoạn khoảng 100 chữ bằng tiếng Anh, đi thẳng vào câu phân tích, không được có câu dẫn mở đầu như là: oke, here's an analysis of....."

    try:
        response_financial_1 = chat_session.send_message(user_input_financial_1)
        financial_analysis_1 = response_financial_1.text
    except Exception as e:
        financial_analysis_1 = "Không thể phân tích doanh thu và lợi nhuận."

    # Phần 11: Phân tích lợi nhuận tăng trưởng của từng ngành và dóng góp
    finance_data_2 = calc_yoy_growth_2024_by_icb2(df_income_statement)
    finance_data_22 = calc_icb2_profit_share_2023_2024(df_income_statement)
    sample_finance_2 = ("• Nhóm Tài chính (đóng góp 53% tổng LNST và 34,5% tổng GT vốn hóa toàn thị trường): Ngân hàng, Dịch vụ Tài chính (chủ yếu là Chứng khoán) và Bảo hiểm cùng có LNST tăng thấp hơn  mức bình quân toàn thị trường. Với Ngân hàng, LNST tăng cao so với cùng kỳ (+21,6% YoY) nhưng tăng thấp so với quý gần nhất (+6% QoQ) do tín dụng tăng không ổn định và áp lực trích  lập gia tăng. Trong khi đó, LNST của Chứng khoán tăng +5,7% YoY và giảm -6,2% QoQ, kém đi so với bức tranh lợi nhuận của quý gần nhất (+124,9% YoY và +35,5% QoQ) do không còn  hiệu ứng nền so sánh thấp cùng kỳ và TTCK không có nhiều biến động về điểm số cũng như thanh khoản trong quý 2 vừa qua."
                        "• Nhóm Phi tài chính: Các ngành sản xuất và tiêu dùng có lợi nhuận tăng trưởng vượt trội, cùng theo xu hướng hồi phục của bối cảnh vĩ mô Việt Nam và thế giới, bao gồm Bán lẻ (+1.403,3%), Du lịch & Giải trí (+406,2%), Tài nguyên Cơ bản (+278,7%). Ngược lại, LNST của Tiện ích (Điện, Nước, Khí đốt) và Y tế vẫn tiếp tục tạo đáy trong khi giảm trở lại ở Dầu khí.")
    user_input_financial_2 = f"Dựa trên dữ liệu về phần trăm tăng trưởng lợi nhuận sau thuế của từng nhóm ngành như sau: {finance_data_2} và dữ liệu về phần trăm đóng góp của chúng vào tổng lợi nhuận sau thuế của thị trường của từng nhóm ngành trong năm 2023 và 2024 như sau: {finance_data_22}, kết hợp với cách phân tích của đoạn văn mẫu {sample_finance_2}, hãy viết 1 đoạn văn phân tích về thị trường, đoạn khoảng 180 chữ bằng tiếng Anh, đi thẳng vào câu phân tích, không được có câu dẫn mở đầu như là: oke, here's an analysis of....."

    try:
        response_financial_2 = chat_session.send_message(user_input_financial_2)
        financial_analysis_2 = response_financial_2.text
    except Exception as e:
        financial_analysis_2 = "Không thể phân tích doanh thu và lợi nhuận."

    # Phần 12: Phân tích 4 phân loại của ngành (bỏ qua phần EBIT)
    finance_data_3 = classify_industry_growth(df_income_statement)
    sample_finance_3 = (
        "• In the GROWTH group, the YoY net profit trends are uneven across industries. For example, Retail and Tourism & Entertainment "
        "lead the early stage of growth with ample revenue growth and improving EBIT margins; the IT sector shows steady growth; "
        "Telecommunications and Basic Resources (e.g., Steel) have lost their low-base advantage while facing challenges in revenue growth and EBIT improvement. "
        "In Chemicals, growth comes from the Fertilizer, Plastics, and Rubber segments, while the leading company in the sector has just recovered but still shows a slight YoY decline (-1.3%) due to slow EBIT recovery and low revenue growth. "
        "In Auto & Auto Parts, non-core income and real estate-related segments remain the main drivers despite a sharp decline in core profit (-45.7% YoY)."
        " • In the RECOVERY group, Real Estate (driven by project wholesale and financial income), Personal Goods, and Food & Beverages benefit from positive business performance. "
        "In the BOTTOMING group, the Utilities sector shows a slowdown in losses with slight recovery in Gas, while in the WEAK group, some industries continue to decline or reverse from growth to decline."
    )
    user_input_financial_3 = (
        f"Based on the following industry classification data: {finance_data_3}, combined with the analysis approach in the sample below (bỏ qua phần phân tích biên EBIT): {sample_finance_3}, "
        "please write 2 concise market analysis paragraphs in English, each around 80 words, directly analyzing the market without any introductory phrases like 'okay, here's an analysis of...'."
    )

    try:
        response_financial_3 = chat_session.send_message(user_input_financial_3)
        financial_analysis_3 = response_financial_3.text
    except Exception as e:
        financial_analysis_3 = ("In the GROWTH group, Retail and Tourism & Entertainment lead with strong revenue and EBIT improvements, while IT grows steadily. Telecommunications and Basic Resources face challenges as their low-base advantage fades. Chemicals benefit from Fertilizer, Plastics, and Rubber, though the leader still sees a slight decline (-1.3% YoY). Auto & Auto Parts rely on non-core income, with core profit dropping (-45.7% YoY). In the RECOVERY group, Real Estate, Personal Goods, and Food & Beverages show strong performance. BOTTOMING sees Utilities stabilizing, while the WEAK group continues to struggle, with some sectors reversing from growth to contraction.")    
        return {
        "Tổng quan công ty": company_overview,
        "Phân tích doanh thu và lợi nhuận": financial_analysis,
        "Điểm nhấn đầu tư": company_investment,
        "Phân tích 4 chart": compute_financial_analysis,
        "Phân tích Nợ/VCSH": debt_financial_analysis,
        "Phân tích năm - Phần 1": yearly_analysis_part1,
        "Phân tích năm - Phần 2": yearly_analysis_part2,
        "Phân tích năm - Phần 3": yearly_analysis_part3,
        "Phân tích năm - Phần 4": yearly_analysis_part4,
        "Phân tích năm - Phần 5":  financial_analysis_1,
        "Phân tích năm - Phần 6": financial_analysis_2,
        "Phân tích năm - Phần 7": financial_analysis_3
    }
    
# Cấu hình AI Model
generation_config = {
    "temperature": 0,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

def generate_data(symbol):
    # Load dữ liệu từ Excel
    # df = Quote(symbol, source='VCI').history(start='2024-01-01', end='2024-12-31', interval='1D')
    # stock_vnindex = Quote(symbol="VNINDEX", source="VCI")
    # df_vnindex = stock_vnindex.history(start="2024-01-01", end="2024-12-31", interval='1D')
    # df_infor = pd.read_excel("Infor.xlsx")
    # df_mkc = pd.read_excel("Vietnam_Marketcap.xlsx")
    # df_balance_sheet = pd.read_excel("balance_sheet.xlsx")
    # df_income_statement = pd.read_excel("income_statement.xlsx")
    # df_price = pd.read_excel("Vietnam_Price.xlsx")
    # df_waterfall = pd.read_excel("Khop_lenh_Thoa_thuan.xlsx")
    # df_money_flow = pd.read_excel("money_flow.xlsx")

    # Gọi các hàm xử lý dữ liệu
    info_data = get_infor(symbol, df_infor)
    analysis_data = analyze_stock_data(symbol, df)
    financial_index_data = financial_index(symbol, df, df_mkc, df_balance_sheet, df_income_statement)
    market_data = get_market_data(symbol, df_vnindex, df)
    finance_data = chart_finance(df_income_statement, symbol)
    stock_data = get_stock_price_fluctuation(symbol, df)
    chatbot_data = get_chatbotAI(symbol, df_income_statement)
    fin_indicators_data = compute_financial_indicators(symbol, df_income_statement, df_balance_sheet)
    yearly_summary_data = compute_yearly_summary(symbol, df_income_statement)
    summary_sector = get_dinh_gia_table(symbol, df_mkc, df_price, df_income_statement, df_balance_sheet, top_n=5)
    calc_profit_growth_by_sector_data = calc_profit_growth_by_sector(df_income_statement)
    calc_yoy_growth_2024_by_icb2_data = calc_yoy_growth_2024_by_icb2(df_income_statement)
    calc_icb2_profit_share_2023_2024_data = calc_icb2_profit_share_2023_2024(df_income_statement)
    classify_industry_growth_data = classify_industry_growth(df_income_statement)
    marketcap_by_sector_data = marketcap_by_sector(df_mkc, df_income_statement)
    extract_buy_sell_and_net_yearly_data = extract_buy_sell_and_net_yearly(df_waterfall)
    extract_financial_data_data = extract_financial_data(symbol, df_income_statement, df_balance_sheet, df_money_flow)

    # Gộp tất cả dữ liệu vào một dictionary
    data = {
        # "Thông tin": info_data,
        # "Phân tích": analysis_data,
        # "Chỉ số tài chính": financial_index_data,
        **finance_data,   # Lưu ý: Nếu các dictionary có key trùng nhau thì key sau sẽ ghi đè key trước
        **market_data,
        **stock_data
    }
    if info_data is not None:
        data["Thông tin"] = info_data
    if analysis_data is not None:
        data["Phân tích"] = analysis_data
    if financial_index_data is not None:
        data["Chỉ số tài chính"] = financial_index_data
    if chatbot_data is not None:
        data["Chatbot Analysis"] = chatbot_data
    if fin_indicators_data is not None:
        data["Financial Indicators"] = fin_indicators_data
    if yearly_summary_data is not None:
        data["Yearly summary"] = yearly_summary_data
    if summary_sector is not None:
        data["Sector summary"] = summary_sector
    if calc_profit_growth_by_sector_data is not None:
        data["calc_profit_growth_by_sector_data"] = calc_profit_growth_by_sector_data
    if calc_yoy_growth_2024_by_icb2_data is not None:
        data["calc_yoy_growth_2024_by_icb2_data"] = calc_yoy_growth_2024_by_icb2_data
    if calc_icb2_profit_share_2023_2024_data is not None:
        data["calc_icb2_profit_share_2023_2024_data"] = calc_icb2_profit_share_2023_2024_data
    if classify_industry_growth_data is not None:
        data["classify_industry_growth_data"] = classify_industry_growth_data
    if marketcap_by_sector_data is not None:
        data["marketcap_by_sector_data"] = marketcap_by_sector_data
    if extract_buy_sell_and_net_yearly_data is not None:
        data["extract_buy_sell_and_net_yearly_data"] = extract_buy_sell_and_net_yearly_data
    if extract_financial_data_data is not None:
        data["extract_financial_data_data"] = extract_financial_data_data

    # Xuất dữ liệu ra file JSON
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("Dữ liệu đã được lưu vào data.json cho mã", symbol)


if __name__ == "__main__":
    generate_data(symbol)