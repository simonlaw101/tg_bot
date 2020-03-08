class Helper:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.cmds = {'help':self.help,
                     'h':self.help}
        self.desc = {}
        
        stk_example = ('/stk CODE\n'
                        'example 1: get stock price of HSBC\n'
                        'e.g. /stk 5\n'
                        'e.g. /stk 0005')
        
        fx_example = ('/fx CCY [to CCY]\n'
                      'example 1: get exchange rate of HKD to CNY\n'
                      'e.g. /fx hkd to cny\n\n'
                      'example 2: get exchange rate of JPY to HKD\n'
                      'e.g. /fx jpy\n\n'
                      '(if only 1 currency, to HKD by default)')

        alert_example = ('/alert CODE [OPERATOR] AMT\n'
                         '/alert CCY [to CCY] [OPERATOR] AMT\n'
                         'example 1: set alert when HSBC stock is lower than 50\n'
                         'e.g. /alert 5 50\n'
                         'e.g. /alert 0005 &lt50\n\n'
                         'example 2: set alert when rate of JPY to HKD is lower than 0.07\n'
                         'e.g. /alert jpy to hkd 0.07\n'
                         'e.g. /alert jpy 0.07\n\n'
                         'example 3: set alert when rate of HKD to TWD is higher than 3.8\n'
                         'e.g. /alert hkd to twd &gt3.8\n\n'
                         '(if only 1 currency, to HKD by default)\n'
                         '(if no comparison operator, &lt by default)\n\n\n'
                         '/alert\n'
                         'example 1: view all alerts set\n'
                         'e.g. /alert')
        
        reset_example = ('/reset\n'
                         'example 1: clear alerts on stock 0005\n'
                         'e.g. /reset 5\n'
                         'e.g. /reset 0005\n\n'
                         'example 2: clear alerts on exchange rate JPY to HKD\n'
                         'e.g. /reset jpy\n'
                         'e.g. /reset jpy to hkd\n\n'
                         'example 3: clear all alerts\n'
                         'e.g. /reset')

        ccy_example = ('/ccy\n'
                       'example 1: search curreny with keyword "taiwan"\n'
                       'e.g. /ccy taiwan\n\n'
                       'example 2: list all currencies\n'
                       'e.g. /ccy')

        self.examples = {'stk': stk_example,
                         'fx': fx_example,
                         'alert': alert_example,
                         'reset': reset_example,
                         'ccy': ccy_example}

    def help(self, data):
        data['method'] = 'sendMessage'
        args = data['args'].strip()
        if args in self.examples.keys():
            data['text'] = self.examples[args]
        else:
            data['text'] = '\n\n\n'.join(self.examples.values())
