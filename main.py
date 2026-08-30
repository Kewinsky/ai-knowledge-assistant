from pathlib import Path


def load_markdown_files(directory: str | Path) -> list[tuple[Path, str]]:
    directory_path = Path(directory)

    if not directory_path.is_dir():
        raise NotADirectoryError(f"Expected an existing directory: {directory_path}")

    documents: list[tuple[Path, str]] = []

    for file_path in sorted(directory_path.rglob("*.md")):
        if file_path.is_file():
            content = file_path.read_text(encoding="utf-8")
            documents.append((file_path, content))

    return documents