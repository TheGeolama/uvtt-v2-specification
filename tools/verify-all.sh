#!/usr/bin/env bash
# ==============================================================================
# UVTT v2 Core Verification & Conformance Automation Suite
# Version: 2.0.0-rc1
# Description: Unified test runner and validation gateway for the platform-agnostic
#              Universal VTT v2 specification tools. 
# ==============================================================================

# ANSI Color Codes for high-impact visual terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default configurations
TARGET_MAP=""
EXIT_CODE=0

print_header() {
    echo -e "${BLUE}======================================================================${NC}"
    echo -e "${BOLD}       UVTT v2 System-Agnostic Verification & Conformance Suite       ${NC}"
    echo -e "${BLUE}======================================================================${NC}"
}

print_status() {
    echo -e "${BLUE}[*]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[+] PASS:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!] WARNING:${NC} $1"
}

print_error() {
    echo -e "${RED}[-] FAIL:${NC} $1"
}

show_help() {
    echo "Usage: ./verify-all.sh [options]"
    echo ""
    echo "Options:"
    echo "  -m, --map <file.uvtt2z>   Validate a specific .uvtt2z archive against structural conformance rules"
    echo "  --self-test               Execute internal programmatic self-tests on the python validators"
    echo "  -h, --help                Display this help documentation"
    echo ""
    echo "Examples:"
    echo "  ./verify-all.sh --self-test"
    echo "  ./verify-all.sh -m campaign_level_1.uvtt2z"
}

# Helper to find a file in common locations
find_script() {
    local filename="$1"
    local paths=(
        "."
        "scratch"
        "artifacts"
        "/workspace"
        "/workspace/scratch"
        "/workspace/artifacts"
    )
    for p in "${paths[@]}"; do
        if [ -f "$p/$filename" ]; then
            echo "$p/$filename"
            return 0
        fi
    done
    return 1
}

# Parse command line options
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -m|--map)
            TARGET_MAP="$2"
            shift; shift
            ;;
        --self-test)
            RUN_SELF_TEST=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown argument: $1"
            show_help
            exit 1
            ;;
    esac
done

clear
print_header

# ------------------------------------------------------------------------------
# STEP 1: Dependency and Environment Verification
# ------------------------------------------------------------------------------
print_status "Executing dependency checks..."

# Check Python 3
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python 3 is available (Version: $PY_VERSION)"
else
    print_error "Python 3 is required but was not found in the path."
    EXIT_CODE=1
fi

# Check Go (graceful degradation check)
if command -v go &>/dev/null; then
    GO_VERSION=$(go version | cut -d' ' -f3)
    print_success "Go compiler is available (Version: $GO_VERSION)"
    HAS_GO=true
else
    print_warning "Go compiler is missing. Server-side binary validation steps will be skipped."
    HAS_GO=false
fi

if [ $EXIT_CODE -ne 0 ]; then
    print_error "Environment verification failed. Please install missing dependencies and retry."
    exit $EXIT_CODE
fi

# ------------------------------------------------------------------------------
# STEP 2: Run Cryptographic Decryption Handshake Tests
# ------------------------------------------------------------------------------
echo ""
print_header
print_status "Step 2: Testing Serverless Handshake Decryption & ZKS Gates"

HANDSHAKE_SUITE=$(find_script "test-handshake-suite.py")
if [ $? -eq 0 ]; then
    print_status "Running $HANDSHAKE_SUITE in daemon mock mode..."
    python3 "$HANDSHAKE_SUITE" --mock
    TEST_RESULT=$?
    if [ $TEST_RESULT -eq 0 ]; then
        print_success "All 5 cryptographic edge clearinghouse handshake tests passed."
    else
        print_error "Serverless handshake test suite flagged failures (Exit Code: $TEST_RESULT)."
        EXIT_CODE=1
    fi
else
    # Check alternate naming conventions inside scratch if present
    ALT_HANDSHAKE_SUITE=$(find_script "test_handshake_suite.py")
    if [ $? -eq 0 ]; then
        print_status "Running $ALT_HANDSHAKE_SUITE in daemon mock mode..."
        python3 "$ALT_HANDSHAKE_SUITE" --mock
        TEST_RESULT=$?
        if [ $TEST_RESULT -eq 0 ]; then
            print_success "All 5 cryptographic edge clearinghouse handshake tests passed."
        else
            print_error "Serverless handshake test suite flagged failures (Exit Code: $TEST_RESULT)."
            EXIT_CODE=1
        fi
    else
        print_warning "Cryptographic handshake suite (test-handshake-suite.py) not found in working directories."
    fi
fi

# ------------------------------------------------------------------------------
# STEP 3: Conformance and Geometry Validation
# ------------------------------------------------------------------------------
echo ""
print_header
print_status "Step 3: Verification of Campaign Metadata & Spatial Topology"

VALIDATOR_SCRIPT=$(find_script "verify-uvtt2-conformance.py")
if [ $? -ne 0 ]; then
    # Try alternate naming
    VALIDATOR_SCRIPT=$(find_script "verify_uvtt2_conformance.py")
fi

if [ -z "$VALIDATOR_SCRIPT" ] || [ ! -f "$VALIDATOR_SCRIPT" ]; then
    print_warning "Conformance validator (verify-uvtt2-conformance.py) not found. Skipping."
else
    # Option A: Run automated self-test
    if [ "$RUN_SELF_TEST" = true ] || [ -z "$TARGET_MAP" ]; then
        print_status "No target map archive provided, or --self-test flag active."
        print_status "Executing internal programmatic self-tests inside $VALIDATOR_SCRIPT..."
        python3 "$VALIDATOR_SCRIPT" --self-test
        SELF_TEST_RESULT=$?
        if [ $SELF_TEST_RESULT -eq 0 ]; then
            print_success "Internal validator self-test executed successfully."
        else
            print_error "Validator self-test failed (Exit Code: $SELF_TEST_RESULT)."
            EXIT_CODE=1
        fi
    fi

    # Option B: Validate user's specific map file
    if [ -n "$TARGET_MAP" ]; then
        print_status "Analyzing target campaign file: $TARGET_MAP"
        if [ -f "$TARGET_MAP" ]; then
            python3 "$VALIDATOR_SCRIPT" "$TARGET_MAP"
            MAP_TEST_RESULT=$?
            if [ $MAP_TEST_RESULT -eq 0 ]; then
                print_success "File '$TARGET_MAP' conforms fully to the UVTT v2.0.0-rc1 standard!"
            else
                print_error "File '$TARGET_MAP' failed structural/cryptographic validation (Exit Code: $MAP_TEST_RESULT)."
                EXIT_CODE=1
            fi
        else
            # Try to resolve map path in other dirs too
            RESOLVED_MAP=$(find_script "$TARGET_MAP")
            if [ $? -eq 0 ]; then
                python3 "$VALIDATOR_SCRIPT" "$RESOLVED_MAP"
                MAP_TEST_RESULT=$?
                if [ $MAP_TEST_RESULT -eq 0 ]; then
                    print_success "File '$RESOLVED_MAP' conforms fully to the UVTT v2.0.0-rc1 standard!"
                else
                    print_error "File '$RESOLVED_MAP' failed structural/cryptographic validation (Exit Code: $MAP_TEST_RESULT)."
                    EXIT_CODE=1
                fi
            else
                print_error "Target map file not found: $TARGET_MAP"
                EXIT_CODE=1
            fi
        fi
    fi
fi

# ------------------------------------------------------------------------------
# STEP 4: Server-side Go Binary Validation (Optional)
# ------------------------------------------------------------------------------
if [ "$HAS_GO" = true ]; then
    echo ""
    print_header
    print_status "Step 4: Compiling and Running Server-Side Go Validator"
    
    GO_SCRIPT=$(find_script "validate_conformance.go")
    if [ $? -ne 0 ]; then
        GO_SCRIPT=$(find_script "validate-conformance.go")
    fi
    
    if [ -n "$GO_SCRIPT" ] && [ -f "$GO_SCRIPT" ]; then
        print_status "Compiling $GO_SCRIPT to local build binary..."
        go build -o uvtt2-validator "$GO_SCRIPT"
        BUILD_RESULT=$?
        if [ $BUILD_RESULT -eq 0 ]; then
            print_success "Server-side Go validator compiled cleanly."
            
            # If we have a map, run the binary against it
            if [ -n "$TARGET_MAP" ]; then
                RESOLVED_MAP="$TARGET_MAP"
                if [ ! -f "$RESOLVED_MAP" ]; then
                    RESOLVED_MAP=$(find_script "$TARGET_MAP")
                fi
                
                if [ -n "$RESOLVED_MAP" ] && [ -f "$RESOLVED_MAP" ]; then
                    print_status "Running binary validation on $RESOLVED_MAP..."
                    ./uvtt2-validator "$RESOLVED_MAP"
                    GO_RUN_RESULT=$?
                    if [ $GO_RUN_RESULT -eq 0 ]; then
                        print_success "Go binary confirmed structural & Landing Zone integrity!"
                    else
                        print_error "Go binary rejected package topology (Exit Code: $GO_RUN_RESULT)."
                        EXIT_CODE=1
                    fi
                else
                    print_error "Could not resolve map target '$TARGET_MAP' for Go validation."
                    EXIT_CODE=1
                fi
            else
                print_status "No active map file targeted. Go validator compiled but not executed on real asset."
            fi
            
            # Clean up binary
            rm -f uvtt2-validator
        else
            print_error "Failed to compile Go validator (Exit Code: $BUILD_RESULT)."
            EXIT_CODE=1
        fi
    else
        print_warning "Go validator code (validate_conformance.go) was not found in directory."
    fi
fi

# ------------------------------------------------------------------------------
# SUMMARY REPORT
# ------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}======================================================================${NC}"
echo -e "${BOLD}                        FINAL VERIFICATION STATUS                     ${NC}"
echo -e "${BLUE}======================================================================${NC}"

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "  ${BOLD}${GREEN}ALL SECURE GATES PASSED SUCCESSFULLY${NC}"
    echo -e "  Your UVTT v2 environment and components conform cleanly to the standard."
else
    echo -e "  ${BOLD}${RED}VERIFICATION CONFORMANCE FAILURE(S) DETECTED${NC}"
    echo -e "  One or more compliance tests failed. Check diagnostic outputs above."
fi
echo -e "${BLUE}======================================================================${NC}"

exit $EXIT_CODE
