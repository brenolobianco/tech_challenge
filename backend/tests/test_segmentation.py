from app.models import Upload, User
from app.services.campaign_service import generate_campaigns


class TestSegmentationRules:
    def _create_upload_with_user(self, db, age, income):
        upload = Upload(filename="test.csv", status="pending", total_rows=1, valid_rows=1, invalid_rows=0)
        db.add(upload)
        db.flush()
        user = User(original_id=1, name="Test", age=age, city="NYC", income=income, upload_id=upload.id)
        db.add(user)
        db.commit()
        return upload, user

    def test_starter_campaign(self, db_session):
        upload, user = self._create_upload_with_user(db_session, age=25, income=2000)
        generate_campaigns(db_session, upload.id)
        campaign_names = [c.name for c in user.campaigns]
        assert "Starter" in campaign_names

    def test_growth_campaign(self, db_session):
        upload, user = self._create_upload_with_user(db_session, age=35, income=5000)
        generate_campaigns(db_session, upload.id)
        campaign_names = [c.name for c in user.campaigns]
        assert "Growth" in campaign_names

    def test_premium_by_age(self, db_session):
        upload, user = self._create_upload_with_user(db_session, age=55, income=2000)
        generate_campaigns(db_session, upload.id)
        campaign_names = [c.name for c in user.campaigns]
        assert "Premium" in campaign_names

    def test_premium_by_income(self, db_session):
        upload, user = self._create_upload_with_user(db_session, age=30, income=15000)
        generate_campaigns(db_session, upload.id)
        campaign_names = [c.name for c in user.campaigns]
        assert "Premium" in campaign_names

    def test_high_value_youth(self, db_session):
        upload, user = self._create_upload_with_user(db_session, age=25, income=8000)
        generate_campaigns(db_session, upload.id)
        campaign_names = [c.name for c in user.campaigns]
        assert "High Value Youth" in campaign_names

    def test_overlap_premium_and_high_value_youth(self, db_session):
        upload, user = self._create_upload_with_user(db_session, age=25, income=8000)
        generate_campaigns(db_session, upload.id)
        campaign_names = [c.name for c in user.campaigns]
        assert "Premium" in campaign_names
        assert "High Value Youth" in campaign_names

    def test_boundary_age_30_income_3000_is_growth(self, db_session):
        upload, user = self._create_upload_with_user(db_session, age=30, income=3000)
        generate_campaigns(db_session, upload.id)
        campaign_names = [c.name for c in user.campaigns]
        assert "Growth" in campaign_names
        assert "Starter" not in campaign_names

    def test_boundary_age_50_income_10000_is_growth(self, db_session):
        upload, user = self._create_upload_with_user(db_session, age=50, income=10000)
        generate_campaigns(db_session, upload.id)
        campaign_names = [c.name for c in user.campaigns]
        assert "Growth" in campaign_names

    def test_idempotency(self, db_session):
        upload, user = self._create_upload_with_user(db_session, age=25, income=8000)
        generate_campaigns(db_session, upload.id)
        generate_campaigns(db_session, upload.id)
        campaign_names = [c.name for c in user.campaigns]
        assert campaign_names.count("Premium") == 1
        assert campaign_names.count("High Value Youth") == 1

    def test_no_campaigns_for_unmatched_user(self, db_session):
        upload, user = self._create_upload_with_user(db_session, age=30, income=2999)
        generate_campaigns(db_session, upload.id)
        campaign_names = [c.name for c in user.campaigns]
        assert len(campaign_names) == 0
