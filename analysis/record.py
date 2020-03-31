from abc import ABC

class Record(ABC):

    def to_csv_entry(self):
        dat = sorted(vars(self).items(), key=lambda t: t[0])
        return ",".join([v for k, v in dat])

