import uuid

from fastapi import HTTPException

from src.core.repositories.repositories import Repositories

from starlette import status

from src.core.domain.pagination.schema.pagination_schema import PaginationParams, PaginatedResponse
from src.core.domain.researcher_profile.researcher_profile_model.reasearcher_profile_model import \
    ResearcherProfile
from src.core.domain.researcher_profile.researcher_profile_schema.researcher_profile_schemas import \
    ResearcherProfileCreate, ResearcherProfileResponse, ResearcherProfileUpdate
from src.core.domain.user.user_model.user_model import User


class ResearcherProfileService:
    def __init__(self, repos: Repositories) -> None:
        self._repos = repos

    async def create_profile(
            self,
            profile_data: ResearcherProfileCreate
    ) -> ResearcherProfileResponse:
        """
        Asynchronous function to create a ResearcherProfile. If successful, the newly added
        ResearcherProfile will be returned, else an exception will be raised.

        :param profile_data: data to create the profile

        :return ResearcherProfileResponse:
        """

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


    async def delete_profile(
            self,
            profile_id: uuid.UUID
    ) -> None:
        """
        Asynchronous function to delete a ResearcherProfile. Nothing is returned.

        :param profile_id: id of the profile that will be deleted.

        :raises:
        """
        async with self._repos as repos:
            profile = await repos.profiles.get_user_by_id(profile_id)

            if not profile:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

            await repos.users.delete(profile_id)
            await repos.commit()


    async def update_profile(
            self,
            profile_id: uuid.UUID,
            profile_data: ResearcherProfileUpdate,
            current_user: User
    ) -> ResearcherProfileResponse:
        """
        Asynchronous function to update a ResearcherProfile. If successful, the updated profile
        is returned, else an exception will be raised.

        :param profile_id: id of the profile that will be updated.
        :param profile_data: data for the update.
        :param current_user:

        :return ResearcherProfileResponse:
        """
        async with self._repos as repos:
            profile = await repos.profiles.get_by_id(profile_id)

            if not profile:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

            if current_user.role == 'researcher':
                if profile_data.metrics:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Only admins can update metrics")

                profile.update(profile_data)

            else:
                profile.update(profile_data)

            await repos.profiles.save(profile)
            await repos.commit()

            return ResearcherProfileResponse.model_validate(profile)

    async def fetch_profiles(
            self,
            params: PaginationParams
    ) -> PaginatedResponse[ResearcherProfileResponse]:
        """
        Asynchronous function to fetch all ResearcherProfiles. If there are no ResearcherProfiles,
        the list is returned empty.

        :return list[ResearcherProfileResponse]:
        """
        async with self._repos as repos:
            result = await repos.profiles.fetch(params)

            return PaginatedResponse(
                items=[ResearcherProfileResponse.model_validate(p) for p in result.items],
                total=result.total,
                page=result.page,
                page_size=result.page_size,
                pages=result.pages,
            )