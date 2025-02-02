# Testing Guidelines

## Core Principles

1. **Unit Test Isolation**
   - Each unit test MUST test only one unit of functionality in isolation
   - All external dependencies MUST be mocked
   - Tests should be independent and repeatable

2. **What Must Be Mocked**
   - External API calls
   - Database operations
   - File system operations
   - Network requests
   - Time-dependent operations
   - Random number generation
   - Environment variables
   - Configuration files

## Implementation Examples

### 1. API Client Testing

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

class TestExternalAPIClient:
    @patch('requests.post')  # Mock external HTTP requests
    @patch('time.time')      # Mock time-dependent operations
    def test_api_call(self, mock_time, mock_post):
        """Test API client with proper mocking."""
        # Arrange
        mock_time.return_value = 1234567890
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        client = ExternalAPIClient()
        
        # Act
        result = client.make_request({"data": "test"})
        
        # Assert
        assert result["status"] == "success"
        mock_post.assert_called_once_with(
            "https://api.example.com",
            json={"data": "test"}
        )
```

### 2. File Operations Testing

```python
class TestFileProcessor:
    @patch('builtins.open', new_callable=mock_open)  # Mock file operations
    @patch('os.path.exists')                         # Mock file system checks
    def test_process_file(self, mock_exists, mock_file):
        """Test file processing with mocked file system."""
        # Arrange
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = "test data"
        
        processor = FileProcessor()
        
        # Act
        result = processor.process("test.txt")
        
        # Assert
        assert result == "PROCESSED: test data"
        mock_exists.assert_called_once_with("test.txt")
        mock_file.assert_called_once_with("test.txt", "r")
```

### 3. Database Operations Testing

```python
class TestDatabaseOperations:
    @patch('sqlalchemy.create_engine')  # Mock database engine
    def test_db_query(self, mock_engine):
        """Test database operations with mocked connection."""
        # Arrange
        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [{"id": 1, "name": "test"}]
        mock_connection.execute.return_value = mock_result
        mock_engine.return_value.connect.return_value = mock_connection
        
        db = Database()
        
        # Act
        results = db.query("SELECT * FROM users")
        
        # Assert
        assert len(results) == 1
        assert results[0]["name"] == "test"
```

## Best Practices

### 1. Mock Types and Usage

```python
# 1. Basic Mock
mock = Mock()
mock.method.return_value = "result"

# 2. MagicMock (more permissive)
mock = MagicMock()
mock.__str__.return_value = "string representation"

# 3. AsyncMock (for async functions)
mock = AsyncMock()
mock.async_method.return_value = "result"

# 4. PropertyMock (for properties)
with patch('MyClass.property_name', new_callable=PropertyMock) as mock_property:
    mock_property.return_value = "value"
```

### 2. Mocking Best Practices

```python
# GOOD: Mock at the correct level
@patch('module.requests.post')
def test_api_call(mock_post):
    mock_post.return_value = Mock(status_code=200)
    
# BAD: Don't mock built-in types
@patch('str.lower')  # Don't do this!
def test_string_processing(mock_lower):
    pass

# GOOD: Use spec for type safety
mock_client = Mock(spec=ApiClient)
```

### 3. Test Structure

```python
class TestUserService:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup fresh mocks for each test."""
        self.mock_db = Mock(spec=Database)
        self.mock_cache = Mock(spec=Cache)
        self.service = UserService(
            db=self.mock_db,
            cache=self.mock_cache
        )
    
    def test_user_creation(self):
        """Follow Arrange-Act-Assert pattern."""
        # Arrange
        user_data = {"name": "Test User"}
        self.mock_db.insert.return_value = {"id": 1, **user_data}
        
        # Act
        result = self.service.create_user(user_data)
        
        # Assert
        assert result["id"] == 1
        assert result["name"] == "Test User"
        self.mock_db.insert.assert_called_once_with(user_data)
```

### 4. Error Testing

```python
def test_api_error_handling():
    """Always test error scenarios."""
    with patch('requests.post') as mock_post:
        # Arrange
        mock_post.side_effect = RequestException("Network error")
        client = ApiClient()
        
        # Act & Assert
        with pytest.raises(ApiError) as exc_info:
            client.make_request({})
        assert str(exc_info.value) == "API request failed: Network error"
```

## What NOT to Mock

1. **Built-in Types**: Never mock `str`, `int`, `list`, etc.
2. **Pure Functions**: Don't mock functions with no external dependencies
3. **The System Under Test**: Don't mock the actual code you're testing

```python
# BAD: Don't mock the system under test
@patch.object(UserService, 'validate_user')  # Wrong!
def test_user_service(mock_validate):
    service = UserService()
    
# GOOD: Mock only dependencies
def test_user_service():
    mock_db = Mock(spec=Database)
    service = UserService(db=mock_db)
```

## Test Data Management

### 1. Factories

```python
@pytest.fixture
def user_factory():
    """Create test users with custom attributes."""
    def create_user(**kwargs):
        default_data = {
            "id": 1,
            "name": "Test User",
            "email": "test@example.com"
        }
        return User(**{**default_data, **kwargs})
    return create_user

def test_user_processing(user_factory):
    user = user_factory(name="Custom Name")
    assert user.name == "Custom Name"
```

### 2. Constants

```python
# test_constants.py
TEST_USER_ID = "test-user-123"
TEST_EMAIL = "test@example.com"
TEST_API_KEY = "test-api-key-456"

def test_user_authentication():
    with patch('os.getenv') as mock_env:
        mock_env.return_value = TEST_API_KEY
        # Test implementation
```

## Verification and Assertions

```python
def test_with_verification():
    """Verify mock interactions thoroughly."""
    mock = Mock()
    
    # Act
    system_under_test.process(mock)
    
    # Assert calls
    mock.method.assert_called_once()
    mock.other_method.assert_not_called()
    
    # Assert call arguments
    mock.method.assert_called_once_with(expected_arg)
    
    # Assert call order
    assert mock.mock_calls == [
        call.method(expected_arg),
        call.other_method()
    ]
``` 