import datetime
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from src.modules.metrics.model.source.model import Source, SourceName
from src.modules.metrics.schema.metric_schemas import (
    ResearcherMetricCreate,
    ResearcherMetricUpdate,
)
from src.modules.metrics.service.researcher_metric_service import ResearcherMetricService


def make_metric(**kwargs):
    m = MagicMock()
    m.id = kwargs.get("id", uuid.uuid4())
    m.date = kwargs.get("date", datetime.date.today())
    m.h_index = kwargs.get("h_index", 10)
    m.i10_index = kwargs.get("i10_index", 5)
    m.total_citations = kwargs.get("total_citations", 100)
    m.total_publications = kwargs.get("total_publications", 20)
    m.source = kwargs.get("source", Source(SourceName.scholar, ""))
    return m


def make_researcher(**kwargs):
    r = MagicMock()
    r.id = kwargs.get("id", uuid.uuid4())
    r.metrics = kwargs.get("researcher_metric", [])
    return r


def make_user(researcher_profile=None):
    u = MagicMock()
    u.researcherProfile = researcher_profile
    return u


def make_repos(
    profile=None,
    metric=None,
    all_metrics=None,
    all_profiles=None,
    user=None,
):
    repos = AsyncMock()

    # profiles
    repos.profiles.get_by_id = AsyncMock(return_value=profile)
    repos.profiles.get_all = AsyncMock(return_value=all_profiles or [])
    repos.profiles.save = AsyncMock()

    # researcher_metric
    repos.metrics.get_by_id = AsyncMock(return_value=metric)
    repos.metrics.get_all = AsyncMock(return_value=all_metrics or [])
    repos.metrics.get_by_date = AsyncMock(return_value=all_metrics or [])
    repos.metrics.save = AsyncMock(side_effect=lambda m: m)
    repos.metrics.delete = AsyncMock()

    # users
    repos.users.get_by_id = AsyncMock(return_value=user)

    repos.commit = AsyncMock()

    # context manager
    uow_mock = MagicMock()
    uow_mock.__aenter__ = AsyncMock(return_value=repos)
    uow_mock.__aexit__ = AsyncMock(return_value=False)

    return uow_mock, repos


# create_metric
class TestCreateMetric:

    @pytest.mark.asyncio
    async def test_create_metric_success(self):
        researcher = make_researcher()
        saved_metric = make_metric()
        uow, repos = make_repos(profile=researcher)
        repos.metrics.save = AsyncMock(return_value=saved_metric)

        service = ResearcherMetricService(uow)
        data = ResearcherMetricCreate(
            h_index=10,
            i10_index=5,
            total_citations=100,
            total_publications=20,
            source=Source(SourceName.scholar, ""),
        )

        metric = await service.create_metric(researcher.id, data)
        repos.profiles.save.assert_called_once_with(researcher)
        repos.commit.assert_called_once()
        assert metric.date  == researcher.metrics[0].date

    @pytest.mark.asyncio
    async def test_create_metric_researcher_not_found(self):
        uow, _ = make_repos(profile=None)
        service = ResearcherMetricService(uow)
        data = ResearcherMetricCreate(
            h_index=10,
            i10_index=5,
            total_citations=100,
            total_publications=20,
            source=Source(SourceName.scholar, ""),
        )

        with pytest.raises(HTTPException) as exc:
            await service.create_metric(uuid.uuid4(), data)

        assert exc.value.status_code == 404
        assert "Researcher not found" in exc.value.detail


# delete_metric
class TestDeleteMetric:

    @pytest.mark.asyncio
    async def test_delete_metric_success(self):
        metric = make_metric()
        researcher = make_researcher(metrics=[metric])
        uow, repos = make_repos(metric=metric, all_profiles=[researcher])

        service = ResearcherMetricService(uow)
        await service.delete_metric(metric.id)

        repos.metrics.delete.assert_called_once_with(metric.id)
        repos.profiles.save.assert_called_once_with(researcher)
        repos.commit.assert_called_once()
        assert len(researcher.metrics) == 0

    @pytest.mark.asyncio
    async def test_delete_metric_not_found(self):
        uow, _ = make_repos(metric=None)
        service = ResearcherMetricService(uow)

        with pytest.raises(HTTPException) as exc:
            await service.delete_metric(uuid.uuid4())

        assert exc.value.status_code == 404
        assert "Metric not found" in exc.value.detail


# update_metric
class TestUpdateMetric:

    @pytest.mark.asyncio
    async def test_update_metric_success(self):
        metric = make_metric()
        uow, repos = make_repos(metric=metric)
        repos.metrics.save = AsyncMock(return_value=metric)

        service = ResearcherMetricService(uow)
        data = ResearcherMetricUpdate(h_index=99)

        await service.update_metric(metric.id, data)

        metric.update.assert_called_once_with(data)
        repos.metrics.save.assert_called_once_with(metric)
        repos.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_metric_not_found(self):
        uow, _ = make_repos(metric=None)
        service = ResearcherMetricService(uow)

        with pytest.raises(HTTPException) as exc:
            await service.update_metric(uuid.uuid4(), ResearcherMetricUpdate())

        assert exc.value.status_code == 404


# get_metric_by_user_id
class TestGetMetricByUserId:

    @pytest.mark.asyncio
    async def test_returns_metrics_for_valid_user(self):
        metric = make_metric()
        researcher = make_researcher(metrics=[metric])
        user = make_user(researcher_profile=researcher)
        uow, _ = make_repos(user=user)

        service = ResearcherMetricService(uow)
        result = await service.get_metric_by_user_id(user.id)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_user_not_found(self):
        uow, _ = make_repos(user=None)
        service = ResearcherMetricService(uow)

        with pytest.raises(HTTPException) as exc:
            await service.get_metric_by_user_id(uuid.uuid4())

        assert exc.value.status_code == 404
        assert "User not found" in exc.value.detail

    @pytest.mark.asyncio
    async def test_user_without_researcher_profile(self):
        user = make_user(researcher_profile=None)
        uow, _ = make_repos(user=user)
        service = ResearcherMetricService(uow)

        with pytest.raises(HTTPException) as exc:
            await service.get_metric_by_user_id(user.id)

        assert exc.value.status_code == 404
        assert "ResearcherProfile not found" in exc.value.detail


# get_metric_by_date
class TestGetMetricByDate:

    @pytest.mark.asyncio
    async def test_returns_metrics_for_date(self):
        metrics = [make_metric(), make_metric()]
        uow, repos = make_repos(all_metrics=metrics)
        repos.metrics.get_by_date = AsyncMock(return_value=metrics)

        service = ResearcherMetricService(uow)
        result = await service.get_metric_by_date(datetime.date.today())

        assert len(result) == 2
        repos.metrics.get_by_date.assert_called_once_with(datetime.date.today())

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_metrics(self):
        uow, repos = make_repos()
        repos.metrics.get_by_date = AsyncMock(return_value=[])

        service = ResearcherMetricService(uow)
        result = await service.get_metric_by_date(datetime.date.today())

        assert result == []


# list_metrics
class TestListMetrics:

    @pytest.mark.asyncio
    async def test_returns_all_metrics(self):
        metrics = [make_metric(), make_metric(), make_metric()]
        uow, repos = make_repos(all_metrics=metrics)

        service = ResearcherMetricService(uow)
        result = await service.list_metrics()

        assert len(result) == 3
        repos.metrics.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_metrics(self):
        uow, repos = make_repos(all_metrics=[])

        service = ResearcherMetricService(uow)
        result = await service.list_metrics()

        assert result == []
