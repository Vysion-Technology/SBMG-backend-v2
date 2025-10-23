"""Request models for geographical entities like districts, blocks, and villages."""
from models.base import DistrictBase, BlockBase, GPBase, VillageBase


# Request models
class CreateDistrictRequest(DistrictBase):
    """Request model for creating a district."""



class UpdateDistrictRequest(DistrictBase):
    """Request model for updating a district."""



class CreateBlockRequest(BlockBase):
    """Request model for creating a block."""



class UpdateBlockRequest(BlockBase):
    """Request model for updating a block."""



class CreateGPRequest(GPBase):
    """Request model for creating a village."""



class UpdateGPRequest(GPBase):
    """Request model for updating a village."""



class CreateVillageRequest(VillageBase):
    """Request model for creating a village (in villages table)."""



class UpdateVillageRequest(VillageBase):
    """Request model for updating a village (in villages table)."""
