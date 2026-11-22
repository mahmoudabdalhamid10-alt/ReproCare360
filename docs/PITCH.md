# Pitch outline - Future Health Digital Innovation Challenge

## Problem

Male reproductive health is under-discussed. Men often search in private,
find forum anecdotes instead of guidelines, and delay seeing a doctor -
including for red-flag symptoms where hours matter (torsion) and for
infertility workups where both partners should be tested early.

## Solution

ReproCare 360: a privacy-first awareness platform that runs entirely on the
user's device.

- **Semen Lab** - WHO 2021 reference comparison; paste a lab report and it
  is parsed.
- **Safety Center** - conservative triage that can only raise urgency.
- **Care Pathway** - ordered, source-linked next steps.
- **Evidence AI** - retrieval over a curated knowledge base: source
  passages, never generated text; weak matches rejected.
- **My Journal + Report** - anonymous local tracking and a printable
  self-contained HTML report.

## What makes it different

1. **Privacy by architecture**: one local SQLite file, no accounts, no
   network.
2. **Honesty by default**: every learned component is evaluated and the
   numbers are published - including the lifestyle model that does not beat
   chance, which the UI therefore de-emphasizes.
3. **Safety-first triage**: the rules can only escalate, never reassure.

## Honest results (measured, see README and reports/)

- Evidence AI: held-out R@1 0.65 / R@3 0.70 with query expansion (n=20,
  wide uncertainty); 5/5 unrelated queries rejected.
- Lifestyle model: AUC 0.57 +/- 0.19 - no better than chance, presented as
  experimental.

## Demo flow

1. Paste a sample lab report -> parsed and flagged against WHO limits.
2. Type "sudden severe pain in my left testicle" -> emergency guidance.
3. Ask "does weed reduce sperm count" -> curated passage with source label.
4. Ask "how to change a car tire" -> correctly rejected.
5. Download the HTML report.

## Roadmap (not built)

- Clinician review of knowledge-base entries with exact citations.
- Localization (Arabic first).
- Validated patient-language triage study.
