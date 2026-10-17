import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
from pathlib import Path
from urllib.parse import urlsplit


def clean_referrer(url):
    if not isinstance(url, str) or not url.strip():
        return "Unknown"
    value = url.strip()
    try:
        domain = urlsplit(value if "://" in value else "//" + value).hostname
    except ValueError:
        return "Unknown"
    return domain.removeprefix("www.") if domain else "Unknown"


def count_referrers(input_file):
    data = pd.read_csv(input_file, delimiter=';')
    if "REFERRER" not in data.columns:
        raise ValueError("Input CSV requires a REFERRER column")
    return data["REFERRER"].apply(clean_referrer).value_counts()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Summarize order referrer domains.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Save a chart instead of opening a window")
    args = parser.parse_args(argv)
    counts = count_referrers(args.input)
    if counts.empty:
        parser.error("Input CSV contains no orders")
    figure, axes = plt.subplots(figsize=(12, 7))
    sns.barplot(x=counts.index, y=counts.values, color="#25776b", ax=axes)
    axes.set(xlabel="Referrer", ylabel="Number of Orders", title="Orders by Referrer")
    plt.setp(axes.get_xticklabels(), rotation=45, ha="right")
    figure.tight_layout()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(args.output)
    else:
        plt.show()
    plt.close(figure)


if __name__ == "__main__":
    main()
