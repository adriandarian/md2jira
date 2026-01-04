# ==============================================================================
# RPM Spec file for spectra
# ==============================================================================
# Build with: rpmbuild -ba spectra.spec
# ==============================================================================

Name:           spectra
Version:        2.0.0
Release:        1%{?dist}
Summary:        CLI tool for synchronizing markdown documentation with Jira

License:        MIT
URL:            https://github.com/adriandarian/spectra
Source0:        https://github.com/adriandarian/spectra/archive/v%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel >= 3.10
BuildRequires:  python3-pip
BuildRequires:  python3-setuptools

Requires:       python3 >= 3.10
Requires:       python3-requests >= 2.28.0
Requires:       python3-pyyaml >= 6.0

%description
A production-grade CLI tool for synchronizing markdown documentation with Jira.

Features:
- Full Epic Sync - Sync user stories, subtasks, descriptions, and comments
- Markdown-Native - Write epic documentation in markdown, sync to Jira
- Smart Matching - Fuzzy title matching between markdown stories and Jira issues
- Safe by Default - Dry-run mode, confirmations, and detailed previews
- Command Pattern - Undo-capable operations with full audit trail
- Plugin System - Extensible architecture for custom integrations

%prep
%autosetup -n %{name}-%{version}

%build
%py3_build

%install
%py3_install

# Install shell completions
install -d %{buildroot}%{_datadir}/bash-completion/completions
install -d %{buildroot}%{_datadir}/zsh/site-functions
install -d %{buildroot}%{_datadir}/fish/vendor_completions.d

%{buildroot}%{_bindir}/spectra --completions bash > %{buildroot}%{_datadir}/bash-completion/completions/spectra
%{buildroot}%{_bindir}/spectra --completions zsh > %{buildroot}%{_datadir}/zsh/site-functions/_spectra
%{buildroot}%{_bindir}/spectra --completions fish > %{buildroot}%{_datadir}/fish/vendor_completions.d/spectra.fish

%files
%license LICENSE
%doc README.md CHANGELOG.md
%{_bindir}/spectra
%{python3_sitelib}/spectra/
%{python3_sitelib}/spectra-%{version}*
%{_datadir}/bash-completion/completions/spectra
%{_datadir}/zsh/site-functions/_spectra
%{_datadir}/fish/vendor_completions.d/spectra.fish

%changelog
* %(date "+%a %b %d %Y") Adrian Darian <adrian.the.hactus@gmail.com> - 2.0.0-1
- Initial RPM package

