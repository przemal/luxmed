from datetime import date
from typing import Dict
from typing import List

from luxmed.examination import LuxMedExamination
from luxmed.transformers import filter_args
from luxmed.transformers import map_id_name
from luxmed.transport import LuxMedTransport
from luxmed.urls import USER_URL
from luxmed.urls import USER_PERMISSIONS_URL
from luxmed.urls import VISIT_TERMS_RESERVATION_URL
from luxmed.visits import LuxMedVisits


class LuxMed:
    """LUX MED Group patient portal (unofficial) API client."""

    def __init__(self, user_name: str, password: str, app_uuid: str = None, client_uuid: str = None,
                 lang_code: str = 'en'):
        """Args:
            user_name (str): Your LUX MED login.
            password (str): Your LUX MED password.
            app_uuid (str, optional): Application UUID. Defaults to random UUID.
            client_uuid (str, optional): Client UUID. Defaults to random UUID.
            lang_code (str, optional): Two letter (ISO 639-1) language code. Defaults to en.
        """
        self._transport = LuxMedTransport(
            user_name=user_name, password=password,
            app_uuid=app_uuid, client_uuid=client_uuid, lang_code=lang_code)
        self.examination = LuxMedExamination(self._transport)
        self.visits = LuxMedVisits(self._transport)

    def _visit_filters(self, **kwargs) -> Dict:
        return self._transport.get(VISIT_TERMS_RESERVATION_URL, params=filter_args(**kwargs))

    def _mapped_visit_filters(self, category: str, **kwargs) -> Dict[int, str]:
        return map_id_name(self._visit_filters(**kwargs)[category])

    def cities(self, from_date: date = None) -> Dict[int, str]:
        """Cities the service is available in.

        Args:
            from_date (date): A day in time at which the availability should be queried?? Defaults to the current date.
        """
        return self._mapped_visit_filters('Cities', from_date=from_date)

    def clinics(self, city_id: int, from_date: date = None) -> Dict[int, str]:
        """Clinics available in the given city."""
        return self._mapped_visit_filters('Clinics', city_id=city_id, from_date=from_date)

    def doctors(self, city_id: int, service_id: int, clinic_id: int = None, from_date: date = None) -> Dict[int, str]:
        """Doctors available in the given city and providing specified service."""
        return self._mapped_visit_filters(
            'Doctors', city_id=city_id, clinic_id=clinic_id, from_date=from_date, service_id=service_id)

    def languages(self, from_date: date = None) -> Dict[int, str]:
        """Languages the service is accessible in."""
        return self._mapped_visit_filters('Languages', from_date=from_date)

    def payers(self, city_id: int, service_id: int, clinic_id: int = None, from_date: date = None) -> List[Dict]:
        """Payers available for the given city and service."""
        return self._visit_filters(
            city_id=city_id, clinic_id=clinic_id, from_date=from_date, service_id=service_id)['Payers']

    def services(self, city_id: int, clinic_id: int = None, from_date: date = None) -> Dict[int, str]:
        """Services available in the given city."""
        return self._mapped_visit_filters('Services', city_id=city_id, clinic_id=clinic_id, from_date=from_date)

    def user(self) -> Dict:
        """User profile."""
        return self._transport.get(USER_URL)

    def user_permissions(self) -> Dict:
        """User module permissions/restrictions."""
        return self._transport.get(USER_PERMISSIONS_URL)
