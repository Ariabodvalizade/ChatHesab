# database/connection.py
import mysql.connector
from mysql.connector import Error
import logging
from contextlib import contextmanager
from config import DB_CONFIG

logger = logging.getLogger(__name__)


class DatabaseConnection:
    def __init__(self):
        self.config = DB_CONFIG
        self.connection = None

    def connect(self):
        """برقراری اتصال به دیتابیس"""
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(**self.config)
                logger.info("اتصال به دیتابیس برقرار شد")
            return self.connection
        except Error as e:
            logger.error(f"خطا در اتصال به دیتابیس: {e}")
            raise

    def disconnect(self):
        """قطع اتصال از دیتابیس"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("اتصال به دیتابیس قطع شد")

    @contextmanager
    def get_cursor(self, dictionary=True):
        """Context manager برای مدیریت cursor"""
        connection = self.connect()
        cursor = connection.cursor(dictionary=dictionary)
        try:
            yield cursor
            connection.commit()
        except Exception as e:
            connection.rollback()
            logger.error(f"خطا در تراکنش دیتابیس: {e}")
            raise
        finally:
            cursor.close()

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """اجرای کوئری با مدیریت خودکار connection"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())

            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return cursor.lastrowid

    def execute_many(self, query, data):
        """اجرای چندین کوئری به صورت همزمان"""
        with self.get_cursor() as cursor:
            cursor.executemany(query, data)
            return cursor.rowcount


# نمونه singleton از connection
db = DatabaseConnection()


# توابع کمکی برای استفاده آسان‌تر
def get_db():
    """دریافت نمونه از دیتابیس"""
    return db


def init_database():
    """ایجاد جداول دیتابیس در صورت عدم وجود"""
    try:
        with open("database/schema.sql", "r", encoding="utf-8") as f:
            schema = f.read()

        # اجرای دستورات SQL به صورت جداگانه
        statements = [s.strip() for s in schema.split(";") if s.strip()]

        connection = db.connect()
        cursor = connection.cursor()

        for statement in statements:
            cursor.execute(statement)

        connection.commit()
        cursor.close()

        logger.info("جداول دیتابیس با موفقیت ایجاد شدند")

    except Exception as e:
        logger.error(f"خطا در ایجاد جداول: {e}")
        raise
