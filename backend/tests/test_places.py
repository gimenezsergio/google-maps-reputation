import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.config import settings
from app.core.database import Base
from app.api.deps import get_current_super_admin, get_db as deps_get_db
from app.models.user import User, UserRole
from app.models.commerce import Commerce
from app.models.feedback import Feedback
from app.api.admin import _normalize_google_place_ref

# --- DATABASE SETUP FOR TESTING ---
from sqlalchemy.pool import StaticPool

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Define mock super admin
mock_admin = User(id=999, username="admin_test", role=UserRole.SUPER_ADMIN)


def override_current_super_admin():
    return mock_admin


# Apply overrides to the app
app.dependency_overrides[deps_get_db] = override_get_db
app.dependency_overrides[get_current_super_admin] = override_current_super_admin

client = TestClient(app)


class TestPlacesReputation(unittest.TestCase):

    def setUp(self):
        # Create all tables in memory before each test
        Base.metadata.create_all(bind=test_engine)
        
        # Save original API Key to restore later
        self.original_api_key = settings.GOOGLE_PLACES_API_KEY
        settings.GOOGLE_PLACES_API_KEY = "test-api-key-12345"

    def tearDown(self):
        # Restore settings
        settings.GOOGLE_PLACES_API_KEY = self.original_api_key
        
        # Drop all tables in memory
        Base.metadata.drop_all(bind=test_engine)

    def test_normalize_place_ref(self):
        # Test ChIJ place ID should be conserved as-is
        chij_id = "ChIJP3Sa8VgpGo8RkFaZq5RfGkY"
        self.assertEqual(_normalize_google_place_ref(chij_id), chij_id)

        # Test hex ref should be converted to write-review URL
        hex_ref = "0x95bcb7cc9d854b17:0x94e08a6cf1d26cb9"
        expected_hex_url = f"https://www.google.com/maps/place//data=!4m3!3m2!1s{hex_ref}!12e1"
        self.assertEqual(_normalize_google_place_ref(hex_ref), expected_hex_url)

        # Test maps URL containing hex ref
        maps_url = "https://www.google.com/maps/place/Caf%C3%A9+de+la+Plaza/@-34.6015792,-58.5144865,17z/data=!4m6!3m5!1s0x95bcb7cc9d854b17:0x94e08a6cf1d26cb9!8m2!3d-34.6015792!4d-58.5119116!16s%2Fg%2F11b6s6l6x2"
        self.assertEqual(_normalize_google_place_ref(maps_url), expected_hex_url)

        # Test generic URL remains as-is
        generic_url = "https://example.com/some-page"
        self.assertEqual(_normalize_google_place_ref(generic_url), generic_url)

    @patch("httpx.Client.post")
    def test_search_places_success(self, mock_post):
        # Setup mock response from Google Places API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "places": [
                {
                    "id": "ChIJP3Sa8VgpGo8RkFaZq5RfGkY",
                    "displayName": {"text": "Café de la Plaza Devoto", "languageCode": "es"},
                    "formattedAddress": "Av. Lincoln 3990, Buenos Aires"
                }
            ]
        }
        mock_post.return_value = mock_response

        # Request to our endpoint
        response = client.get("/api/v1/admin/search-places?q=Cafe de la Plaza Devoto")
        
        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Café de la Plaza Devoto")
        self.assertEqual(results[0]["address"], "Av. Lincoln 3990, Buenos Aires")
        self.assertEqual(results[0]["google_place_id"], "ChIJP3Sa8VgpGo8RkFaZq5RfGkY")

        # Verify Google API was called correctly
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://places.googleapis.com/v1/places:searchText")
        self.assertEqual(kwargs["headers"]["X-Goog-Api-Key"], "test-api-key-12345")
        self.assertEqual(kwargs["json"]["textQuery"], "Cafe de la Plaza Devoto")

    def test_search_places_missing_api_key(self):
        # Unset API key
        settings.GOOGLE_PLACES_API_KEY = ""

        response = client.get("/api/v1/admin/search-places?q=Cafe")
        self.assertEqual(response.status_code, 400)
        self.assertIn("La API Key de Google Places no está configurada", response.json()["detail"])

    @patch("httpx.Client.post")
    def test_search_places_google_error(self, mock_post):
        # Setup mock response indicating error from Google
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "API key not valid."
        mock_post.return_value = mock_response

        response = client.get("/api/v1/admin/search-places?q=Cafe")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Google Places API retornó error 403", response.json()["detail"])

    def test_create_commerce_saving_chij(self):
        chij_id = "ChIJP3Sa8VgpGo8RkFaZq5RfGkY"
        commerce_data = {
            "name": "Café de la Plaza Devoto",
            "slug": "cafe-de-la-plaza-devoto",
            "logo_url": "https://example.com/logo.png",
            "google_place_id": chij_id,
            "tags": ["cafeteria", "desayuno"],
            "admin_username": "devoto_admin",
            "admin_password": "SecurePassword123!"
        }

        # Call creation endpoint
        response = client.post("/api/v1/admin/commerce", json=commerce_data)
        self.assertEqual(response.status_code, 200)
        
        # Verify response structure and database storage
        res_data = response.json()
        self.assertEqual(res_data["google_place_id"], chij_id)
        self.assertEqual(res_data["slug"], "cafe-de-la-plaza-devoto")

        # Directly query DB to confirm
        db = next(override_get_db())
        saved_commerce = db.query(Commerce).filter(Commerce.slug == "cafe-de-la-plaza-devoto").first()
        self.assertIsNotNone(saved_commerce)
        self.assertEqual(saved_commerce.google_place_id, chij_id)
        db.close()

    def test_generate_google_maps_url_logic(self):
        # Simulate the python-based URL generation logic matching frontend
        def build_url(place_id, name=""):
            if place_id.startswith("ChIJ"):
                import urllib.parse
                return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(name)}&query_place_id={place_id}"
            return place_id

        chij_id = "ChIJP3Sa8VgpGo8RkFaZq5RfGkY"
        name = "Café de la Plaza Devoto"
        generated_url = build_url(chij_id, name)
        
        expected_url = "https://www.google.com/maps/search/?api=1&query=Caf%C3%A9%20de%20la%20Plaza%20Devoto&query_place_id=ChIJP3Sa8VgpGo8RkFaZq5RfGkY"
        self.assertEqual(generated_url, expected_url)


if __name__ == "__main__":
    unittest.main()
