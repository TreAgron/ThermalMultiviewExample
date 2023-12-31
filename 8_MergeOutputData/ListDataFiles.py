import glob, os
from pathlib import Path
import pandas as pd
import numpy as np
from timeit import default_timer as timer
from datetime import timedelta, datetime

directory_path = r'C:\...\ThermalMultiviewExample'

files_path = Path(os.path.join(directory_path, 'ThermalData'))
file_list = list(files_path.glob('**/Angles*.csv'))

df = pd.DataFrame(list())
start = timer()
counter = 1
file = file_list[0]
for file in file_list:
    df_angles = pd.read_csv(file)
    start_time = np.min(df_angles['TimeStamp'])

    df_angles['StartTime'] = str(start_time)

    df = df.append(df_angles)

    end = timer()
    print(counter, ' of ', len(file_list), ' missions completed.')
    print('Time passed: ', timedelta(seconds=end - start))
    counter += 1

df.to_csv(os.path.join(os.path.join(directory_path, 'Output'), 'CombinedAngles.csv'))