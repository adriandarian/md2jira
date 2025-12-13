# Terraform Provider for Jira - Makefile

BINARY_NAME=terraform-provider-jira
VERSION=1.0.0
OS_ARCH=$(shell go env GOOS)_$(shell go env GOARCH)
PLUGIN_DIR=~/.terraform.d/plugins/registry.terraform.io/md2jira/jira/$(VERSION)/$(OS_ARCH)

.PHONY: build install clean test testacc fmt lint help

## build: Build the provider binary
build:
	go build -o $(BINARY_NAME)

## install: Install the provider locally for testing
install: build
	mkdir -p $(PLUGIN_DIR)
	cp $(BINARY_NAME) $(PLUGIN_DIR)/

## clean: Remove build artifacts
clean:
	rm -f $(BINARY_NAME)
	rm -rf dist/

## test: Run unit tests
test:
	go test ./... -v

## testacc: Run acceptance tests (requires JIRA credentials)
testacc:
	TF_ACC=1 go test ./... -v -timeout 120m

## fmt: Format Go code
fmt:
	go fmt ./...
	gofmt -s -w .

## lint: Run linter
lint:
	golangci-lint run ./...

## docs: Generate documentation
docs:
	go generate ./...

## deps: Download dependencies
deps:
	go mod download
	go mod tidy

## release: Build release binaries for all platforms
release:
	@mkdir -p dist
	GOOS=darwin GOARCH=amd64 go build -o dist/$(BINARY_NAME)_darwin_amd64
	GOOS=darwin GOARCH=arm64 go build -o dist/$(BINARY_NAME)_darwin_arm64
	GOOS=linux GOARCH=amd64 go build -o dist/$(BINARY_NAME)_linux_amd64
	GOOS=linux GOARCH=arm64 go build -o dist/$(BINARY_NAME)_linux_arm64
	GOOS=windows GOARCH=amd64 go build -o dist/$(BINARY_NAME)_windows_amd64.exe

## help: Show this help message
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@sed -n 's/^##//p' $(MAKEFILE_LIST) | column -t -s ':' | sed -e 's/^/ /'

# Default target
.DEFAULT_GOAL := help

