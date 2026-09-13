# Public data and model provenance

[Documentation index](README.md) · [Notebook index](../notebooks/README.md) · [Checksum manifest](../data/manifest.json)

Sources were checked on **13 September 2026**. The `public-data-v1` release contains small derived subsets with attribution and per-file SHA-256 checksums. Source archives and model weights are not stored in Git. Each prepared pack includes `provenance.json` with the source identifiers and processing decisions needed to inspect it.

## EuroSAT multispectral

Source: [EuroSAT by Patrick Helber and collaborators](https://github.com/phelber/EuroSAT), mirrored by [TorchGeo at a fixed dataset revision](https://huggingface.co/datasets/torchgeo/eurosat/tree/1ce6f1bfb56db63fd91b6ecc466ea67f2509774c). Archive: `EuroSATallBands.zip`; SHA-256 `751f070f9bffa2eed48b24ca2dd0b02959280c08837e8c9a5532a67ba611df59`. The original dataset has 27,000 georeferenced chips in ten classes. The repository's [MIT licence](../data/licenses/EuroSAT-MIT.txt) and [TorchGeo licence](../data/licenses/TorchGeo-MIT.txt) accompany the prepared pack. Contains Copernicus Sentinel data.

The subset contains **2,999 chips**: 2,000 training, 500 validation and 499 test. Selection uses seed 42 within each class of the upstream [EuroSATSpatial longitude-based lists](https://torchgeo.readthedocs.io/en/latest/_modules/torchgeo/datasets/eurosat.html), targeting 200/50/50 chips per class. One test chip was excluded because its footprint was within 2 km of an earlier partition. Distances use EPSG:3035; footprints, original CRS, affine transforms, filenames and source-chip checksums remain available. The 100 km grouping for bootstrap uncertainty is separate from the partition definition.

Band order: B01, B02, B03, B04, B05, B06, B07, B08, B09, B10, B11, B12, B8A. RGB uses B04/B03/B02. The 64 × 64 chips retain original unsigned integer DN; division by 10,000 is an experiment scaling convention. No Sentinel C1 L2A offset is applied to EuroSAT. Original scene IDs and exact per-chip acquisition dates are unavailable here, limiting claims about temporal independence. Labels come from EuroSAT; WorldCover is not substituted as reference truth.

## Sentinel-2 Collection 1 L2A

The [Earth Search collection](https://earth-search.aws.element84.com/v1/collections/sentinel-2-c1-l2a) provides public HTTP COGs. Two Sentinel-2A observations cover the same 512 × 512, 10 m UTM grid north of Lake Almanor, California (EPSG:32610):

| Role | Item | Acquisition UTC | Baseline |
| --- | --- | --- | --- |
| Before | `S2A_T10TFK_20200812T185701_L2A` | 2020-08-12 19:03:28.562 | 05.00 |
| After | `S2A_T10TFK_20210827T185458_L2A` | 2021-08-27 19:03:24.370 | 05.00 |

The pack retains B04, B03, B02 and B08 at 10 m; B12 from the first date remains at 20 m. SCL is resampled from 20 m to the reference grid using nearest neighbour. Every reflectance asset declares scale **0.0001**, offset **−0.1**, and raw nodata **0**. These are reprocessed products: acquisition year alone must not determine calibration. Native values and scale/offset metadata are retained, then applied exactly once in analysis.

SCL classes 4/5/6/7 are retained after inspection; other classes and invalid index inputs are masked. Two-date analysis uses the valid intersection. The same satellite, tile and processing baseline establish several comparability conditions, but season, smoke, illumination and imperfect masks remain limitations. The result is a spectral indicator without independent change labels.

Terms: [Copernicus Sentinel legal notice](https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice), linked by the collection. The STAC label `proprietary` points to these custom Sentinel terms; it is not a CC0 declaration. Attribution: **Contains modified Copernicus Sentinel data (2020, 2021)**. Source asset URLs, checksums where supplied, sun angles, exact bounds and processing metadata are included in the pack.

## ESA WorldCover

Source: [ESA WorldCover 2021 v200](https://esa-worldcover.org/en/data-access), tile `N39W123`, categorical map. The subset preserves the native EPSG:4326 grid before the contract notebook reprojects it using nearest neighbour. Licence: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Attribution: **© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium**. The notebook uses this map to demonstrate categorical resampling. It is not an independent accuracy reference. WorldCover 2020 and 2021 use different algorithm versions, so their direct difference would mix real change with processing changes.

## AHN4 and Dutch orthophoto

Source: [AHN dataroom](https://www.ahn.nl/dataroom), original TOP tile `39FN1`. The pack contains two crops from `C_39FN1.LAZ`, original 0.5 m DTM and DSM products, and an RGB orthophoto for the tree example. AHN data are released under CC0, as recorded in the [provider distribution feed](https://service.pdok.nl/rws/ahn/atom/dtm_05m.xml). Original source coordinates, classifications, return attributes and GPS times survive the LAZ cropping.

| Crop | EPSG:28992 bounds (left, bottom, right, top; metres) | LiDAR UTC interval |
| --- | --- | --- |
| Trees, Ede | 174650, 447600, 174906, 447856 | 2022-02-12 09:02:23.644–09:02:30.542 |
| Conductor corridor | 170880, 446000, 171020, 446600 | 2022-02-12 08:20:11.041–08:20:21.795 |

Horizontal reference is **Amersfoort / RD New, EPSG:28992**; height is **NAP, EPSG:5709**, in metres; compound CRS is **EPSG:7415**. The upstream LAS header lacks a CRS record. The crop adds the provider-documented CRS without a coordinate transform. UTC dates are derived from adjusted GPS standard time using the 18-second GPS–UTC offset applicable in 2022. The original AHN4 DTM/DSM use weighted IDW; newer regridded products are not mixed in.

The orthophoto is [Beeldmateriaal Nederland](https://www.beeldmateriaal.nl/dataroom), `2022_ortho25`, leaf-on RGB at 0.25 m. A bounded WMS request produces a 1024 × 1024 PNG, georeferenced from its explicit EPSG:28992 request grid. This is display RGB suitable for the detector, not analytical surface reflectance. The exact orthophoto flight date is unavailable, so the notebook states the winter/leaf-on temporal mismatch. Licence and attribution: **Beeldmateriaal Nederland / beeldmateriaal.nl, 2022, CC BY 4.0**.

Box-level DSM−DTM percentiles are surface statistics. They do not validate individual tree heights. Class 14 provides observed conductor points; class 1 remains unclassified. Fitted geometry has separate provenance and layers. No operational clearance or independent vertical accuracy claim is made.

## Public pretrained models

| Model | Pinned identity | Use |
| --- | --- | --- |
| [torchvision ResNet18](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.resnet18.html) | `ResNet18_Weights.IMAGENET1K_V1`, official `resnet18-f37072fd.pth` | ImageNet backbone; new ten-class head; short layer4/head fine-tune |
| [DeepForest tree model](https://huggingface.co/weecology/deepforest-tree) | Revision `cc21436bc5d572dde8ff5f93c1e71a32f563cace` | Public MIT model; pretrained tree-box inference |

The models retain their authorship and upstream terms. Weights are fetched from their original public hosts and cached locally. DeepForest loads its public safetensors model and its torchvision backbone dependency. No model weights from private repositories are used or redistributed in the data packs.

## Rebuild the subsets

Maintainer scripts are included for inspection and rebuilding. Normal notebook use downloads only the prepared packs. Full acquisition requires roughly 7.4 GB of source archives plus temporary raster extraction space. On Windows, the satellite preparer also caches full source COGs before cropping to avoid an observed GDAL/libcurl shutdown hang; allow several additional GB. This maintainer-only cache does not change the approximately 236 MB notebook download:

~~~text
uv run --frozen python scripts/acquire_archives.py
uv run --frozen python scripts/prepare_eurosat.py
uv run --frozen python scripts/prepare_satellite.py
uv run --frozen python scripts/prepare_ahn.py
uv run --frozen python scripts/package_data.py
~~~

Source bytes are pinned where a complete archive is downloaded. Provider endpoints, WMS rendering and geospatial writer versions can change; regenerated derived bytes must be reviewed and assigned a new release version rather than silently replacing published checksums. The small tracked CI fixtures are documented by their [own provenance file](../data/fixtures/provenance.json).
