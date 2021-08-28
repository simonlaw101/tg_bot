class Constant:
    S_EXAMPLE = ('/s CODE\n'
                 'example 1: get stock price of HSBC\n'
                 'e.g. /s 5\n'
                 'e.g. /s 0005\n\n'
                 'example 2: get Bitcoin price\n'
                 'e.g. /s BTC-USD\n\n'
                 '(if no code provided, get HSBC stock price by default)')

    C_EXAMPLE = ('/c CCY [to CCY]\n'
                 'example 1: get exchange rate of HKD to CNY\n'
                 'e.g. /c hkd to cny\n\n'
                 'example 2: get exchange rate of JPY to HKD\n'
                 'e.g. /c jpy\n\n'
                 '(if only 1 currency, to HKD by default)\n'
                 '(if no currency code, JPY to HKD by default)')

    I_EXAMPLE = ('/i CODE\n'
                 'example 1: get S&P 500 Index\n'
                 'e.g. /i gspc\n\n'
                 'example 2: get Hang Seng Index\n'
                 'e.g. /i\n'
                 'e.g. /i hsi\n\n'
                 '(if no code provided, get Hang Seng Index by default)')

    ALERT_EXAMPLE = ('/alert CODE [OPERATOR] AMT\n'
                     '/alert CCY [to CCY] [OPERATOR] AMT\n'
                     '/alert IDX [OPERATOR] AMT\n'
                     'example 1: set alert when HSBC stock is lower than 50\n'
                     'e.g. /alert 5 50\n'
                     'e.g. /alert 0005 &lt50\n\n'
                     'example 2: set alert when rate of JPY to HKD is lower than 0.07\n'
                     'e.g. /alert jpy to hkd 0.07\n'
                     'e.g. /alert jpy 0.07\n\n'
                     'example 3: set alert when rate of HKD to TWD is higher than 3.8\n'
                     'e.g. /alert hkd to twd &gt3.8\n\n'
                     'example 4: set alert when Hang Seng Index is lower than 25000\n'
                     'e.g. /alert hsi 25000\n'
                     'e.g. /alert hsi &lt25000\n\n'
                     '(if only 1 currency, to HKD by default)\n'
                     '(if no comparison operator, &lt by default)\n\n\n'
                     '/alert\n'
                     'example 1: view all alerts set\n'
                     'e.g. /alert')

    RESET_EXAMPLE = ('/reset CODE\n'
                     '/reset CCY [to CCY]\n'
                     '/reset IDX\n'
                     'example 1: clear alerts on stock 0005\n'
                     'e.g. /reset 5\n'
                     'e.g. /reset 0005\n\n'
                     'example 2: clear alerts on exchange rate JPY to HKD\n'
                     'e.g. /reset jpy\n'
                     'e.g. /reset jpy to hkd\n\n'
                     'example 3: clear alerts on Hang Seng Index\n'
                     'e.g. /reset hsi\n\n\n'
                     '/reset\n'
                     'example 1: clear all alerts\n'
                     'e.g. /reset')

    OCR_EXAMPLE = ('/ocr LANGUAGE\n'
                   'example 1: read English text from image\n'
                   'e.g. /ocr\n'
                   'e.g. /ocr eng\n\n'
                   'example 2: read traditional Chinese text from image\n'
                   'e.g. /ocr cht\n\n'
                   '(if no language provided, read English by default)')

    DOODLE_EXAMPLE = ('Step 1: /doodle and click "Draw"\n'
                      'Step 2: Draw your masterpiece\n'
                      'Step 3: Click &#x2713;\n'
                      'Step 4: Copy and paste here!')

    CLOUD_EXAMPLE = ('/cloud FILENAME\n'
                     'example 1: upload file to the cloud with file name "test"\n'
                     'e.g. reply to file with command /cloud test\n'
                     'or send file with caption /cloud test\n\n'
                     '(if no file name provided, timestamp by default)\n\n\n'
                     '/cloud\n'
                     'example 2: view all files in the cloud\n'
                     'e.g. /cloud')

    CCY_DCT = {'AED': 'Emirati Dirham',
               'ARS': 'Argentine Peso',
               'AUD': 'Australian Dollar',
               'BGN': 'Bulgarian Lev',
               'BHD': 'Bahraini Dinar',
               'BND': 'Bruneian Dollar',
               'BRL': 'Brazilian Real',
               'BWP': 'Botswana Pula',
               'CAD': 'Canadian Dollar',
               'CHF': 'Swiss Franc',
               'CLP': 'Chilean Peso',
               'CNY': 'Chinese Yuan Renminbi',
               'COP': 'Colombian Peso',
               'CZK': 'Czech Koruna',
               'DKK': 'Danish Krone',
               'EUR': 'Euro',
               'GBP': 'British Pound',
               'HKD': 'Hong Kong Dollar',
               'HRK': 'Croatian Kuna',
               'HUF': 'Hungarian Forint',
               'IDR': 'Indonesian Rupiah',
               'ILS': 'Israeli Shekel',
               'INR': 'Indian Rial',
               'ISK': 'Icelandic Krona',
               'JPY': 'Japanese Yen',
               'KRW': 'South Korean Won',
               'KWD': 'Kuwaiti Dinar',
               'KZT': 'Kazakhstani Tenge',
               'LKR': 'Sri Lankan Rupee',
               'LYD': 'Libyan Dinar',
               'MUR': 'Mauritian Rupee',
               'MXN': 'Mexican Peso',
               'MYR': 'Malaysian Ringgit',
               'NOK': 'Norwegian Krone',
               'NPR': 'Nepalese Rupee',
               'NZD': 'New Zealand Dollar',
               'OMR': 'Omani Rial',
               'PHP': 'Philippine Peso',
               'PKR': 'Pakistani Rupee',
               'PLN': 'Polish Zloty',
               'QAR': 'Qatari Riyal',
               'RON': 'Romanian New Leu',
               'RUB': 'Russian Ruble',
               'SAR': 'Saudi Arabian Riyal',
               'SEK': 'Swedish Krona',
               'SGD': 'Singapore Dollar',
               'THB': 'Thai Baht',
               'TRY': 'Turkish Lira',
               'TTD': 'Trinidadian Dollar',
               'TWD': 'Taiwan New Dollar',
               'USD': 'US Dollar',
               'VEF': 'Venezuelan Bolivar',
               'ZAR': 'South African Rand'}

    IDX_DCT = {'%5EGSPC': 'S&P 500',
               '%5EDJI': 'Dow Jones Industrial Average',
               '%5EIXIC': 'NASDAQ Composite',
               '%5ENYA': 'NYSE COMPOSITE (DJ)',
               '%5EXAX': 'NYSE AMEX COMPOSITE INDEX',
               '%5EBUK100P': 'Cboe UK 100 Price Return',
               '%5ERUT': 'Russell 2000',
               '%5EVIX': 'Vix',
               '%5EFTSE': 'FTSE 100',
               '%5EGDAXI': 'DAX PERFORMANCE-INDEX',
               '%5EFCHI': 'CAC 40',
               '%5ESTOXX50E': 'ESTX 50 PR.EUR',
               '%5EN100': 'EURONEXT 100',
               '%5EBFX': 'BEL 20',
               'IMOEX.ME': 'MOEX Russia Index',
               '%5EN225': 'Nikkei 225',
               '%5EHSI': 'HANG SENG INDEX',
               '000001.SS': 'SSE Composite Index',
               '%5ESTI': 'STI Index',
               '%5EAXJO': 'S&P/ASX 200',
               '%5EAORD': 'ALL ORDINARIES',
               '%5EBSESN': 'S&P BSE SENSEX',
               '%5EJKSE': 'Jakarta Composite Index',
               '%5EKLSE': 'FTSE Bursa Malaysia KLCI',
               '%5ENZ50': 'S&P/NZX 50 INDEX GROSS',
               '%5EKS11': 'KOSPI Composite Index',
               '%5ETWII': 'TSEC weighted index',
               '%5EGSPTSE': 'S&P/TSX Composite index',
               '%5EBVSP': 'IBOVESPA',
               '%5EMXX': 'IPC MEXICO',
               '%5EIPSA': 'S&P/CLX IPSA',
               '%5EMERV': 'MERVAL',
               '%5ETA125.TA': 'TA-125',
               '%5ECASE30': 'EGX 30 Price Return Index',
               '%5EJN0U.JO': 'Top 40 USD Net TRI Index'}

    IDX_DCT_NO_PREFIX = {k.replace('%5E', ''): v for k, v in IDX_DCT.items()}

    STK_DETAIL_TEMPLATE_ENG = ('<b><u>{s.daily.name}</u>\n'
                               '{s.real.np}    {s.change} ({s.pctChange}%)\n\n'
                               'Open:          {s.opening.openPrice}\n'
                               'Day High:   {s.real.dyh}\n'
                               'Day Low:    {s.real.dyl}\n'
                               'Previous Close:     {s.daily.preCPrice}\n'
                               'Volume:      {s.real.vol}\n'
                               'Turnover:   {s.real.tvr}\n'
                               'P/E:         {s.peRatio:0.2f}\n'
                               'Yield:      {s.dividendYield:0.2f}%\n'
                               'Market Capital:   {s.calculation.marketValue}\n'
                               'Shares Issued:    {s.daily.issuedShare}\n'
                               '10 Days RSI:      {s.daily.rsi10}\n'
                               '14 Days RSI:      {s.daily.rsi14}\n'
                               '20 Days RSI:      {s.daily.rsi20}\n'
                               '10-Days High:     {s.daily.tenDayHigh}\n'
                               '1-Month High:     {s.daily.mthHigh}\n'
                               '52-week High:    {s.daily.wk52High}\n'
                               '10-Days Low:      {s.daily.tenDayLow}\n'
                               '1-Month Low:      {s.daily.mthLow}\n'
                               '52-week Low:     {s.daily.wk52Low}\n'
                               '10 Days SMA:      {s.daily.ma10}\n'
                               '20 Days SMA:      {s.daily.ma20}\n'
                               '50 Days SMA:      {s.daily.ma50}\n'
                               'EPS:                 {s.daily.eps}\n'
                               'Dividend:        {s.daily.dividend}\n'
                               'Spread:           {s.calculation.spread}\n'
                               'Lot Size:          {s.daily.lotSize}\n'
                               'Cost per Lot:     {s.minSubscriptionFee:0.2f}\n'
                               '</b>')

    STK_DETAIL_TEMPLATE_CHI = ('<b><u>{s.daily.nameChi}</u>\n'
                               '{s.real.np}    {s.change} ({s.pctChange}%)\n\n'
                               '開市價:　　　　{s.opening.openPrice}\n'
                               '最高價:　　　　{s.real.dyh}\n'
                               '最低價:　　　　{s.real.dyl}\n'
                               '前收市價:　　　{s.daily.preCPrice}\n'
                               '成交量:　　　　{s.real.vol}\n'
                               '成交金額:　　　{s.real.tvr}\n'
                               '市盈率:　　　　{s.peRatio:0.2f}倍\n'
                               '息率:　　　　　{s.dividendYield:0.2f}%\n'
                               '市值:　　　　　{s.calculation.marketValue}\n'
                               '發行股數:　　　{s.daily.issuedShare}\n'
                               '10日RSI:　　　 {s.daily.rsi10}\n'
                               '14日RSI:　　　 {s.daily.rsi14}\n'
                               '20日RSI:　　　 {s.daily.rsi20}\n'
                               '10日高:　　　   {s.daily.tenDayHigh}\n'
                               '1個月高:　　　 {s.daily.mthHigh}\n'
                               '52周高:　　　   {s.daily.wk52High}\n'
                               '10日低:　　　   {s.daily.tenDayLow}\n'
                               '1個月低:　　　 {s.daily.mthLow}\n'
                               '52周低:　　　   {s.daily.wk52Low}\n'
                               '10日平均價:　   {s.daily.ma10}\n'
                               '20日平均價:　   {s.daily.ma20}\n'
                               '50日平均價:　   {s.daily.ma50}\n'
                               '全年每股盈利:　{s.daily.eps}元\n'
                               '全年每股派息:　{s.daily.dividend}元\n'
                               '買賣差價:　　　{s.calculation.spread}\n'
                               '每手股數:　　　{s.daily.lotSize}股\n'
                               '入場費:　　　　{s.minSubscriptionFee:0.2f}元\n'
                               '大手成交:　　　{s.bulkTrade.Trade[0].Date}\n'
                               '每股(元):　　　 {s.bulkTradePrice}\n'
                               '股數(萬):　　　 {s.bulkTradeQty}\n'
                               '沽空紀錄:　　　{s.shortPut.Trade[0].Date}\n'
                               '沽空量:　　　　{s.shortPut.Trade[0].Qty}\n'
                               '平均價:　　　　{s.shortPut.Trade[0].Price}\n'
                               '沽空金額:　　　{s.shortPut.Trade[0].Amount}\n'
                               '</b>')

    ALERT_ERR_MSG = ('Please use the following format.\n'
                     'For stock:\n'
                     'e.g. /alert 5 50\n'
                     'e.g. /alert 0005 &gt50\n\n'
                     'For exchange rate:\n'
                     'e.g. /alert jpy 0.07\n'
                     'e.g. /alert aud &lt5\n'
                     'e.g. /alert jpy to hkd 0.07\n'
                     'e.g. /alert twd to hkd &gt3.8\n\n'
                     'For index:\n'
                     'e.g. /alert hsi 25000\n'
                     'e.g. /alert hsi &lt25000\n'
                     'e.g. /alert hsi &gt28000')

    RESET_ERR_MSG = ('Please use the following format.\n'
                     'For stock:\n'
                     'e.g. /reset 5\n'
                     'e.g. /reset 0005\n\n'
                     'For exchange rate:\n'
                     'e.g. /reset jpy\n'
                     'e.g. /reset twd to hkd\n\n'
                     'For index:\n'
                     'e.g. /reset hsi')
