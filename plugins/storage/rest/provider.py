"""REST Store Module.

This module provides a high-level interface for REST API storage operations,
abstracting away the underlying HTTP implementation details.

Example:
    >>> from pepperpy.storage import RESTStore, StorageProvider
    >>> provider = StorageProvider.from_config({
    ...     "provider": "rest",
    ...     "base_url": "https://api.example.com"
    ... })
    >>> store = RESTStore(provider)
    >>> store.put("users/123", {"name": "Alice"})
"""

from typing import Any, Dict, List, Optional

from pepperpy.core.validation import ValidationError

from .provider import StorageError, StorageProvider


class RESTStore:
    """High-level interface for REST API storage.

    This class provides a simplified interface for storing and retrieving
    data using REST APIs, with support for different HTTP methods and
    content types.

    Args:
        provider: Storage provider instance
        base_path: Optional base path for requests
        **kwargs: Additional store options
            - headers: Default headers
            - timeout: Request timeout
            - verify_ssl: Whether to verify SSL certificates

    Example:
        >>> store = RESTStore(provider, base_path="/api/v1")
        >>> store.put("users", {"name": "Alice"})
        >>> user = store.get("users/123")
    """

    def __init__(
        self,
        provider: StorageProvider,
        base_path: Optional[str] = None,
        **kwargs: Any,
    ):
        """Initialize the REST store.

        Args:
            provider: Storage provider instance
            base_path: Optional base path for requests
            **kwargs: Additional store options

        Raises:
            ValidationError: If provider is invalid
        """
        if not isinstance(provider, StorageProvider):
            raise ValidationError("Invalid storage provider")

        self.provider = provider
        self.base_path = base_path.rstrip("/") if base_path else ""
        self.options = kwargs

    def _make_path(self, path: str) -> str:
        """Create a full request path.

        Args:
            path: Resource path

        Returns:
            Full request path
        """
        path = path.lstrip("/")
        if self.base_path:
            return f"{self.base_path}/{path}"
        return path

    def put(
        self,
        path: str,
        data: Any,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Store data at path.

        Args:
            path: Resource path
            data: Data to store
            **kwargs: Additional request options
                - headers: Request headers
                - params: Query parameters
                - timeout: Request timeout

        Returns:
            Response data

        Raises:
            StorageError: If request fails
            ValidationError: If path or data is invalid

        Example:
            >>> response = store.put(
            ...     "users/123",
            ...     {"name": "Alice"},
            ...     headers={"Content-Type": "application/json"}
            ... )
        """
        if not path:
            raise ValidationError("Path cannot be empty")

        try:
            full_path = self._make_path(path)
            result = self.provider.put(
                full_path,
                data,
                **{**self.options, **kwargs},
            )
            return result if isinstance(result, dict) else {"success": True}
        except Exception as e:
            raise StorageError(f"PUT request failed: {e}")

    def get(
        self,
        path: str,
        **kwargs: Any,
    ) -> Any:
        """Retrieve data from path.

        Args:
            path: Resource path
            **kwargs: Additional request options
                - headers: Request headers
                - params: Query parameters
                - timeout: Request timeout

        Returns:
            Response data

        Raises:
            StorageError: If request fails
            ValidationError: If path is invalid

        Example:
            >>> data = store.get(
            ...     "users/123",
            ...     params={"fields": "name,email"}
            ... )
        """
        if not path:
            raise ValidationError("Path cannot be empty")

        try:
            full_path = self._make_path(path)
            return self.provider.get(
                full_path,
                **{**self.options, **kwargs},
            )
        except Exception as e:
            raise StorageError(f"GET request failed: {e}")

    def post(
        self,
        path: str,
        data: Any,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create resource at path.

        Args:
            path: Resource path
            data: Resource data
            **kwargs: Additional request options
                - headers: Request headers
                - params: Query parameters
                - timeout: Request timeout

        Returns:
            Response data

        Raises:
            StorageError: If request fails
            ValidationError: If path or data is invalid

        Example:
            >>> response = store.post(
            ...     "users",
            ...     {"name": "Alice"},
            ...     headers={"Content-Type": "application/json"}
            ... )
        """
        if not path:
            raise ValidationError("Path cannot be empty")

        try:
            full_path = self._make_path(path)
            return self.provider.post(
                full_path,
                data,
                **{**self.options, **kwargs},
            )
        except Exception as e:
            raise StorageError(f"POST request failed: {e}")

    def patch(
        self,
        path: str,
        data: Any,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Update resource at path.

        Args:
            path: Resource path
            data: Update data
            **kwargs: Additional request options
                - headers: Request headers
                - params: Query parameters
                - timeout: Request timeout

        Returns:
            Response data

        Raises:
            StorageError: If request fails
            ValidationError: If path or data is invalid

        Example:
            >>> response = store.patch(
            ...     "users/123",
            ...     {"status": "active"},
            ...     headers={"Content-Type": "application/json"}
            ... )
        """
        if not path:
            raise ValidationError("Path cannot be empty")

        try:
            full_path = self._make_path(path)
            return self.provider.patch(
                full_path,
                data,
                **{**self.options, **kwargs},
            )
        except Exception as e:
            raise StorageError(f"PATCH request failed: {e}")

    def delete(
        self,
        path: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Delete resource at path.

        Args:
            path: Resource path
            **kwargs: Additional request options
                - headers: Request headers
                - params: Query parameters
                - timeout: Request timeout

        Returns:
            Response data

        Raises:
            StorageError: If request fails
            ValidationError: If path is invalid

        Example:
            >>> response = store.delete("users/123")
        """
        if not path:
            raise ValidationError("Path cannot be empty")

        try:
            full_path = self._make_path(path)
            result = self.provider.delete(
                full_path,
                **{**self.options, **kwargs},
            )
            return result if isinstance(result, dict) else {"success": True}
        except Exception as e:
            raise StorageError(f"DELETE request failed: {e}")

    def list(
        self,
        path: str,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """List resources at path.

        Args:
            path: Resource path
            **kwargs: Additional request options
                - headers: Request headers
                - params: Query parameters
                - timeout: Request timeout

        Returns:
            List of resources

        Raises:
            StorageError: If request fails
            ValidationError: If path is invalid

        Example:
            >>> resources = store.list(
            ...     "users",
            ...     params={"status": "active", "limit": 10}
            ... )
        """
        if not path:
            raise ValidationError("Path cannot be empty")

        try:
            full_path = self._make_path(path)
            return self.provider.list(
                full_path,
                **{**self.options, **kwargs},
            )
        except Exception as e:
            raise StorageError(f"LIST request failed: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get store capabilities.

        Returns:
            Dict with store capabilities including:
                - provider: Provider type
                - base_path: Base request path
                - supports_get: GET support
                - supports_put: PUT support
                - supports_post: POST support
                - supports_patch: PATCH support
                - supports_delete: DELETE support
                - supports_list: LIST support

        Example:
            >>> caps = store.get_capabilities()
            >>> if caps["supports_patch"]:
            ...     store.patch("users/123", {"status": "active"})
        """
        capabilities = self.provider.get_capabilities()
        capabilities.update({
            "base_path": self.base_path,
            "options": self.options,
            "supports_get": True,
            "supports_put": True,
            "supports_post": True,
            "supports_patch": True,
            "supports_delete": True,
            "supports_list": True,
        })
        return capabilities
