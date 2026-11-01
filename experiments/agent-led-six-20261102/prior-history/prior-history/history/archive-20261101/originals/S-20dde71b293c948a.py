"""Self-test for metrics.py using fixed synthetic values with hand-checkable answers.

Runs with the standard library only: python3 test_metrics.py
Exits non-zero on any mismatch so it can gate a container run.
"""

import math
import sys

import metrics


FAILS = []


def approx(a, b, tol=1e-9):
    if a is None or b is None:
        return a is b
    return abs(a - b) <= tol


def check(name, got, want, tol=1e-9):
    ok = approx(got, want, tol)
    status = "ok" if ok else "FAIL"
    print(f"[{status}] {name}: got={got!r} want={want!r}")
    if not ok:
        FAILS.append(name)


def main():
    # ---- AUROC ----
    # Perfect separation.
    check("auroc perfect", metrics.auroc([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]), 1.0)
    # Perfectly reversed.
    check("auroc reversed", metrics.auroc([0, 0, 1, 1], [0.9, 0.8, 0.2, 0.1]), 0.0)
    # All tied scores -> 0.5.
    check("auroc all tied", metrics.auroc([0, 1, 0, 1], [0.5, 0.5, 0.5, 0.5]), 0.5)
    # One positive higher than 2 of 3 negatives: AUC = 2/3.
    # scores: neg=0.1, neg=0.4, pos=0.3, neg=0.5 -> pos beats negs 0.1,? 0.3>0.1 yes,
    # 0.3>0.4 no, 0.3>0.5 no -> 1/3.
    check("auroc one of three", metrics.auroc([0, 0, 1, 0], [0.1, 0.4, 0.3, 0.5]), 1 / 3)
    # Tie between positive and negative splits half credit.
    # negs: 0.2,0.6 ; pos: 0.6 -> beats 0.2 (=1), ties 0.6 (=0.5) -> 1.5/2 = 0.75
    check("auroc tie half credit", metrics.auroc([0, 0, 1], [0.2, 0.6, 0.6]), 0.75)
    # Single class -> undefined.
    check("auroc single class None", metrics.auroc([1, 1, 1], [0.1, 0.5, 0.9]), None)

    # ---- Average Precision (scikit-learn definition) ----
    # Perfect ranking, 2 pos, 2 neg, positives ranked first.
    # ranks: pos@1 prec 1/1=1, pos@2 prec 2/2=1 -> AP = (1+1)/2 = 1.0
    check("ap perfect", metrics.average_precision([1, 1, 0, 0], [0.9, 0.8, 0.2, 0.1]), 1.0)
    # Reversed ranking: negatives score higher; positives land at ranks 3,4.
    # desc order: neg,n eg,pos,pos -> prec@pos1(tp1,fp2)=1/3, prec@pos2(tp2,fp2)=2/4=1/2
    check(
        "ap reversed",
        metrics.average_precision([1, 1, 0, 0], [0.1, 0.2, 0.8, 0.9]),
        (1 / 3 + 1 / 2) / 2,
    )
    # No positives -> undefined.
    check("ap no positive None", metrics.average_precision([0, 0, 0], [0.1, 0.2, 0.3]), None)
    # Mixed order single positive ranked 2nd of 4: ranks pos@2 -> precision 1/2.
    check("ap single pos rank2", metrics.average_precision([0, 1, 0, 0], [0.9, 0.8, 0.1, 0.0]), 0.5)
    # Tie group: scores [0.5(pos),0.5(neg)], single positive. Ties counted after group.
    # group has tp=1,fp=1 -> precision=1/2, recall=1 -> AP=0.5.
    check("ap tie group", metrics.average_precision([1, 0], [0.5, 0.5]), 0.5)

    # ---- MAE ----
    check("mae simple", metrics.mae([1.0, 2.0, 3.0], [1.0, 2.0, 5.0]), (0 + 0 + 2) / 3)
    check("mae signed", metrics.mae([-1.0, 0.0], [1.0, 0.0]), (2 + 0) / 2)

    # ---- Spearman ----
    # Perfect monotonic (not linear) -> 1.
    check("spearman monotonic", metrics.spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)
    check("spearman reversed", metrics.spearman([1, 2, 3, 4], [40, 30, 20, 10]), -1.0)
    # Known example with ties. x ranks (tie avg): x=[1,2,2,3] -> ranks [1, 2.5, 2.5, 4]
    # y=[1,1,2,2] -> ranks [1.5,1.5,3.5,3.5]. Compute Pearson of ranks by hand.
    xr = [1.0, 2.5, 2.5, 4.0]
    yr = [1.5, 1.5, 3.5, 3.5]
    mx = sum(xr) / 4
    my = sum(yr) / 4
    cov = sum((a - mx) * (b - my) for a, b in zip(xr, yr))
    vx = sum((a - mx) ** 2 for a in xr)
    vy = sum((b - my) ** 2 for b in yr)
    want_sp = cov / math.sqrt(vx * vy)
    check("spearman ties", metrics.spearman([1, 2, 2, 3], [1, 1, 2, 2]), want_sp)
    # Constant vector -> undefined.
    check("spearman constant None", metrics.spearman([1, 1, 1], [1, 2, 3]), None)

    # ---- Non-finite guard ----
    try:
        metrics.auroc([0, 1], [0.1, float("nan")])
        check("non-finite guard", False, True)
    except ValueError:
        check("non-finite guard", True, True)

    if FAILS:
        print(f"\n{len(FAILS)} FAILED: {FAILS}")
        return 1
    print("\nAll metric self-tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())