class Helper:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.cmds = {'help': self.help,
                     'h': self.help}
        self.desc = {}

        stk_example = ('/s CODE\n'
                       'example 1: get stock price of HSBC\n'
                       'e.g. /s 5\n'
                       'e.g. /s 0005')

        fx_example = ('/c CCY [to CCY]\n'
                      'example 1: get exchange rate of HKD to CNY\n'
                      'e.g. /c hkd to cny\n\n'
                      'example 2: get exchange rate of JPY to HKD\n'
                      'e.g. /c jpy\n\n'
                      '(if only 1 currency, to HKD by default)')

        i_example = ('/i CODE\n'
                     'example 1: get S&P 500 Index\n'
                     'e.g. /i gspc\n\n'
                     'example 2: get Hang Seng Index\n'
                     'e.g. /i\n'
                     'e.g. /i hsi\n\n'
                     '(if no code provided, get Hang Seng Index by default)')

        alert_example = ('/alert CODE [OPERATOR] AMT\n'
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

        reset_example = ('/reset CODE\n'
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

        ccy_example = ('/ccy [KEYWORD]\n'
                       'example 1: search curreny with keyword "taiwan"\n'
                       'e.g. /ccy taiwan\n\n'
                       'example 2: list all currencies\n'
                       'e.g. /ccy')

        idx_example = ('/idx [KEYWORD]\n'
                       'example 1: search index with keyword "Hang Seng"\n'
                       'e.g. /idx hang seng\n\n'
                       'example 2: list all indices\n'
                       'e.g. /idx')

        us_example = ('/us CODE\n'
                      'example 1: search IBM US stock price\n'
                      'e.g. /us ibm')

        ma_example = ('/ma CODE\n'
                      'example 1: search 2888 stock moving average\n'
                      'e.g. /ma 2888\n'
                      'e.g. /ma 02888')

        rsi_example = ('/rsi CODE\n'
                       'example 1: search HSBC stock relative strength index\n'
                       'e.g. /rsi 5\n'
                       'e.g. /rsi 0005')

        self.examples = {'s': stk_example,
                         'c': fx_example,
                         'i': i_example,
                         'alert': alert_example,
                         'reset': reset_example,
                         'ccy': ccy_example,
                         'idx': idx_example,
                         'us': us_example,
                         'ma': ma_example,
                         'rsi': rsi_example}

    def help(self, data):
        data['method'] = 'sendMessage'
        args = data['args'].strip().split()
        if len(args) == 0:
            data['text'] = '\n\n\n'.join(self.examples.values())
        else:
            dct = {k: v for k, v in self.examples.items() if k in args}
            dct = self.examples if len(dct) == 0 else dct
            data['text'] = '\n\n\n'.join(dct.values())
