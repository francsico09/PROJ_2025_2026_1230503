import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_test_env():
    """Configura variáveis de ambiente para testes"""
    test_env = {
        'DATABASE_URL': 'sqlite+aiosqlite:///:memory:',
        'LDAP_HOST': 'localhost',
        'LDAP_PORT': '389',
        'LDAP_BASE_DN': 'dc=example,dc=com',
        'LDAP_ADMIN_DN': 'cn=admin,dc=example,dc=com',
        'LDAP_ADMIN_PASSWORD': 'password',
        'LDAP_PEOPLE_OU': 'ou=people',
        'JWT_SECRET': 'test-secret-key-for-testing',
        'JWT_ALGORITHM': 'HS256',
        'JWT_EXPIRE_MINUTES': '480',
        'ORCID_CLIENT_ID': '',
        'ORCID_CLIENT_SECRET': '',
        'ORCID_BASE_URL': 'https://pub.orcid.org/v3.0',
        'SCHOLAR_BASE_URL': 'https://scholar.google.com/citations',
        'SCOPUS_API_KEY': 'test-key',
        'SCOPUS_BASE_URL': 'https://api.elsevier.com/content',
        'SCOPUS_INST_TOKEN': '',
        'WOS_API_KEY': 'test-key',
        'WOS_BASE_URL': 'https://api.clarivate.com/apis/wos-starter/v1',
        'DEBUG': 'False'
    }

    # Atualiza variáveis de ambiente
    for key, value in test_env.items():
        os.environ[key] = value

    return test_env

if __name__ == '__main__':
    # Configura variáveis
    setup_test_env()

    # Executa pytest com argumentos passados
    cmd = ['pytest'] + sys.argv[1:]
    sys.exit(subprocess.call(cmd))

