#!/bin/bash

# Vertex AI Native Grant Agent Startup Script
# Multi-Agent System (MAS) initialization and service startup

set -e

echo "🚀 Starting Vertex AI Native Grant Agent..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running in virtual environment
check_virtual_env() {
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        print_success "Virtual environment detected: $VIRTUAL_ENV"
    else
        print_warning "No virtual environment detected. Consider using one."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Check dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check Python version
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    required_version="3.9"
    
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
        print_success "Python version $python_version meets requirements (>= $required_version)"
    else
        print_error "Python version $python_version is too old. Requires >= $required_version"
        exit 1
    fi
    
    # Check required Python packages
    required_packages=("fastapi" "uvicorn" "redis" "neo4j" "google-cloud-aiplatform")
    
    for package in "${required_packages[@]}"; do
        if python3 -c "import $package" 2>/dev/null; then
            print_success "$package is installed"
        else
            print_error "$package is not installed"
            print_status "Installing $package..."
            pip install "$package"
        fi
    done
}

# Check external services
check_services() {
    print_status "Checking external services..."
    
    # Check Redis
    if redis-cli ping >/dev/null 2>&1; then
        print_success "Redis is running"
    else
        print_warning "Redis is not running. Starting with Docker..."
        if command -v docker >/dev/null 2>&1; then
            docker run --name redis-grant-agent -p 6379:6379 -d redis:latest >/dev/null 2>&1 || print_warning "Redis container may already exist"
            sleep 2
            if redis-cli ping >/dev/null 2>&1; then
                print_success "Redis started successfully"
            else
                print_error "Failed to start Redis"
                exit 1
            fi
        else
            print_error "Docker not found. Please install Redis manually or install Docker."
            exit 1
        fi
    fi
    
    # Check Neo4j
    if curl -s http://localhost:7474 >/dev/null 2>&1; then
        print_success "Neo4j is running"
    else
        print_warning "Neo4j is not running. Starting with Docker..."
        if command -v docker >/dev/null 2>&1; then
            docker run --name neo4j-grant-agent \
                -p 7474:7474 -p 7687:7687 \
                -d \
                -e NEO4J_AUTH=neo4j/grantpassword \
                neo4j:latest >/dev/null 2>&1 || print_warning "Neo4j container may already exist"
            sleep 10
            if curl -s http://localhost:7474 >/dev/null 2>&1; then
                print_success "Neo4j started successfully"
                print_status "Neo4j credentials: neo4j/grantpassword"
            else
                print_error "Failed to start Neo4j"
                exit 1
            fi
        else
            print_error "Docker not found. Please install Neo4j manually or install Docker."
            exit 1
        fi
    fi
}

# Check Google Cloud authentication
check_gcp_auth() {
    print_status "Checking Google Cloud authentication..."
    
    if gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 >/dev/null 2>&1; then
        active_account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1)
        print_success "Authenticated with Google Cloud as: $active_account"
    else
        print_warning "Not authenticated with Google Cloud"
        print_status "Please run: gcloud auth login"
        exit 1
    fi
    
    # Check if project is set
    project=$(gcloud config get-value project 2>/dev/null)
    if [[ -n "$project" ]]; then
        print_success "Google Cloud project: $project"
    else
        print_warning "No Google Cloud project set"
        print_status "Please run: gcloud config set project YOUR_PROJECT_ID"
        exit 1
    fi
}

# Check configuration
check_config() {
    print_status "Checking configuration..."
    
    if [[ -f "config.env" ]]; then
        print_success "Configuration file found: config.env"
        
        # Check critical environment variables
        source config.env
        
        critical_vars=("GOOGLE_CLOUD_PROJECT" "NEO4J_PASSWORD")
        for var in "${critical_vars[@]}"; do
            if [[ -n "${!var}" ]]; then
                print_success "$var is configured"
            else
                print_warning "$var is not configured in config.env"
            fi
        done
    else
        print_error "Configuration file not found: config.env"
        print_status "Creating default configuration..."
        
        cat > config.env << EOF
# Google Vertex AI Native Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_REGION=us-central1
VERTEX_AI_MODEL=gemini-1.5-pro
VERTEX_AI_FAST_MODEL=gemini-1.5-flash

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=grantpassword

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Service Configuration
ARTIFACT_STORAGE_BACKEND=local
DOC_TEMP_STORAGE_PATH=/tmp/grant_docs
MAX_CONCURRENT_REQUESTS=50

# Logging
LOG_LEVEL=INFO
EOF
        
        print_success "Default configuration created. Please edit config.env with your settings."
        exit 1
    fi
}

# Initialize directories
init_directories() {
    print_status "Initializing directories..."
    
    directories=("/tmp/grant_docs" "logs" "output" "uploads")
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            print_success "Created directory: $dir"
        fi
    done
}

# Main startup function
start_service() {
    print_status "Starting Vertex AI Grant Agent service..."
    
    # Set environment variables
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    
    # Start the service
    python3 vertex_grant_agent.py
}

# Health check function
health_check() {
    print_status "Performing health check..."
    
    # Wait for service to start
    sleep 5
    
    # Check if service is responding
    if curl -s http://localhost:8080/health >/dev/null 2>&1; then
        print_success "Service is healthy and responding"
        
        # Display service info
        echo
        echo "=================================================="
        echo "🎉 Vertex AI Grant Agent is running!"
        echo "=================================================="
        echo "Service URL: http://localhost:8080"
        echo "Health Check: http://localhost:8080/health"
        echo "API Documentation: http://localhost:8080/docs"
        echo "=================================================="
        echo
        echo "📚 API Endpoints:"
        echo "• POST /upload_documents - Upload documents"
        echo "• POST /generate_grant_proposal - Generate proposals"
        echo "• GET /health - Service health status"
        echo
        echo "📊 External Services:"
        echo "• Redis: localhost:6379"
        echo "• Neo4j: http://localhost:7474 (UI)"
        echo "• Neo4j Bolt: bolt://localhost:7687"
        echo
        echo "🛑 To stop the service: Ctrl+C"
        echo "=================================================="
    else
        print_error "Service health check failed"
        exit 1
    fi
}

# Main execution
main() {
    print_status "Vertex AI Native Grant Agent - Multi-Agent System (MAS)"
    echo
    
    # Run checks
    check_virtual_env
    check_dependencies
    check_services
    check_gcp_auth
    check_config
    init_directories
    
    print_success "All checks passed! Starting service..."
    echo
    
    # Start service in background for health check
    start_service &
    SERVICE_PID=$!
    
    # Perform health check
    health_check
    
    # Wait for the service process
    wait $SERVICE_PID
}

# Trap for cleanup
cleanup() {
    print_status "Shutting down service..."
    if [[ -n "${SERVICE_PID}" ]]; then
        kill $SERVICE_PID 2>/dev/null || true
    fi
    print_success "Service stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Run main function
main "$@" 