from datetime import date
from typing import Dict
from typing import Iterator

from luxmed.mapping import LuxMedReadOnlyMapping
from luxmed.transformers import filter_args
from luxmed.transport import LuxMedTransport
from luxmed.urls import BASE_URL
from luxmed.urls import EXAMINATION_RESULTS_URL
from luxmed.utils import find_link_rel
from luxmed.utils import year_ago


class LuxMedExaminationResult(LuxMedReadOnlyMapping):
    def details(self) -> Dict:
        """Examination result details."""
        return self._transport.get(BASE_URL + find_link_rel(
            self.data['Links'], 'examination-result-details')['Href'])

    def document(self) -> bytes:
        """Examination result details in PDF."""
        return self._transport.get(BASE_URL + find_link_rel(
            self.data['DownloadLinks'], 'examination-result-document')['Href'])


class LuxMedExamination:
    def __init__(self, transport: LuxMedTransport):
        self._transport = transport

    def results(self, from_date: date = None, to_date: date = None) -> Iterator[LuxMedExaminationResult]:
        """Yields examination results between the given dates.

        Args:
            from_date (date, optional): Show results starting with this date. Defaults to year ago.
            to_date (date, optional): Show results until this date. Defaults to today.
        """
        if not from_date:
            from_date = year_ago()
        if not to_date:
            to_date = date.today()

        for result in self._transport.get(
                    EXAMINATION_RESULTS_URL,
                    params=filter_args(from_date=from_date, to_date=to_date)
                )['MedicalExaminationsResults']:
            yield LuxMedExaminationResult(result, self._transport)
