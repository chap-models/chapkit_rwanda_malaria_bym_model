"""ML service for chapkit_rwanda_malaria_bym_model.

Wraps the Rwanda Malaria BYM R-INLA model
(https://github.com/knutdrand/Kigali-Malaria-modelling-23-27-Feb) as a chapkit
shell-r service. The R-INLA model is unchanged; main.py only configures the
HTTP service, the runner that drives scripts/train.R + scripts/predict.R, and
the metadata chap-core surfaces in its model catalogue.
"""

import os
from pathlib import Path

from chapkit import BaseConfig
from chapkit.api import AssessedStatus, MLServiceBuilder, MLServiceInfo, ModelMetadata, PeriodType
from chapkit.artifact import ArtifactHierarchy
from chapkit.ml import ShellModelRunner


class RwandaMalariaBymModelConfig(BaseConfig):
    """Configuration for chapkit_rwanda_malaria_bym_model.

    The chap_core config_format on the runner writes
    additional_continuous_covariates at the top level of config.yml, which is
    what scripts/predict.R reads via parse_model_configuration().
    """

    prediction_periods: int = 3


# Positional args match the original Kigali MLproject command shape:
#   train.R     {train_data} {model} {model_config} {polygons}
#   predict.R   {model} {historic_data} {future_data} {out_file} {model_config} {polygons}
# `model.rds` and `config.yml` are passed as literal in-workspace paths;
# config.yml is always written by chapkit, model.rds is not consumed by this
# model but the train.R signature accepts the positional slot.
train_command = "Rscript scripts/train.R {data_file} model.rds config.yml {geo_file}"
predict_command = (
    "Rscript scripts/predict.R model.rds {historic_file} {future_file} {output_file} config.yml {geo_file}"
)

runner: ShellModelRunner[RwandaMalariaBymModelConfig] = ShellModelRunner(
    train_command=train_command,
    predict_command=predict_command,
    config_format="chap_core",
)

info = MLServiceInfo(
    id="chapkit-rwanda-malaria-bym-model",
    display_name="Rwanda Malaria BYM Model",
    version="0.1.0",
    description=(
        "Spatio-temporal Bayesian model for malaria incidence in Rwanda at the sector "
        "(ADM3) level: BYM spatial effects, RW1 temporal effects, and IID space-time "
        "interaction with lagged climate covariates. Implemented with R-INLA. "
        "Ported from knutdrand/Kigali-Malaria-modelling-23-27-Feb."
    ),
    model_metadata=ModelMetadata(
        author="Similien NDAGIJIMANA",
        organization="HISP Centre, University of Oslo",
        contact_email="knut.rand@dhis2.org",
        author_assessed_status=AssessedStatus.gray,
        citation_info=(
            'Climate Health Analytics Platform. 2025. "Kigali Malaria BYM Model". '
            "HISP Centre, University of Oslo. "
            "https://dhis2-chap.github.io/chap-core/external_models/overview_of_supported_models.html"
        ),
    ),
    period_type=PeriodType.monthly,
    min_prediction_periods=1,
    max_prediction_periods=24,
    required_covariates=["population", "rainfall", "mean_temperature", "relative_humidity"],
    allow_free_additional_continuous_covariates=True,
    requires_geo=True,
)

HIERARCHY = ArtifactHierarchy(
    name="rwanda_malaria_bym_model",
    level_labels={0: "ml_training_workspace", 1: "ml_prediction"},
)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/chapkit.db")
if DATABASE_URL.startswith("sqlite") and ":///" in DATABASE_URL:
    db_path = Path(DATABASE_URL.split("///")[1])
    db_path.parent.mkdir(parents=True, exist_ok=True)

app = (
    MLServiceBuilder(
        info=info,
        config_schema=RwandaMalariaBymModelConfig,
        hierarchy=HIERARCHY,
        runner=runner,
        database_url=DATABASE_URL,
    )
    .with_monitoring()
    .with_registration()
    .build()
)


if __name__ == "__main__":
    from chapkit.api import run_app

    run_app("main:app", reload=False, port=9091)
