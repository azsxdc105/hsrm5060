#!/bin/bash

# Claims Management System Deployment Script
# Usage: ./deploy.sh [command]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="claims-management"
DOCKER_COMPOSE_FILE="docker-compose.yml"
BACKUP_DIR="./backups"
LOG_DIR="./logs"

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

# Check if Docker and Docker Compose are installed
check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    log_success "Dependencies check passed"
}

# Create necessary directories
setup_directories() {
    log_info "Setting up directories..."
    
    mkdir -p $BACKUP_DIR
    mkdir -p $LOG_DIR
    mkdir -p uploads
    mkdir -p ssl
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/datasources
    mkdir -p scripts
    
    log_success "Directories created"
}

# Generate environment file
generate_env() {
    log_info "Generating environment configuration..."
    
    if [ ! -f .env ]; then
        cat > .env << EOF
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Database Configuration
DATABASE_URL=postgresql://claims_user:claims_password@db:5432/claims_db
POSTGRES_DB=claims_db
POSTGRES_USER=claims_user
POSTGRES_PASSWORD=$(openssl rand -hex 16)

# Cache Configuration
CACHE_TYPE=RedisCache
CACHE_REDIS_URL=redis://redis:6379/0

# Email Configuration (Update with your SMTP settings)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# SMS Configuration (Optional)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=your-twilio-number

# Google Cloud Vision (Optional)
GOOGLE_APPLICATION_CREDENTIALS=/app/google-credentials.json

# Monitoring
GRAFANA_ADMIN_PASSWORD=$(openssl rand -hex 16)
EOF
        log_success "Environment file created (.env)"
        log_warning "Please update the .env file with your actual configuration values"
    else
        log_info "Environment file already exists"
    fi
}

# Build and start services
deploy() {
    log_info "Deploying $APP_NAME..."
    
    check_dependencies
    setup_directories
    generate_env
    
    # Build and start services
    log_info "Building Docker images..."
    docker-compose -f $DOCKER_COMPOSE_FILE build
    
    log_info "Starting services..."
    docker-compose -f $DOCKER_COMPOSE_FILE up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Initialize database
    log_info "Initializing database..."
    docker-compose exec app python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
    
    # Run database optimization
    log_info "Optimizing database..."
    docker-compose exec app python quick_optimize.py
    
    # Seed initial data
    log_info "Seeding initial data..."
    docker-compose exec app python seed_data.py
    
    log_success "Deployment completed successfully!"
    log_info "Application is available at: http://localhost"
    log_info "Grafana dashboard: http://localhost:3000 (admin/admin123)"
    log_info "Prometheus: http://localhost:9090"
}

# Stop services
stop() {
    log_info "Stopping services..."
    docker-compose -f $DOCKER_COMPOSE_FILE down
    log_success "Services stopped"
}

# Restart services
restart() {
    log_info "Restarting services..."
    docker-compose -f $DOCKER_COMPOSE_FILE restart
    log_success "Services restarted"
}

# View logs
logs() {
    if [ -n "$2" ]; then
        docker-compose -f $DOCKER_COMPOSE_FILE logs -f "$2"
    else
        docker-compose -f $DOCKER_COMPOSE_FILE logs -f
    fi
}

# Backup database
backup() {
    log_info "Creating database backup..."
    
    BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
    
    docker-compose exec db pg_dump -U claims_user claims_db > "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        log_success "Database backup created: $BACKUP_FILE"
    else
        log_error "Database backup failed"
        exit 1
    fi
}

# Restore database
restore() {
    if [ -z "$2" ]; then
        log_error "Please specify backup file: ./deploy.sh restore <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$2" ]; then
        log_error "Backup file not found: $2"
        exit 1
    fi
    
    log_warning "This will replace the current database. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        log_info "Restoring database from: $2"
        docker-compose exec -T db psql -U claims_user -d claims_db < "$2"
        log_success "Database restored successfully"
    else
        log_info "Restore cancelled"
    fi
}

# Update application
update() {
    log_info "Updating application..."
    
    # Pull latest changes (if using git)
    if [ -d ".git" ]; then
        git pull
    fi
    
    # Rebuild and restart
    docker-compose -f $DOCKER_COMPOSE_FILE build
    docker-compose -f $DOCKER_COMPOSE_FILE up -d
    
    log_success "Application updated successfully"
}

# Show status
status() {
    log_info "Service status:"
    docker-compose -f $DOCKER_COMPOSE_FILE ps
    
    log_info "Health checks:"
    curl -s http://localhost/health && echo " - Nginx: OK" || echo " - Nginx: FAIL"
    curl -s http://localhost:5000/admin/health && echo " - App: OK" || echo " - App: FAIL"
}

# Clean up
cleanup() {
    log_warning "This will remove all containers, images, and volumes. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        log_info "Cleaning up..."
        docker-compose -f $DOCKER_COMPOSE_FILE down -v --rmi all
        docker system prune -f
        log_success "Cleanup completed"
    else
        log_info "Cleanup cancelled"
    fi
}

# Show help
show_help() {
    echo "Claims Management System Deployment Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  deploy    - Deploy the application (build and start all services)"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  logs      - View logs (optionally specify service name)"
    echo "  backup    - Create database backup"
    echo "  restore   - Restore database from backup file"
    echo "  update    - Update application (pull changes and rebuild)"
    echo "  status    - Show service status and health"
    echo "  cleanup   - Remove all containers, images, and volumes"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy"
    echo "  $0 logs app"
    echo "  $0 restore backups/backup_20231201_120000.sql"
}

# Main script logic
case "$1" in
    deploy)
        deploy
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs "$@"
        ;;
    backup)
        backup
        ;;
    restore)
        restore "$@"
        ;;
    update)
        update
        ;;
    status)
        status
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
