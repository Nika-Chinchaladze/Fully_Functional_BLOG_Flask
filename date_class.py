from datetime import datetime
from calendar import month_name


class CurrentDate:
    def __init__(self):
        self.year = datetime.today().year
        self.month = datetime.today().month
        self.day = datetime.today().day

    def get_date(self):
        answer = {
            "year": self.year,
            "month": month_name[self.month],
            "day": self.day
        }
        return answer
