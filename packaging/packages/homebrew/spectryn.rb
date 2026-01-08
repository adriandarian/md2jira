# frozen_string_literal: true

# Homebrew formula for spectra
# To install:
#   brew tap adriandarian/spectra https://github.com/adriandarian/spectra
#   brew install spectra
#
# Or install directly:
#   brew install adriandarian/spectra/spectra

class Spectra < Formula
  include Language::Python::Virtualenv

  desc "Production-grade CLI tool for synchronizing markdown documentation with Jira"
  homepage "https://github.com/adriandarian/spectra"
  url "https://github.com/adriandarian/spectryn/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "20f47c5f0e1c280877e26678c5464f6872f6e96287369b5e674306e19050f5d4"
  license "MIT"
  head "https://github.com/adriandarian/spectra.git", branch: "main"

  depends_on "python@3.12"

  resource "certifi" do
    url "https://github.com/adriandarian/spectryn/archive/refs/tags/v1.0.0.tar.gz"
    sha256 "20f47c5f0e1c280877e26678c5464f6872f6e96287369b5e674306e19050f5d4"
  end

  resource "charset-normalizer" do
    url "https://github.com/adriandarian/spectryn/archive/refs/tags/v1.0.0.tar.gz"
    sha256 "20f47c5f0e1c280877e26678c5464f6872f6e96287369b5e674306e19050f5d4"
  end

  resource "idna" do
    url "https://github.com/adriandarian/spectryn/archive/refs/tags/v1.0.0.tar.gz"
    sha256 "20f47c5f0e1c280877e26678c5464f6872f6e96287369b5e674306e19050f5d4"
  end

  resource "pyyaml" do
    url "https://github.com/adriandarian/spectryn/archive/refs/tags/v1.0.0.tar.gz"
    sha256 "20f47c5f0e1c280877e26678c5464f6872f6e96287369b5e674306e19050f5d4"
  end

  resource "requests" do
    url "https://github.com/adriandarian/spectryn/archive/refs/tags/v1.0.0.tar.gz"
    sha256 "20f47c5f0e1c280877e26678c5464f6872f6e96287369b5e674306e19050f5d4"
  end

  resource "urllib3" do
    url "https://github.com/adriandarian/spectryn/archive/refs/tags/v1.0.0.tar.gz"
    sha256 "20f47c5f0e1c280877e26678c5464f6872f6e96287369b5e674306e19050f5d4"
  end

  def install
    virtualenv_install_with_resources

    # Generate shell completions
    generate_completions_from_executable(bin/"spectra", "--completions")
  end

  def caveats
    <<~EOS
      To use spectra, set these environment variables:
        export JIRA_URL="https://your-company.atlassian.net"
        export JIRA_EMAIL="your.email@company.com"
        export JIRA_API_TOKEN="your-api-token"

      Or create a config file at ~/.spectra.yaml

      Shell completions have been installed for bash, zsh, and fish.
    EOS
  end

  test do
    assert_match "spectra", shell_output("#{bin}/spectra --version")
    assert_match "usage:", shell_output("#{bin}/spectra --help")
  end
end

