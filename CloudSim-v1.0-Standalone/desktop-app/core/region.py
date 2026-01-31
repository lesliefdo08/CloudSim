"""
Region Management - AWS-style global region registry
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum
import json
from pathlib import Path


class ServiceScope(Enum):
    """Service availability scope"""
    GLOBAL = "global"  # Available across all regions (IAM, CloudFront)
    REGIONAL = "regional"  # Region-specific (EC2, S3, RDS)


@dataclass
class Region:
    """Represents an AWS-style region"""
    code: str  # e.g., "us-east-1"
    name: str  # e.g., "US East (N. Virginia)"
    location: str  # e.g., "Virginia, USA"
    enabled: bool = True
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class RegionRegistry:
    """Global registry for managing regions"""
    
    _instance = None
    _regions: Dict[str, Region] = {}
    _current_region: Optional[str] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_regions()
        return cls._instance
    
    def _initialize_regions(self):
        """Initialize default regions"""
        self._regions = {
            "us-east-1": Region(
                code="us-east-1",
                name="US East (N. Virginia)",
                location="Virginia, USA"
            ),
            "us-west-2": Region(
                code="us-west-2",
                name="US West (Oregon)",
                location="Oregon, USA"
            ),
            "eu-west-1": Region(
                code="eu-west-1",
                name="EU West (Ireland)",
                location="Dublin, Ireland"
            ),
            "ap-southeast-1": Region(
                code="ap-southeast-1",
                name="Asia Pacific (Singapore)",
                location="Singapore"
            ),
            "local": Region(
                code="local",
                name="Local Development",
                location="Localhost"
            )
        }
        
        # Set default region
        self._current_region = "us-east-1"
    
    def get_region(self, code: str) -> Optional[Region]:
        """Get region by code"""
        return self._regions.get(code)
    
    def list_regions(self, enabled_only: bool = True) -> List[Region]:
        """List all regions"""
        regions = list(self._regions.values())
        if enabled_only:
            regions = [r for r in regions if r.enabled]
        return sorted(regions, key=lambda r: r.code)
    
    def get_current_region(self) -> Region:
        """Get currently selected region"""
        return self._regions[self._current_region]
    
    def set_current_region(self, code: str) -> bool:
        """Set current region"""
        if code in self._regions:
            self._current_region = code
            return True
        return False
    
    def add_region(self, region: Region) -> bool:
        """Add a custom region"""
        if region.code not in self._regions:
            self._regions[region.code] = region
            return True
        return False
    
    def is_valid_region(self, code: str) -> bool:
        """Check if region code is valid"""
        return code in self._regions


@dataclass
class RegionalResource:
    """Base class for region-scoped resources"""
    region: str
    
    def validate_region(self):
        """Validate that region exists"""
        registry = RegionRegistry()
        if not registry.is_valid_region(self.region):
            raise ValueError(f"Invalid region: {self.region}")


class RegionContext:
    """Context manager for temporary region switching"""
    
    def __init__(self, region_code: str):
        self.region_code = region_code
        self.previous_region = None
        self.registry = RegionRegistry()
    
    def __enter__(self):
        self.previous_region = self.registry.get_current_region().code
        self.registry.set_current_region(self.region_code)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.previous_region:
            self.registry.set_current_region(self.previous_region)


# Global registry instance
def get_current_region() -> str:
    """Convenience function to get current region code"""
    return RegionRegistry().get_current_region().code


def set_current_region(code: str) -> bool:
    """Convenience function to set current region"""
    return RegionRegistry().set_current_region(code)


def list_all_regions() -> List[Region]:
    """Convenience function to list all regions"""
    return RegionRegistry().list_regions()
