import logging
import os
import time

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI=os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://mk_user:mk_pass@postgres-db:5432/matkul_db",
    ),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
)
db = SQLAlchemy(app)


class MataKuliah(db.Model):
    __tablename__ = "mata_kuliah"

    kode = db.Column(db.String(10), primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    sks = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.Integer)

    def to_dict(self):
        return {
            "kode": self.kode,
            "nama": self.nama,
            "sks": self.sks,
            "semester": self.semester,
        }


def error(pesan, status):
    return jsonify({"error": pesan}), status


def json_object():
    data = request.get_json(silent=True)
    if data is None:
        return {}, None
    if not isinstance(data, dict):
        return None, error("body harus berupa objek JSON", 400)
    return data, None


def is_integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


@app.get("/matkul")
def list_mk():
    data = MataKuliah.query.order_by(MataKuliah.kode).all()
    return jsonify([matkul.to_dict() for matkul in data])


@app.post("/matkul")
def create_mk():
    data, invalid_body = json_object()
    if invalid_body:
        return invalid_body

    kode = data.get("kode")
    nama = data.get("nama")
    sks = data.get("sks")
    semester = data.get("semester")
    if not isinstance(kode, str) or not kode.strip():
        return error("kode wajib diisi", 400)
    if not isinstance(nama, str) or not nama.strip():
        return error("nama wajib diisi", 400)
    if len(kode.strip()) > 10 or len(nama.strip()) > 100:
        return error("kode atau nama melebihi batas panjang", 400)
    if not is_integer(sks) or sks <= 0:
        return error("sks wajib berupa bilangan bulat positif", 400)
    if semester is not None and not is_integer(semester):
        return error("semester harus berupa bilangan bulat atau null", 400)

    matkul = MataKuliah(
        kode=kode.strip(),
        nama=nama.strip(),
        sks=sks,
        semester=semester,
    )
    db.session.add(matkul)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("kode mata kuliah sudah ada", 409)

    return jsonify(matkul.to_dict()), 201


@app.get("/matkul/<kode>")
def get_mk(kode):
    matkul = db.session.get(MataKuliah, kode)
    if matkul is None:
        return error("mata kuliah tidak ditemukan", 404)
    return jsonify(matkul.to_dict())


@app.put("/matkul/<kode>")
def update_mk(kode):
    matkul = db.session.get(MataKuliah, kode)
    if matkul is None:
        return error("mata kuliah tidak ditemukan", 404)

    data, invalid_body = json_object()
    if invalid_body:
        return invalid_body

    if "nama" in data:
        nama = data["nama"]
        if not isinstance(nama, str) or not nama.strip():
            return error("nama harus berupa teks dan tidak boleh kosong", 400)
        if len(nama.strip()) > 100:
            return error("nama maksimal 100 karakter", 400)
        matkul.nama = nama.strip()

    if "sks" in data:
        sks = data["sks"]
        if not is_integer(sks) or sks <= 0:
            return error("sks harus berupa bilangan bulat positif", 400)
        matkul.sks = sks

    if "semester" in data:
        semester = data["semester"]
        if semester is not None and not is_integer(semester):
            return error("semester harus berupa bilangan bulat atau null", 400)
        matkul.semester = semester

    db.session.commit()
    return jsonify(matkul.to_dict())


@app.delete("/matkul/<kode>")
def delete_mk(kode):
    matkul = db.session.get(MataKuliah, kode)
    if matkul is None:
        return error("mata kuliah tidak ditemukan", 404)

    db.session.delete(matkul)
    db.session.commit()
    return "", 204


def init_db(retries=30, delay_seconds=2):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            with app.app_context():
                db.create_all()
                if db.session.query(MataKuliah).count() == 0:
                    db.session.add_all(
                        [
                            MataKuliah(
                                kode="IF301",
                                nama="Sistem Terdistribusi",
                                sks=3,
                                semester=5,
                            ),
                            MataKuliah(
                                kode="IF302",
                                nama="Basis Data Lanjut",
                                sks=3,
                                semester=5,
                            ),
                            MataKuliah(
                                kode="IF303",
                                nama="Jaringan Komputer",
                                sks=3,
                                semester=4,
                            ),
                        ]
                    )
                    db.session.commit()
            logger.info("Database mata kuliah siap")
            return
        except Exception as exc:  # PostgreSQL may still be starting during compose up.
            last_error = exc
            logger.warning(
                "Menunggu database mata kuliah siap (%s/%s): %s",
                attempt,
                retries,
                exc,
            )
            if attempt < retries:
                time.sleep(delay_seconds)

    raise RuntimeError("database mata kuliah tidak tersedia") from last_error


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
