"""Interactive key storage; never accepts a secret as a command argument."""

import os
from getpass import getpass
from pathlib import Path


def main():
    folder = Path(__file__).resolve().parents[1] / "secrets"
    folder.mkdir(mode=0o700, exist_ok=True)
    key = getpass("Paste OpenAI API project key (hidden): ").strip()
    if not key or any(character.isspace() for character in key):
        raise SystemExit("No key saved: expected a nonempty token without whitespace.")
    try:
        fd = os.open(folder / "openai-api-key", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise SystemExit("Existing key file preserved; use a reviewed rotation procedure to replace it.") from None
    with os.fdopen(fd, "w") as file:
        file.write(key)
    print("Key saved in secrets/openai-api-key with owner-only permissions; value not displayed.")


if __name__ == "__main__":
    main()
