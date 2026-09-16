"""
Backend test configuration and fixtures
"""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.entities import User, Customer, Application, Document, Job, FaceVerification
from app.core.security import hash_password
from app.domain.enums import RoleName, ApplicationStatus


# Use in-memory SQLite for tests with StaticPool to share connection
TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Session:
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """Create a test client with overridden database dependency"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session: Session) -> User:
    """Create an admin user"""
    user = User(
        email="admin@test.com",
        full_name="Admin User",
        hashed_password=hash_password("admin123"),
        role=RoleName.ADMIN.value,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def analyst_user(db_session: Session) -> User:
    """Create an analyst user"""
    user = User(
        email="analyst@test.com",
        full_name="Analyst User",
        hashed_password=hash_password("analyst123"),
        role=RoleName.ANALYST.value,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def reviewer_user(db_session: Session) -> User:
    """Create a reviewer user"""
    user = User(
        email="reviewer@test.com",
        full_name="Reviewer User",
        hashed_password=hash_password("reviewer123"),
        role=RoleName.REVIEWER.value,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def applicant_user(db_session: Session) -> User:
    """Create an applicant user with customer profile"""
    user = User(
        email="applicant@test.com",
        full_name="Applicant User",
        hashed_password=hash_password("applicant123"),
        role=RoleName.APPLICANT.value,
    )
    db_session.add(user)
    db_session.flush()
    
    customer = Customer(
        user_id=user.id,
        first_name="Applicant",
        last_name="User",
        national_id="0012345679",
        nationality="ایران",
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(applicant_user: User, db_session: Session) -> dict:
    """Create authorization headers for applicant"""
    from app.core.security import create_access_token
    token = create_access_token(applicant_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user: User) -> dict:
    """Create authorization headers for admin"""
    from app.core.security import create_access_token
    token = create_access_token(admin_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def reviewer_headers(reviewer_user: User) -> dict:
    """Create authorization headers for reviewer"""
    from app.core.security import create_access_token
    token = create_access_token(reviewer_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_application(db_session: Session, applicant_user: User) -> Application:
    """Create a sample application"""
    customer = db_session.query(Customer).filter(Customer.user_id == applicant_user.id).first()
    app = Application(
        application_number="APP-1001",
        customer_id=customer.id,
        status=ApplicationStatus.DRAFT.value,
        source="web",
        current_step="personal",
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)
    return app


@pytest.fixture
def submitted_application(db_session: Session, applicant_user: User) -> Application:
    """Create a submitted application"""
    customer = db_session.query(Customer).filter(Customer.user_id == applicant_user.id).first()
    app = Application(
        application_number="APP-1002",
        customer_id=customer.id,
        status=ApplicationStatus.SUBMITTED.value,
        source="web",
        current_step="submit",
        submitted_at=datetime.now(timezone.utc),
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)
    return app


from datetime import datetime, timezone