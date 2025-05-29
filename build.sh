#!/bin/bash
# Build script for AI Automation Builder Add-on

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ADDON_NAME="ai-automation-builder"
VERSION="1.0.0"
ARCHITECTURES=("amd64" "aarch64" "armhf" "armv7" "i386")

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
check_directory() {
    if [[ ! -f "config.yaml" ]] || [[ ! -f "Dockerfile" ]]; then
        log_error "This script must be run from the add-on root directory"
        log_error "Required files: config.yaml, Dockerfile"
        exit 1
    fi
    log_success "Directory check passed"
}

# Validate configuration files
validate_config() {
    log_info "Validating configuration files..."
    
    # Check if required files exist
    local required_files=("config.yaml" "Dockerfile" "run.py" "dependency_manager.py" "app.py" "run.sh")
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Required file missing: $file"
            exit 1
        fi
    done
    
    # Validate YAML syntax
    if command -v python3 &> /dev/null; then
        python3 -c "
import yaml
with open('config.yaml', 'r') as f:
    yaml.safe_load(f)
print('✓ config.yaml syntax is valid')
" || {
            log_error "config.yaml has invalid syntax"
            exit 1
        }
    fi
    
    log_success "Configuration validation passed"
}

# Check dependencies
check_dependencies() {
    log_info "Checking build dependencies..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is required but not installed"
        exit 1
    fi
    
    # Check Docker Buildx
    if ! docker buildx version &> /dev/null; then
        log_warning "Docker Buildx not available - multi-architecture builds may not work"
    fi
    
    log_success "Dependencies check passed"
}

# Clean build artifacts
clean_build() {
    log_info "Cleaning build artifacts..."
    
    # Remove Python cache
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    # Remove temporary files
    rm -f *.log 2>/dev/null || true
    rm -rf .pytest_cache 2>/dev/null || true
    
    log_success "Build artifacts cleaned"
}

# Test the Python code
test_code() {
    log_info "Testing Python code..."
    
    # Basic syntax check
    for py_file in *.py; do
        if [[ -f "$py_file" ]]; then
            python3 -m py_compile "$py_file" || {
                log_error "Syntax error in $py_file"
                exit 1
            }
        fi
    done
    
    # Test dependency manager
    log_info "Testing dependency manager..."
    python3 -c "
import sys
sys.path.insert(0, '.')
from dependency_manager import DependencyManager
manager = DependencyManager()
print('✓ DependencyManager imported successfully')
"
    
    log_success "Code tests passed"
}

# Build for single architecture
build_single_arch() {
    local arch=$1
    log_info "Building for architecture: $arch"
    
    docker build \
        --platform linux/$arch \
        --tag "$ADDON_NAME:$VERSION-$arch" \
        --tag "$ADDON_NAME:latest-$arch" \
        . || {
        log_error "Build failed for $arch"
        return 1
    }
    
    log_success "Build completed for $arch"
}

# Build for all architectures
build_all_architectures() {
    log_info "Building for all architectures..."
    
    local build_args=""
    for arch in "${ARCHITECTURES[@]}"; do
        build_args="$build_args --platform linux/$arch"
    done
    
    if docker buildx version &> /dev/null; then
        # Use buildx for multi-arch build
        docker buildx build \
            $build_args \
            --tag "$ADDON_NAME:$VERSION" \
            --tag "$ADDON_NAME:latest" \
            . || {
            log_error "Multi-architecture build failed"
            return 1
        }
    else
        # Build each architecture separately
        for arch in "${ARCHITECTURES[@]}"; do
            build_single_arch "$arch" || return 1
        done
    fi
    
    log_success "All architecture builds completed"
}

# Create release package
create_release() {
    log_info "Creating release package..."
    
    local release_dir="release"
    local package_name="${ADDON_NAME}-${VERSION}.tar.gz"
    
    # Create release directory
    mkdir -p "$release_dir"
    
    # Create tarball with all necessary files
    tar -czf "$release_dir/$package_name" \
        --exclude="release" \
        --exclude=".git" \
        --exclude="*.log" \
        --exclude="__pycache__" \
        --exclude="*.pyc" \
        --exclude=".pytest_cache" \
        . || {
        log_error "Failed to create release package"
        return 1
    }
    
    log_success "Release package created: $release_dir/$package_name"
}

# Generate installation instructions
generate_install_docs() {
    log_info "Generating installation documentation..."
    
    cat > INSTALL.md << EOF
# Installation Instructions for AI Automation Builder

## Prerequisites
- Home Assistant Supervisor
- Docker support
- Internet connection for dependency installation

## Installation Methods

### Method 1: Add-on Store (Recommended)
1. Go to Supervisor → Add-on Store
2. Click menu (⋮) → Repositories
3. Add: \`https://github.com/yourusername/ai-automation-builder\`
4. Install "AI Automation Builder"

### Method 2: Manual Installation
1. Copy the add-on files to: \`/usr/share/hassio/addons/local/ai-automation-builder/\`
2. Restart Home Assistant Supervisor
3. Install from Local Add-ons

## Configuration
\`\`\`yaml
api_key: "your-api-key"  # Optional
model: "gpt-3.5-turbo"
port: 5001
ha_token: "your-long-lived-token"
log_level: "info"
\`\`\`

## First Run
1. Start the add-on
2. Check logs for dependency installation progress
3. Open Web UI when ready
4. Create your first automation!

## Support
- GitHub Issues: https://github.com/yourusername/ai-automation-builder/issues
- Home Assistant Community: https://community.home-assistant.io/
EOF
    
    log_success "Installation documentation generated"
}

# Main build function
main() {
    log_info "🚀 Starting AI Automation Builder build process..."
    
    # Run all checks and build steps
    check_directory
    validate_config
    check_dependencies
    clean_build
    test_code
    
    # Build options
    case "${1:-all}" in
        "single")
            if [[ -n "$2" ]]; then
                build_single_arch "$2"
            else
                log_error "Architecture required for single build (e.g., amd64)"
                exit 1
            fi
            ;;
        "all"|"")
            build_all_architectures
            ;;
        "package")
            create_release
            ;;
        "docs")
            generate_install_docs
            ;;
        "clean")
            clean_build
            log_success "Clean completed"
            exit 0
            ;;
        *)
            log_error "Unknown build option: $1"
            echo "Usage: $0 [all|single|package|docs|clean] [architecture]"
            exit 1
            ;;
    esac
    
    # Generate documentation
    generate_install_docs
    
    log_success "🎉 Build process completed successfully!"
    log_info "Next steps:"
    log_info "1. Test the add-on in your Home Assistant instance"
    log_info "2. Create a GitHub release with the built images"
    log_info "3. Update the add-on repository"
}

# Handle script interruption
trap 'log_warning "Build interrupted by user"; exit 1' INT TERM

# Run main function with all arguments
main "$@"