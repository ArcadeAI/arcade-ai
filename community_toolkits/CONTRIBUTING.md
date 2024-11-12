# Contributing to Arcade AI Community Toolkits

Your toolkit must be a public Github repository.
Your toolkit must be under the MIT license.
Your toolkit must be a PyPi package.
Your toolkit must have been generated using Arcade AI CLI command `arcade new`.

Explanation of the format for contributing to the community toolkits.
Owner (Github Username): If you are contributing a toolkit that is hosted under your personal Github account, use your Github username. If you are contributing a toolkit that is hosted under an organization, use the organization name.
Toolkit Name: The name of the toolkit as it appears in the PyPi package.
Description: A short description of the toolkit.
PyPI Link: The link to the specific version of the PyPi package you are contributing.
GitHub Link: The web URL to the GitHub repository.

## Bumping a toolkit's version
In an effort to prevent undesired changes to a toolkit, we will not automatically bump a toolkit's version when it is contributed to the community toolkits.
Instead, you will need to manually update the version of the toolkit in the [community_toolkits.txt](community_toolkits.txt) file.

To update the version of the toolkit, you will need to:
1. Find the line in the [community_toolkits.txt](community_toolkits.txt) file that corresponds to your toolkit.
2. Update the version of the toolkit in the [community_toolkits.txt](community_toolkits.txt) file.
3. Open a Pull Request with the changes to the [community_toolkits.txt](community_toolkits.txt) file.
