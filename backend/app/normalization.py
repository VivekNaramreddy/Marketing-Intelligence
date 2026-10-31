"""Input adapters and strict normalization. Rates use percentage points (2.4 = 2.4%)."""
import io
import math
import re
from datetime import date, datetime

import pandas as pd

NUMERIC = ['followers', 'engagement_rate', 'views', 'likes', 'comments', 'shares', 'posts']
ALIASES = {'period': 'date', 'period_date': 'date', 'engagement_rate_%': 'engagement_rate', 'follower_count': 'followers', 'brand_name': 'brand'}


def read_file(filename: str, content: bytes) -> list[dict]:
    try:
        if filename.lower().endswith('.csv'):
            frame = pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False)
        elif filename.lower().endswith('.xlsx'):
            frame = pd.read_excel(io.BytesIO(content), dtype=object, keep_default_na=False, engine='openpyxl')
            frame = frame.map(lambda v: v.date().isoformat() if isinstance(v, datetime) else v.isoformat() if isinstance(v, date) else v)
        else:
            raise ValueError('Upload a CSV or .xlsx Excel file.')
        return frame.to_dict(orient='records')
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError('Unable to read this file. Check its format and contents.') from exc


def normalize(rows: list[dict]) -> list[dict]:
    if not rows:
        raise ValueError('The dataset is empty.')
    result = []
    for index, raw in enumerate(rows, 2):
        row = {}
        for key, value in raw.items():
            canonical = re.sub(r'[\s/]+', '_', str(key).strip().lower())
            canonical = ALIASES.get(canonical, canonical)
            if canonical in row:
                raise ValueError(f'Row {index}: duplicate column mapping for {canonical}.')
            row[canonical] = value
        record = {}
        for field in ['brand', 'platform']:
            value = row.get(field)
            if value is None or not str(value).strip():
                raise ValueError(f'Row {index}: {field} is required.')
            record[field] = str(value).strip()
        platform = record['platform'].lower()
        record['platform'] = {'twitter': 'X/Twitter', 'x': 'X/Twitter', 'x/twitter': 'X/Twitter', 'facebook': 'Facebook', 'instagram': 'Instagram', 'youtube': 'YouTube', 'tiktok': 'TikTok'}.get(platform, record['platform'])
        date = row.get('date')
        record['date'] = None
        if date is not None and str(date).strip():
            try:
                text = str(date).strip()
                if not re.fullmatch(r'\d{4}-\d{2}(-\d{2})?', text):
                    raise ValueError()
                record['date'] = pd.Timestamp(text).date().isoformat()
            except Exception as exc:
                raise ValueError(f'Row {index}: date must be YYYY-MM or YYYY-MM-DD.') from exc
        for field in NUMERIC:
            value = row.get(field)
            record[field] = None
            if value is None or str(value).strip() == '':
                continue
            try:
                text = str(value).strip().replace(',', '')
                if field == 'engagement_rate':
                    text = text.removesuffix('%')
                number = float(text)
                if not math.isfinite(number) or number < 0 or (field == 'engagement_rate' and number > 100):
                    raise ValueError()
                if field != 'engagement_rate' and not number.is_integer():
                    raise ValueError()
                record[field] = number
            except (ValueError, TypeError) as exc:
                raise ValueError(f'Row {index}: invalid {field} value {value!r}. Counts must be whole, nonnegative numbers; rates must be 0–100.') from exc
        if all(record[field] is None for field in NUMERIC):
            raise ValueError(f'Row {index}: provide at least one metric.')
        result.append(record)
    keys = [(r['brand'], r['platform'], r['date']) for r in result]
    if len(set(keys)) != len(keys):
        raise ValueError('Duplicate brand/platform/date observations in this import. Keep one observation per combination.')
    return result
