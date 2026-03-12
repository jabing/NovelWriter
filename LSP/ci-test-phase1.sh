#!/bin/bash

# CI Test Script for Phase 1
# This script runs all Phase 1 tests with coverage and reporting

set -e  # Exit on error

echo "=== NovelWriter LSP - Phase 1 CI Test Suite ==="
echo "Running at $(date)"
echo

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate  # This will be adjusted for Windows

echo "Installing dependencies..."
pip install -r requirements.txt
pip install -e ".[dev]"

echo
echo "=== Running Phase 1 Tests ==="
echo

# Run Phase 1 tests with coverage
pytest tests/phase1/ \
    --cov=novelwriter_lsp.server \
    --cov=novelwriter_lsp.types \
    --cov=novelwriter_lsp.parser \
    --cov=novelwriter_lsp.index \
    --cov=novelwriter_lsp.features.definition \
    --cov=novelwriter_lsp.features.references \
    --cov=novelwriter_lsp.features.symbols \
    --cov-report=term-missing \
    --cov-report=html:coverage-report \
    --cov-report=xml:coverage.xml \
    -v \
    --tb=short

echo
echo "=== Generating Coverage Report ==="

# Generate coverage summary
echo "Coverage Report Summary:"
python -c "
import coverage
cov = coverage.Coverage()
cov.load()
total = cov.report()
print(f'Total Coverage: {total:.1f}%')

# Phase 1 modules specific coverage
modules = [
    'novelwriter_lsp.server',
    'novelwriter_lsp.types', 
    'novelwriter_lsp.parser',
    'novelwriter_lsp.index',
    'novelwriter_lsp.features.definition',
    'novelwriter_lsp.features.references',
    'novelwriter_lsp.features.symbols'
]

phase1_total = 0
phase1_count = 0

for module in modules:
    try:
        percentage = cov.report(module, precision=1)
        phase1_total += percentage
        phase1_count += 1
        print(f'{module}: {percentage:.1f}%')
    except:
        print(f'{module}: No coverage data')

if phase1_count > 0:
    avg_coverage = phase1_total / phase1_count
    print(f'Phase 1 Average Coverage: {avg_coverage:.1f}%')
    
    if avg_coverage >= 80:
        print('✅ Phase 1 Coverage >= 80% - PASSED')
    else:
        print(f'❌ Phase 1 Coverage < 80% - FAILED (required: 80%, actual: {avg_coverage:.1f}%)')
        exit(1)
else:
    print('❌ No coverage data available for Phase 1 modules')
    exit(1)
"

echo
echo "=== Test Results Summary ==="

# Check test results
if [ $? -eq 0 ]; then
    echo "✅ All Phase 1 tests passed!"
    echo "✅ Coverage requirements met!"
    echo
    echo "=== Next Steps ==="
    echo "- Phase 1 is complete!"
    echo "- Ready to start Phase 2: Database Integration"
    echo "- Coverage report available in: coverage-report/index.html"
    echo "- XML coverage report available for CI: coverage.xml"
    exit 0
else
    echo "❌ Phase 1 tests failed!"
    echo "❌ Coverage requirements not met!"
    echo
    echo "Check the test output above for details."
    exit 1
fi