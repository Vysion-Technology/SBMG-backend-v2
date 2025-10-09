from models.base import DistrictBase, BlockBase, VillageBase


# Request models
class CreateDistrictRequest(DistrictBase):
    """Request model for creating a district."""

    pass


class UpdateDistrictRequest(DistrictBase):
    """Request model for updating a district."""

    pass


class CreateBlockRequest(BlockBase):
    """Request model for creating a block."""

    pass


class UpdateBlockRequest(BlockBase):
    """Request model for updating a block."""

    pass


class CreateVillageRequest(VillageBase):
    """Request model for creating a village."""

    pass


class UpdateVillageRequest(VillageBase):
    """Request model for updating a village."""

    pass
