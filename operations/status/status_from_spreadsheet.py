from datetime import datetime
import re

import pandas as pd

from app import db
from models.journal import Journal, JournalStatus


class StatusFromSpreadsheet:
    def __init__(self, file_path):
        self.df = None
        self.file_path = file_path

    def update_status(self):
        self.read_data()
        self.save_data()

    def read_data(self):
        self.df = pd.read_excel(self.file_path)

    def save_data(self):
        for index, row in self.df.iterrows():
            issn = row.get("ISSN")
            status = row.get("Status")
            history = row.get("Change History")
            journal = Journal.find_by_issn(issn)

            if status == "Discontinued":
                journal.status = JournalStatus.CEASED.value
                year = re.findall(r"\d{4}", history) if type(history) is str else None
                journal.status_as_of = (
                    datetime(int(year[0]), 1, 1) if year else datetime.now()
                )
                print(
                    "setting issn {} with status {}".format(
                        journal.issn_l, JournalStatus.CEASED.value
                    )
                )

            elif status == "Changed Name":
                journal.status = JournalStatus.RENAMED.value
                journal.status_as_of = datetime.now()
                print(
                    "setting issn {} with status {}".format(
                        journal.issn_l, JournalStatus.RENAMED.value
                    )
                )

            elif status == "Incorporated":
                journal.status = JournalStatus.INCORPORATED.value
                journal.status_as_of = datetime.now()
                print(
                    "setting issn {} with status {}".format(
                        journal.issn_l, JournalStatus.INCORPORATED.value
                    )
                )

        db.session.commit()
