"""
Evaluation Engine for Step 1 Segmentation
Calculates:
1. Boundary Precision, Recall, F1 at tolerance windows (e.g. 5s, 10s)
2. Mean and Median Temporal IoU (Overlap of work units)
3. Label Purity / Homogeneity
"""
import sys
import json
from datetime import datetime
import numpy as np

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def parse_iso(ts_str):
    if not ts_str:
        return None
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    return datetime.fromisoformat(ts_str).timestamp()

def compute_iou(seg1, seg2):
    s1, e1 = seg1[0], seg1[1]
    s2, e2 = seg2[0], seg2[1]
    inter_s = max(s1, s2)
    inter_e = min(e1, e2)
    inter = max(0.0, inter_e - inter_s)
    union_s = min(s1, s2)
    union_e = max(e1, e2)
    union = max(1e-6, union_e - union_s)
    return inter / union

def evaluate_session_boundaries(pred_segments, gt_segments, tolerance_sec=5.0):
    """
    pred_segments: list of (start_epoch, end_epoch, label)
    gt_segments: list of (start_epoch, end_epoch, true_code)
    """
    gt_starts = [g[0] for g in gt_segments]
    gt_ends = [g[1] for g in gt_segments]
    
    pred_starts = [p[0] for p in pred_segments]
    pred_ends = [p[1] for p in pred_segments]
    
    # Match starts
    matched_gt_s = set()
    matched_pred_s = set()
    for pi, ps in enumerate(pred_starts):
        best_diff = tolerance_sec + 1.0
        best_gi = None
        for gi, gs in enumerate(gt_starts):
            if gi in matched_gt_s:
                continue
            diff = abs(ps - gs)
            if diff <= tolerance_sec and diff < best_diff:
                best_diff = diff
                best_gi = gi
        if best_gi is not None:
            matched_gt_s.add(best_gi)
            matched_pred_s.add(pi)
            
    tp_s = len(matched_pred_s)
    fp_s = len(pred_starts) - tp_s
    fn_s = len(gt_starts) - tp_s
    
    prec_s = tp_s / (tp_s + fp_s) if (tp_s + fp_s) > 0 else 0.0
    rec_s = tp_s / (tp_s + fn_s) if (tp_s + fn_s) > 0 else 0.0
    f1_s = 2 * prec_s * rec_s / (prec_s + rec_s) if (prec_s + rec_s) > 0 else 0.0
    
    # Calculate Temporal IoU for each GT segment against best matching pred segment
    ious = []
    for gt in gt_segments:
        best_iou = 0.0
        for pred in pred_segments:
            iou = compute_iou(gt, pred)
            if iou > best_iou:
                best_iou = iou
        ious.append(best_iou)
        
    mean_iou = float(np.mean(ious)) if ious else 0.0
    median_iou = float(np.median(ious)) if ious else 0.0
    
    return {
        "start_precision": prec_s,
        "start_recall": rec_s,
        "start_f1": f1_s,
        "mean_iou": mean_iou,
        "median_iou": median_iou,
        "total_gt": len(gt_segments),
        "total_pred": len(pred_segments)
    }

if __name__ == "__main__":
    print("Evaluator module loaded successfully.")
