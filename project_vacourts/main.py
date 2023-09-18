from datetime import datetime, timedelta
from va_courts_tools import VaCourtsTool

import pandas as pd

sess = VaCourtsTool(debug=True)

result = sess.initialize()
if not result[0]:
    print(result)
    exit()

result = sess.get_cases_for(courtIdx=0, date=datetime.now())
# result = sess.get_all_cases(start=datetime.now())

if not result[0]: exit()

df = pd.DataFrame(result[1])

df.to_csv('output/vacourt_data.csv')
