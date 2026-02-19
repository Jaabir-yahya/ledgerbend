#!/bin/bash

# LedgerBend Frontend Startup Script
# Usage: ./start.sh [command]

set -e

FRONTEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║           LedgerBend Streamlit Frontend                    ║"
    echo "║         Universal Double-Entry Ledger                      ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is not installed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Python 3 found${NC}"
}

check_backend() {
    echo -e "${YELLOW}🔍 Checking backend...${NC}"
    if curl -s http://localhost:8000/api/v1/health > /dev/null; then
        echo -e "${GREEN}✅ Backend is running${NC}"
        return 0
    else
        echo -e "${RED}⚠️  Backend is not responding${NC}"
        echo -e "${YELLOW}   Please start the backend first:${NC}"
        echo -e "   cd .. && python main.py"
        return 1
    fi
}

install_deps() {
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    pip install -q -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
}

copy_env() {
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}📝 Creating .env file...${NC}"
        cp .env.example .env
        echo -e "${GREEN}✅ .env file created${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env with your settings${NC}"
    fi
}

run_app() {
    echo -e "${YELLOW}🚀 Starting Streamlit...${NC}"
    echo -e "${BLUE}   URL: http://localhost:8501${NC}"
    echo ""
    streamlit run app.py
}

run_demo() {
    echo -e "${YELLOW}🎯 Loading demo data...${NC}"
    python init_demo_data.py
}

run_verify() {
    echo -e "${YELLOW}🔍 Verifying setup...${NC}"
    python verify_setup.py
}

show_help() {
    echo "Usage: ./start.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start    - Start the Streamlit app (default)"
    echo "  install  - Install dependencies"
    echo "  demo     - Load demo data"
    echo "  verify   - Verify setup and backend connectivity"
    echo "  help     - Show this help"
    echo ""
    echo "Examples:"
    echo "  ./start.sh              # Start the app"
    echo "  ./start.sh install      # Install dependencies"
    echo "  ./start.sh demo         # Load demo data"
}

# Main
print_header
cd "$FRONTEND_DIR"

# Check if .env exists, if not copy example
copy_env

# Parse command
case "${1:-start}" in
    start)
        check_python
        check_backend || true  # Don't fail if backend is not running
        run_app
        ;;
    install)
        check_python
        install_deps
        echo -e "${GREEN}✅ Installation complete${NC}"
        ;;
    demo)
        check_python
        check_backend || exit 1
        run_demo
        ;;
    verify)
        check_python
        run_verify
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac
