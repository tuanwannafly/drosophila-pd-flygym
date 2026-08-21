# Dataset Validation

`DatasetValidator` checks:

- manifest fields and dataset type
- numeric schema version
- metadata availability and parse errors
- missing or unsafe declared paths
- duplicate paths and duplicate content hashes
- declared SHA-256 and byte-size values
- trajectory-file presence
- readable, positive frame counts

Validation is an integrity gate. A passing report means the files satisfy the
intake contract; it does not establish biological validity or a disease model.
