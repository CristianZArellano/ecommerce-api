# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Project Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Database setup
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Testing
```bash
# Run all tests
python manage.py test

# Run specific test class
python manage.py test store.tests.ProductViewSetTests

# Run with verbosity
python manage.py test --verbosity=2
```

### Database Management
```bash
# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database (for development)
rm db.sqlite3 test_db.sqlite3
python manage.py migrate
```

## Architecture Overview

This is a Django REST Framework e-commerce API with the following key architectural patterns:

### Core Structure
- **Django Project**: `ecommerce_api/` - Main project configuration
- **Main App**: `store/` - Contains all e-commerce models, views, and business logic
- **Database**: SQLite (development) - Uses `test_db.sqlite3` as configured in settings

### Key Architectural Patterns

#### 1. Caching System with CachingMixin
The codebase implements a sophisticated caching system using a reusable `CachingMixin` class:

- **Location**: `store/views.py:27-176`
- **Purpose**: Provides automatic caching for `list` and `retrieve` operations
- **Cache Keys**: Uses structured keys like `{base_key}_list:` and `{base_key}_detail:{id}`
- **Invalidation**: Automatically invalidates cache on CUD operations
- **Bypass Logic**: Skips cache when search/filter parameters are present

#### 2. Permission System with AdminOrReadOnlyViewSet
- **Location**: `store/views.py:178-193`
- **Pattern**: Public read access, admin-only write access
- **Implementation**: Uses `IsAuthenticatedOrReadOnly` for GET, `IsAdminUser` for CUD operations

#### 3. Serializer Strategy
- **List vs Detail**: Uses different serializers for list (`ProductListSerializer`) vs detail (`ProductDetailSerializer`) views
- **Performance**: List serializer includes only essential fields for optimal performance
- **Relationships**: Uses `SlugRelatedField` for category relationships

### Data Models

#### Core Models (store/models.py)
- **Category**: Product categories with slug auto-generation and cascade deletion protection
- **Product**: Main product model with pricing, inventory, and relationship management
- **Order**: Customer orders with status tracking
- **OrderItem**: Individual items within orders

#### Key Model Features
- **Slug Auto-generation**: Both Category and Product models auto-generate slugs from names
- **Validation**: Custom validation for prices, quantities, and business rules
- **Indexes**: Comprehensive database indexing for performance
- **Deletion Protection**: Prevents deletion of entities with related OrderItems

### API Endpoints Structure

#### Categories API (`/api/categories/`)
- Standard CRUD operations
- Only shows active categories (`is_active=True`)
- Cached responses for performance

#### Products API (`/api/products/`)
- Standard CRUD operations with filtering and search
- Special endpoints:
  - `/api/products/featured/` - Featured products
  - `/api/products/discounted/` - Products with discounts
  - `/api/products/reports/` - Sales and analytics reports
- Search across: name, description, SKU
- Filter by: category slug
- Order by: price, stock

#### Reports System
- **Location**: `store/views.py:292-378`
- **Types**: `sales_by_category`, `profit_margin`, `combined`
- **Performance**: Uses raw SQL for complex aggregations
- **Access**: Admin-only functionality

## Development Guidelines

### Cache Management
- Cache keys are automatically managed by the `CachingMixin`
- Manual cache invalidation is handled in `_invalidate_related_caches()` method
- Cache TTL is configurable via `CACHE_TTL` setting (default: 5 minutes)

### Testing Patterns
- **Base Class**: `BaseAPITestCase` provides common test data setup
- **Cache Testing**: Uses `unittest.mock.patch` for cache behavior verification
- **Permission Testing**: Comprehensive tests for anonymous, regular user, and admin access
- **Unique Constraints**: Uses `time.time()` and `uuid.uuid4()` for unique test data

### Model Relationships
- **Category → Product**: One-to-many with `PROTECT` on delete
- **Product → OrderItem**: One-to-many with `PROTECT` on delete
- **Order → OrderItem**: One-to-many with `CASCADE` on delete

### Performance Considerations
- Uses `select_related('category')` in Product querysets
- Database indexes on frequently queried fields
- Raw SQL queries for complex reporting
- Conditional caching based on query parameters

## Configuration Notes

### Django Settings Key Points
- **Database**: Uses `test_db.sqlite3` (not standard `db.sqlite3`)
- **Cache Backend**: `django.core.cache.backends.locmem.LocMemCache`
- **DRF Authentication**: Session + Basic authentication
- **Logging**: Configured for DEBUG level with console output

### URL Configuration
- **API Root**: `/api/`
- **Admin**: `/admin/`
- **DRF Auth**: `/api-auth/`

## Common Development Tasks

### Adding New Models
1. Define model in `store/models.py`
2. Create serializer in `store/serializers.py`
3. Add ViewSet in `store/views.py` (inherit from `CachingMixin` and `AdminOrReadOnlyViewSet`)
4. Register in `store/urls.py` router
5. Run migrations

### Modifying Cache Behavior
- Override `_invalidate_related_caches()` method in ViewSet
- Adjust `get_cache_key_list()` or `get_cache_key_detail()` for custom cache keys
- Update `CACHE_TTL` in settings for different timeout

### Adding New API Endpoints
- Use `@action` decorator for custom endpoints
- Follow existing patterns for caching custom endpoints
- Add appropriate permission checks
- Include comprehensive tests

## Security Notes
- **Secret Key**: Currently uses development secret key (change for production)
- **Debug Mode**: Enabled for development
- **CSRF Protection**: Enabled via middleware
- **Admin Access**: Required for all CUD operations on products/categories