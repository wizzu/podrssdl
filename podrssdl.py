
import click
import feedparser
import requests
import time

from pathlib import Path
from unidecode import unidecode
from urllib.parse import urlparse


WRITE_CHUNK_SIZE = 1028 * 8
TIMESTAMP_FORMAT = '%Y%m%d'


def filenameslug(str):
    s = "".join( x for x in str if (x.isalnum() or x in "_- "))
    # "remove" accents
    s = unidecode(s)
    s = s.replace(" ", "_")
    return s.lower()


def sizeof_fmt(num, suffix="B"):
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if round(num) < 1024.0:
            if unit == "":
                return f"{num:4d} {unit}{suffix}"
            else:
                return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Yi{suffix}"


def dlurltofile(url, filename):
    r = requests.get(url, stream=True)
    r.raise_for_status()
    bytescount = 0
    with open(filename, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=WRITE_CHUNK_SIZE):
            fd.write(chunk)
            bytescount += len(chunk)
    return bytescount


def dlpodentry(podname, dirname, entry):
    title = entry.title
    ts = entry.published_parsed

    podlink = None
    for link in entry.links:
        if link.href:
            urlparsed = urlparse(link.href)
            if urlparsed.path.endswith('.mp3'):
                podlink = link.href
                break

    # Assumption: Only one entry per date
    # This is likely not a generic situation.
    tsstr = time.strftime(TIMESTAMP_FORMAT, ts)
    filename = f"{dirname}/{podname.lower()}-{tsstr}-{filenameslug(title)}.mp3"

    print(f'Entry {tsstr} "{title}", link {podlink} -> {filename}')

    if not podlink:
        print("No link for entry, skipping")
        return

    try:
        Path(dirname).mkdir(parents=True, exist_ok=False)
        print(f"Created directory {dirname}")
    except FileExistsError:
        pass

    fileobj = Path(filename)
    if fileobj.is_file() and fileobj.stat().st_size > 0:
        print(f"Podcast file exists, skipping")
        return

    bytescount = dlurltofile(podlink, filename)
    print(f"Downloaded to {filename} ({sizeof_fmt(bytescount)})")


@click.command()
@click.option('--dir', default='pods', help='directory where to download podcast mp3 files')
@click.option('--maxcount', default=100, help='maximum number of entries to download')
@click.argument('url')
def podrssdl(dir, maxcount, url):
    """Download a podcast mp3 files from RSS URL."""

    feed = feedparser.parse(url)
    podname = feed.feed.title

    print(f'Parsed feed {podname}')

    for entry in feed.entries[:maxcount]:
        dlpodentry(podname, dir, entry)


if __name__ == '__main__':
    podrssdl()
