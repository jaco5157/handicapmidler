# Referral Reporting

Aggregate order referrer domains into an interactive or saved chart. Python 3.11+ is required; no service deployment is involved.

From the repository root:

```sh
cd tools/reporting/referrals
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python referrals.py --input fixtures/referrals.csv
MPLBACKEND=Agg .venv/bin/python referrals.py --input fixtures/referrals.csv --output output/referrals.png
.venv/bin/python -m unittest discover -s tests -v
```

Input is a semicolon-delimited CSV with a `REFERRER` column, one row per order. Protocol, leading `www.` and URL paths are removed; missing referrers are grouped as `Unknown`. Only synthetic example domains are tracked in `fixtures/`.

Pass real export paths with `--input`. Keep exports in ignored `private/` storage and generated charts in ignored `output/`; never commit customer/order data. Existing local exports were retained under `private/` during relocation. Discard generated charts to roll back a run.