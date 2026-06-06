import pytest
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from mortgage.models import SavedScenario

User = get_user_model()

LIST_URL = '/api/mortgage/scenarios/'


def detail_url(scenario_id):
    return f'{LIST_URL}{scenario_id}/'


def valid_loan(**overrides):
    """A valid variable P&I loan payload; override individual fields per test."""
    loan = {
        'loan_amount': '650000.00',
        'annual_rate': '6.20',
        'rate_type': 'variable',
        'repayment_type': 'principal_and_interest',
        'repayment_frequency': 'monthly',
        'loan_term_years': 30,
    }
    loan.update(overrides)
    return loan


@pytest.fixture
def user(db):
    return User.objects.create(auth0_id='auth0|alice', email='alice@example.com', username='alice')


@pytest.fixture
def other_user(db):
    return User.objects.create(auth0_id='auth0|bob', email='bob@example.com', username='bob')


@pytest.fixture
def client(user):
    """An APIClient authenticated as `user`, bypassing Auth0 JWT validation."""
    api = APIClient()
    api.force_authenticate(user=user)
    return api


class TestScenarioCreate:
    def test_create_with_loan_persists_split(self, client):
        resp = client.post(LIST_URL, {'name': 'First home', 'loan': valid_loan()}, format='json')

        assert resp.status_code == 201
        body = resp.json()
        assert body['name'] == 'First home'
        assert len(body['splits']) == 1

        split = body['splits'][0]
        assert split['loan_amount'] == '650000.00'
        assert split['repayment_frequency'] == 'monthly'
        # Computed fields are populated by the calculator service, not the client.
        assert float(split['repayment_amount']) > 0
        assert float(split['total_interest']) > 0
        assert float(split['total_repayment']) > 0

        # 'loan' is write-only — it must not leak back into the response.
        assert 'loan' not in body

    def test_create_without_loan_is_rejected(self, client):
        resp = client.post(LIST_URL, {'name': 'No loan'}, format='json')

        assert resp.status_code == 400
        assert 'loan' in resp.json()
        assert SavedScenario.objects.count() == 0

    def test_create_fixed_without_revert_rate_is_rejected(self, client):
        loan = valid_loan(rate_type='fixed', fixed_rate_period_years=3)  # missing revert_rate
        resp = client.post(LIST_URL, {'name': 'Bad fixed', 'loan': loan}, format='json')

        assert resp.status_code == 400
        assert SavedScenario.objects.count() == 0

    def test_create_requires_authentication(self, user):
        resp = APIClient().post(LIST_URL, {'name': 'x', 'loan': valid_loan()}, format='json')
        assert resp.status_code in (401, 403)


class TestScenarioUpdate:
    def test_patch_name_only_keeps_existing_split(self, client):
        created = client.post(LIST_URL, {'name': 'Original', 'loan': valid_loan()}, format='json').json()
        scenario_id = created['id']

        resp = client.patch(detail_url(scenario_id), {'name': 'Renamed'}, format='json')

        assert resp.status_code == 200
        body = resp.json()
        assert body['name'] == 'Renamed'
        assert len(body['splits']) == 1  # split preserved

    def test_patch_loan_replaces_split(self, client):
        created = client.post(LIST_URL, {'name': 'Original', 'loan': valid_loan()}, format='json').json()
        scenario_id = created['id']
        original_split_id = created['splits'][0]['id']

        resp = client.patch(
            detail_url(scenario_id),
            {'loan': valid_loan(loan_amount='400000.00')},
            format='json',
        )

        assert resp.status_code == 200
        body = resp.json()
        assert len(body['splits']) == 1
        assert body['splits'][0]['loan_amount'] == '400000.00'
        # Old split was deleted and recreated, not mutated in place.
        assert body['splits'][0]['id'] != original_split_id


class TestScenarioScoping:
    def test_list_returns_only_own_scenarios(self, client, user, other_user):
        SavedScenario.objects.create(user=user, name='Mine')
        SavedScenario.objects.create(user=other_user, name='Theirs')

        resp = client.get(LIST_URL)

        assert resp.status_code == 200
        names = [s['name'] for s in resp.json()]
        assert names == ['Mine']

    def test_cannot_retrieve_other_users_scenario(self, client, other_user):
        theirs = SavedScenario.objects.create(user=other_user, name='Theirs')

        resp = client.get(detail_url(theirs.id))

        assert resp.status_code == 404  # scoped queryset hides it

    def test_delete_own_scenario(self, client, user):
        mine = SavedScenario.objects.create(user=user, name='Mine')

        resp = client.delete(detail_url(mine.id))

        assert resp.status_code == 204
        assert SavedScenario.objects.filter(id=mine.id).count() == 0
