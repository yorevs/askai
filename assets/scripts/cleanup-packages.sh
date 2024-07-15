#!/bin/bash

# Purpose: Cleanup all python packages, leaving only the defaults.

# Python site-packages directory.
SITE_PACKAGES_DIR=${SITE_PACKAGES_DIR:-'/usr/local/lib/python3.11/site-packages'}

pushd "$SITE_PACKAGES_DIR" &>/dev/null || exit 1

# Save all installed packages
python3 -m pip list --format=freeze > installed_packages.txt

# Save the default packages
echo -e "pip\nsetuptools\nwheel" > default_packages.txt

# Read default packages
default_packages=$(cat default_packages.txt)

# Loop through installed packages and uninstall those not in default_packages
while IFS= read -r package; do
    package_name=$(echo "${package}" | cut -d'=' -f1)
    if ! grep -q "^$package_name$" default_packages.txt; then
        python3 -m pip uninstall -y "${package_name}"
    fi
done < installed_packages.txt

# Clean up
rm -f installed_packages.txt

# Upgrade default packages.
pip install --force-reinstall --upgrade "${default_packages}"

popd &>/dev/null || exit 1

echo 'Done.'
exit 0
