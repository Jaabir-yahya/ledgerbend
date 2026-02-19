"""
Setup verification script.

Checks that everything is properly configured before running the app.
"""
import sys
import requests
import os
from pathlib import Path

def print_header():
    print("=" * 60)
    print("🔍 LedgerBend Frontend Setup Verification")
    print("=" * 60)
    print()

def check_python_version():
    """Check Python version."""
    print("📦 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (requires 3.8+)")
        return False

def check_dependencies():
    """Check if required packages are installed."""
    print("\n📦 Checking dependencies...")
    
    required = [
        "streamlit",
        "pandas",
        "requests",
        "plotly",
        "python-dotenv"
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace("-", "_"))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (missing)")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages. Run: pip install {' '.join(missing)}")
        return False
    return True

def check_environment():
    """Check environment file."""
    print("\n📝 Checking environment configuration...")
    
    env_file = Path(".env")
    if env_file.exists():
        print("   ✅ .env file found")
        
        # Load and check variables
        from dotenv import load_dotenv
        load_dotenv()
        
        api_url = os.getenv("API_BASE_URL", "")
        if api_url:
            print(f"   ✅ API_BASE_URL: {api_url}")
        else:
            print("   ⚠️  API_BASE_URL not set (will use default)")
        
        return True
    else:
        print("   ❌ .env file not found")
        print("   Run: cp .env.example .env")
        return False

def check_backend():
    """Check backend connectivity."""
    print("\n🔌 Checking backend connectivity...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_url = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
    health_url = f"{api_url}/health"
    
    try:
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Backend is running")
            print(f"   Status: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"   ❌ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Cannot connect to backend at {api_url}")
        print("   Make sure the backend is running:")
        print("   cd .. && python main.py")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_file_structure():
    """Check required files exist."""
    print("\n📁 Checking file structure...")
    
    required_files = [
        "app.py",
        "config.py",
        "api_client.py",
        "requirements.txt",
        ".env.example",
        "pages/dashboard.py",
        "pages/transactions.py",
        "pages/ledger.py",
        "pages/accounts.py",
        "pages/parties.py",
        "pages/inventory.py",
        "pages/reports.py",
        "pages/use_cases.py",
    ]
    
    all_exist = True
    for file in required_files:
        path = Path(file)
        if path.exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} (missing)")
            all_exist = False
    
    return all_exist

def main():
    print_header()
    
    results = []
    
    results.append(("Python Version", check_python_version()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("Environment", check_environment()))
    results.append(("File Structure", check_file_structure()))
    results.append(("Backend", check_backend()))
    
    print("\n" + "=" * 60)
    print("📋 Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All checks passed! You're ready to go.")
        print("   Run: streamlit run app.py")
        return 0
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
