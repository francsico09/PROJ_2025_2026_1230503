import uuid
import datetime

from src.modules.user.model.user_model import User
from src.modules.user.model.role.user_role import UserRole
from src.modules.researcher_profile.model.reasearcher_profile_model import ResearcherProfile
from src.modules.metrics.model.researcher_metric_model import ResearcherMetric
from src.modules.metrics.model.source.model import SourceName, Source
from src.modules.extraction.model.extraction_run_model import ExtractionRun, ExtractionTrigger, ExtractionStatus
from src.core.repositories.repositories import Repositories


def make_run(researcher_id: uuid.UUID) -> ExtractionRun:
    return ExtractionRun(
        id=uuid.uuid4(),
        researcher_id=researcher_id,
        triggered_at=datetime.datetime.utcnow(),
        triggered_by=ExtractionTrigger.manual,
        status=ExtractionStatus.completed,
        sources_attempted=[SourceName.scholar],
        sources_succeeded=[SourceName.scholar],
    )


def make_metric(r_id: uuid.UUID, run_id: uuid.UUID, h, i10, cit, pub) -> ResearcherMetric:
    return ResearcherMetric(
        id=uuid.uuid4(),
        researcher_id=r_id,
        extraction_run_id=run_id,
        source=Source(SourceName.scholar, "url.scholar.com"),
        date=datetime.datetime.now(),
        h_index=h,
        total_citations=cit,
        total_publications=pub,
        i10_index=i10,
    )


async def bootstrap():
    async with Repositories() as repo:

        users = await repo.users.get_all()
        if any(u.role == UserRole.admin for u in users):
            return

        print("Initializing Bootstrap...")

        # ------------------ ADMIN ------------------
        admin = User(
            id=uuid.uuid4(),
            name="Admin",
            email="admin@isep.ipp.pt",
            active=True,
            role=UserRole.admin,
            researcherProfile=None
        )
        await repo.users.save(admin)

        # ------------------ RESEARCHER 1 ------------------
        profile1 = ResearcherProfile(
            id=uuid.uuid4(),
            scholar_id="sch_1",
            orcid="0000-0000-0000-0001",
            wos_id=None,
            scopus_id=None,
            keywords=["AI", "ML"],
            metrics=[],
            biography="AI researcher"
        )

        user1 = User(
            id=uuid.uuid4(),
            name="Ana Costa",
            email="ana@isep.ipp.pt",
            active=True,
            role=UserRole.researcher,
            researcherProfile=profile1
        )
        await repo.users.save(user1)  # perfil criado em cascade, sem métricas

        run1 = make_run(profile1.id)
        await repo.extraction_runs.save(run1)  # run pode ser criado, perfil já existe

        for m in [
            make_metric(profile1.id, run1.id, 10, 15, 300, 20),
            make_metric(profile1.id, run1.id, 12, 18, 400, 25),
            make_metric(profile1.id, run1.id, 15, 22, 500, 30),
            make_metric(profile1.id, run1.id, 18, 30, 800, 40),
            make_metric(profile1.id, run1.id, 20, 35, 1000, 50),
        ]:
            await repo.metrics.save(m)

        # ------------------ RESEARCHER 2 ------------------
        profile2 = ResearcherProfile(
            id=uuid.uuid4(),
            scholar_id="sch_2",
            orcid="0000-0000-0000-0002",
            wos_id=None,
            scopus_id=None,
            keywords=["Networks"],
            metrics=[],
            biography="Networks researcher"
        )

        user2 = User(
            id=uuid.uuid4(),
            name="Bruno Lima",
            email="bruno@isep.ipp.pt",
            active=True,
            role=UserRole.researcher,
            researcherProfile=profile2
        )
        await repo.users.save(user2)

        run2 = make_run(profile2.id)
        await repo.extraction_runs.save(run2)

        for m in [
            make_metric(profile2.id, run2.id, 8, 10, 200, 15),
            make_metric(profile2.id, run2.id, 9, 12, 250, 18),
            make_metric(profile2.id, run2.id, 11, 15, 300, 20),
            make_metric(profile2.id, run2.id, 13, 18, 400, 28),
            make_metric(profile2.id, run2.id, 16, 25, 600, 35),
        ]:
            await repo.metrics.save(m)

        # ------------------ RESEARCHER 3 ------------------
        profile3 = ResearcherProfile(
            id=uuid.uuid4(),
            scholar_id="sch_3",
            orcid="0000-0000-0000-0003",
            wos_id=None,
            scopus_id=None,
            keywords=["Security"],
            metrics=[],
            biography="Security researcher"
        )

        user3 = User(
            id=uuid.uuid4(),
            name="Carla Mendes",
            email="carla@isep.ipp.pt",
            active=True,
            role=UserRole.researcher,
            researcherProfile=profile3
        )
        await repo.users.save(user3)

        run3 = make_run(profile3.id)
        await repo.extraction_runs.save(run3)

        for m in [
            make_metric(profile3.id, run3.id, 5, 8, 100, 10),
            make_metric(profile3.id, run3.id, 6, 10, 150, 12),
            make_metric(profile3.id, run3.id, 7, 12, 200, 15),
            make_metric(profile3.id, run3.id, 9, 15, 300, 18),
            make_metric(profile3.id, run3.id, 11, 20, 450, 25),
        ]:
            await repo.metrics.save(m)

        # ------------------ RESEARCHER 4 ------------------
        profile4 = ResearcherProfile(
            id=uuid.uuid4(),
            scholar_id="sch_4",
            orcid="0000-0000-0000-0004",
            wos_id=None,
            scopus_id=None,
            keywords=["Data Science"],
            metrics=[],
            biography="Data scientist"
        )

        user4 = User(
            id=uuid.uuid4(),
            name="Diogo Rocha",
            email="diogo@isep.ipp.pt",
            active=True,
            role=UserRole.researcher,
            researcherProfile=profile4
        )
        await repo.users.save(user4)

        run4 = make_run(profile4.id)
        await repo.extraction_runs.save(run4)

        for m in [
            make_metric(profile4.id, run4.id, 14, 20, 600, 30),
            make_metric(profile4.id, run4.id, 16, 25, 700, 35),
            make_metric(profile4.id, run4.id, 18, 28, 800, 40),
            make_metric(profile4.id, run4.id, 20, 32, 900, 45),
            make_metric(profile4.id, run4.id, 22, 40, 1200, 60),
        ]:
            await repo.metrics.save(m)

        # ------------------ RESEARCHER 5 ------------------
        profile5 = ResearcherProfile(
            id=uuid.uuid4(),
            scholar_id="sch_5",
            orcid="0000-0000-0000-0005",
            wos_id=None,
            scopus_id=None,
            keywords=["Robotics"],
            metrics=[],
            biography="Robotics researcher"
        )

        user5 = User(
            id=uuid.uuid4(),
            name="Eduardo Pinto",
            email="eduardo@isep.ipp.pt",
            active=True,
            role=UserRole.researcher,
            researcherProfile=profile5
        )
        await repo.users.save(user5)

        run5 = make_run(profile5.id)
        await repo.extraction_runs.save(run5)

        for m in [
            make_metric(profile5.id, run5.id, 7, 9, 180, 14),
            make_metric(profile5.id, run5.id, 8, 11, 220, 16),
            make_metric(profile5.id, run5.id, 10, 14, 280, 19),
            make_metric(profile5.id, run5.id, 12, 18, 350, 24),
            make_metric(profile5.id, run5.id, 14, 22, 500, 30),
        ]:
            await repo.metrics.save(m)

        await repo.commit()
        print("Bootstrap concluded!")