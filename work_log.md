# Engineering Work Log & Decision Journal

## Day 1 — Environment Setup, Dataset Exploration & Baseline Segmentation Pipeline

### Objective
- Set up local working environment and Git version control.
- Ingest and analyze Dataset A (`events.jsonl` vs `gt.jsonl` and `gt_manifest.json`).
- Understand event structure, idle time dynamics, and ground truth task boundaries.
- Build an initial boundary detection algorithm and establish evaluation metrics (IoU, boundary precision/recall, label alignment).

### Key Decisions & Architecture Rationale
1. **Workspace Architecture:**
   - The provided data directory resides on a Google Drive virtual mount with read-only permissions (`AYUSH\itsay:(GR)`).
   - To maintain Git integrity and allow fast disk I/O without copying 12+ GB of screenshot data, established the working repository at `C:\Users\itsay\AI_Engineer` with paths configured to read raw datasets directly from the source directory.
2. **Segmentation Strategy:**
   - Explored Dataset A ground truth: sessions contain multiple chunks that must be chronologically merged.
   - Identified key transition indicators: idle gaps (> 15-30s), active window switches, and URL/case ID shifts.
   - Decided to avoid hardcoded process names to guarantee zero leakage when transferring to Dataset B.

### Experiments & Next Steps
- Implement `src/eda_dataset_a.py` to calculate exact empirical distributions of task durations and idle intervals.
- Build `src/evaluate_segmentation.py` for automated scoring against ground truth.
