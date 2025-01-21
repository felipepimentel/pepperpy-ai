"""SQLite memory provider implementation."""
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, cast

from .base import BaseMemoryProvider, Message

logger = logging.getLogger(__name__)

@BaseMemoryProvider.register("sqlite")
class SQLiteMemoryProvider(BaseMemoryProvider):
    """SQLite memory provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the SQLite memory provider.
        
        Args:
            config: Configuration dictionary containing:
                - database_path: Path to SQLite database file
                - table_name: Optional table name (defaults to "messages")
        """
        super().__init__(config)
        self.database_path = Path(config["database_path"])
        self.table_name = config.get("table_name", "messages")
        self.conn: Optional[sqlite3.Connection] = None
    
    async def initialize(self) -> bool:
        """Initialize the provider.
        
        Returns:
            True if initialization was successful.
            
        Raises:
            ValueError: If initialization fails.
        """
        if self.is_initialized:
            return True
            
        try:
            # Create database directory if it doesn't exist
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect to database
            self.conn = sqlite3.connect(str(self.database_path))
            
            # Create messages table if it doesn't exist
            cursor = self.conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    role TEXT NOT NULL,
                    metadata TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            self.conn.commit()
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize SQLite provider: {str(e)}")
            await self.cleanup()
            raise ValueError(f"SQLite initialization failed: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up resources used by the provider."""
        if self.conn:
            self.conn.close()
            self.conn = None
        self.is_initialized = False
    
    async def add_message(self, message: Message) -> None:
        """Add a message to memory.
        
        Args:
            message: Message to add.
            
        Raises:
            ValueError: If provider is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized")
            
        if not self.conn:
            raise ValueError("Database connection not initialized")
            
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"INSERT INTO {self.table_name} (content, role, metadata, timestamp) VALUES (?, ?, ?, ?)",
                (
                    message.content,
                    message.role,
                    json.dumps(message.metadata),
                    message.timestamp.isoformat()
                )
            )
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to add message: {str(e)}")
            raise RuntimeError(f"Failed to add message: {str(e)}")
    
    async def get_messages(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        role: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Get messages from memory.
        
        Args:
            start_time: Optional start time filter.
            end_time: Optional end time filter.
            role: Optional role filter.
            limit: Optional limit on number of messages.
            
        Returns:
            List of messages.
            
        Raises:
            ValueError: If provider is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized")
            
        if not self.conn:
            raise ValueError("Database connection not initialized")
            
        try:
            # Build query
            query = f"SELECT content, role, metadata, timestamp FROM {self.table_name}"
            params: List[Union[str, int]] = []
            conditions = []
            
            if start_time:
                conditions.append("timestamp >= ?")
                params.append(start_time.isoformat())
                
            if end_time:
                conditions.append("timestamp <= ?")
                params.append(end_time.isoformat())
                
            if role:
                conditions.append("role = ?")
                params.append(role)
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY timestamp DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(str(limit))
                
            # Execute query
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert rows to messages
            messages = []
            for row in rows:
                content, role_str, metadata_str, timestamp_str = row
                messages.append(Message(
                    content=cast(str, content),
                    role=cast(str, role_str),
                    metadata=json.loads(metadata_str) if metadata_str else {},
                    timestamp=datetime.fromisoformat(timestamp_str)
                ))
                
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get messages: {str(e)}")
            raise RuntimeError(f"Failed to get messages: {str(e)}")
    
    async def clear_messages(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        role: Optional[str] = None
    ) -> None:
        """Clear messages from memory.
        
        Args:
            start_time: Optional start time filter.
            end_time: Optional end time filter.
            role: Optional role filter.
            
        Raises:
            ValueError: If provider is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized")
            
        if not self.conn:
            raise ValueError("Database connection not initialized")
            
        try:
            # Build query
            query = f"DELETE FROM {self.table_name}"
            params: List[str] = []
            conditions = []
            
            if start_time:
                conditions.append("timestamp >= ?")
                params.append(start_time.isoformat())
                
            if end_time:
                conditions.append("timestamp <= ?")
                params.append(end_time.isoformat())
                
            if role:
                conditions.append("role = ?")
                params.append(role)
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            # Execute query
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to clear messages: {str(e)}")
            raise RuntimeError(f"Failed to clear messages: {str(e)}")
    
    async def search_messages(
        self,
        query: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Search messages in memory.
        
        Args:
            query: Search query.
            limit: Optional limit on number of results.
            
        Returns:
            List of matching messages.
            
        Raises:
            ValueError: If provider is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized")
            
        if not self.conn:
            raise ValueError("Database connection not initialized")
            
        try:
            # Build query
            sql = f"""
                SELECT content, role, metadata, timestamp 
                FROM {self.table_name}
                WHERE content LIKE ?
                ORDER BY timestamp DESC
            """
            params: List[Union[str, int]] = [f"%{query}%"]
            
            if limit:
                sql += " LIMIT ?"
                params.append(str(limit))
                
            # Execute query
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            # Convert rows to messages
            messages = []
            for row in rows:
                content, role_str, metadata_str, timestamp_str = row
                messages.append(Message(
                    content=cast(str, content),
                    role=cast(str, role_str),
                    metadata=json.loads(metadata_str) if metadata_str else {},
                    timestamp=datetime.fromisoformat(timestamp_str)
                ))
                
            return messages
            
        except Exception as e:
            logger.error(f"Failed to search messages: {str(e)}")
            raise RuntimeError(f"Failed to search messages: {str(e)}") 