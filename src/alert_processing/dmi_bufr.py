import pandas as pd
import re
from datetime import timedelta, datetime
from ftplib import FTP

__all__ = [
    "get_dmi_bufr_stats",
    "check_dmi_ftp",
]

_dir_lines = list()


def parse_list_line(line: str):
    match = re.search(r".+ftp.+?(\d+) (.*) (\S+.bufr)\Z", line)

    if match:
        _dir_lines.append(
            dict(
                size=int(match.group(1)),
                date_string=match.group(2),
                filename=match.group(3),
            )
        )


def get_dmi_bufr_stats(user: str, passwd: str, host: str = "ftpserver.dmi.dk") -> pd.DataFrame:
    """NOTE: THIS MIGHT NOT WORKING. The DMI ftp server is not always responding to list queries on `./upload`."""
    with FTP(host=host) as ftp:
        ftp.login(user=user, passwd=passwd)
        ftp.dir('upload', parse_list_line)

    return pd.DataFrame(_dir_lines).assign(
        datetime=lambda df: pd.to_datetime(df.filename.str[5:-5], errors='coerce', utc=True)
    )


def check_dmi_ftp(
        current_time: datetime,
        max_age: timedelta,
        **dmi_credentials,
) -> bool:
    """NOTE: THIS MIGHT NOT WORKING. The DMI ftp server is not always responding to list queries on `./upload`."""
    dmi_bufr_stats = get_dmi_bufr_stats(**dmi_credentials)
    dmi_bufr_age = current_time - dmi_bufr_stats['datetime'].max()
    return dmi_bufr_age > max_age
