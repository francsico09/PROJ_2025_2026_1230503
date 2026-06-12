import pytest
import uuid
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Setup Environment Variables for Tests
os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///:memory:')
os.environ.setdefault('LDAP_HOST', 'localhost')
os.environ.setdefault('LDAP_PORT', '389')
os.environ.setdefault('LDAP_BASE_DN', 'dc=example,dc=com')
os.environ.setdefault('LDAP_ADMIN_DN', 'cn=admin,dc=example,dc=com')
os.environ.setdefault('LDAP_ADMIN_PASSWORD', 'password')
os.environ.setdefault('LDAP_PEOPLE_OU', 'ou=people')
os.environ.setdefault('JWT_SECRET', 'test-secret-key-for-testing')
os.environ.setdefault('JWT_ALGORITHM', 'HS256')
os.environ.setdefault('JWT_EXPIRE_MINUTES', '480')
os.environ.setdefault('ORCID_CLIENT_ID', '')
os.environ.setdefault('ORCID_CLIENT_SECRET', '')
os.environ.setdefault('ORCID_BASE_URL', 'https://pub.orcid.org/v3.0')
os.environ.setdefault('SCHOLAR_BASE_URL', 'https://scholar.google.com/citations')
os.environ.setdefault('SCOPUS_API_KEY', 'test-key')
os.environ.setdefault('SCOPUS_BASE_URL', 'https://api.elsevier.com/content')
os.environ.setdefault('SCOPUS_INST_TOKEN', '')
os.environ.setdefault('WOS_API_KEY', 'test-key')
os.environ.setdefault('WOS_BASE_URL', 'https://api.clarivate.com/apis/wos-starter/v1')
os.environ.setdefault('DEBUG', 'False')

from src.core.domain.extraction_run.extraction_run_model.extraction_run_model import ExtractionRun, \
    ExtractionTrigger, ExtractionStatus
from src.core.domain.pagination.schema.pagination_schema import PaginationParams
from src.core.domain.researcher_metric.researcher_metric_model.researcher_metric_model import ResearcherMetric
from src.core.domain.researcher_metric.researcher_metric_model.source_model import Source, SourceName
from src.core.domain.researcher_profile.researcher_profile_model.reasearcher_profile_model import \
    ResearcherProfile
from src.core.domain.user.user_model.user_model import User
from src.core.domain.user.user_model.user_role import UserRole


# User Fixtures
@pytest.fixture
def user_id():
    """Gera um UUID para testes."""
    return uuid.uuid4()


@pytest.fixture
def user_data(user_id):
    """Cria dados de exemplo para um usuário."""
    return {
        'id': user_id,
        'name': 'João Silva',
        'email': 'joao@example.com',
        'active': True,
        'role': UserRole.researcher,
        'researcherProfile': None
    }


@pytest.fixture
def sample_user(user_data):
    """Cria uma instância de usuário para testes."""
    return User(**user_data)


@pytest.fixture
def sample_admin_user():
    """Cria um usuário admin para testes."""
    return User(
        id=uuid.uuid4(),
        name='Admin User',
        email='admin@example.com',
        active=True,
        role=UserRole.admin,
        researcherProfile=None
    )


# Researcher Profile Fixtures
@pytest.fixture
def profile_id():
    """Gera um UUID para o perfil."""
    return uuid.uuid4()


@pytest.fixture
def profile_data(profile_id):
    """Cria dados de exemplo para um perfil de pesquisador."""
    return {
        'id': profile_id,
        'keywords': ['machine learning', 'AI'],
        'metrics': [],
        'scholar_id': 'scholar_123',
        'orcid': '0000-0001-2345-6789',
        'wos_id': 'wos_123',
        'scopus_id': 'scopus_123',
        'biography': 'Pesquisador em IA',
        'affiliation': 'Universidade XYZ'
    }


@pytest.fixture
def sample_profile(profile_data):
    """Cria uma instância de perfil para testes."""
    return ResearcherProfile(**profile_data)



# Researcher Metric Fixtures
@pytest.fixture
def metric_id():
    """Gera um UUID para a métrica."""
    return uuid.uuid4()


@pytest.fixture
def metric_data(metric_id, profile_id):
    """Cria dados de exemplo para uma métrica de pesquisador."""
    return {
        'id': metric_id,
        'researcher_id': profile_id,
        'extraction_run_id': uuid.uuid4(),
        'source': Source(SourceName.scholar, url='https://scholar.google.com'),
        'date': datetime.now(timezone.utc),
        'h_index': 15,
        'total_citations': 500,
        'total_publications': 30,
        'i10_index': 10,
        'i10_index_5y': 8,
        'h_index_5y': 10,
        'citations_5y': 200,
        'cites_per_year': {'2022': 50, '2023': 75},
        'publications': []
    }


@pytest.fixture
def sample_metric(metric_data):
    """Cria uma instância de métrica para testes."""
    return ResearcherMetric(**metric_data)



# Extraction Run Fixtures
@pytest.fixture
def extraction_run_id():
    """Gera um UUID para o extraction run."""
    return uuid.uuid4()


@pytest.fixture
def sample_extraction_run(extraction_run_id, profile_id):
    """Cria um extraction run para testes."""
    return ExtractionRun(
        id=extraction_run_id,
        researcher_id=profile_id,
        triggered_at=datetime.now(timezone.utc),
        triggered_by=ExtractionTrigger.created_by_admin,
        status=ExtractionStatus.completed,
        sources_attempted=[SourceName.scholar],
        sources_succeeded=[SourceName.scholar]
    )


# Repository Fixtures
@pytest.fixture
def mock_repos():
    """Cria um mock das repositories com contexto assíncrono."""
    repos = AsyncMock()
    repos.users = AsyncMock()
    repos.profiles = AsyncMock()
    repos.metrics = AsyncMock()
    repos.extraction_runs = AsyncMock()
    repos.commit = AsyncMock()
    repos.rollback = AsyncMock()
    repos.__aenter__ = AsyncMock(return_value=repos)
    repos.__aexit__ = AsyncMock(return_value=None)
    return repos


@pytest.fixture
def mock_ldap_service():
    """Cria um mock do serviço LDAP."""
    ldap_service = MagicMock()
    ldap_service.exists_with_email = MagicMock(return_value=True)
    return ldap_service


# Pagination Fixtures
@pytest.fixture
def pagination_params():
    """Cria parâmetros de paginação para testes."""
    return PaginationParams(page=1, page_size=20)


@pytest.fixture
def paginated_result_empty():
    """Cria um resultado paginado vazio para testes."""
    result = MagicMock()
    result.items = []
    result.total = 0
    result.page = 1
    result.page_size = 20
    result.pages = 0
    return result


@pytest.fixture
def paginated_result_with_item(sample_user):
    """Cria um resultado paginado com um item para testes."""
    result = MagicMock()
    result.items = [sample_user]
    result.total = 1
    result.page = 1
    result.page_size = 20
    result.pages = 1
    return result

