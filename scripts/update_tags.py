import os
from pathlib import Path

import yaml


MONGO_APP_TAG = os.getenv("MONGO_APP_TAG", "latest")

MONGO_APP_VALUES_PATH = os.getenv("MONGO_APP_VALUES_PATH", "~/Desktop/mongo-app-helm/mongo-app/values.yaml")


def main():
    values_path = Path(MONGO_APP_VALUES_PATH).expanduser()
    values = None
    with values_path.open("r", encoding="utf-8") as f:
        values = yaml.safe_load(f)

    values["mongo-app"]["image"]["tag"] = MONGO_APP_TAG
    values["mongo-app-ui"]["image"]["tag"] = MONGO_APP_TAG

    with values_path.open("w") as f:
        yaml.safe_dump(values, f, sort_keys=False)


if __name__ == "__main__":
    main()
