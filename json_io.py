import json


def read(db: str):
    with open(db, encoding='utf-8') as f:
        data = json.load(f)
    return data


def write(db: str, record: dict):
    with open(db, encoding='utf-8') as f:
        data = json.load(f)
        data.append(record)
    with open(db, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)