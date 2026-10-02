"""Complete-row finite mean input extraction with source-declared units."""
import math


def extract_mean_input(acquisition, field, entity_field, unit):
    """Only a grounded field unit is accepted; caller unit text grants no authority."""
    if acquisition.origin != 'public' or not acquisition.public_only:
        raise ValueError('public owned source required')
    declared = acquisition.request.get('field_units', {}).get(field)
    if not declared or declared != unit:
        raise ValueError('resolved declared field unit required')
    def value(row, key):
        for segment in key.split('.'):
            if not isinstance(row, dict): return None
            row = row.get(segment)
        return row
    entities, values = [], []
    for row in acquisition.records:
        identity, number = value(row, entity_field), value(row, field)
        if not isinstance(identity, str) or not identity or identity in entities:
            raise ValueError('unique source entity keys required')
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number):
            raise ValueError('qualified mean rejects missing/nonfinite/nonnumeric rows')
        entities.append(identity); values.append(number)
    if not values: raise ValueError('nonempty source vector required')
    return {'values': values}, {'field': field, 'entity_field': entity_field, 'unit': unit,
        'entities': entities, 'included_rows': len(values), 'excluded_rows': 0,
        'source_content_sha256': acquisition.content_sha256, 'coverage': acquisition.coverage.model_dump(mode='json') if acquisition.coverage else None}
