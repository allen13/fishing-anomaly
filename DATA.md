# Anonymized AIS Training Data

## Last Update
April 11, 2025

## Description
This is a dataset for training machine learning solutions for detecting fishing events as well as gear type by analyzing AIS vessel tracks. We use a similar dataset to train our fishing detection and vessel classification neural networks.

Data can be downloaded from: [Global Fishing Watch - Public Training Data v1](https://globalfishingwatch.org/data-download/datasets/public-training-data-v1)

The data are stored as individual CSV files, one for each of the following fishing gear types:
- Drifting longlines
- Fixed gear
- Pole and line
- Purse seines
- Trawlers
- Trollers
- Unknown

## Files and Version

The current version is 1.0. You can find these CSV files:

- **drifting_longlines.csv**: Drifting longline vessels
- **fixed_gear.csv**: Fixed gear vessels
- **pole_and_line.csv**: Pole and line vessels
- **purse_seines.csv**: Purse seine vessels
- **trawlers.csv**: Trawl vessels
- **trollers.csv**: Trolling vessels
- **unknown.csv**: Vessels with unknown gear type

## Schema for All Files

| Column | Description |
|--------|-------------|
| **mmsi** | Anonymized vessel identifier |
| **timestamp** | Unix timestamp |
| **distance_from_shore** | Distance from shore (meters) |
| **distance_from_port** | Distance from port (meters) |
| **speed** | Vessel speed (knots) |
| **course** | Vessel course |
| **lat** | Latitude in decimal degrees |
| **lon** | Longitude in decimal degrees |
| **is_fishing** | Label indicating fishing activity:<br>• 0 = Not fishing<br>• >0 = Fishing. Values between 0 and 1 indicate the average score for the position if scored by multiple people.<br>• -1 = No data |
| **source** | The training data batch |

## Source
The training data was prepared by Global Fishing Watch (GFW), Dalhousie University, and a crowd sourcing campaign. False positives are marked as "false_positives".


## License
Copyright Global Fishing Watch. Non-Commercial Use Only. 

The Site and the Services are provided for Non-Commercial use only in accordance with the [CC BY-NC 4.0 license](https://creativecommons.org/licenses/by-nc/4.0/). 

If you would like to use the Site and/or the Services for commercial purposes, please contact us at support@globalfishingwatch.org. See also our Terms of Use.

## Suggested Citation
Global Fishing Watch. 2020. Anonymized AIS training data, Version 1.0.