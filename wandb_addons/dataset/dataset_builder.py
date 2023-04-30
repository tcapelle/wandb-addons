import os
from typing import Any, Mapping, Optional, Union

import wandb
from etils import epath
import tensorflow_datasets as tfds


class WandbDatasetBuilder(tfds.core.GeneratorBasedBuilder):
    def __init__(
        self,
        *,
        name: str,
        dataset_path: str,
        features: tfds.features.FeatureConnector,
        version: Optional[Union[tfds.core.utils.Version, str]] = None,
        config: Union[None, str, tfds.core.BuilderConfig] = None,
        data_dir: Optional[epath.PathLike] = None,
        description: Optional[str] = None,
        release_notes: Optional[Mapping[str, str]] = None,
        homepage: Optional[str] = None,
        file_format: Optional[Union[str, tfds.core.FileFormat]] = None,
        disable_shuffling: Optional[bool] = False,
        **kwargs: Any,
    ):
        if wandb.run is None:
            raise wandb.Error(
                "You must call `wandb.init()` before instantiating a subclass of `WandbDatasetBuilder`"
            )

        self.name = name
        self.dataset_path = dataset_path
        self.VERSION = (
            tfds.core.utils.Version(version)
            if version is not None
            else self._get_version()
        )
        self.RELEASE_NOTES = release_notes
        if config:
            if isinstance(config, str):
                config = tfds.core.BuilderConfig(
                    name=config, version=version, release_notes=release_notes
                )
            self.BUILDER_CONFIGS = [config]
        self._feature_spec = features
        self._description = (
            description or "Dataset built without a DatasetBuilder class."
        )
        self._homepage = homepage
        self._disable_shuffling = disable_shuffling

        self._wandb__artifact = self._initialize_wandb_artifact()

        super().__init__(
            data_dir=data_dir,
            config=config,
            version=version,
            file_format=file_format,
            **kwargs,
        )

    def _initialize_wandb_artifact(self):
        return wandb.Artifact(
            name=self.name,
            type="dataset",
            description=self._description,
            metadata={
                "description": self._description,
                "release-notes": self.RELEASE_NOTES,
                "homepage": self._homepage,
            },
        )

    def _get_version(self) -> tfds.core.utils.Version:
        try:
            api = wandb.Api()
            versions = api.artifact_versions(
                type_name="dataset",
                name=f"{wandb.run.entity}/{wandb.run.project}/{self.name}",
            )
            return next(versions).source_version[1:] + ".0.0"
        except wandb.errors.CommError:
            return tfds.core.utils.Version("0.0.0")

    def _info(self) -> tfds.core.DatasetInfo:
        return tfds.core.DatasetInfo(
            builder=self,
            description=self._description,
            features=self._feature_spec,
            homepage=self._homepage,
            disable_shuffling=self._disable_shuffling,
        )

    def build_and_upload(self):
        super().download_and_prepare()
        self._wandb__artifact.add_dir(self.data_dir)
        wandb.log_artifact(self._wandb__artifact)
