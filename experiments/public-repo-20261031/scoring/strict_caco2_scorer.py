"""Strict single-task scorer. Original row identities are primary keys, including empty/duplicate IDs.
The fixed host MAE function is imported as a reviewed exact source excerpt.
"""
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import statistics
from fixed_mae import _mae

TASK='caco2_wang'
FIELDS={'task','split','row_index','Drug_ID','Drug','y_pred'}


def csv_rows(data):
    reader=csv.DictReader(io.StringIO(data.decode('utf-8-sig'),newline=''))
    rows=list(reader)
    if not reader.fieldnames or len(set(reader.fieldnames))!=len(reader.fieldnames):raise ValueError('duplicate_or_empty_csv_header')
    if any(None in row or any(v is None for v in row.values()) for row in rows):raise ValueError('malformed_csv_row')
    return reader.fieldnames,rows


def finite(value):
    if isinstance(value,bool):raise ValueError('boolean_not_number')
    try:number=float(value)
    except (TypeError,ValueError,OverflowError):raise ValueError('not_number') from None
    if not math.isfinite(number):raise ValueError('not_finite')
    return number


def truth_identity(original,blind):
    if not original or len(original)!=len(blind):raise ValueError('truth_coverage')
    for a,b in zip(original,blind):
        if set(a)!={'Drug_ID','Drug','Y'} or set(b)!={'Drug_ID','Drug'}:raise ValueError('truth_schema')
        if any(a[k]!=b[k] for k in ('Drug_ID','Drug')):raise ValueError('truth_blind_identity')
        finite(a['Y'])


def validate_valid(predictions,blind):
    if not blind or len(predictions)!=len(blind):raise ValueError('valid_coverage')
    seen=set();values=[]
    for i,(p,b) in enumerate(zip(predictions,blind)):
        if set(p)!=FIELDS:raise ValueError('prediction_schema')
        if p['task']!=TASK or p['split']!='valid':raise ValueError('prediction_scope')
        key=(p['task'],p['split'],p['row_index'])
        if key in seen:raise ValueError('duplicate_row_identity')
        seen.add(key)
        if p['row_index']!=str(i) or p['Drug_ID']!=b['Drug_ID'] or p['Drug']!=b['Drug']:raise ValueError('prediction_identity_or_order')
        values.append(finite(p['y_pred']))
    return values


def select_valid_from_original_csv(data,blind_valid,blind_test):
    fields,rows=csv_rows(data)
    if set(fields)!=FIELDS or len(fields)!=6 or len(rows)!=len(blind_valid)+len(blind_test):raise ValueError('source_prediction_schema_or_coverage')
    offset=0;selected=[]
    for split,blind in (('valid',blind_valid),('test',blind_test)):
        for i,b in enumerate(blind):
            p=rows[offset];offset+=1
            if p['task']!=TASK or p['split']!=split or p['row_index']!=str(i):raise ValueError('source_prediction_scope_or_order')
            if any(p[k]!=b[k] for k in ('Drug_ID','Drug')):raise ValueError('source_prediction_identity')
            finite(p['y_pred'])
            if split=='valid':selected.append(p)
    validate_valid(selected,blind_valid)
    return selected


def score_once(original,blind,predictions):
    truth_identity(original,blind)
    values=validate_valid(predictions,blind)
    pairs=[(finite(t['Y']),p) for t,p in zip(original,values)]
    mae=_mae(pairs)
    if not math.isfinite(mae):raise ValueError('nonfinite_metric')
    errors=[p-y for y,p in pairs]
    absolute=[abs(x) for x in errors]
    # Only fixed aggregate diagnostics are exported. No row residuals or labels.
    ordered=sorted(absolute)
    q=lambda p:ordered[min(len(ordered)-1,math.ceil(p*len(ordered))-1)]
    return dict(task=TASK,split='official_valid',n=len(pairs),metric='MAE',direction='minimize',
        value=mae,status='ok',definition='mean(abs(supplied_numeric_Y - y_pred))',
        official_aggregate_score=None,
        diagnostic_aggregates=dict(rmse=math.sqrt(math.fsum(x*x for x in errors)/len(errors)),
            signed_mean_error=math.fsum(errors)/len(errors),median_absolute_error=statistics.median(absolute),
            p90_absolute_error=q(.90),p95_absolute_error=q(.95),
            absolute_error_bin_counts={'lt_0.25':sum(x<.25 for x in absolute),
                '0.25_to_lt_0.5':sum(.25<=x<.5 for x in absolute),'0.5_to_lt_1':sum(.5<=x<1 for x in absolute),
                'ge_1':sum(x>=1 for x in absolute)}))
