import calendar
import datetime
import pickle

class DB:
    def __init__(self):
        self.db = pickle.load(open('db.pkl','rb'))

    def add(self, date):
        self.db.add(date)
        self.commit()

    def get_calendar(self):
        c = calendar.TextCalendar(calendar.SUNDAY)
        today = datetime.datetime.today()
        s = c.formatmonth(today.year,today.month)
        for i in self.db:
            s = s.replace(' '+str(i)+'\n',' <b>'+str(i)+'</b>\n')
            s = s.replace(' '+str(i)+' ',' <b>'+str(i)+'</b> ')
            s = s.replace('\n'+str(i)+' ','\n<b>'+str(i)+'</b> ')
        s = s.replace(' ','  ')
        return s

    def commit(self):
        pickle.dump(self.db, open('db.pkl','wb'))

    def reset(self):
        self.db = set()
        self.commit()
