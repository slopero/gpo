class FormController:
    REQUIRED_FIELDS = {
        "mark": "Марка",
        "model": "Модель",
        "type_ts": "Тип ТС",
        "year_ts": "Год выпуска ТС",
        "region": "Регион сделки",
        "date_deal": "Дата сделки",
        "power": "Мощность двигателя",
        "volume": "Объем двигателя",
        "type_engine": "Тип двигателя",
        "type_kpp": "Тип КПП",
        "type_body": "Тип кузова",
    }

    def __init__(self, params_model):
        self.params_model = params_model
        self.selected_record_id = None

    def save_params(self, data):
        payload_check = self._build_payload_check(data)
        missing_fields = [
            label for key, label in self.REQUIRED_FIELDS.items() if not payload_check.get(key)
        ]

        if missing_fields:
            return False, "Не заполнены обязательные поля: " + ", ".join(missing_fields)

        try:
            payload = self._build_payload(data, payload_check)
        except ValueError:
            return False, "Проверьте числовые поля: Год, Мощность, Объем, Владельцы, Пробег"

        self.selected_record_id = self.params_model.save_params(payload)
        return True, "Данные сохранены"

    def get_saved_records(self):
        return self.params_model.get_records_brief()

    def select_record(self, record_id):
        self.selected_record_id = int(record_id)
        return self.selected_record_id

    def get_record_data(self, record_id):
        data = self.params_model.get_record_by_id(record_id)
        if data is not None:
            self.selected_record_id = data.get("id", int(record_id))
        return data

    def get_selected_record_id(self):
        return self.selected_record_id

    def _build_payload_check(self, data):
        return {key: self._get_clean_value(data, key) for key in self.REQUIRED_FIELDS}

    def _build_payload(self, data, payload_check):
        return {
            "mark": payload_check["mark"],
            "model": payload_check["model"],
            "type_ts": payload_check["type_ts"],
            "year_ts": self._to_int(payload_check["year_ts"]),
            "region": payload_check["region"],
            "date_deal": payload_check["date_deal"],
            "power": self._to_int(payload_check["power"]),
            "volume": self._to_float(payload_check["volume"]),
            "count_owners": self._to_int(self._get_clean_value(data, "count_owners")),
            "type_engine": payload_check["type_engine"],
            "type_wheels": self._to_str_or_none(self._get_clean_value(data, "type_wheels")),
            "count_kilometers": self._to_int(self._get_clean_value(data, "count_kilometers")),
            "type_kpp": payload_check["type_kpp"],
            "type_body": payload_check["type_body"],
            "damage": self._to_str_or_none(self._get_clean_value(data, "damage")),
            "quality": self._to_str_or_none(self._get_clean_value(data, "quality")),
        }

    @staticmethod
    def _get_clean_value(data, key):
        return (data.get(key, "") or "").strip()

    @staticmethod
    def _to_str_or_none(value):
        value = (value or "").strip()
        return value or None

    @staticmethod
    def _to_int(value):
        value = (value or "").strip()
        if not value:
            return None
        return int(value)

    @staticmethod
    def _to_float(value):
        value = (value or "").strip().replace(",", ".")
        if not value:
            return None
        return float(value)
    
    def find_similar_vehicles(self, record_id: int, progress_callback=None) -> list:
        """Поиск аналогов для записи с указанным ID"""
        from db.external_db import ExternalDB
        
        if progress_callback:
            progress_callback("Загрузка данных записи...", 10)
        
        record = self.params_model.get_record_by_id(record_id)
        if not record:
            return []
        
        if progress_callback:
            progress_callback("Подключение к базе данных...", 30)
        
        external_db = ExternalDB(progress_callback=progress_callback)
        
        if external_db.data is None and external_db.conn is None:
            if progress_callback:
                progress_callback("Выберите файл базы данных...", 40)
            if not external_db.select_database_interactive():
                return []
        
        if progress_callback:
            progress_callback("Поиск аналогов...", 60)
        
        results = external_db.find_similar(record)
        
        if progress_callback:
            progress_callback(f"Готово! Найдено {len(results)} аналогов", 100)
        
        return results
