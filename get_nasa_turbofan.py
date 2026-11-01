"""Download NASA C-MAPSS and export one subset as labeled CSV files.

Run: python3 get_nasa_turbofan.py --subset FD001
CSV output: video/csv/FD001/ (relative to this script).
Requires only the Python standard library.

The related slope-change paper (section 6.3) specifies 100 training and 100 test engines,
but does not name FD001 or FD003; both match those counts. FD001 is a default,
not a confirmed identification of the authors' subset.
Source: https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data
"""

import argparse
import csv
import io
from pathlib import Path
import shutil
import urllib.request
from zipfile import ZipFile, is_zipfile


URL = "https://data.nasa.gov/docs/legacy/CMAPSSData.zip"
COLUMNS = ["engine_id", "cycle"] + [f"setting_{i}" for i in range(1, 4)] + [
    f"sensor_{i}" for i in range(1, 22)
]


def read_trajectory(archive, name):
    rows = []
    with archive.open(name) as raw:
        for line_number, line in enumerate(io.TextIOWrapper(raw), 1):
            values = line.split()
            if not values:
                continue
            if len(values) != 26:
                raise ValueError(f"{name}:{line_number}: expected 26 columns")
            row = [int(values[0]), int(values[1])] + list(map(float, values[2:]))
            rows.append(row)
    if not rows:
        raise ValueError(f"{name} is empty")
    return rows


def write_csv(path, columns, rows):
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        writer.writerows(rows)


def get_data(subset="FD001", output=Path(__file__).resolve().parent):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    archive_path = output / "CMAPSSData.zip"
    if not archive_path.exists():
        print(f"Downloading {URL}")
        temporary = archive_path.with_suffix(".zip.part")
        try:
            request = urllib.request.Request(URL, headers={"User-Agent": "NASA-CMAPSS-downloader/1.0"})
            with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as target:
                shutil.copyfileobj(response, target)
            if not is_zipfile(temporary):
                raise ValueError("NASA returned a response that is not a ZIP archive")
            temporary.replace(archive_path)
        finally:
            temporary.unlink(missing_ok=True)

    destination = output / "video" / "csv" / subset
    destination.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive_path) as archive:
        names = [f"{kind}_{subset}.txt" for kind in ("train", "test", "RUL")]
        for name in names:
            (destination / name).write_bytes(archive.read(name))
        train = read_trajectory(archive, names[0])
        test = read_trajectory(archive, names[1])
        rul = [int(value) for value in archive.read(names[2]).decode("ascii").split()]

    train_last, test_last = {}, {}
    for row in train:
        train_last[row[0]] = max(train_last.get(row[0], 0), row[1])
    for row in test:
        test_last[row[0]] = max(test_last.get(row[0], 0), row[1])
    if sorted(test_last) != list(range(1, len(rul) + 1)):
        raise ValueError("RUL labels do not match the test engine IDs")
    # RUL file row 1 belongs to test engine 1, and so on.
    failure_cycle = {engine: last + rul[engine - 1] for engine, last in test_last.items()}
    write_csv(destination / "train.csv", COLUMNS + ["rul"],
              (row + [train_last[row[0]] - row[1]] for row in train))
    # Test RUL is ground truth for evaluation, never an input feature.
    write_csv(destination / "test.csv", COLUMNS + ["rul"],
              (row + [failure_cycle[row[0]] - row[1]] for row in test))
    write_csv(destination / "test_engine_labels.csv",
              ["engine_id", "last_observed_cycle", "rul_at_last_cycle", "failure_cycle"],
              ([engine, test_last[engine], rul[engine - 1], failure_cycle[engine]]
               for engine in sorted(test_last)))
    print(f"{subset}: {len(train_last)} training engines ({len(train):,} rows); "
          f"{len(test_last)} test engines ({len(test):,} rows)")
    print(f"Saved raw text and CSV files to {destination}")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subset", choices=["FD001", "FD002", "FD003", "FD004"], default="FD001")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    get_data(args.subset, args.output)
