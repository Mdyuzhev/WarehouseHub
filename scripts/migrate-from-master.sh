#!/bin/bash
# =============================================================================
# Миграция тестовых компонентов из warehouse-master
# =============================================================================

set -e

MASTER_DIR="/home/flomaster/warehouse-master"
TESTING_DIR="/home/flomaster/warehouse-testing"

echo "Migrating test components from warehouse-master..."

# E2E Tests
echo "[1/6] Copying e2e-tests..."
cp -r "$MASTER_DIR/e2e-tests" "$TESTING_DIR/"

# UI Tests
echo "[2/6] Copying ui-tests..."
cp -r "$MASTER_DIR/ui-tests" "$TESTING_DIR/"

# Load Tests
echo "[3/6] Copying loadtest..."
cp -r "$MASTER_DIR/loadtest" "$TESTING_DIR/"

# K8s manifests for load testing
echo "[4/6] Copying k8s/loadtest..."
mkdir -p "$TESTING_DIR/k8s"
cp -r "$MASTER_DIR/k8s/loadtest" "$TESTING_DIR/k8s/"

# Infrastructure
echo "[5/6] Copying infrastructure (selenoid, allure)..."
mkdir -p "$TESTING_DIR/infrastructure"
cp -r "$MASTER_DIR/selenoid" "$TESTING_DIR/infrastructure/"
cp -r "$MASTER_DIR/allure" "$TESTING_DIR/infrastructure/"

# Create .gitkeep for empty dirs
echo "[6/6] Creating .gitkeep files..."
touch "$TESTING_DIR/infrastructure/selenoid/video/.gitkeep" 2>/dev/null || true
touch "$TESTING_DIR/infrastructure/selenoid/logs/.gitkeep" 2>/dev/null || true

echo ""
echo "Migration complete!"
echo ""
echo "Next steps:"
echo "1. cd $TESTING_DIR"
echo "2. git init"
echo "3. git add ."
echo "4. git commit -m 'Initial commit: migrate testing from warehouse-master'"
echo "5. Create repo in GitLab: http://192.168.1.74:8080/root/warehouse-testing"
echo "6. git remote add origin http://192.168.1.74:8080/root/warehouse-testing.git"
echo "7. git push -u origin main"
