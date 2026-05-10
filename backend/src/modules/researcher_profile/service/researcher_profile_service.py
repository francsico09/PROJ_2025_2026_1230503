import uuid

from fastapi import HTTPException

from src.core.repositories.repositories import Repositories
from src.modules.researcher_profile.schema.researcher_profile_schemas import ResearcherProfileResponse, \
    ResearcherProfileCreate, ResearcherProfileUpdate
from src.modules.user.model.user_model import User
from src.modules.researcher_profile.model.reasearcher_profile_model import ResearcherProfile

from starlette import status


class ResearcherProfileService:
    def __init__(self, repos: Repositories) -> None:
        self._repos = repos

    """
    Asynchronous function to create a ResearcherProfile. If successful, the newly added 
    ResearcherProfile will be returned, else an exception will be raised.
    
    :param profile ResearcherProfile profile: the profile that will be created.
    
    :return ResearcherProfileResponse:
    
    :raises:
    """
    async def create_profile(
            self,
            profile_data: ResearcherProfileCreate
    ) -> ResearcherProfileResponse:
        async with self._repos as repos:
            existing_scholar = await repos.profiles.get_by_scholar_id(profile_data.scholar_id)

            if existing_scholar:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A profile with this Scholar ID already exists")

            existing_scholar = await repos.profiles.get_by_orcid(profile_data.orcid)
            if existing_scholar:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A profile with this ORCID already exists")


            profile = ResearcherProfile(
                id=uuid.uuid4(),
                keywords=profile_data.keywords,
                metrics=[],
                scholar_id=profile_data.scholar_id if profile_data.scholar_id else None,
                orcid=profile_data.orcid if profile_data.orcid else None,
                wos_id=profile_data.wos_id if profile_data.wos_id else None,
                biography=profile_data.biography if profile_data.biography else None,
                affiliation=profile_data.affiliation if profile_data.affiliation else None
            )

            await repos.profiles.save(profile)
            await repos.commit()

            return ResearcherProfileResponse.model_validate(profile)

    """
    Asynchronous function to delete a ResearcherProfile. Nothing is returned.
    
    :param profile_id UUID: id of the profile that will be deleted.
    
    :raises:
    """
    async def delete_profile(
            self,
            profile_id: uuid.UUID
    ) -> None:
        async with self._repos as repos:
            profile = await repos.profiles.get_user_by_id(profile_id)

            if not profile:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

            await repos.users.delete(profile_id)
            await repos.commit()

    """
    Asynchronous function to update a ResearcherProfile. If successful, the updated profile
    is returned, else an exception will be raised.
    
    :param profile_id UUID: id of the profile that will be updated.
    
    :return ResearcherProfileResponse:
    
    :raises:
    """
    async def update_profile(
            self,
            profile_id: uuid.UUID,
            profile_data: ResearcherProfileUpdate,
            current_user: User
    ) -> ResearcherProfileResponse:
        async with self._repos as repos:
            profile = await repos.profiles.get_by_id(profile_id)

            if not profile:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

            if current_user.role == 'researcher':
                if profile_data.metrics:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Only admins can update metrics on researcher profiles")

                profile.update(profile_data)
            else:
                profile.update(profile_data)

            await repos.profiles.save(profile)
            await repos.commit()

            return ResearcherProfileResponse.model_validate(profile)

    """
    Asynchronous function to fetch a ResearcherProfile by the scholar id. If successful, the updated profile
    is returned, else an exception will be raised.

    :param scholar_id str: scholar id of the profile that will be fetched.

    :return ResearcherProfileResponse:

    :raises:
    """
    async def get_profile_by_scholar_id(
            self,
            scholar: str
    ) -> ResearcherProfileResponse:
        async with self._repos as repos:
            profile = await repos.profiles.get_by_scholar(scholar)

            if not profile:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

            return ResearcherProfileResponse.model_validate(profile)

    """
    Asynchronous function to fetch a ResearcherProfile by the orcid. If successful, the updated profile
    is returned, else an exception will be raised.

    :param orcid str: orcid of the profile that will be fetched.

    :return ResearcherProfileResponse:

    :raises:
    """
    async def get_profile_by_orcid(
            self,
            orcid: str
    ) -> ResearcherProfileResponse:
        async with self._repos as repos:
            profile = await repos.profiles.get_by_orcid(orcid)

            if not profile:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

            return ResearcherProfileResponse.model_validate(profile)

    """
    Asynchronous function to fetch all ResearcherProfiles. If there are no ResearcherProfiles, 
    the list is returned empty.
    
    :return list[ResearcherProfileResponse]:
    """
    async def list_profiles(
            self
    ) -> list[ResearcherProfileResponse]:
        async with self._repos as repos:
            return await repos.profiles.get_all()
