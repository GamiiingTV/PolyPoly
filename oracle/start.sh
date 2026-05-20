#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$SCRIPT_DIR"

echo ""
echo "  ╔═══════════════════════════════════════════════╗"
echo "  ║         O • R • A • C • L • E                ║"
echo "  ║  Orchestrated Research Agents for             ║"
echo "  ║  Collective Learning and Exploration          ║"
echo "  ╚═══════════════════════════════════════════════╝"
echo ""

# Load .env if present
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

# Install Python dependencies
echo "▶ Installing Python dependencies..."
pip install -r "$SCRIPT_DIR/requirements.txt" -q
echo "  ✓ Dependencies ready"

# Build frontend if Node.js is available
if command -v node &>/dev/null; then
    echo "▶ Building React dashboard..."
    cd "$SCRIPT_DIR/frontend"
    npm install -q
    npm run build -q
    cd "$SCRIPT_DIR"
    echo "  ✓ Dashboard built successfully"
else
    echo "▶ Node.js not found — start frontend separately:"
    echo "  cd oracle/frontend && npm install && npm run dev"
fi

# Start backend
echo ""
echo "▶ Launching O.R.A.C.L.E..."
echo ""
echo "  Dashboard:  http://localhost:8000"
echo "  API docs:   http://localhost:8000/docs"
echo "  WebSocket:  ws://localhost:8000/ws/dashboard"
echo ""

cd "$REPO_ROOT"
python -m uvicorn oracle.backend.main:app --host 0.0.0.0 --port 8000
