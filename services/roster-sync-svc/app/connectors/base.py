"""Base connector interface for roster synchronization."""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class ConnectorError(Exception):
    """Base exception for connector errors."""
    pass


class BaseConnector(ABC):
    """Abstract base class for roster data connectors."""
    
    connector_type: str = None
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize connector with configuration."""
        self.config = config
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the data source.
        
        Returns:
            bool: True if connection successful, False otherwise
            
        Raises:
            ConnectorError: If connection fails
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the data source."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to the data source.
        
        Returns:
            Dict containing:
                - success: bool
                - message: str
                - Additional connection info
        """
        pass
    
    @abstractmethod
    async def sync_data(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Synchronize all data from the source.
        
        Args:
            progress_callback: Optional callback for progress updates.
                              Should accept (message: str, percent: int) parameters.
        
        Returns:
            Dict containing sync results with counts of:
                - processed: int
                - created: int  
                - updated: int
                - failed: int
                - Additional sync metrics
        
        Raises:
            ConnectorError: If sync fails
        """
        pass
    
    async def validate_config(self) -> Dict[str, Any]:
        """
        Validate connector configuration.
        
        Returns:
            Dict containing:
                - valid: bool
                - errors: List[str]
                - warnings: List[str]
        """
        errors = []
        warnings = []
        
        # Basic validation - subclasses should override for specific validation
        if not isinstance(self.config, dict):
            errors.append("Configuration must be a dictionary")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get connector information.
        
        Returns:
            Dict containing connector metadata
        """
        return {
            "connector_type": self.connector_type,
            "name": self.__class__.__name__,
            "module": self.__class__.__module__,
            "config_keys": list(self.config.keys()) if isinstance(self.config, dict) else []
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


class MockConnector(BaseConnector):
    """Mock connector for testing purposes."""
    
    connector_type = "mock"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connected = False
    
    async def connect(self) -> bool:
        """Mock connection."""
        await asyncio.sleep(0.1)  # Simulate connection delay
        self.connected = True
        self.logger.info("Mock connector connected")
        return True
    
    async def disconnect(self) -> None:
        """Mock disconnection."""
        self.connected = False
        self.logger.info("Mock connector disconnected")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Mock connection test."""
        if not self.connected:
            await self.connect()
        
        return {
            "success": True,
            "message": "Mock connection successful",
            "mock_data": True
        }
    
    async def sync_data(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Mock data sync."""
        if not self.connected:
            await self.connect()
        
        total_steps = 5
        
        for step in range(total_steps):
            if progress_callback:
                await progress_callback(
                    f"Mock sync step {step + 1}/{total_steps}",
                    int((step / total_steps) * 100)
                )
            await asyncio.sleep(0.2)  # Simulate work
        
        if progress_callback:
            await progress_callback("Mock sync completed", 100)
        
        return {
            "processed": 100,
            "created": 60,
            "updated": 35,
            "failed": 5,
            "mock_data": True
        }
