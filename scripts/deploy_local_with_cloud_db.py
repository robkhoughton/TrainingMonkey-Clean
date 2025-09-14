#!/usr/bin/env python3
"""
Local Deployment Script with Cloud Database Connection
This script sets up and runs the Training Monkey app locally with direct connection to the cloud database.
Includes the new ACWR configuration features we just implemented.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_step(step_num, description):
    """Print a formatted step"""
    print(f"\n🔧 Step {step_num}: {description}")
    print("-" * 40)

def run_command(command, cwd=None, check=True):
    """Run a command and return the result"""
    print(f"Running: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            check=check, 
            capture_output=True, 
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def check_prerequisites():
    """Check if all prerequisites are installed"""
    print_step(1, "Checking Prerequisites")
    
    # Check Python
    try:
        result = run_command("python --version", check=False)
        if result.returncode == 0:
            print("✅ Python is installed")
        else:
            print("❌ Python is not installed or not in PATH")
            return False
    except:
        print("❌ Python is not installed or not in PATH")
        return False
    
    # Check Node.js
    try:
        result = run_command("node --version", check=False)
        if result.returncode == 0:
            print("✅ Node.js is installed")
        else:
            print("❌ Node.js is not installed or not in PATH")
            return False
    except:
        print("❌ Node.js is not installed or not in PATH")
        return False
    
    # Check npm
    try:
        result = run_command("npm --version", check=False)
        if result.returncode == 0:
            print("✅ npm is installed")
        else:
            print("❌ npm is not installed or not in PATH")
            return False
    except:
        print("❌ npm is not installed or not in PATH")
        return False
    
    return True

def setup_database_connection():
    """Set up database connection to cloud database"""
    print_step(2, "Setting up Cloud Database Connection")
    
    # Check if .env file exists
    app_dir = Path(__file__).parent.parent / "app"
    env_file = app_dir / ".env"
    
    if not env_file.exists():
        print("📋 .env file not found. Running database connection setup...")
        setup_script = Path(__file__).parent / "setup_local_database_connection.py"
        if setup_script.exists():
            run_command(f"python {setup_script}", cwd=Path(__file__).parent)
        else:
            print("❌ Database setup script not found!")
            return False
    else:
        print("✅ .env file already exists")
    
    # Test database connection
    print("\n🔍 Testing database connection...")
    test_script = Path(__file__).parent / "test_database_connection.py"
    if test_script.exists():
        result = run_command(f"python {test_script}", cwd=app_dir, check=False)
        if result.returncode == 0:
            print("✅ Database connection successful")
        else:
            print("❌ Database connection failed")
            return False
    else:
        print("⚠️  Database test script not found, skipping test")
    
    return True

def check_database_tables():
    """Check if required database tables exist (following project database rules)"""
    print_step(3, "Checking Database Tables")
    
    app_dir = Path(__file__).parent.parent / "app"
    
    print("📋 Checking if user_dashboard_configs table exists...")
    try:
        # Import database utilities
        sys.path.insert(0, str(app_dir))
        from db_utils import execute_query
        
        # Check if table exists
        execute_query("SELECT 1 FROM user_dashboard_configs LIMIT 1;")
        print("✅ user_dashboard_configs table exists in cloud database")
        return True
        
    except Exception as e:
        print("⚠️  user_dashboard_configs table not found in cloud database")
        print()
        print("📋 To create the table, run this SQL in your cloud database SQL Editor:")
        print("   File: sql/user_dashboard_configs.sql")
        print()
        print("💡 According to project database rules, table creation should be done")
        print("   manually via SQL Editor, not automatically in code.")
        return False

def install_dependencies():
    """Install Python and Node.js dependencies"""
    print_step(4, "Installing Dependencies")
    
    project_root = Path(__file__).parent.parent
    
    # Install Python dependencies
    print("📦 Installing Python dependencies...")
    requirements_file = project_root / "app" / "strava_requirements.txt"
    if requirements_file.exists():
        run_command(f"pip install -r {requirements_file}")
        print("✅ Python dependencies installed")
    else:
        print("⚠️  Python requirements file not found")
    
    # Install Node.js dependencies
    print("\n📦 Installing Node.js dependencies...")
    frontend_dir = project_root / "frontend"
    if frontend_dir.exists():
        run_command("npm install", cwd=frontend_dir)
        print("✅ Node.js dependencies installed")
    else:
        print("❌ Frontend directory not found")
        return False
    
    return True

def build_frontend():
    """Build the React frontend"""
    print_step(5, "Building React Frontend")
    
    project_root = Path(__file__).parent.parent
    frontend_dir = project_root / "frontend"
    
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    # Clean previous build
    print("🧹 Cleaning previous build...")
    build_dir = frontend_dir / "build"
    if build_dir.exists():
        import shutil
        shutil.rmtree(build_dir)
    
    # Build React app
    print("🔨 Building React app...")
    run_command("npm run build", cwd=frontend_dir)
    print("✅ React app built successfully")
    
    # Copy build files to app directory
    print("📁 Copying build files to app directory...")
    app_build_dir = project_root / "app" / "build"
    if app_build_dir.exists():
        import shutil
        shutil.rmtree(app_build_dir)
    
    import shutil
    shutil.copytree(build_dir, app_build_dir)
    print("✅ Build files copied to app directory")
    
    return True

def start_development_server():
    """Start the Flask development server"""
    print_step(6, "Starting Development Server")
    
    app_dir = Path(__file__).parent.parent / "app"
    
    print("🚀 Starting Flask development server...")
    print("\n" + "=" * 60)
    print(" Training Monkey - Local Development Server")
    print("=" * 60)
    print("\n📱 Available URLs:")
    print("  • Landing Page:  http://localhost:5000/landing")
    print("  • Login Page:    http://localhost:5000/login")
    print("  • Dashboard:     http://localhost:5000/dashboard")
    print("  • Parameter Viz: http://localhost:5000/acwr-visualization")
    print("\n🆕 New Features Available:")
    print("  • Overtraining Risk Over Time chart on dashboard")
    print("  • Configurable ACWR parameters")
    print("  • Apply custom config to dashboard from Parameter Visualization")
    print("\n⚙️  Configuration:")
    print("  • Connected to: Google Cloud PostgreSQL")
    print("  • Environment:  Development")
    print("  • Debug Mode:   Enabled")
    print("\n" + "=" * 60)
    print("Press Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    # Start the server
    try:
        run_command("python run_flask.py", cwd=app_dir, check=False)
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")

def main():
    """Main deployment function"""
    print_header("Training Monkey - Local Deployment with Cloud Database")
    
    print("This script will:")
    print("1. Check prerequisites (Python, Node.js, npm)")
    print("2. Set up cloud database connection")
    print("3. Check database tables")
    print("4. Install dependencies")
    print("5. Build React frontend")
    print("6. Start development server")
    
    response = input("\nProceed with deployment? (Y/n): ").strip().lower()
    if response not in ['', 'y', 'yes']:
        print("Deployment cancelled.")
        return
    
    # Run deployment steps
    if not check_prerequisites():
        print("❌ Prerequisites check failed")
        return
    
    if not setup_database_connection():
        print("❌ Database connection setup failed")
        return
    
    if not check_database_tables():
        print("⚠️  Required database table not found - you may need to create it manually")
        print("   See sql/user_dashboard_configs.sql for the table definition")
        print("   According to project database rules, table creation should be done via SQL Editor")
    
    if not install_dependencies():
        print("❌ Dependency installation failed")
        return
    
    if not build_frontend():
        print("❌ Frontend build failed")
        return
    
    # Start the server
    start_development_server()

if __name__ == "__main__":
    main()
