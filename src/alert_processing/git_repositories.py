import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

__all__ = [
    'get_last_commit_datetime'
]

logger = logging.getLogger(__name__)


# %%
def get_last_commit_datetime(repository_path: Path) -> Optional[datetime]:
    """
    Read the date of the latest commit of HEAD located in `repository_path`.

    If `repository_path` is a subdirectory, only commits related to files located below will be considered.
    """
    try:
        stdout = subprocess.check_output(
            [
                'git',
                "-C", repository_path,
                'log',
                '-n 1',
                '--format=%aI',
                '--', '.'
            ],
        )

        datetime_string = stdout.decode("utf-8").strip()
        return datetime.fromisoformat(datetime_string)
    except subprocess.CalledProcessError as e:
        print(f"Failed while parsing: {repository_path}")
        return None


def check_last_commit(
        repository_path: Path,
        current_time: datetime,
        max_age: timedelta,
) -> bool:
    last_commit_datetime = get_last_commit_datetime(repository_path)
    commit_age = current_time - last_commit_datetime
    logger.debug(f"Commit age {repository_path}: {commit_age}")
    return commit_age > max_age

# %%
