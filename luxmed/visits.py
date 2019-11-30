from datetime import date
from datetime import timedelta
from enum import IntEnum
from enum import unique
from itertools import chain
from typing import Dict
from typing import Iterator
from typing import List

from luxmed.transformers import filter_args
from luxmed.transport import LuxMedTransport
from luxmed.urls import HISTORY_VISITS_URL
from luxmed.urls import RESERVED_VISITS_URL
from luxmed.urls import VISIT_TERMS_URL


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
            from_date (date, optional): Show past appointments since this date.
                Defaults to a year ago (leap/366 days).
            to_date (date, optional): Show past appointments until this date. Defaults to the current date.

        Returns:
            Historic appointments.
        """
        if not from_date:
            from_date = str(date.today() - timedelta(days=366))
        if not to_date:
            to_date = str(date.today())
        return self._transport.get(HISTORY_VISITS_URL, params=filter_args(
            from_date=from_date, to_date=to_date))

    def reserved(self) -> List[Dict]:
        """Currently reserved doctor appointments.

        Returns:
            Reserved appointments.
        """
        return self._transport.get(RESERVED_VISITS_URL, headers=self._headers)
