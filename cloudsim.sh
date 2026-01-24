#!/bin/bash

# CloudSim - Local Cloud Lab Platform
# Command-line controller for managing CloudSim services

# Function to print welcome banner
print_banner() {
    echo "=========================================="
    echo "    CloudSim Platform Controller"
    echo "    Local Cloud Computing Lab"
    echo "=========================================="
    echo ""
}

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null
    then
        echo "✗ ERROR: Docker is not installed"
        echo ""
        echo "Docker is required to run CloudSim."
        echo "Please install Docker from: https://docs.docker.com/get-docker/"
        echo ""
        exit 1
    fi
}

# Function to check if Docker Compose is installed
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null
    then
        echo "✗ ERROR: Docker Compose is not installed"
        echo ""
        echo "Docker Compose is required to run CloudSim."
        echo "Please install Docker Compose from: https://docs.docker.com/compose/install/"
        echo ""
        exit 1
    fi
}

# Function to start CloudSim services
start_services() {
    echo "Starting CloudSim services..."
    echo ""
    
    # Start services in detached mode
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✓ CloudSim services started successfully!"
        echo ""
        echo "Access points:"
        echo "  - LocalStack API: http://localhost:4566"
        echo "  - MinIO Console:  http://localhost:9001"
        echo ""
    else
        echo ""
        echo "✗ Failed to start CloudSim services"
        exit 1
    fi
}

# Function to stop CloudSim services
stop_services() {
    echo "Stopping CloudSim services..."
    echo ""
    
    # Stop all services
    docker-compose down
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✓ CloudSim services stopped successfully!"
        echo ""
    else
        echo ""
        echo "✗ Failed to stop CloudSim services"
        exit 1
    fi
}

# Function to show service status
show_status() {
    echo "CloudSim Service Status:"
    echo ""
    
    # Show running containers
    docker-compose ps
    
    echo ""
}

# Function to show usage instructions
show_usage() {
    echo "Usage: ./cloudsim.sh [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start    Start CloudSim services"
    echo "  stop     Stop CloudSim services"
    echo "  status   Show running CloudSim containers"
    echo ""
    echo "Examples:"
    echo "  ./cloudsim.sh start"
    echo "  ./cloudsim.sh status"
    echo "  ./cloudsim.sh stop"
    echo ""
}

# Main script execution starts here
print_banner

# Check system requirements
check_docker
check_docker_compose

# Get the command from first argument
COMMAND=$1

# Execute command based on user input
case $COMMAND in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    status)
        show_status
        ;;
    *)
        # No command or invalid command provided
        show_usage
        exit 1
        ;;
esac
