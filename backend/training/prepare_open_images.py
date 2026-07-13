from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


TRAINING_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = TRAINING_DIR / "data" / "motionguard"
DEFAULT_CLASSES = [
    "person",
    "car",
    "truck",
    "bus",
    "motorcycle",
    "bicycle",
    "backpack",
    "handbag",
    "suitcase",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert an Open Images subset into YOLO format for MotionGuard.")
    parser.add_argument("--classes-csv", required=True, help="oidv7-class-descriptions-boxable.csv")
    parser.add_argument("--train-boxes", help="train-annotations-bbox.csv")
    parser.add_argument("--train-images", help="train-images-boxable-with-rotation.csv")
    parser.add_argument("--val-boxes", help="validation-annotations-bbox.csv")
    parser.add_argument("--val-images", help="validation-images-with-rotation.csv")
    parser.add_argument("--test-boxes", help="test-annotations-bbox.csv")
    parser.add_argument("--test-images", help="test-images-with-rotation.csv")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--classes", default=",".join(DEFAULT_CLASSES), help="Comma-separated display class names.")
    parser.add_argument("--max-train", type=int, default=1200)
    parser.add_argument("--max-val", type=int, default=300)
    parser.add_argument("--max-test", type=int, default=300)
    parser.add_argument("--use-original", action="store_true", help="Download OriginalURL instead of Thumbnail300KURL.")
    parser.add_argument("--no-download", action="store_true", help="Only write labels for images already present.")
    return parser.parse_args()


def load_class_map(path: Path, wanted_classes: list[str]) -> tuple[dict[str, int], dict[int, str]]:
    wanted = {name.lower(): index for index, name in enumerate(wanted_classes)}
    label_to_class_id: dict[str, int] = {}
    class_id_to_name = {index: name for index, name in enumerate(wanted_classes)}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            display = row["DisplayName"].strip().lower()
            if display in wanted:
                label_to_class_id[row["LabelName"]] = wanted[display]

    missing = [name for name in wanted_classes if name.lower() not in {class_id_to_name[item].lower() for item in label_to_class_id.values()}]
    if missing:
        raise RuntimeError(f"Class names not found in Open Images class CSV: {', '.join(missing)}")
    return label_to_class_id, class_id_to_name


def collect_boxes(boxes_path: Path, label_to_class_id: dict[str, int], max_images: int) -> dict[str, list[str]]:
    labels_by_image: dict[str, list[str]] = defaultdict(list)
    selected: set[str] = set()
    with boxes_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            label_name = row["LabelName"]
            if label_name not in label_to_class_id:
                continue
            image_id = row["ImageID"]
            if image_id not in selected:
                if len(selected) >= max_images:
                    continue
                selected.add(image_id)

            xmin = float(row["XMin"])
            xmax = float(row["XMax"])
            ymin = float(row["YMin"])
            ymax = float(row["YMax"])
            width = max(0.0, xmax - xmin)
            height = max(0.0, ymax - ymin)
            if width <= 0 or height <= 0:
                continue
            x_center = xmin + width / 2
            y_center = ymin + height / 2
            labels_by_image[image_id].append(
                f"{label_to_class_id[label_name]} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
            )
    return labels_by_image


def resolve_image_metadata_path(path: Path) -> Path:
    if path.exists():
        return path
    alternate = None
    filename = path.name
    if "boxable-" in filename:
        alternate = filename.replace("boxable-", "")
    elif filename.endswith("with-rotation.csv") and "images-" in filename:
        alternate = filename.replace("images-", "images-boxable-")

    if alternate:
        alternate_path = path.with_name(alternate)
        if alternate_path.exists():
            print(f"WARNING: using alternate images CSV because {path} was missing: {alternate_path}")
            return alternate_path

    return path


def write_missing_ids(output_dir: Path, split: str, missing_ids: list[str]) -> None:
    if not missing_ids:
        return
    output_file = output_dir / f"missing-{split}.txt"
    output_file.write_text("\n".join(missing_ids) + "\n", encoding="utf-8")
    print(f"{split}: wrote missing image list to {output_file}")


def url_candidates_by_image_id(images_path: Path, image_ids: set[str], use_original: bool) -> dict[str, list[str]]:
    preferred_fields = ["OriginalURL", "Thumbnail300KURL", "ThumbnailURL"]
    if not use_original:
        preferred_fields = ["Thumbnail300KURL", "ThumbnailURL", "OriginalURL"]

    urls: dict[str, list[str]] = {}
    with images_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            image_id = row["ImageID"]
            if image_id in image_ids and image_id not in urls:
                candidates: list[str] = []
                for field in preferred_fields:
                    url = row.get(field)
                    if url and url not in candidates:
                        candidates.append(url)
                if candidates:
                    urls[image_id] = candidates
                    if len(urls) == len(image_ids):
                        break
    return urls


def flickr_alternate_urls(url: str) -> list[str]:
    # Some Flickr image URLs may be unavailable at one size, but available at another size.
    # Example suffixes: _z (640px), _c, _b, _o (original), etc.
    match = re.search(r"(.+)_([a-z0-9]+)(\.(jpg|jpeg|png))$", url, re.IGNORECASE)
    if not match:
        return [url]
    base, suffix, ext = match.group(1), match.group(2), match.group(3)
    alternate_sizes = ["o", "b", "c", "z", "n", "m", "t"]
    candidates = [url]
    for size in alternate_sizes:
        if size == suffix:
            continue
        candidates.append(f"{base}_{size}{ext}")
    return candidates


def download_image(url: str, destination: Path) -> bool:
    request = Request(url, headers={"User-Agent": "MotionGuardAI/1.0"})
    try:
        with urlopen(request, timeout=30) as response:
            data = response.read()
    except (OSError, URLError) as exc:
        print(f"download failed: {url} ({exc})")
        return False
    destination.write_bytes(data)
    return True


def download_image_candidates(image_id: str, urls: list[str], destination: Path) -> bool:
    seen = set()
    for url in urls:
        for candidate in flickr_alternate_urls(url):
            if candidate in seen:
                continue
            seen.add(candidate)
            if download_image(candidate, destination):
                return True
    print(f"all downloads failed for image {image_id}")
    return False


def write_split(
    split: str,
    boxes_path: Path,
    images_path: Path,
    label_to_class_id: dict[str, int],
    output_dir: Path,
    max_images: int,
    use_original: bool,
    no_download: bool,
) -> tuple[int, int, list[str]]:
    labels_by_image = collect_boxes(boxes_path, label_to_class_id, max_images)
    image_dir = output_dir / "images" / split
    label_dir = output_dir / "labels" / split
    image_dir.mkdir(parents=True, exist_ok=True)
    label_dir.mkdir(parents=True, exist_ok=True)

    urls = {} if no_download else url_candidates_by_image_id(images_path, set(labels_by_image), use_original)
    written = 0
    missing = 0
    missing_ids: list[str] = []
    for image_id, label_lines in labels_by_image.items():
        image_path = image_dir / f"{image_id}.jpg"
        if not image_path.exists() and not no_download:
            candidates = urls.get(image_id, [])
            if not candidates or not download_image_candidates(image_id, candidates, image_path):
                missing += 1
                missing_ids.append(f"{image_id}\t{','.join(candidates) if candidates else 'no_urls'}")
                continue
        if not image_path.exists():
            missing += 1
            missing_ids.append(f"{image_id}\tfile_not_found")
            continue
        (label_dir / f"{image_id}.txt").write_text("\n".join(label_lines) + "\n", encoding="utf-8")
        written += 1
        if written % 100 == 0:
            print(f"{split}: wrote {written} images")
    write_missing_ids(output_dir, split, missing_ids)
    return written, missing, missing_ids


def write_dataset_yaml(output_dir: Path, class_id_to_name: dict[int, str]) -> None:
    names = "\n".join(f"  {index}: {name}" for index, name in class_id_to_name.items())
    content = f"""path: {output_dir.as_posix()}
train: images/train
val: images/val
test: images/test

names:
{names}
"""
    (TRAINING_DIR / "datasets" / "motionguard-openimages.yaml").write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    wanted_classes = [item.strip().lower() for item in args.classes.split(",") if item.strip()]
    output_dir = Path(args.output).resolve()
    label_to_class_id, class_id_to_name = load_class_map(Path(args.classes_csv), wanted_classes)
    write_dataset_yaml(output_dir, class_id_to_name)

    split_configs = [
        ("train", args.train_boxes, args.train_images, args.max_train),
        ("val", args.val_boxes, args.val_images, args.max_val),
        ("test", args.test_boxes, args.test_images, args.max_test),
    ]

    for split, boxes, images, max_images in split_configs:
        if not boxes or not images:
            print(f"{split}: skipped because boxes/images CSV was not provided")
            continue
        image_path = resolve_image_metadata_path(Path(images))
        if not image_path.exists() and not args.no_download:
            print(f"ERROR: images metadata CSV not found for {split}: {image_path}")
            return 3
        written, missing, missing_ids = write_split(
            split,
            Path(boxes),
            image_path,
            label_to_class_id,
            output_dir,
            max_images,
            args.use_original,
            args.no_download,
        )
        print(f"{split}: ready={written}, missing={missing}")
        if missing_ids:
            print(f"{split}: {len(missing_ids)} missing images listed in {output_dir / f'missing-{split}.txt'}")

    print(f"Dataset folder: {output_dir}")
    print(f"Dataset YAML: {TRAINING_DIR / 'datasets' / 'motionguard-openimages.yaml'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
