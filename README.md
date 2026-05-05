# MS1-Based Workflow for the Identification of Plastic Oligomers and NIAS

This repository contains a Python-based workflow for MS1-level annotation of compounds using retention time (RT) and elution order constraints.

The workflow supports two modes:
- **Without standards**: annotation based on elution order only
- **With standards**: annotation using RT windows defined by internal standards

It was developed for the analysis of PET-related compounds and non-intentionally added substances (NIAS), but is adaptable to other compound classes analyzed by reversed-phase chromatography.

## Workflow Overview

The workflow consists of the following steps:

1. **Mass filtering**
   - Retains features within a user-defined ppm tolerance

2. **Standards detection (optional)**
   - Matches standards using RT alignment tolerance

3. **RT window segmentation (standards mode)**
   - Divides chromatographic space using detected standards

4. **Elution order generation**
   - Generates all plausible elution sequences based on RT order tolerance

5. **Combination generation**
   - Identifies valid metabolite combinations consistent with RT constraints
  
