# spectra Package Distribution

This directory contains packaging configurations for distributing spectra across multiple platforms.

## Supported Package Managers

| Platform | Package Manager | Status | Installation |
|----------|-----------------|--------|--------------|
| macOS | Homebrew | ✅ Ready | `brew install adriandarian/spectra/spectra` |
| macOS/Linux | Homebrew (linuxbrew) | ✅ Ready | Same as above |
| Windows | Chocolatey | ✅ Ready | `choco install spectra` |
| Linux | pip/pipx | ✅ Ready | `pip install spectra` |
| Linux | RPM (Fedora/RHEL) | ✅ Spec Ready | Build from spec file |
| Linux | DEB (Ubuntu/Debian) | ✅ Control Ready | Build with debhelper |

## Quick Install

### Universal (All Platforms)

```bash
pip install spectra
# or
pipx install spectra
```

### macOS (Homebrew)

```bash
# Add the tap
brew tap adriandarian/spectra

# Install
brew install spectra
```

### Windows (Chocolatey)

```powershell
# Requires Python 3.10+
choco install spectra
```

### Linux (Universal Script)

```bash
curl -fsSL https://raw.githubusercontent.com/adriandarian/spectra/main/packaging/linux/install.sh | bash
```

## Building Packages

### Homebrew

1. Update the formula with correct SHA256 hashes:

```bash
# Get SHA256 of release tarball
curl -sL https://github.com/adriandarian/spectra/archive/refs/tags/v2.0.0.tar.gz | shasum -a 256
```

2. Create a tap repository and add the formula:

```bash
# Create tap repo: homebrew-spectra
# Add packaging/homebrew/spectra.rb to the repo
```

### Chocolatey

```powershell
cd packaging/chocolatey

# Build the package
choco pack

# Test locally
choco install spectra -s . -y

# Push to Chocolatey (requires API key)
choco push spectra.2.0.0.nupkg --source https://push.chocolatey.org/
```

### RPM (Fedora/RHEL/CentOS)

```bash
# Install build tools
sudo dnf install rpm-build python3-devel

# Set up rpmbuild directories
mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Copy spec file
cp packaging/linux/spectra.spec ~/rpmbuild/SPECS/

# Download source
spectool -g -R ~/rpmbuild/SPECS/spectra.spec

# Build
rpmbuild -ba ~/rpmbuild/SPECS/spectra.spec
```

### DEB (Ubuntu/Debian)

```bash
# Install build tools
sudo apt install devscripts debhelper dh-python python3-all python3-setuptools

# Create source package structure
# Copy debian/ directory contents
# Run: debuild -us -uc
```

## CI/CD Integration

For automated package building and publishing, see `.github/workflows/release.yml` for GitHub Actions examples that:

1. Build packages on release tags
2. Publish to PyPI
3. Update Homebrew tap
4. Push to Chocolatey
5. Create GitHub releases with attached artifacts

## Directory Structure

```
packaging/
├── README.md           # This file
├── homebrew/
│   └── spectra.rb      # Homebrew formula
├── chocolatey/
│   ├── spectra.nuspec  # Chocolatey package spec
│   └── tools/
│       ├── chocolateyinstall.ps1
│       └── chocolateyuninstall.ps1
└── linux/
    ├── install.sh      # Universal installer script
    ├── spectra.spec    # RPM spec file
    └── debian/
        └── control     # Debian package control file
```

## Version Updates

When releasing a new version:

1. Update `pyproject.toml` version
2. Update `packaging/homebrew/spectra.rb` version and SHA256
3. Update `packaging/chocolatey/spectra.nuspec` version
4. Update `packaging/linux/spectra.spec` version
5. Tag release: `git tag v2.0.0 && git push --tags`

