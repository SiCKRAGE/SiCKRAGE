#!/bin/bash
set -eux

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $SCRIPT_DIR/..

VERSION="${1}"
TARGET="${2}"

echo "Current version: $VERSION"
echo "Bumping version: $TARGET"

sed -i '' -e "1,/^version/ s/^version.*/version = \"$TARGET\"/" Cargo.toml
cargo update -p sentry-cli

# Do not tag and commit changes made by "npm version"
export npm_config_git_tag_version=false
npm version "${TARGET}"
