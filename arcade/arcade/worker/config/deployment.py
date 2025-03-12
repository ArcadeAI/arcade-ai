import base64
import io
import os
import secrets
import tarfile
from pathlib import Path
from typing import Any

import httpx
import toml
from arcadepy import Arcade, NotFoundError
from httpx import Client
from packaging.requirements import Requirement
from pydantic import BaseModel, field_validator, model_validator


# Base class for versioned packages
class Package(BaseModel):
    name: str
    specifier: str | None = None

    @classmethod
    def from_requirement(cls, requirement_str: str) -> "Package":
        req = Requirement(requirement_str)
        return cls(name=req.name, specifier=str(req.specifier) if req.specifier else None)


# Base class for a list of packages
class Packages(BaseModel):
    packages: list[Package]

    # Convert string package i.e. "arcade>1.0.0" to a name and specifier
    # Specifiers are currently unused
    @field_validator("packages", mode="before")
    @classmethod
    def parse_package_requirements(cls, packages: list[str]) -> list[Package]:
        """Convert package requirement strings to Package objects."""
        return [Package.from_requirement(pkg) for pkg in packages]


# Base class for a local package
class LocalPackage(BaseModel):
    name: str
    content: str


# Base class for a list of local packages
class LocalPackages(BaseModel):
    packages: list[str]


# Custom repository configurations
class PackageRepository(Packages):
    index: str
    index_url: str
    trusted_host: str


# Pypi is a special case of a package repository
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

    # Validate that the secret is a non-empty string and not 'dev'
    @field_validator("secret")
    @classmethod
    def valid_secret(cls, v: str) -> str:
        if v.strip("") == "" or v == "dev":
            raise ValueError("Secret must be a non-empty string and not 'dev'")
        return v


# Cloud request for deploying a worker
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
        # Attempt to deploy worker to the cloud
        try:
            cloud_response = cloud_client.put(
                str(cloud_client.base_url) + "/api/v1/workers",
                json=self.model_dump(mode="json"),
                timeout=120,
            )
            cloud_response.raise_for_status()
        except httpx.ConnectError as e:
            raise ValueError(f"Failed to connect to cloud: {e}")
        except Exception:
            msg = cloud_response.json().get("msg", f"{cloud_response.status_code}: Unknown error")
            raise ValueError(f"Failed to start worker: {msg}")

        try:
            # Check if worker already exists
            engine_client.workers.get(self.name)
            engine_client.workers.update(
                id=self.name,
                enabled=self.enabled,
                http={
                    "uri": cloud_response.json()["data"]["worker_endpoint"],
                    "secret": self.secret,
                    "timeout": self.timeout,
                    "retry": self.retries,
                },
            )
        # If worker does not exist, create it
        except NotFoundError:
            engine_client.workers.create(
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

    # Search for local packages and compress the source code to send
    def compress_local_packages(self) -> list[LocalPackage] | None:
        """Compress local packages into a list of LocalPackage objects."""
        if self.local_source is None:
            return None

        # Compress local packages into a list of LocalPackage objects
        def process_package(package_path_str: str) -> LocalPackage:
            package_path = self.toml_path.parent / package_path_str

            if not package_path.exists():
                raise FileNotFoundError(f"Local package not found: {package_path}")
            if not package_path.is_dir():
                raise FileNotFoundError(f"Local package is not a directory: {package_path}")

            # Check that the package is a valid python package
            if (
                not (package_path / "pyproject.toml").is_file()
                and not (package_path / "setup.py").is_file()
            ):
                raise ValueError(f"'{package_path}' must contain a pyproject.toml or setup.py file")

            # Compress the package into a byte stream and tar
            byte_stream = io.BytesIO()
            with tarfile.open(fileobj=byte_stream, mode="w:gz") as tar:
                tar.add(package_path, arcname=package_path.name)

            byte_stream.seek(0)
            package_bytes = byte_stream.read()
            package_bytes_b64 = base64.b64encode(package_bytes).decode("utf-8")

            return LocalPackage(name=package_path.name, content=package_bytes_b64)

        return list(map(process_package, self.local_source.packages))

    # Validate that there are no duplicate packages for each worker
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
    toml_path: Path
    worker: list[Worker]

    # Validate that there are no duplicate worker names
    @model_validator(mode="after")
    def validate_workers(self) -> "Deployment":
        for worker in self.worker:
            if sum(worker.config.id == w.config.id for w in self.worker) > 1:
                raise ValueError(f"Duplicate worker name: {worker.config.id}")
        return self

    # Load a deployment from a toml file
    @classmethod
    def from_toml(cls, toml_path: Path) -> "Deployment":
        try:
            with open(toml_path) as f:
                toml_data = toml.load(f)

            if not toml_data:
                raise ValueError(f"Empty TOML file: {toml_path}")

            # Add the toml path to each worker so relative packages can be found
            if "worker" in toml_data:
                for worker in toml_data["worker"]:
                    worker["toml_path"] = toml_path

            return cls(**toml_data, toml_path=toml_path)

        except toml.TomlDecodeError as e:
            raise ValueError(f"Invalid TOML format in {toml_path}: {e!s}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {toml_path}")

    def save(self) -> None:
        print("writing deployment file", self.toml_path)
        with open(self.toml_path, "w") as f:
            data = self.model_dump()
            del data["toml_path"]
            for worker in data["worker"]:
                del worker["toml_path"]
            toml.dump(data, f)


def create_demo_deployment(toml_path: Path, toolkit_name: str) -> None:
    """Create a deployment from a toml file."""
    deployment = Deployment(
        toml_path=toml_path,
        worker=[
            Worker(
                toml_path=toml_path,
                config=Config(
                    id="demo-worker",
                    enabled=True,
                    timeout=30,
                    retries=3,
                    secret=secrets.token_hex(16),
                ),
                local_source=LocalPackages(packages=[f"./{toolkit_name}"]),
            )
        ],
    )
    deployment.save()


def update_deployment_with_local_packages(toml_path: Path, toolkit_name: str) -> None:
    """Update a deployment from a toml file."""
    deployment = Deployment.from_toml(toml_path)
    if deployment.worker[0].local_source is None:
        deployment.worker[0].local_source = LocalPackages(packages=[f"./{toolkit_name}"])
    else:
        deployment.worker[0].local_source.packages.append(f"./{toolkit_name}")
    deployment.save()
