# Engineering Work Log & Decision Journal

## Day 1 — Environment Setup, Dataset Exploration & Baseline Segmentation Pipeline

### 1. Objective
- Set up local working environment and Git version control.
- Ingest and analyze Dataset A (`events.jsonl` vs `gt.jsonl` and `gt_manifest.json`).
- Characterize ground truth task boundaries, execution durations, and transition behavior.
- Build an initial boundary detection algorithm and establish rigorous evaluation metrics (IoU, boundary precision/recall, label alignment).

### 2. Engineering Decisions & Architecture Rationale
- **Storage Architecture:** Established working repository at `C:\Users\itsay\AI_Engineer` to avoid permission issues on the read-only G: drive mount while streaming datasets directly from source.
- **Dataset A Insights:** Median task execution duration is 31.7s. 86.8% of transitions are interleaved switches between different processes. Processes are cross-application (Chrome + Excel / Word).
- **Dataset B Insights:** Production data shifts to Microsoft Edge and uses distinct URL hash routes (`#/payroll-items`, `#/leave-applications`, `#/onboarding`, `#/social-insurance`, `#/resident-tax`).

### 3. Hypotheses Tested & Iterations
- **Iteration 1:** Baseline rule-based detector (F1: 0.508, IoU: 0.438).
- **Iteration 2:** Multi-app awareness & continuous boundary alignment (V2) improved IoU to 0.485 (peak 0.604) and F1 to 0.528.
- **Iteration 3 (Failed Experiment & Lesson Learned):** Midpoint pause splitting dropped F1 to 0.401. Ground truth proves that task boundaries align with the *initiation* of new actions rather than idle midpoints.

---

## Day 2 — Dataset B Segmentation Execution & Business Process ROI Prioritization (Step 2)

### 1. Objective
- Execute batch segmentation across all 15 sessions in Dataset B to produce `segments.jsonl` (Deliverable 1).
- Validate formatting and schema against submission specifications.
- Conduct deep-dive operational analysis (volume, duration, operator spread, manual operation intensity).
- Formulate an objective ROI Prioritization Framework and select the #1 automation target for Step 3.

---

### 2. Batch Segmentation Results (`segments.jsonl`)
- **Total Segments Recovered:** 346 coherent business process executions across 15 sessions.
- **Output File:** `C:\Users\itsay\AI_Engineer\segments.jsonl`
- **Validation:** Every line verified as valid JSON matching `{"session_id": "...", "start": "...", "end": "...", "label": "..."}` with UTC ISO 8601 timestamps ending in `Z`.

---

### 3. Step 2: Operational Analysis & Empirical Findings

#### Process Volume & Time Consumption Summary

| Process Label | Executions | Total Time (Min) | % of Total Time | Median Duration (s) | Active Operators | Sessions |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`payroll_items`** | **93** | **63.5** | **36.3%** | **33.0s** | **4 / 4** | **11 / 15** |
| **`leave_applications`** | **92** | **37.8** | **21.6%** | **22.5s** | **4 / 4** | **11 / 15** |
| **`onboarding`** | **69** | **26.8** | **15.3%** | **20.0s** | **4 / 4** | **9 / 15** |
| **`social_insurance`** | **38** | **20.7** | **11.8%** | **25.5s** | **4 / 4** | **8 / 15** |
| **`resident_tax`** | **24** | **12.4** | **7.1%** | **28.5s** | **4 / 4** | **8 / 15** |
| *Desktop Docs (Word/Excel/Notepad)* | 30 | 13.8 | 7.9% | 15.0 - 53.5s | 1 - 2 | 1 - 2 |
| **Total** | **346** | **175.0** | **100.0%** | — | — | **15** |

#### Key Operational Insights:
1. **Extreme Pareto Distribution:**
   - Top 2 processes (`payroll_items` + `leave_applications`) consume **57.9%** of all employee working time.
   - Adding `onboarding` accounts for **73.2%** of company operations.
2. **Work Breakdown in `payroll_items`:**
   - Discovered through event tracing that operators perform repetitive copy-paste loops from desktop memos into internal portal table cells (`<td>`), opening detail `<textarea>` elements, pasting notes (`Ctrl+V`), and clicking save `<button>`s.
   - High manual burden: 12 clicks, 12 keystrokes, and 3 clipboard transfers per execution.

---

### 4. Step 2: Automation Prioritization Framework (ROI Ranking)

We defined an objective **Automation ROI Score**:
$$\text{ROI Score} = \frac{\text{Volume} \times \text{Total Time (min)} \times (1 + \text{Manual Intensity} / 100)}{\text{Complexity Score}}$$

Where:
- **Complexity Score = 1.0**: Structured Web Portal Form (standard DOM, clean HTTP/form interactions, low branching).
- **Complexity Score = 2.0**: Cross-App Desktop + Web workflow (requires inter-process clipboard handling and OS automation).

#### Final Prioritization Table:

| Rank | Candidate Process | Executions | Total Time (Min) | Time Share | Feasibility | ROI Score | Decision |
| :---: | :--- | :---: | :---: | :---: | :--- | :---: | :--- |
| **1** | **`payroll_items`** | **93** | **63.5 min** | **36.3%** | **High** (Web Portal Form) | **4,281.5** | **SELECTED FOR STEP 3 PROTOTYPE** |
| 2 | `leave_applications` | 92 | 37.8 min | 21.6% | High (Web Portal Form) | 2,190.9 | Deferred to Phase 2 (Shared Architecture) |
| 3 | `onboarding` | 69 | 26.8 min | 15.3% | Medium-High | 1,220.5 | Deferred to Phase 2 |
| 4 | `social_insurance` | 38 | 20.7 min | 11.8% | Medium | 534.9 | Deferred to Phase 3 |
| 5 | `resident_tax` | 24 | 12.4 min | 7.1% | Medium | 205.3 | Deferred to Phase 3 |

---

### 5. Architectural Decision for Step 3 Prototype
- **Selected Target:** `payroll_items` (給与備考・控除整備 / Payroll Items & Deductions Maintenance).
- **Justification:**
  - Highest time savings (36.3% of company back-office time).
  - Highest transaction volume (93 executions across all 4 machines).
  - High feasibility: Standardized web inputs, deterministic mapping, zero ambiguous human judgment required for routine entries.
- **Form of Prototype Chosen:**
  - A robust, modular **Python Automation Engine** (CLI + automated pipeline with batch validation, audit logging, and human-in-the-loop exception review).
- **Planned for Day 3:**
  - Implement the end-to-end automation prototype for `payroll_items`.
  - Simulate incoming memo batches, validate schema/business rules, execute auto-filling/submission, and generate audit reports.
