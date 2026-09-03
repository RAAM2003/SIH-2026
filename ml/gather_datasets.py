"""Download prototype datasets while keeping source files and provenance separate."""

from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path = [entry for entry in sys.path if Path(entry or ".").resolve() != SCRIPT_DIR]


ROOT = Path(__file__).resolve().parent / "datasets"


def download_adivaani() -> None:
    from datasets import load_dataset

    for language in ("santhali", "mundari"):
        dataset = load_dataset(
            "adivaanihf/adivaani-tribal-english-parallel-corpus",
            language,
            split="train",
        )
        target = ROOT / ("santali" if language == "santhali" else "mundari") / "raw" / "adivaani.parquet"
        dataset.to_parquet(target)
        print(f"{language}: {len(dataset)} rows -> {target}")


def download_education_santali() -> None:
    from huggingface_hub import hf_hub_download

    target_dir = ROOT / "santali" / "raw"
    source = hf_hub_download(
        repo_id="coild-aikosh/Education_v2",
        filename="HIN-SAT/Source_Reviewed/EDU/Source_Reviewed.txt",
        repo_type="dataset",
    )
    output = target_dir / "Education_v2_HIN_SAT_Source_Reviewed.txt"
    output.write_bytes(Path(source).read_bytes())
    print(f"saved {output}")


def main() -> None:
    for directory in (
        ROOT / language / stage
        for language in ("santali", "mundari", "ho")
        for stage in ("raw", "cleaned", "validated")
    ):
        directory.mkdir(parents=True, exist_ok=True)
    try:
        download_adivaani()
    except Exception as exc:
        print(f"Adi Vaani was not downloaded: {type(exc).__name__}: {exc}")
    try:
        download_education_santali()
    except Exception as exc:
        print(f"Education_v2 was not downloaded: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()