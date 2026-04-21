"""
Tests for Customer Booking Service
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from unittest.mock import AsyncMock, patch

from app.main import app
from app.db.session import get_db
from app.db.base import Base


# ─── Fixtures ──────────────────────────────────────────────────────────────────
TEST_DB_URL = "postgresql+asyncpg://test:test@localhost/test_booking_db"


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(TEST_DB_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    mock_user = {"user_id": "test-user-123", "role": "CUSTOMER", "email": "test@example.com"}

    with patch("app.core.auth.get_current_user", return_value=mock_user):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            yield c

    app.dependency_overrides.clear()


# ─── Booking creation tests ────────────────────────────────────────────────────
VALID_BOOKING = {
    "sender_name": "Ravi Kumar",
    "sender_phone": "9876543210",
    "sender_address_line1": "123 MG Road",
    "sender_city": "Chennai",
    "sender_state": "Tamil Nadu",
    "sender_pincode": "600001",
    "receiver_name": "Priya Singh",
    "receiver_phone": "9123456789",
    "receiver_address_line1": "45 Bandra West",
    "receiver_city": "Mumbai",
    "receiver_state": "Maharashtra",
    "receiver_pincode": "400050",
    "weight_kg": 2.5,
    "contents_description": "Electronics",
    "service_type": "STANDARD",
    "payment_mode": "PREPAID",
    "pickup_date": "2026-05-01",
}


@pytest.mark.asyncio
async def test_create_booking_success(client):
    with patch("app.core.kafka_producer.kafka_producer.publish", new_callable=AsyncMock):
        response = await client.post("/api/v1/bookings/", json=VALID_BOOKING)

    assert response.status_code == 201
    data = response.json()
    assert data["awb_number"].startswith("SS")
    assert len(data["awb_number"]) >= 16
    assert data["status"] == "BOOKING_CREATED"
    assert data["sender_city"] == "Chennai"
    assert data["receiver_city"] == "Mumbai"
    assert data["total_charge"] > 0


@pytest.mark.asyncio
async def test_create_booking_invalid_phone(client):
    payload = {**VALID_BOOKING, "sender_phone": "1234567890"}  # Invalid (doesn't start with 6-9)
    response = await client.post("/api/v1/bookings/", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_booking_invalid_pincode(client):
    payload = {**VALID_BOOKING, "receiver_pincode": "12345"}  # Only 5 digits
    response = await client.post("/api/v1/bookings/", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_cod_booking_requires_cod_amount(client):
    payload = {**VALID_BOOKING, "payment_mode": "COD"}  # Missing cod_amount
    response = await client.post("/api/v1/bookings/", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_cod_booking_success(client):
    payload = {**VALID_BOOKING, "payment_mode": "COD", "cod_amount": 1500.0}
    with patch("app.core.kafka_producer.kafka_producer.publish", new_callable=AsyncMock):
        response = await client.post("/api/v1/bookings/", json=payload)
    assert response.status_code == 201
    assert response.json()["payment_mode"] == "COD"


@pytest.mark.asyncio
async def test_list_bookings_empty(client):
    response = await client.get("/api/v1/bookings/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_booking_by_awb(client):
    with patch("app.core.kafka_producer.kafka_producer.publish", new_callable=AsyncMock):
        create_res = await client.post("/api/v1/bookings/", json=VALID_BOOKING)
    awb = create_res.json()["awb_number"]

    get_res = await client.get(f"/api/v1/bookings/{awb}")
    assert get_res.status_code == 200
    assert get_res.json()["awb_number"] == awb


@pytest.mark.asyncio
async def test_get_nonexistent_booking(client):
    response = await client.get("/api/v1/bookings/SS999999999999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_booking(client):
    with patch("app.core.kafka_producer.kafka_producer.publish", new_callable=AsyncMock):
        create_res = await client.post("/api/v1/bookings/", json=VALID_BOOKING)
    awb = create_res.json()["awb_number"]

    cancel_res = await client.post(
        f"/api/v1/bookings/{awb}/cancel",
        json={"reason": "Customer requested cancellation"},
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["awb_number"] == awb


# ─── Pricing tests ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_calculate_price(client):
    response = await client.post(
        "/api/v1/pricing/calculate",
        json={
            "sender_pincode": "600001",
            "receiver_pincode": "400050",
            "weight_kg": 2.0,
            "service_type": "STANDARD",
            "payment_mode": "PREPAID",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_charge"] > 0
    assert data["zone"] in ["A", "B", "C", "D", "E"]
    assert "all_services" in data


@pytest.mark.asyncio
async def test_calculate_price_cod_surcharge(client):
    prepaid_res = await client.post(
        "/api/v1/pricing/calculate",
        json={"sender_pincode": "600001", "receiver_pincode": "400050",
              "weight_kg": 2.0, "service_type": "STANDARD", "payment_mode": "PREPAID"},
    )
    cod_res = await client.post(
        "/api/v1/pricing/calculate",
        json={"sender_pincode": "600001", "receiver_pincode": "400050",
              "weight_kg": 2.0, "service_type": "STANDARD", "payment_mode": "COD",
              "cod_amount": 1000},
    )
    assert cod_res.json()["total_charge"] > prepaid_res.json()["total_charge"]


@pytest.mark.asyncio
async def test_serviceability_check(client):
    response = await client.get("/api/v1/pricing/serviceability/600001")
    assert response.status_code == 200
    data = response.json()
    assert data["serviceable"] is True
    assert "available_services" in data


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ─── AWB utility tests ─────────────────────────────────────────────────────────
def test_awb_generation():
    from shared.utils.awb import generate_awb, validate_awb
    awb = generate_awb("SS")
    assert awb.startswith("SS")
    assert len(awb) >= 16
    assert validate_awb(awb)


def test_awb_uniqueness():
    from shared.utils.awb import generate_awb
    awbs = {generate_awb("SS") for _ in range(1000)}
    assert len(awbs) > 990  # Allow minimal collision probability


def test_volumetric_weight():
    from shared.utils.awb import calculate_volumetric_weight, get_chargeable_weight
    vol = calculate_volumetric_weight(30, 20, 15)
    assert vol == pytest.approx(1.8)
    assert get_chargeable_weight(1.0, 1.8) == 1.8
    assert get_chargeable_weight(2.0, 1.8) == 2.0
