# Engineering Work Log & Decision Journal

## Day 1 — Environment Setup, Dataset Exploration & Baseline Segmentation Pipeline

### 1. Objective
- Set up local working environment and Git version control.
- Ingest and analyze Dataset A (`events.jsonl` vs `gt.jsonl` and `gt_manifest.json`).
- Characterize ground truth task boundaries, execution durations, and transition behavior.
- Build an initial boundary detection algorithm and establish rigorous evaluation metrics (IoU, boundary precision/recall, label alignment).

---

### 2. Engineering Decisions & Architecture Rationale

#### A. Workspace & Storage Architecture
- **Discovery:** The provided workspace directory resides on a Google Drive virtual filesystem mount (`G:\.shortcut-targets-by-id\...`) configured with generic read permissions (`AYUSH\itsay:(GR)`). Direct writes were blocked with Windows `Access is denied`.
- **Decision:** Established the active Git working repository at `C:\Users\itsay\AI_Engineer`. Configured all scripts to stream raw event logs directly from `G:\` without duplicating the 12+ GB dataset (primarily screenshots) to local SSD.
- **Git Strategy:** Initialized local Git repository with strict `.gitignore` to track all code (`src/`), analysis scripts, work logs, and deliverables without bloating Git history with raw binary data.

#### B. Exploratory Data Analysis (EDA) on Dataset A
- Evaluated all 63 sessions (~2,009 ground truth executions) across HR, Finance, and Operations domains.
- **Empirical Findings:**
  - Median task execution duration is **31.7 seconds** (10th percentile: 23.2s, 75th percentile: 44.8s). Routine back-office tasks consistently take between 20 to 60 seconds per case.
  - Multi-app composition: Individual business processes are not single-app tasks. For example, process `H` (銀行勘定照合) spans `Google Chrome` and `Microsoft Excel`, while process `C` (育児・産休申請確認) spans `Google Chrome`, `Microsoft Word`, and `Notepad`.
  - Transitions: 86.8% of transitions are interleaved switches between different business processes, while 13.2% are back-to-back executions of the same process.

#### C. Exploratory Analysis on Dataset B (Target Production Data)
- Ingested all 15 sessions (~20,477 events) of Dataset B.
- **Key Discoveries:**
  - Browser change: Dataset B primarily uses **Microsoft Edge** (13,300 events) rather than Google Chrome (0 events in B).
  - Web portal routes: Discovered that internal business systems route operations through distinct URL hash fragments (`#/payroll-items`, `#/leave-applications`, `#/onboarding`, `#/social-insurance`, `#/resident-tax`).
  - Office documents: Word documents reflect specific administrative procedures (`keiyaku_kaijo_tetsuzuki`, `nyusha_checklist_shinsotsu_batch`, `settai_keihi_kitei`), and Excel files capture calculations (`expense_calc`, `budget_analysis`).

---

### 3. Hypotheses Tested & Iterations

#### Iteration 1: Baseline Rule-Based Boundary Detector
- **Hypothesis:** Splitting purely on app switches, window title changes, and raw idle pauses (> 4.5s) will recover task units.
- **Result:**
  - Average F1 (@10s): 0.508
  - Average Mean IoU: 0.438
  - Issue: Caused oversegmentation because switching from the web portal to Excel/Word within an ongoing case was prematurely treated as a task boundary.

#### Iteration 2: Multi-App Awareness & Continuous Boundary Alignment (V2)
- **Hypothesis:** Suppress sub-window flutter (e.g., transient "Opening" titles in Word) and extend segment boundaries continuously until the next process starts (unless genuine downtime > 30s occurs).
- **Result:**
  - Average Mean IoU increased significantly from 0.438 to **0.485** (peak sessions reaching IoU **0.561 - 0.604**).
  - Average F1 (@10s): **0.528**.
  - Mean predicted count: 28.0 vs Ground Truth mean count: 26.5 (exceptionally close).

#### Iteration 3: Idle Pause Midpoint Split vs Initiation Split (V3)
- **Hypothesis:** Setting the boundary split at the midpoint of an idle pause `(T_prev + T_curr) / 2` might capture the exact hand-off moment.
- **Experiment:** Modified split timestamps to pause midpoints and re-benchmarked across sessions.
- **Result:** F1 dropped from 0.528 to 0.401.
- **Insight / What Did Not Work:** In ground truth, task boundaries strictly align with the *initiation* of the new case (the user's first click or keystroke after the pause) rather than the midpoint of operator idle time. Reverted to initiation-based timestamping (`curr["timestamp_sec"]`).

---

### 4. Day 1 Outcome & Next Steps for Day 2
- Developed a robust, generalized segmentation engine (`src/segmentation_engine.py`) validated against Dataset A ground truth.
- Successfully verified execution on Dataset B sample session (`ses_20260701-183232-LAPTOP-76QMG9DE`), producing clean, valid `segments.jsonl` format.
- **Ready for Day 2:**
  1. Execute batch segmentation across all 15 sessions in Dataset B to generate final `segments.jsonl` (Deliverable 1).
  2. Perform Step 2 Business Process Analysis: aggregate frequencies, durations, and process variants.
  3. Formulate the ROI Prioritization Matrix to select the top automation candidate.
