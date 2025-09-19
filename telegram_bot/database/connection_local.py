# database/connection_local.py - Local SQLite database connection
import sqlite3
import logging
from contextlib import contextmanager
from ..config_local import DB_CONFIG

logger = logging.getLogger(__name__)


class LocalDatabaseConnection:
    def __init__(self):
        self.db_path = DB_CONFIG["database"]
        self.connection = None

    def connect(self):
        """برقراری اتصال به دیتابیس SQLite"""
        try:
            if self.connection is None:
                self.connection = sqlite3.connect(
                    self.db_path,
                    check_same_thread=DB_CONFIG.get("check_same_thread", True),
                )
                self.connection.row_factory = (
                    sqlite3.Row
                )  # برای دسترسی به ستون‌ها با نام
                logger.info("اتصال به دیتابیس محلی برقرار شد")
            return self.connection
        except Exception as e:
            logger.error(f"خطا در اتصال به دیتابیس محلی: {e}")
            raise

    def disconnect(self):
        """قطع اتصال از دیتابیس"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("اتصال به دیتابیس محلی قطع شد")

    @contextmanager
    def get_cursor(self):
        """Context manager برای مدیریت cursor"""
        connection = self.connect()
        cursor = connection.cursor()
        try:
            yield cursor
            connection.commit()
        except Exception as e:
            connection.rollback()
            logger.error(f"خطا در تراکنش دیتابیس محلی: {e}")
            raise
        finally:
            cursor.close()

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """اجرای کوئری با مدیریت خودکار connection"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())

            if fetch_one:
                row = cursor.fetchone()
                return dict(row) if row else None
            elif fetch_all:
                rows = cursor.fetchall()
                return [dict(row) for row in rows] if rows else []
            else:
                return cursor.lastrowid

    def execute_many(self, query, data):
        """اجرای چندین کوئری به صورت همزمان"""
        with self.get_cursor() as cursor:
            cursor.executemany(query, data)
            return cursor.rowcount


# نمونه singleton از connection
local_db = LocalDatabaseConnection()


# توابع کمکی برای استفاده آسان‌تر
def get_local_db():
    """دریافت نمونه از دیتابیس محلی"""
    return local_db


def init_local_database():
    """ایجاد جداول دیتابیس SQLite در صورت عدم وجود"""
    try:
        # اسکریپت SQLite (تبدیل شده از MySQL)
        schema_sqlite = """
        -- جدول کاربران
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            phone_number TEXT UNIQUE,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            trial_end_date DATETIME,
            subscription_end_date DATETIME,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- جدول حساب‌های بانکی
        CREATE TABLE IF NOT EXISTS bank_accounts (
            account_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            bank_name TEXT NOT NULL,
            account_name TEXT NOT NULL,
            initial_balance REAL DEFAULT 0,
            current_balance REAL DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        -- جدول تراکنش‌ها
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            type TEXT CHECK(type IN ('income', 'expense')) NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            transaction_date DATETIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (account_id) REFERENCES bank_accounts(account_id) ON DELETE CASCADE
        );

        -- جدول چک‌ها
        CREATE TABLE IF NOT EXISTS checks (
            check_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            type TEXT CHECK(type IN ('issued', 'received')) NOT NULL,
            amount REAL NOT NULL,
            due_date DATE NOT NULL,
            recipient_issuer TEXT,
            description TEXT,
            status TEXT CHECK(status IN ('pending', 'cleared', 'bounced', 'cancelled')) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (account_id) REFERENCES bank_accounts(account_id) ON DELETE CASCADE
        );

        -- جدول دسته‌بندی‌ها
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT CHECK(type IN ('income', 'expense')) NOT NULL,
            parent_id INTEGER,
            icon TEXT,
            is_default BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES categories(category_id) ON DELETE SET NULL,
            UNIQUE(name, type)
        );

        -- جدول طرح‌های پس‌انداز
        CREATE TABLE IF NOT EXISTS savings_plans (
            plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_name TEXT NOT NULL,
            plan_type TEXT,
            target_amount REAL,
            current_amount REAL DEFAULT 0,
            monthly_contribution REAL,
            start_date DATE NOT NULL,
            end_date DATE,
            status TEXT CHECK(status IN ('active', 'completed', 'cancelled', 'paused')) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        -- جدول اشتراک‌ها
        CREATE TABLE IF NOT EXISTS subscriptions (
            subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_type TEXT NOT NULL,
            amount_paid REAL NOT NULL,
            start_date DATETIME NOT NULL,
            end_date DATETIME NOT NULL,
            payment_reference TEXT,
            status TEXT CHECK(status IN ('active', 'expired', 'cancelled')) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        -- جدول یادآوری‌ها
        CREATE TABLE IF NOT EXISTS reminders (
            reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            reminder_date DATE NOT NULL,
            is_sent BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        -- جدول تنظیمات کاربر
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            notification_enabled BOOLEAN DEFAULT 1,
            daily_reminder_time TIME,
            currency TEXT DEFAULT 'تومان',
            language TEXT DEFAULT 'fa',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        -- درج دسته‌بندی‌های پیش‌فرض
        INSERT OR IGNORE INTO categories (name, type, icon, is_default) VALUES
        -- دسته‌بندی‌های هزینه
        ('خانه', 'expense', '🏠', 1),
        ('خواربار', 'expense', '🛒', 1),
        ('رستوران و کافی‌شاپ', 'expense', '🍔', 1),
        ('حمل و نقل', 'expense', '🚗', 1),
        ('پوشاک', 'expense', '👕', 1),
        ('درمان و سلامت', 'expense', '🏥', 1),
        ('آموزش', 'expense', '📚', 1),
        ('سرگرمی', 'expense', '🎮', 1),
        ('موبایل و اینترنت', 'expense', '📱', 1),
        ('تعمیرات', 'expense', '🔧', 1),
        ('هدیه', 'expense', '🎁', 1),
        ('اقساط و وام', 'expense', '💳', 1),
        ('مالیات', 'expense', '🏢', 1),
        ('سفر', 'expense', '✈️', 1),
        ('سایر', 'expense', '💰', 1),
        -- دسته‌بندی‌های درآمد
        ('حقوق', 'income', '💼', 1),
        ('کسب و کار', 'income', '🏪', 1),
        ('سرمایه‌گذاری', 'income', '💹', 1),
        ('اجاره', 'income', '🏠', 1),
        ('پروژه', 'income', '🎯', 1),
        ('هدیه', 'income', '🎁', 1),
        ('سایر', 'income', '💸', 1);
        """

        connection = local_db.connect()
        cursor = connection.cursor()

        # اجرای دستورات SQL به صورت جداگانه
        statements = [s.strip() for s in schema_sqlite.split(";") if s.strip()]

        for statement in statements:
            cursor.execute(statement)

        connection.commit()
        cursor.close()

        logger.info("جداول دیتابیس محلی با موفقیت ایجاد شدند")

    except Exception as e:
        logger.error(f"خطا در ایجاد جداول محلی: {e}")
        raise
