import os
import subprocess
import zipfile

from generate_single_toolkit_doc import generate_md_file


def pip_to_module_name(pip_name):
    """
    Convert a pip package name to a Python module name.

    Parameters:
    pip_name (str): The pip package name.

    Returns:
    str: The corresponding Python module name.
    """
    # Replace hyphens with underscores
    module_name = pip_name.replace("-", "_")
    # Replace dots with underscores (if needed)
    module_name = module_name.replace(".", "_")
    return module_name


def download_toolkit(toolkit_name, toolkit_version):
    # Create a directory for the toolkit
    os.makedirs(toolkit_name, exist_ok=True)
    try:
        # Download the pip package's .whl file
        subprocess.run(
            [  # noqa: S607
                "pip",
                "download",
                f"{toolkit_name}=={toolkit_version}",
                "--no-deps",
                "-d",
                toolkit_name,
            ],
            check=True,
        )
    except subprocess.CalledProcessError:
        return False
    return True


def unzip_toolkit(toolkit_name):
    # Find the .whl file
    wheel_file = None
    toolkit_dir = os.path.join(os.path.dirname(__file__), toolkit_name)
    for file in os.listdir(toolkit_dir):
        if file.endswith(".whl"):
            # More permissive check - just look for .whl files since the name format can vary
            wheel_file = file
            break

    if not wheel_file:
        return False

    try:
        # Extract the .whl file into the toolkit directory
        with zipfile.ZipFile(
            os.path.join(os.path.dirname(__file__), toolkit_name, wheel_file), "r"
        ) as zip_ref:
            zip_ref.extractall(toolkit_name)
    except zipfile.BadZipFile:
        return False
    return True


def install_toolkit(toolkit_name, toolkit_version):
    # Create a directory for the toolkit
    try:
        # Download the pip package's .whl file
        subprocess.run(
            [  # noqa: S607
                "pip",
                "install",
                f"{toolkit_name}=={toolkit_version}",
                "--no-deps",
            ],
            check=True,
        )
    except subprocess.CalledProcessError:
        return False
    return True


def generate_toolkit_docs(toolkit_file_path):
    print(f"Generating docs for {toolkit_file_path}")
    pass


def run():
    docs_dir = os.path.join(os.path.dirname(__file__), "docs")
    os.makedirs(docs_dir, exist_ok=True)

    with open(os.path.join(os.path.dirname(__file__), "community_toolkits.txt")) as file:
        toolkits = file.readlines()[1:]

    for toolkit in toolkits:
        toolkit_owner, toolkit_name, toolkit_pypi_link, toolkit_github_link = toolkit.split(",")
        toolkit_pypi_name, toolkit_pypi_version = (
            toolkit_pypi_link.split("project/")[1].strip("/").split("/")
        )

        if not install_toolkit(toolkit_pypi_name, toolkit_pypi_version):
            print(f"Failed to install {toolkit_pypi_name}=={toolkit_pypi_version}")
            continue

        generate_md_file(
            pip_to_module_name(toolkit_pypi_name),
            toolkit_pypi_link,
            toolkit_github_link,
            os.path.join(os.path.dirname(__file__), "docs", toolkit_pypi_name + ".md"),
        )

        # if download_toolkit(toolkit_pypi_name, toolkit_pypi_version):
        #     zip_file_path = os.path.join(os.path.dirname(__file__), toolkit_pypi_name)
        #     print(
        #         f"Downloaded {toolkit_pypi_name}=={toolkit_pypi_version} successfully to {zip_file_path}."
        #     )
        # if unzip_toolkit(toolkit_pypi_name):
        #     toolkit_file_path = os.path.join(
        #         os.path.dirname(__file__), toolkit_pypi_name, toolkit_pypi_name
        #     )
        #     print(
        #         f"Unzipped {toolkit_pypi_name}=={toolkit_pypi_version} successfully to {toolkit_file_path}."
        #     )

        # if generate_toolkit_docs(toolkit_file_path):
        #     toolkit_docs_path = os.path.join(os.path.dirname(__file__), "docs", toolkit_pypi_name)
        #     print(
        #         f"Generated docs for {toolkit_pypi_name}=={toolkit_pypi_version} successfully to {toolkit_docs_path}."
        #     )

        # Delete the toolkit directory
        # toolkit_dir = os.path.join(os.path.dirname(__file__), toolkit_pypi_name)
        # if os.path.exists(toolkit_dir):
        #     shutil.rmtree(toolkit_dir)
        #     print(f"Cleaned up {toolkit_dir}")


if __name__ == "__main__":
    run()
