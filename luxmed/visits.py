from datetime import date
from datetime import datetime
from datetime import timedelta
from enum import IntEnum
from enum import unique
from itertools import chain
from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import Tuple
from typing import Union

from inflection import camelize

from luxmed.transformers import filter_args
from luxmed.transport import LuxMedTransport
from luxmed.urls import HISTORY_VISITS_URL
from luxmed.urls import RESERVED_VISITS_URL
from luxmed.urls import VISIT_RESERVE_TEMPORARY_URL
from luxmed.urls import VISIT_RESERVE_URL
from luxmed.urls import VISIT_TERMS_URL
from luxmed.urls import VISIT_TERMS_VALUATION_URL
from luxmed.utils import year_ago


@unique
class VisitHours(IntEnum):
    ALL = 0
    BEFORE_10 = 1
    BETWEEN_10_TO_17 = 2
    PAST_17 = 3


class LuxMedVisits:
    """Doctor appointments."""

    def __init__(self, transport: LuxMedTransport):
        self._transport = transport
        self._headers = {'Api-Version': '2.0'}

    @staticmethod
    def _common_reservation_data(
            clinic_id: int, doctor_id: int, room_id: int, service_id: int, start_date_time: Union[datetime, str],
            is_additional: bool = False, referral_required_by_service: bool = False) -> Iterator[Tuple[str, Any]]:
        for key, value in locals().items():
            if isinstance(value, datetime):
                value = value.isoformat()
            yield camelize(key), value

    def _post_reservation_to(self, url: str, *args, payer_details: List[Dict], **kwargs) -> Dict:
        data = dict(self._common_reservation_data(*args, **kwargs))
        data['PayerDetailsList'] = payer_details
        return self._transport.post(url, json=data)

    def cancel(self, reservation_id: int):
        """Cancels given appointment reservation ID.

        Args:
            reservation_id (int): Previously reserved appointment ID.
        """
        self._transport.delete('{}/{}'.format(RESERVED_VISITS_URL, reservation_id))

    def evaluate(self, *args, payer_details: List[Dict], **kwargs) -> Dict:
        """Evaluate given appointment.

        Args:
            clinic_id (int): Selected clinic ID.
            doctor_id (int): Selected doctor ID.
            payer_details (list): Payer details.
            room_id (int): Selected room ID.
            service_id (int): Selected service ID.
            start_date_time (datetime or str): Selected appointment start date time.
                When given as datetime must include timezone info and can not contain microseconds.

            is_additional (bool, optional): ?
            referral_required_by_service (bool, optional): ?

        Returns:
            Evaluation details.
        """
        return self._post_reservation_to(VISIT_TERMS_VALUATION_URL, *args, payer_details=payer_details, **kwargs)

    def find(self, city_id: int, service_id: int, language_id: int, payer_id: int,
             clinic_id: int = None, doctor_id: int = None,
             from_date: date = None, to_date: date = None,
             hours: VisitHours = VisitHours.ALL) -> Iterator[Dict]:
        """Find all available doctor appointments.

        Args:
            city_id (int): City where the appointment should take place in.
            service_id (int): Desired service.
            language_id (int): The language the doctor should be able to communicate in.
            payer_id (int): Who is going to paid for the appointment.
            clinic_id (int, optional): The clinic where the appointment should take place in.
                Clinic must be located within the given city boundaries.
            doctor_id (int, optional): Show only appointments from this doctor.
            from_date (date, optional): Start searching from this date. Defaults to current day.
            to_date (date, optional): Search until this date. Defaults to a week, starting from the from_date.
            hours (VisitHours, optional): Show only appointments within those hours. Defaults to all.

        Yields:
            Available appointments.
        """
        if not to_date:
            to_date = (from_date or date.today()) + timedelta(days=7)
        available = self._transport.get(VISIT_TERMS_URL, params=filter_args(
            city_id=city_id, service_id=service_id, language_id=language_id, payer_id=payer_id,
            clinic_id=clinic_id, doctor_id=doctor_id,
            from_date=from_date, to_date=to_date,
            time_of_day=hours.value), headers=self._headers)

        for visits in chain(
                available.get('AgregateAvailableVisitTerms', []),
                available.get('AgregateAvailableAdditionalVisitTerms', [])):
            for visit in visits['AvailableVisitsTermPresentation']:
                yield visit

    def history(self, from_date: date = None, to_date: date = None) -> List[Dict]:
        """Historic doctor appointments.

        Args:
            from_date (date, optional): Show past appointments since this date. Defaults to a year ago.
            to_date (date, optional): Show past appointments until this date. Defaults to the current date.

        Returns:
            Historic appointments.
        """
        if not from_date:
            from_date = year_ago()
        if not to_date:
            to_date = date.today()
        return self._transport.get(HISTORY_VISITS_URL, params=filter_args(
            from_date=from_date, to_date=to_date))

    def reserve_temporarily(self, *args, payer_details: List[Dict], **kwargs) -> Dict:
        """Temporarily reserves given appointment.
        Given appointment details should come directly from the freshly fetched available visits.

        Returns temporary reservation ID, which latter on can be used for permanent reservation.

        Args:
            clinic_id (int): Selected clinic ID.
            doctor_id (int): Selected doctor ID.
            payer_details (list): Payer details.
            room_id (int): Selected room ID.
            service_id (int): Selected service ID.
            start_date_time (datetime or str): Selected appointment start date time.
                When given as datetime must include timezone info and can not contain microseconds.

            is_additional (bool, optional): ?
            referral_required_by_service (bool, optional): ?

        Returns:
            Temporary reservation details.
        """
        return self._post_reservation_to(VISIT_RESERVE_TEMPORARY_URL, *args, payer_details=payer_details, **kwargs)

    def reserve(self, *args, payer_data: Dict, **kwargs) -> Dict:
        """Reserves given appointment.
        Given appointment details should come directly from the freshly fetched available visits.

        Args:
            clinic_id (int): Selected clinic ID.
            doctor_id (int): Selected doctor ID.
            payer_data (dict): Payer data.
            room_id (int): Selected room ID.
            service_id (int): Selected service ID.
            start_date_time (datetime or str): Selected appointment start date time.
                When given as datetime must include timezone info and can not contain microseconds.

            is_additional (bool, optional): ?
            referral_required_by_service (bool, optional): ?

        Returns:
            Reservation details.
        """

        temp_reservation = self.reserve_temporarily(*args, payer_details=[payer_data], **kwargs)
        self.evaluate(*args, payer_details=[payer_data], **kwargs)  # not really needed? but lets follow app

        data = dict(self._common_reservation_data(*args, **kwargs))
        del data['ReferralRequiredByService']
        data['PayerData'] = payer_data
        data['TemporaryReservationId'] = temp_reservation['Id']
        return self._transport.post(VISIT_RESERVE_URL, json=data)

    def reserved(self) -> List[Dict]:
        """Currently reserved doctor appointments.

        Returns:
            Reserved appointments.
        """
        return self._transport.get(RESERVED_VISITS_URL, headers=self._headers)
