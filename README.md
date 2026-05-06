# chapkit_rwanda_malaria_bym_model

Rwanda Malaria BYM model (R-INLA), packaged as a [chapkit](https://github.com/dhis2-chap/chapkit) shell-r service.

A spatio-temporal Bayesian model for malaria incidence at the sector (ADM3)
level, combining BYM spatial effects, RW1 temporal effects, and IID
space-time interaction with lagged climate covariates. Implemented in
R-INLA. The original MLproject lives at
[knutdrand/Kigali-Malaria-modelling-23-27-Feb](https://github.com/knutdrand/Kigali-Malaria-modelling-23-27-Feb);
this repo wraps the same R-INLA model body in chapkit's HTTP service so it
can be discovered, run, and managed by chap-core like any other registered
ML service.

## Layout

```
chapkit_rwanda_malaria_bym_model/
├── main.py              # ShellModelRunner wiring + MLServiceInfo metadata
├── scripts/
│   ├── train.R          # no-op (BYM fits during predict)
│   └── predict.R        # BYM + RW1 + IID, R-INLA, requires polygons
├── pyproject.toml
├── uv.lock
├── Dockerfile           # FROM ghcr.io/dhis2-chap/chapkit-r-inla:latest
├── compose.yml
└── Makefile
```

## Quick start

```bash
uv lock
docker compose up --build
# In another shell:
uv run chapkit test --url http://localhost:9091
```

`make test` builds the image, boots a one-shot container, runs `chapkit
test` against it (which synthesises panel data + polygons and drives a
full train -> predict cycle), and tears the container down.

## Model details

- **Family**: Poisson with `offset = log(population)`.
- **Spatial**: BYM (`f(ID, model = "bym", graph = ...)`), with a rook
  adjacency graph built at predict-time from the supplied polygons.
- **Temporal**: RW1 over month-year time index.
- **Space-time interaction**: IID over (sector x time).
- **Covariates**: lagged climate variables (configurable depth, default 2).
- **Required covariates**: population, rainfall, mean_temperature,
  relative_humidity. Free additional continuous covariates are accepted
  via the chap-core config.

## Configuration

`main.py` exposes a small Config class that translates to YAML in the
workspace at predict-time:

| Field                | Default | Notes                                                      |
| -------------------- | ------- | ---------------------------------------------------------- |
| `prediction_periods` | `3`     | chap-core expects this on every chapkit Config.            |

`additional_continuous_covariates` (one per climate covariate the model
should use as a lagged predictor) is honoured automatically: the chap_core
config_format writes it into `config.yml`, and `scripts/predict.R` reads
it via `parse_model_configuration()` and builds lag1/lag2 features for
each one. Posterior sample count is fixed at 1000 (matching the upstream
Kigali source); change it in `scripts/predict.R` if you need a different
draw count.

## Notes on the port

This repo is a chapkit packaging of the upstream model. The R-INLA model
body in `scripts/predict.R` is preserved verbatim from
`knutdrand/Kigali-Malaria-modelling-23-27-Feb/predict.R`. Only two
adaptations were necessary, both small and concentrated near the top of
`predict_chap()`:

1. **Column adapters**: a tolerant rename block (mirroring
   [chapkit_ewars_model](https://github.com/chap-models/chapkit_ewars_model)'s
   `apply_adapters`) translates chap-core's canonical names
   (`disease_cases`, `population`, `year`, `location`) to the Kigali
   internals (`Cases`, `E`, `ID_year`, `ID_spat`). The original MLproject
   adapter map ran server-side; chapkit doesn't, so the model script has
   to do it.
2. **`time_period` derivation**: when `year` / `month` aren't present
   (chapkit's test data generator only emits `time_period`), they're
   parsed out of the `YYYY-MM` string. Real chap-core CSVs ship year and
   month columns, in which case the derivation is skipped.

`scripts/train.R` is the upstream Kigali no-op verbatim - the BYM model
fits during predict via R-INLA's missing-data trick.

The CLI entrypoint and `predict_chap()` signature are unchanged; main.py
passes the chapkit `ShellModelRunner` placeholders in the same positional
order the original MLproject command used
(`{model} {historic} {future} {output} {config} {polygons}`), so
predict.R's `args[1..6]` block is the upstream's verbatim.

## Image platform

`chapkit-r-inla` is amd64-only (R-INLA ships x86_64 binaries only). On
Apple Silicon the image runs under Rosetta and is slower than a native
arm64 build would be. There is no arm64 path until the upstream INLA
project ships arm64 binaries.

## License

GPL-3.0 (matches the chapkit-images / chap-core ecosystem).

## See also

- [chapkit](https://github.com/dhis2-chap/chapkit) - the framework
- [chapkit-images](https://github.com/dhis2-chap/chapkit-images) - the
  base images
- [chap-core](https://github.com/dhis2-chap/chap-core) - the orchestrator
- [chapkit_minimalist_example_r](https://github.com/chap-models/chapkit_minimalist_example_r) -
  a smaller chapkit-R reference (linear regression rather than BYM)
- [knutdrand/Kigali-Malaria-modelling-23-27-Feb](https://github.com/knutdrand/Kigali-Malaria-modelling-23-27-Feb) -
  upstream MLproject this repo was ported from
