
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent

mapping = pd.read_csv(
    ROOT / "reports" / "column_mapping.csv"
)

pending = mapping[
    mapping["translation_status"] == "Requires review"
]

print("=" * 55)
print("PHOENIX - ENGLISH TRANSLATION AUDIT")
print("=" * 55)

print("\nTotal column entries:", len(mapping))
print("Entries requiring review:", len(pending))

print("\nCOLUMNS TO REVIEW:")
if pending.empty:
    print("None")
else:
    print(
        pending[
            ["table", "original_column"]
        ].to_string(index=False)
    )

print("\nAUDIT COMPLETED")
