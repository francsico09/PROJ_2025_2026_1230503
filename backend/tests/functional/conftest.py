"""
Conftest for functional tests.
This module provides fixtures specific to functional testing, including:
- FastAPI TestClient
- In-memory database setup
- Test user and profile fixtures
- Authentication tokens
"""
import pytest
import sys
import os
import uuid
from datetime import datetime, timezone
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event
from sqlalchemy.pool import StaticPool

# Add backend to path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Set environment variables for tests BEFORE importing main
# Using PostgreSQL if available, otherwise SQLite
# IMPORTANTE: For functional testing, PostgreSQL is recommended
# To use local PostgreSQL: TEST_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/test_db
# Or set up PostgreSQL in Docker (see docker-compose.yml in the project root)

db_url = os.environ.get('TEST_DATABASE_URL')
if not db_url:
    # Default to in-memory SQLite
    # Note: This has limitations with PostgreSQL-specific types like ARRAY
    db_url = 'sqlite+aiosqlite:///:memory:'
    print(f"⚠️  Using in-memory SQLite. For full compatibility, use PostgreSQL:")
    print(f"   TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/test_db")

os.environ['DATABASE_URL'] = db_url

os.environ.setdefault('LDAP_HOST', 'localhost')
os.environ.setdefault('LDAP_PORT', '389')
os.environ.setdefault('LDAP_BASE_DN', 'dc=example,dc=com')
os.environ.setdefault('LDAP_ADMIN_DN', 'cn=admin,dc=example,dc=com')
os.environ.setdefault('LDAP_ADMIN_PASSWORD', 'password')
os.environ.setdefault('LDAP_PEOPLE_OU', 'ou=people')
os.environ.setdefault('JWT_SECRET', 'test-secret-key-for-testing')
os.environ.setdefault('JWT_ALGORITHM', 'HS256')
os.environ.setdefault('JWT_EXPIRE_MINUTES', '480')
os.environ.setdefault('DEBUG', 'False')
os.environ.setdefault('ORCID_CLIENT_ID', '')
os.environ.setdefault('ORCID_CLIENT_SECRET', '')
os.environ.setdefault('ORCID_BASE_URL', 'https://pub.orcid.org/v3.0')
os.environ.setdefault('SCHOLAR_BASE_URL', 'https://scholar.google.com/citations')
os.environ.setdefault('SCOPUS_API_KEY', 'test-key')
os.environ.setdefault('SCOPUS_BASE_URL', 'https://api.elsevier.com/content')
os.environ.setdefault('SCOPUS_INST_TOKEN', '')
os.environ.setdefault('WOS_API_KEY', 'test-key')
os.environ.setdefault('WOS_BASE_URL', 'https://api.clarivate.com/apis/wos-starter/v1')

from main import app
from src.database.base.base import Base
from src.core.domain.user.user_model.user_model import User
from src.core.domain.user.user_model.user_role import UserRole
from src.core.domain.researcher_profile.researcher_profile_model.reasearcher_profile_model import ResearcherProfile
from src.core.domain.researcher_metric.researcher_metric_model.researcher_metric_model import ResearcherMetric
from src.core.domain.researcher_metric.researcher_metric_model.source_model import Source, SourceName
from src.core.settings.settings import settings


@pytest.fixture
async def test_engine():
    """Create a test database engine.
    
    By default uses in-memory SQLite, but can be overridden with TEST_DATABASE_URL env var.
    For PostgreSQL support, set: TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/test_db
    """
    # Use a StaticPool for SQLite to avoid threading issues
    connect_args = {}
    poolclass = None
    
    if 'sqlite' in settings.DATABASE_URL:
        connect_args = {"check_same_thread": False}
        poolclass = StaticPool
    
    test_engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        connect_args=connect_args,
        poolclass=poolclass,
    )
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield test_engine
    
    await test_engine.dispose()


@pytest.fixture
async def async_session_factory(test_engine):
    """Create an async session maker for the test database."""
    factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    return factory


@pytest.fixture
async def client(test_engine, async_session_factory):
    """Create a test client with configured test database."""
    # Import and patch the session factory used by the app
    from src.core import session as session_module
    original_factory = session_module.AsyncSessionFactory
    session_module.AsyncSessionFactory = async_session_factory
    
    try:
        async with AsyncClient(app=app, base_url="http://test") as test_client:
            yield test_client
    finally:
        # Restore original factory
        session_module.AsyncSessionFactory = original_factory


@pytest.fixture
async def test_admin_user(async_session_factory):
    """Create a test admin user in the database."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        name='Admin Test User',
        email=f'admin.test.{user_id}@test.com',
        active=True,
        role=UserRole.admin,
        password_hash='hashed_password'
    )
    
    async with async_session_factory() as session:
        session.add(user)
        await session.commit()
    
    return user


@pytest.fixture
async def test_researcher_user(async_session_factory):
    """Create a test researcher user in the database."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        name='Researcher Test User',
        email=f'researcher.test.{user_id}@test.com',
        active=True,
        role=UserRole.researcher,
        password_hash='hashed_password'
    )
    
    async with async_session_factory() as session:
        session.add(user)
        await session.commit()
    
    return user


@pytest.fixture
def admin_token(test_admin_user):
    """Generate a JWT token for the admin user."""
    from jose import jwt
    payload = {
        "sub": str(test_admin_user.id),
        "email": test_admin_user.email,
        "role": test_admin_user.role.value,
    }
    token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


@pytest.fixture
def researcher_token(test_researcher_user):
    """Generate a JWT token for the researcher user."""
    from jose import jwt
    payload = {
        "sub": str(test_researcher_user.id),
        "email": test_researcher_user.email,
        "role": test_researcher_user.role.value,
    }
    token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


@pytest.fixture
async def test_researcher_profile(async_session_factory):
    """Create a test researcher profile in the database."""
    profile_id = uuid.uuid4()
    profile = ResearcherProfile(
        id=profile_id,
        keywords=['machine learning', 'AI'],
        scholar_id='scholar_123',
        orcid='0000-0001-2345-6789',
        wos_id='wos_123',
        scopus_id='scopus_123',
        biography='Test researcher',
        affiliation='Test University'
    )
    
    async with async_session_factory() as session:
        session.add(profile)
        await session.commit()
    
    return profile


@pytest.fixture
async def test_researcher_metric(async_session_factory, test_researcher_profile):
    """Create a test researcher metric in the database."""
    metric_id = uuid.uuid4()
    metric = ResearcherMetric(
        id=metric_id,
        researcher_id=test_researcher_profile.id,
        extraction_run_id=uuid.uuid4(),
        source=Source(SourceName.scholar, url='https://scholar.google.com'),
        date=datetime.now(timezone.utc),
        h_index=15,
        total_citations=500,
        total_publications=30,
        i10_index=10,
        i10_index_5y=8,
        h_index_5y=10,
        citations_5y=200,
    )
    
    async with async_session_factory() as session:
        session.add(metric)
        await session.commit()
    
    return metric


@pytest.fixture
def mock_ldap_service():
    """Mock LDAP service for authentication tests."""
    service = AsyncMock()
    service.authenticate.return_value = True
    service.exists_with_email = AsyncMock(return_value=True)
    service.get_user_by_email = AsyncMock(return_value={
        'id': str(uuid.uuid4()),
        'name': 'Test User',
        'email': 'test@test.com',
        'role': 'researcher'
    })
    return service


@pytest.fixture
async def test_engine():
    """Create a test database engine.
    
    By default uses in-memory SQLite, but can be overridden with TEST_DATABASE_URL env var.
    For PostgreSQL support, set: TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/test_db
    """
    # Use a StaticPool for SQLite to avoid threading issues
    connect_args = {}
    poolclass = None
    
    if 'sqlite' in settings.DATABASE_URL:
        connect_args = {"check_same_thread": False}
        from sqlalchemy.pool import StaticPool
        poolclass = StaticPool
    
    test_engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        connect_args=connect_args,
        poolclass=poolclass,
    )
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield test_engine
    
    await test_engine.dispose()


@pytest.fixture
async def async_session_factory(test_engine):
    """Create an async session maker for the test database."""
    factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    return factory


@pytest.fixture
async def client(test_engine, async_session_factory):
    """Create a test client with configured test database."""
    # Import and patch the session factory used by the app
    from src.core import session as session_module
    original_factory = session_module.AsyncSessionFactory
    session_module.AsyncSessionFactory = async_session_factory
    
    try:
        async with AsyncClient(app=app, base_url="http://test") as test_client:
            yield test_client
    finally:
        # Restore original factory
        session_module.AsyncSessionFactory = original_factory


@pytest.fixture
async def test_admin_user(async_session_factory):
    """Create a test admin user in the database."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        name='Admin Test User',
        email=f'admin.test.{user_id}@test.com',
        active=True,
        role=UserRole.admin,
        password_hash='hashed_password'
    )
    
    async with async_session_factory() as session:
        session.add(user)
        await session.commit()
    
    return user


@pytest.fixture
async def test_researcher_user(async_session_factory):
    """Create a test researcher user in the database."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        name='Researcher Test User',
        email=f'researcher.test.{user_id}@test.com',
        active=True,
        role=UserRole.researcher,
        password_hash='hashed_password'
    )
    
    async with async_session_factory() as session:
        session.add(user)
        await session.commit()
    
    return user


@pytest.fixture
def admin_token(test_admin_user):
    """Generate a JWT token for the admin user."""
    from jose import jwt
    payload = {
        "sub": str(test_admin_user.id),
        "email": test_admin_user.email,
        "role": test_admin_user.role.value,
    }
    token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


@pytest.fixture
def researcher_token(test_researcher_user):
    """Generate a JWT token for the researcher user."""
    from jose import jwt
    payload = {
        "sub": str(test_researcher_user.id),
        "email": test_researcher_user.email,
        "role": test_researcher_user.role.value,
    }
    token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


@pytest.fixture
async def test_researcher_profile(async_session_factory):
    """Create a test researcher profile in the database."""
    profile_id = uuid.uuid4()
    profile = ResearcherProfile(
        id=profile_id,
        keywords=['machine learning', 'AI'],
        scholar_id='scholar_123',
        orcid='0000-0001-2345-6789',
        wos_id='wos_123',
        scopus_id='scopus_123',
        biography='Test researcher',
        affiliation='Test University'
    )
    
    async with async_session_factory() as session:
        session.add(profile)
        await session.commit()
    
    return profile


@pytest.fixture
async def test_researcher_metric(async_session_factory, test_researcher_profile):
    """Create a test researcher metric in the database."""
    metric_id = uuid.uuid4()
    metric = ResearcherMetric(
        id=metric_id,
        researcher_id=test_researcher_profile.id,
        extraction_run_id=uuid.uuid4(),
        source=Source(SourceName.scholar, url='https://scholar.google.com'),
        date=datetime.now(timezone.utc),
        h_index=15,
        total_citations=500,
        total_publications=30,
        i10_index=10,
        i10_index_5y=8,
        h_index_5y=10,
        citations_5y=200,
    )
    
    async with async_session_factory() as session:
        session.add(metric)
        await session.commit()
    
    return metric


@pytest.fixture
def mock_ldap_service():
    """Mock LDAP service for authentication tests."""
    service = AsyncMock()
    service.authenticate.return_value = True
    service.exists_with_email = AsyncMock(return_value=True)
    service.get_user_by_email = AsyncMock(return_value={
        'id': str(uuid.uuid4()),
        'name': 'Test User',
        'email': 'test@test.com',
        'role': 'researcher'
    })
    return service





