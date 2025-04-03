"""Example demonstrating service-based communication between plugins.

This example shows how to use services to enable cross-plugin functionality
while maintaining proper access control and dependency management.
"""

import asyncio

from pepperpy.plugins import (
    DependencyType,
    PepperpyPlugin,
    ProviderPlugin,
    ServiceScope,
    await_service,
    call_service,
    service,
)


# Database plugin that provides data storage services
class DatabasePlugin(ProviderPlugin):
    """A plugin that provides database storage services to other plugins."""

    __metadata__ = {
        "name": "database",
        "version": "1.0.0",
        "description": "Database storage plugin",
        "author": "PepperPy Team",
        "provider_type": "database",  # Provider type is required
    }

    def __init__(self, config=None):
        """Initialize plugin."""
        super().__init__(config)
        # In-memory database for simplicity
        self.database = {}

    def initialize(self) -> None:
        """Initialize plugin."""
        super().initialize()
        # Register the database as a resource
        self.register_resource(
            resource_key="database",
            resource=self.database,
            resource_type="memory",
            metadata={"description": "In-memory database"},
        )
        print(f"✅ Initialized {self.__metadata__['name']}")

    async def async_cleanup(self) -> None:
        """Clean up plugin."""
        await super().async_cleanup()
        print(f"🧹 Cleaned up {self.__metadata__['name']}")

    # Define services using the @service decorator

    @service("store", scope=ServiceScope.PUBLIC)
    def store_data(self, key: str, value: any) -> bool:
        """Store data in the database.

        Args:
            key: Data key
            value: Data value

        Returns:
            True if data was stored successfully
        """
        self.database[key] = value
        print(f"📝 Database: Stored {key}={value}")
        return True

    @service("retrieve", scope=ServiceScope.PUBLIC)
    def retrieve_data(self, key: str) -> any:
        """Retrieve data from the database.

        Args:
            key: Data key

        Returns:
            Stored value or None if key doesn't exist
        """
        value = self.database.get(key)
        print(f"🔍 Database: Retrieved {key}={value}")
        return value

    @service("delete", scope=ServiceScope.DEPENDENT)
    def delete_data(self, key: str) -> bool:
        """Delete data from the database.

        This service is only available to plugins that declare a
        dependency on this plugin.

        Args:
            key: Data key

        Returns:
            True if key existed and was deleted, False otherwise
        """
        if key in self.database:
            del self.database[key]
            print(f"🗑️ Database: Deleted {key}")
            return True
        return False

    @service("list_keys", scope=ServiceScope.PUBLIC)
    def list_keys(self) -> list[str]:
        """List all keys in the database.

        Returns:
            List of keys
        """
        keys = list(self.database.keys())
        print(f"📋 Database: Listed {len(keys)} keys")
        return keys

    @service("clear", scope=ServiceScope.PRIVATE)
    def clear_database(self) -> None:
        """Clear the entire database.

        This service is private and only available to this plugin.
        """
        self.database.clear()
        print("🧹 Database: Cleared all data")

    @service("backup", scope=ServiceScope.PUBLIC, metadata={"admin_only": True})
    async def backup_database(self) -> dict[str, any]:
        """Create a backup of the database.

        This service is asynchronous.

        Returns:
            A copy of the database
        """
        # Simulate a time-consuming operation
        print("💾 Database: Starting backup...")
        await asyncio.sleep(0.5)

        # Create a deep copy
        backup = dict(self.database)
        print(f"✅ Database: Backup completed with {len(backup)} entries")
        return backup


# User Management plugin that depends on the Database plugin
class UserManagementPlugin(PepperpyPlugin):
    """A plugin that manages users using the database plugin services."""

    __metadata__ = {
        "name": "user_management",
        "version": "1.0.0",
        "description": "User management plugin",
        "author": "PepperPy Team",
        "provider_type": "users",  # Provider type is required
    }

    # Declare dependencies on the database plugin
    __dependencies__ = {
        "database": DependencyType.REQUIRED,
    }

    def __init__(self, config=None):
        """Initialize plugin."""
        super().__init__(config)
        self.user_count = 0

    def initialize(self) -> None:
        """Initialize plugin."""
        super().initialize()
        # Register the user count as a resource
        self.register_resource(
            resource_key="user_count",
            resource=self.user_count,
            resource_type="metric",
            metadata={"description": "Number of users created"},
        )
        print(f"✅ Initialized {self.__metadata__['name']}")

    async def async_cleanup(self) -> None:
        """Clean up plugin."""
        await super().async_cleanup()
        print(f"🧹 Cleaned up {self.__metadata__['name']}")

    @service("create_user", scope=ServiceScope.PUBLIC)
    def create_user(self, username: str, data: dict[str, any]) -> bool:
        """Create a new user.

        Args:
            username: User's username
            data: User data

        Returns:
            True if user was created successfully
        """
        # Use the database plugin's store service
        key = f"user:{username}"
        result = call_service("database", "store", self.plugin_id, key, data)

        if result:
            self.user_count += 1
            print(f"👤 UserManagement: Created user {username}")

        return result

    @service("get_user", scope=ServiceScope.PUBLIC)
    def get_user(self, username: str) -> dict[str, any] | None:
        """Get user data.

        Args:
            username: User's username

        Returns:
            User data or None if user doesn't exist
        """
        # Use the database plugin's retrieve service
        key = f"user:{username}"
        user = call_service("database", "retrieve", self.plugin_id, key)

        if user:
            print(f"🔍 UserManagement: Retrieved user {username}")
        else:
            print(f"❓ UserManagement: User {username} not found")

        return user

    @service("delete_user", scope=ServiceScope.DEPENDENT)
    def delete_user(self, username: str) -> bool:
        """Delete a user.

        This service is only available to plugins that declare a
        dependency on this plugin.

        Args:
            username: User's username

        Returns:
            True if user existed and was deleted
        """
        # Use the database plugin's delete service
        key = f"user:{username}"
        result = call_service("database", "delete", self.plugin_id, key)

        if result:
            self.user_count -= 1
            print(f"🗑️ UserManagement: Deleted user {username}")

        return result

    @service("list_users", scope=ServiceScope.PUBLIC)
    def list_users(self) -> list[str]:
        """List all usernames.

        Returns:
            List of usernames
        """
        # Use the database plugin's list_keys service
        keys = call_service("database", "list_keys", self.plugin_id)

        # Filter to get only user keys
        usernames = [key[5:] for key in keys if key.startswith("user:")]
        print(f"📋 UserManagement: Listed {len(usernames)} users")

        return usernames

    @service("backup_users", scope=ServiceScope.PUBLIC)
    async def backup_users(self) -> dict[str, dict[str, any]]:
        """Create a backup of all users.

        This service is asynchronous.

        Returns:
            A dictionary of all users
        """
        print("💾 UserManagement: Starting user backup...")

        # Call the database plugin's async backup service
        full_backup = await await_service("database", "backup", self.plugin_id)

        # Filter to get only user entries
        user_backup = {
            key[5:]: value
            for key, value in full_backup.items()
            if key.startswith("user:")
        }

        print(f"✅ UserManagement: User backup completed with {len(user_backup)} users")
        return user_backup


# Analytics plugin that uses services from both other plugins
class AnalyticsPlugin(PepperpyPlugin):
    """A plugin that provides analytics using other plugins' services."""

    __metadata__ = {
        "name": "analytics",
        "version": "1.0.0",
        "description": "Analytics plugin",
        "author": "PepperPy Team",
        "provider_type": "analytics",  # Provider type is required
    }

    # Declare dependencies
    __dependencies__ = {
        "user_management": DependencyType.REQUIRED,
        "database": DependencyType.OPTIONAL,
    }

    def __init__(self, config=None):
        """Initialize plugin."""
        super().__init__(config)
        self.analytics_data = {}

    def initialize(self) -> None:
        """Initialize plugin."""
        super().initialize()
        # Register analytics data as a resource
        self.register_resource(
            resource_key="analytics_data",
            resource=self.analytics_data,
            resource_type="memory",
            metadata={"description": "Analytics data"},
        )
        print(f"✅ Initialized {self.__metadata__['name']}")

    async def async_cleanup(self) -> None:
        """Clean up plugin."""
        await super().async_cleanup()
        print(f"🧹 Cleaned up {self.__metadata__['name']}")

    @service("track_user_activity", scope=ServiceScope.PUBLIC)
    def track_user_activity(self, username: str, activity: str) -> bool:
        """Track user activity.

        Args:
            username: User's username
            activity: Activity description

        Returns:
            True if activity was tracked successfully
        """
        # Verify user exists
        user = call_service("user_management", "get_user", self.plugin_id, username)

        if not user:
            print(
                f"❌ Analytics: Cannot track activity for non-existent user {username}"
            )
            return False

        # Store activity directly in database if we can access it
        try:
            key = f"activity:{username}:{activity}"
            result = call_service(
                "database",
                "store",
                self.plugin_id,
                key,
                {"username": username, "activity": activity, "timestamp": "now"},
            )
            print(f"📊 Analytics: Tracked activity for user {username}: {activity}")
            return result
        except Exception:
            # Fall back to storing in our internal storage
            if username not in self.analytics_data:
                self.analytics_data[username] = []

            self.analytics_data[username].append(activity)
            print(
                f"📊 Analytics: Tracked activity using fallback storage: {username}: {activity}"
            )
            return True

    @service("get_user_activities", scope=ServiceScope.PUBLIC)
    def get_user_activities(self, username: str) -> list[str]:
        """Get activities for a user.

        Args:
            username: User's username

        Returns:
            List of activity descriptions
        """
        # Try to get activities from database first
        try:
            keys = call_service("database", "list_keys", self.plugin_id)
            activity_keys = [
                key for key in keys if key.startswith(f"activity:{username}:")
            ]

            activities = [key.split(":")[-1] for key in activity_keys]
            print(
                f"📊 Analytics: Retrieved {len(activities)} activities for user {username}"
            )
            return activities
        except Exception:
            # Fall back to internal storage
            activities = self.analytics_data.get(username, [])
            print(
                f"📊 Analytics: Retrieved {len(activities)} activities from fallback storage for user {username}"
            )
            return activities

    @service("get_active_users", scope=ServiceScope.PUBLIC)
    def get_active_users(self) -> list[str]:
        """Get list of users with activity.

        Returns:
            List of usernames
        """
        # Try to get from database first
        try:
            keys = call_service("database", "list_keys", self.plugin_id)
            activity_keys = [key for key in keys if key.startswith("activity:")]

            usernames = list(set(key.split(":")[1] for key in activity_keys))
            print(f"📊 Analytics: Found {len(usernames)} active users")
            return usernames
        except Exception:
            # Fall back to internal storage
            usernames = list(self.analytics_data.keys())
            print(
                f"📊 Analytics: Found {len(usernames)} active users in fallback storage"
            )
            return usernames


async def main():
    """Run the example."""
    print("🚀 Starting plugin services example")

    # Create plugins
    database = DatabasePlugin()
    user_mgmt = UserManagementPlugin()
    analytics = AnalyticsPlugin()

    # Initialize plugins in dependency order
    database.initialize()
    user_mgmt.initialize()
    analytics.initialize()

    # Create some users
    print("\n👥 Creating users:")
    user_mgmt.create_user("alice", {"name": "Alice", "email": "alice@example.com"})
    user_mgmt.create_user("bob", {"name": "Bob", "email": "bob@example.com"})
    user_mgmt.create_user(
        "charlie", {"name": "Charlie", "email": "charlie@example.com"}
    )

    # Track some activities
    print("\n🏃 Tracking activities:")
    analytics.track_user_activity("alice", "login")
    analytics.track_user_activity("alice", "update_profile")
    analytics.track_user_activity("bob", "login")
    analytics.track_user_activity("charlie", "login")
    analytics.track_user_activity("charlie", "logout")

    # List users
    print("\n📋 Listing users:")
    users = user_mgmt.list_users()
    for user in users:
        print(f"  - {user}")

    # Get active users and their activities
    print("\n📊 User activities:")
    active_users = analytics.get_active_users()
    for username in active_users:
        activities = analytics.get_user_activities(username)
        print(f"  {username}: {', '.join(activities)}")

    # Create backup
    print("\n💾 Creating backup:")
    user_backup = await user_mgmt.backup_users()
    print(f"  Backup contains {len(user_backup)} users")

    # Clean up plugins in reverse dependency order
    print("\n🧹 Cleaning up...")
    await analytics.async_cleanup()
    await user_mgmt.async_cleanup()
    await database.async_cleanup()

    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
