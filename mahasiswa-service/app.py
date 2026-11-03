import logging
import os
import time

import requests
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI=os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://mhs_user:mhs_pass@mysql-db:3306/mahasiswa_db",
    ),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
)
db = SQLAlchemy(app)

MATKUL_URL = os.getenv("MATKUL_URL", "http://matkul-service:5000").rstrip("/")
MATKUL_TIMEOUT_SECONDS = 3


class Mahasiswa(db.Model):
    __tablename__ = "mahasiswa"

    nim = db.Column(db.String(15), primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    angkatan = db.Column(db.Integer)

    krs = db.relationship(
        "Krs",
        back_populates="mahasiswa",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "nim": self.nim,
            "nama": self.nama,
            "email": self.email,
            "angkatan": self.angkatan,
        }


class Krs(db.Model):
    __tablename__ = "krs"

    id = db.Column(db.Integer, primary_key=True)
    nim = db.Column(
        db.String(15),
        db.ForeignKey("mahasiswa.nim", ondelete="CASCADE"),
        nullable=False,
    )
    # kode_mk sengaja tidak menjadi foreign key: database Mata Kuliah dimiliki
    # service lain dan hanya boleh diakses melalui API-nya.
    kode_mk = db.Column(db.String(10), nullable=False)

    mahasiswa = db.relationship("Mahasiswa", back_populates="krs")

    __table_args__ = (db.UniqueConstraint("nim", "kode_mk", name="uq_krs_nim_kode_mk"),)


def error(pesan, status):
    return jsonify({"error": pesan}), status


def json_object():
    """Return a JSON object or a 400 response for a non-object JSON body."""
    data = request.get_json(silent=True)
    if data is None:
        return {}, None
    if not isinstance(data, dict):
        return None, error("body harus berupa objek JSON", 400)
    return data, None


def valid_optional_string(data, field, max_length):
    value = data.get(field)
    if value is None:
        return True
    return isinstance(value, str) and len(value.strip()) <= max_length


def valid_angkatan(value):
    return value is None or (isinstance(value, int) and not isinstance(value, bool))


@app.get("/mahasiswa")
def list_mhs():
    data = Mahasiswa.query.order_by(Mahasiswa.nim).all()
    return jsonify([mahasiswa.to_dict() for mahasiswa in data])


@app.post("/mahasiswa")
def create_mhs():
    data, invalid_body = json_object()
    if invalid_body:
        return invalid_body

    nim = data.get("nim")
    nama = data.get("nama")
    if not isinstance(nim, str) or not nim.strip():
        return error("nim wajib diisi", 400)
    if not isinstance(nama, str) or not nama.strip():
        return error("nama wajib diisi", 400)
    nim = nim.strip()
    nama = nama.strip()
    if len(nim) > 15 or len(nama) > 100:
        return error("nim atau nama melebihi batas panjang", 400)
    if not valid_optional_string(data, "email", 100):
        return error("email harus berupa teks maksimal 100 karakter", 400)
    if not valid_angkatan(data.get("angkatan")):
        return error("angkatan harus berupa bilangan bulat atau null", 400)

    email = data.get("email")
    mahasiswa = Mahasiswa(
        nim=nim,
        nama=nama,
        email=email.strip() if isinstance(email, str) else None,
        angkatan=data.get("angkatan"),
    )
    db.session.add(mahasiswa)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("NIM sudah terdaftar", 409)

    return jsonify(mahasiswa.to_dict()), 201


@app.get("/mahasiswa/<nim>")
def get_mhs(nim):
    mahasiswa = db.session.get(Mahasiswa, nim)
    if mahasiswa is None:
        return error("mahasiswa tidak ditemukan", 404)
    return jsonify(mahasiswa.to_dict())


@app.put("/mahasiswa/<nim>")
def update_mhs(nim):
    mahasiswa = db.session.get(Mahasiswa, nim)
    if mahasiswa is None:
        return error("mahasiswa tidak ditemukan", 404)

    data, invalid_body = json_object()
    if invalid_body:
        return invalid_body

    if "nama" in data:
        nama = data["nama"]
        if not isinstance(nama, str) or not nama.strip():
            return error("nama harus berupa teks dan tidak boleh kosong", 400)
        if len(nama.strip()) > 100:
            return error("nama maksimal 100 karakter", 400)
        mahasiswa.nama = nama.strip()

    if "email" in data:
        email = data["email"]
        if not valid_optional_string(data, "email", 100):
            return error("email harus berupa teks maksimal 100 karakter", 400)
        mahasiswa.email = email.strip() if isinstance(email, str) else None

    if "angkatan" in data:
        angkatan = data["angkatan"]
        if not valid_angkatan(angkatan):
            return error("angkatan harus berupa bilangan bulat atau null", 400)
        mahasiswa.angkatan = angkatan

    db.session.commit()
    return jsonify(mahasiswa.to_dict())


@app.delete("/mahasiswa/<nim>")
def delete_mhs(nim):
    mahasiswa = db.session.get(Mahasiswa, nim)
    if mahasiswa is None:
        return error("mahasiswa tidak ditemukan", 404)

    db.session.delete(mahasiswa)
    db.session.commit()
    return "", 204


@app.get("/mahasiswa/<nim>/matkul")
def list_krs(nim):
    if db.session.get(Mahasiswa, nim) is None:
        return error("mahasiswa tidak ditemukan", 404)

    hasil = []
    for krs in Krs.query.filter_by(nim=nim).order_by(Krs.id).all():
        item = {"kode_mk": krs.kode_mk}
        try:
            response = requests.get(
                f"{MATKUL_URL}/matkul/{krs.kode_mk}",
                timeout=MATKUL_TIMEOUT_SECONDS,
            )
            if response.status_code == 200:
                detail = response.json()
                if isinstance(detail, dict):
                    item.update(detail)
            elif response.status_code != 404:
                item["catatan"] = "detail mata kuliah tidak tersedia"
        except (requests.RequestException, ValueError):
            item["catatan"] = "detail mata kuliah tidak tersedia"
        hasil.append(item)

    return jsonify(hasil)


@app.post("/mahasiswa/<nim>/matkul")
def ambil_matkul(nim):
    if db.session.get(Mahasiswa, nim) is None:
        return error("mahasiswa tidak ditemukan", 404)

    data, invalid_body = json_object()
    if invalid_body:
        return invalid_body
    kode_mk = data.get("kode_mk")
    if not isinstance(kode_mk, str) or not kode_mk.strip():
        return error("kode_mk wajib diisi", 400)
    kode_mk = kode_mk.strip()
    if len(kode_mk) > 10:
        return error("kode_mk maksimal 10 karakter", 400)

    try:
        response = requests.get(
            f"{MATKUL_URL}/matkul/{kode_mk}",
            timeout=MATKUL_TIMEOUT_SECONDS,
        )
    except requests.RequestException:
        return error("matkul-service tidak dapat dihubungi", 503)

    if response.status_code == 404:
        return error("mata kuliah tidak ditemukan", 404)
    if not response.ok:
        return error("matkul-service gagal memvalidasi mata kuliah", 503)

    db.session.add(Krs(nim=nim, kode_mk=kode_mk))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("mata kuliah sudah diambil", 409)

    return jsonify({"nim": nim, "kode_mk": kode_mk, "pesan": "berhasil"}), 201


@app.delete("/mahasiswa/<nim>/matkul/<kode_mk>")
def batal_matkul(nim, kode_mk):
    krs = Krs.query.filter_by(nim=nim, kode_mk=kode_mk).first()
    if krs is None:
        return error("data pengambilan tidak ditemukan", 404)

    db.session.delete(krs)
    db.session.commit()
    return "", 204


def init_db(retries=30, delay_seconds=2):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            with app.app_context():
                db.create_all()
            logger.info("Database mahasiswa siap")
            return
        except Exception as exc:  # MySQL may still be starting during compose up.
            last_error = exc
            logger.warning(
                "Menunggu database mahasiswa siap (%s/%s): %s",
                attempt,
                retries,
                exc,
            )
            if attempt < retries:
                time.sleep(delay_seconds)

    raise RuntimeError("database mahasiswa tidak tersedia") from last_error


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
