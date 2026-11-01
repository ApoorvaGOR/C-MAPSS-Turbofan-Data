# Data provenance and license scope

This repository redistributes the FD001 subset of NASA's C-MAPSS Turbofan Engine Degradation Simulation Data Set as CSV files and a reformatted Excel workbook, together with visualization videos and images generated from those measurements. FD001 contains 100 training engines and 100 test engines. The original measurements are simulated engine data provided by the NASA Ames Prognostics Center of Excellence, not new measurements collected by this repository's uploader. The videos visualize simulated measurements; they are not recordings of physical engines.

The original dataset sources are the [NASA Open Data Portal](https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data) and the [NASA Prognostics Center of Excellence Data Set Repository](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/). The processing script downloads the original [CMAPSSData.zip archive](https://data.nasa.gov/docs/legacy/CMAPSSData.zip).

As checked on November 1, 2026, NASA's dataset catalog states **"License not specified."** The downloaded archive contains dataset documentation and the original reference paper, but no separate dataset license file was identified. No NASA-issued CDLA-Permissive-2.0, MIT, CC BY, or CC0 license for this dataset was identified in these sources. This notice does not assign one of those licenses or determine the copyright status of every item in NASA's distribution.

[`LICENSE-DATA.txt`](LICENSE-DATA.txt) accompanies the CSV data, Excel export, and generated visualizations as a record of provenance and the published licensing status. It is not a new license grant or an official NASA license text. This repository does not relicense the underlying NASA data under MIT. No separate software license for the processing scripts has been selected by the repository owner in this package. Third-party Python packages retain their own licenses and are installed separately through `requirements.txt`.

NASA's repository requests acknowledgment of the repository and dataset contributors in publications using the data. Please cite:

> A. Saxena and K. Goebel (2008). *Turbofan Engine Degradation Simulation Data Set*. NASA Prognostics Data Repository, NASA Ames Research Center, Moffett Field, CA.

The original technical reference for the data generation and sensor definitions is:

> A. Saxena, K. Goebel, D. Simon, and N. Eklund (2008). *Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation*. Proceedings of the International Conference on Prognostics and Health Management (PHM08), Denver, CO.

The CSV exports retain the original numerical measurements and add calculated remaining-useful-life (RUL) labels. The Excel workbook transposes these observations into sensor-by-cycle tables and adds measurement descriptions and units. The videos display selected measurements with a trailing mean. Generation details are documented in [`data/README.md`](data/README.md) and [`video/README.md`](video/README.md). RUL values are evaluation labels, not sensor readings or predictions.

The related *Multi-sensor slope change detection* paper does not identify its C-MAPSS subset conclusively. This repository uses FD001 and does not claim to reproduce that paper's exact dataset selection or detection procedure.

NASA's repository states that use of the data is at the user's risk and disclaims liability for the data and systems developed from it. Checks of CSV regeneration and spreadsheet exports establish numerical consistency only; they do not certify physical accuracy, aircraft applicability, or predictive performance. The dataset does not supply exact ground-truth degradation-onset times. This repository is not endorsed by NASA or the original authors.
