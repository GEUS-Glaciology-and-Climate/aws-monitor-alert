import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd

__all__ = [
    "get_modified_time",
    "check_update_time",
]

logger = logging.getLogger(__name__)

def get_modified_time(
        files: Iterable[Path],
        skip_dir: bool = False,
        skip_hidden: bool = True,
) -> pd.DataFrame:
    paths = []
    for path in files:
        if skip_dir and path.is_dir():
            continue
        if skip_hidden and path.name[0] == '.':
            continue
        file_info = dict(
            stem=path.stem,
            path=path.as_posix(),
            modified_datetime=datetime.fromtimestamp(
                path.stat().st_mtime,
                tz=timezone.utc,
            ),
        )
        paths.append(file_info)
    return pd.DataFrame(paths, columns=['stem', 'path', 'modified_datetime'])


def check_update_time(
        dir_path: Path,
        current_time: datetime,
        max_age: timedelta,
) -> bool:
    '''Find the most recent update time for all files in dirpath,
    and return a status boolean if we pass certain time check thresholds.

    Parameters
    ----------
    dir_path : Path
        Directory path to dir containing files or station sub-directories and files
    current_time : datetime
        Current datetime used for determine file age
    max_age : timedelta
        Maximum allowed age of latest modified file before returning True.

    Returns
    -------
    status : bool
        Result of the check. False (default) is passing, True is alert condition
    '''
    modified_time_df = get_modified_time(dir_path.rglob('*'))
    if modified_time_df.empty:
        logger.warning(f"Unable to find any files in {dir_path}")
        return True
    latest_age = current_time - modified_time_df['modified_datetime'].max()
    return latest_age > max_age
