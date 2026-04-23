from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, func, select
from sqlalchemy.orm import Mapped, mapped_column

from db.connection import Base, SessionLocal


class Params(Base):
    __tablename__ = "params"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mark: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    type_ts: Mapped[str] = mapped_column(String(100), nullable=False)
    year_ts: Mapped[int] = mapped_column(Integer, nullable=True)
    region: Mapped[str] = mapped_column(String(100), nullable=True)
    date_deal: Mapped[str] = mapped_column(String(100), nullable=True)
    power: Mapped[int] = mapped_column(Integer, nullable=True)
    volume: Mapped[float] = mapped_column(Float, nullable=True)
    count_owners: Mapped[int] = mapped_column(Integer, nullable=True)
    type_engine: Mapped[str] = mapped_column(String(100), nullable=True)
    type_wheels: Mapped[str] = mapped_column(String(100), nullable=True)
    count_kilometers: Mapped[int] = mapped_column(Integer, nullable=True)
    type_kpp: Mapped[str] = mapped_column(String(100), nullable=True)
    type_body: Mapped[str] = mapped_column(String(100), nullable=True)
    damage: Mapped[str] = mapped_column(String(200), nullable=True)
    quality: Mapped[str] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ParamsModel:
    def save_params(self, data):
        with SessionLocal() as session:
            params = Params(**data)
            session.add(params)
            session.commit()
            session.refresh(params)
            return params.id

    def get_records_brief(self):
        with SessionLocal() as session:
            result = session.execute(select(Params).order_by(Params.id.desc())).scalars().all()
            return [
                {
                    "id": row.id,
                    "mark": row.mark,
                    "model": row.model,
                    "year_ts": row.year_ts,
                    "region": row.region,
                    "date_deal": row.date_deal,
                }
                for row in result
            ]

    def get_record_by_id(self, record_id):
        with SessionLocal() as session:
            row = session.get(Params, record_id)
            if row is None:
                return None
            return {
                "id": row.id,
                "mark": row.mark,
                "model": row.model,
                "type_ts": row.type_ts,
                "year_ts": row.year_ts,
                "region": row.region,
                "date_deal": row.date_deal,
                "power": row.power,
                "volume": row.volume,
                "count_owners": row.count_owners,
                "type_engine": row.type_engine,
                "type_wheels": row.type_wheels,
                "count_kilometers": row.count_kilometers,
                "type_kpp": row.type_kpp,
                "type_body": row.type_body,
                "damage": row.damage,
                "quality": row.quality,
            }
