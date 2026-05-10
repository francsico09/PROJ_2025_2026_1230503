import uuid

from fastapi import APIRouter, status, Depends

from src.core.repositories.repositories import Repositories
from src.modules.auth.auth import require_admin, get_current_user
from src.modules.researcher_profile.schema.researcher_profile_schemas import ResearcherProfileResponse, \
    ResearcherProfileCreate, ResearcherProfileUpdate
from src.modules.researcher_profile.service.researcher_profile_service import ResearcherProfileService
from src.modules.user.model.user_model import User

router = APIRouter(prefix="/researcher_profiles", tags=["ResearcherProfiles"])

def get_researcher_profile_service() -> ResearcherProfileService:
    return ResearcherProfileService(Repositories())

@router.post(
    "/",
    response_model=ResearcherProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new researcher profile"
)
async def create_profile(
        profile_data: ResearcherProfileCreate,
        _: User = Depends(require_admin),
        service: ResearcherProfileService = Depends(get_researcher_profile_service)
) -> ResearcherProfileResponse:
    return await service.create_profile(profile_data)

@router.get(
    "/",
    response_model=list[ResearcherProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all researcher profiles"
)
async def list_profiles(
        service: ResearcherProfileService = Depends(get_researcher_profile_service)
) -> list[ResearcherProfileResponse]:
    return await service.list_profiles()

@router.delete(
    "/{profile_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a researcher profile"
)
async def delete_profile(
        profile_id: uuid.UUID,
        _: User = Depends(require_admin),
        service: ResearcherProfileService = Depends(get_researcher_profile_service)
) -> None:
    await service.delete_profile(profile_id)

@router.patch(
    "/{profile_id}",
    response_model=ResearcherProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a researcher profile"
)
async def update_profile(
        profile_id: uuid.UUID,
        profile_data: ResearcherProfileUpdate,
        current_user: User = Depends(get_current_user),
        service: ResearcherProfileService = Depends(get_researcher_profile_service)
) -> ResearcherProfileResponse:
    return await service.update_profile(profile_id, profile_data, current_user)


@router.get(
    "/by-profile-id/{scholar_id}",
    response_model=ResearcherProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a researcher profile by scholar id"
)
async def get_profile_by_scholar_id(
        scholar_id: str,
        _: User = Depends(require_admin),
        service: ResearcherProfileService = Depends(get_researcher_profile_service)
) -> ResearcherProfileResponse:
    return await service.get_profile_by_scholar_id(scholar_id)


@router.get(
    "/by-orcid/{orcid}",
    response_model=ResearcherProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a researcher profile by orcid"
)
async def get_profile_by_orcid(
        orcid: str,
        _: User = Depends(require_admin),
        service: ResearcherProfileService = Depends(get_researcher_profile_service)
) -> ResearcherProfileResponse:
    return await service.get_profile_by_orcid(orcid)
