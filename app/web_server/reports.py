from datetime import datetime


class ReportValidationError(Exception):
    ...


class ReportForm:
    def __init__(self, form_data):
        try:
            self.occurance_date = datetime.strptime(
                form_data["date-time"], "%d/%m/%Y %H:%M"
            )
            self.duration_minutes = form_data["duration-minutes"]
            if form_data["drug-administered"] == "on":
                self.drugs_administered = True
            else:
                self.drugs_administered = False
            if form_data["hospitalization-required"] == "on":
                self.hospitalization_required = True
            else:
                self.hospitalization_required = False
            self.details_text = form_data["details-text"]
        except KeyError as ex:
            raise ReportValidationError(f"Missing form data, {ex}") from ex
        except ValueError as ex:
            raise ReportValidationError(f"Invalid form data, {ex}") from ex

    def to_dict(self):
        return vars(self)
