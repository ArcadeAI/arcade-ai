import base64
import io
import os
import tarfile
from pathlib import Path
from typing import Any

import httpx
import toml
from arcadepy import Arcade
from httpx import Client
from packaging.requirements import Requirement
from pydantic import BaseModel, field_validator, model_validator


class Package(BaseModel):
    name: str
    specifier: str | None = None

    @classmethod
    def from_requirement(cls, requirement_str: str) -> "Package":
        req = Requirement(requirement_str)
        return cls(name=req.name, specifier=str(req.specifier) if req.specifier else None)


class Packages(BaseModel):
    packages: list[Package]

    @field_validator("packages", mode="before")
    @classmethod
    def parse_package_requirements(cls, packages: list[str]) -> list[Package]:
        """Convert package requirement strings to Package objects."""
        return [Package.from_requirement(pkg) for pkg in packages]


class LocalPackage(BaseModel):
    name: str
    content: str


class LocalPackages(BaseModel):
    packages: list[str]


class PackageRepository(Packages):
    index: str
    index_url: str
    trusted_host: str


class Pypi(PackageRepository):
    index: str = "pypi"
    index_url: str = "https://pypi.org/simple"
    trusted_host: str = "pypi.org"


class Config(BaseModel):
    id: str
    enabled: bool = True
    timeout: int = 30
    retries: int = 3
    secret: str

    @field_validator("secret")
    @classmethod
    def valid_secret(cls, v: str) -> str:
        if v.strip("") == "" or v == "dev":
            raise ValueError("Secret must be a non-empty string and not 'dev'")
        return v


class Request(BaseModel):
    name: str
    secret: str
    enabled: bool
    timeout: int
    retries: int
    pypi: Pypi | None = None
    custom_repositories: list[PackageRepository] | None = None
    local_packages: list[LocalPackage] | None = None

    def execute(self, cloud_client: Client, engine_client: Arcade) -> Any:
        try:
            cloud_response = cloud_client.put(
                str(cloud_client.base_url) + "/api/v1/workers",
                json=self.model_dump(mode="json"),
                timeout=120,
            )
            cloud_response.raise_for_status()
        except Exception:
            msg = cloud_response.json().get("msg", f"{cloud_response.status_code}: Unknown error")

            raise ValueError(f"Failed to start worker: {msg}")

        try:
            # TODO: Remove this once stainless client is updated
            client = httpx.Client()
            request = client.get(
                str(engine_client.base_url) + "/v1/admin/workers/" + self.name,
                headers=cloud_client.headers,
                timeout=120,
            )

            exists = request.status_code == 200

            if not exists:
                engine_client.worker.create(
                    id=self.name,
                    enabled=self.enabled,
                    http={
                        "uri": cloud_response.json()["data"]["worker_endpoint"],
                        "secret": self.secret,
                        "timeout": self.timeout,
                        "retry": self.retries,
                    },
                )
            else:
                engine_client.worker.update(
                    id=self.name,
                    enabled=self.enabled,
                    http={
                        "uri": cloud_response.json()["data"]["worker_endpoint"],
                        "secret": self.secret,
                        "timeout": self.timeout,
                        "retry": self.retries,
                    },
                )
        except Exception as e:
            raise ValueError(f"Failed to add worker to engine: {e}")

        return cloud_response.json()


class Worker(BaseModel):
    toml_path: Path
    config: Config
    pypi_source: Pypi | None = None
    custom_source: list[PackageRepository] | None = None
    local_source: LocalPackages | None = None

    def request(self) -> Request:
        """Convert Deployment to a Request object."""
        self.validate_packages()
        self.compress_local_packages()
        return Request(
            name=self.config.id,
            secret=self.config.secret,
            enabled=self.config.enabled,
            timeout=self.config.timeout,
            retries=self.config.retries,
            pypi=self.pypi_source,
            custom_repositories=self.custom_source,
            local_packages=self.compress_local_packages(),
        )

    def compress_local_packages(self) -> list[LocalPackage] | None:
        """Compress local packages into a list of LocalPackage objects."""
        if self.local_source is None:
            return None

        def process_package(package_path_str: str) -> LocalPackage:
            package_path = self.toml_path.parent / package_path_str

            if not package_path.exists():
                raise FileNotFoundError(f"Local package not found: {package_path}")
            if not package_path.is_dir():
                raise FileNotFoundError(f"Local package is not a directory: {package_path}")
            if (
                not (package_path / "pyproject.toml").is_file()
                and not (package_path / "setup.py").is_file()
            ):
                raise ValueError(f"'{package_path}' must contain a pyproject.toml or setup.py file")

            byte_stream = io.BytesIO()
            with tarfile.open(fileobj=byte_stream, mode="w:gz") as tar:
                tar.add(package_path, arcname=package_path.name)

            byte_stream.seek(0)
            package_bytes = byte_stream.read()
            package_bytes_b64 = base64.b64encode(package_bytes).decode("utf-8")

            return LocalPackage(name=package_path.name, content=package_bytes_b64)

        return list(map(process_package, self.local_source.packages))

    def validate_packages(self) -> None:
        """Validate packages."""
        packages: list[str] = []
        if self.pypi_source:
            for pypi_package in self.pypi_source.packages:
                packages.append(pypi_package.name)
        if self.custom_source:
            for repository in self.custom_source:
                for package in repository.packages:
                    packages.append(package.name)
        if self.local_source:
            for local_package in self.local_source.packages:
                packages.append(os.path.basename(os.path.dirname(Path(local_package))))
        dupes = [x for n, x in enumerate(packages) if x in packages[:n]]
        if dupes:
            raise ValueError(f"Duplicate packages: {dupes}")


class Deployment(BaseModel):
    toml_path: str
    worker: list[Worker]

    @model_validator(mode="after")
    def validate_workers(self) -> "Deployment":
        for worker in self.worker:
            if sum(worker.config.id == w.config.id for w in self.worker) > 1:
                raise ValueError(f"Duplicate worker name: {worker.config.id}")
        return self

    @classmethod
    def from_toml(cls, toml_path: str) -> "Deployment":
        try:
            with open(toml_path) as f:
                toml_data = toml.load(f)

            if not toml_data:
                raise ValueError(f"Empty TOML file: {toml_path}")

            if "worker" in toml_data:
                for worker in toml_data["worker"]:
                    worker["toml_path"] = Path(toml_path)

            return cls(**toml_data, toml_path=toml_path)

        except toml.TomlDecodeError as e:
            raise ValueError(f"Invalid TOML format in {toml_path}: {e!s}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {toml_path}")
