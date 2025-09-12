-- database/schema.sql

-- جدول کاربران
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    trial_end_date DATETIME,
    subscription_end_date DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- جدول حساب‌های بانکی
CREATE TABLE IF NOT EXISTS bank_accounts (
    account_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    bank_name VARCHAR(100) NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    initial_balance DECIMAL(15, 0) DEFAULT 0,
    current_balance DECIMAL(15, 0) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_accounts (user_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- جدول تراکنش‌ها
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    account_id INT NOT NULL,
    type ENUM('income', 'expense') NOT NULL,
    amount DECIMAL(15, 0) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    transaction_date DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES bank_accounts(account_id) ON DELETE CASCADE,
    INDEX idx_user_transactions (user_id),
    INDEX idx_transaction_date (transaction_date),
    INDEX idx_category (category)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- جدول چک‌ها
CREATE TABLE IF NOT EXISTS checks (
    check_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    account_id INT NOT NULL,
    type ENUM('issued', 'received') NOT NULL,
    amount DECIMAL(15, 0) NOT NULL,
    due_date DATE NOT NULL,
    recipient_issuer VARCHAR(255),
    description TEXT,
    status ENUM('pending', 'cleared', 'bounced', 'cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES bank_accounts(account_id) ON DELETE CASCADE,
    INDEX idx_user_checks (user_id),
    INDEX idx_due_date (due_date),
    INDEX idx_status (status)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- جدول دسته‌بندی‌ها
CREATE TABLE IF NOT EXISTS categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type ENUM('income', 'expense') NOT NULL,
    parent_id INT,
    icon VARCHAR(10),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES categories(category_id) ON DELETE SET NULL,
    UNIQUE KEY unique_category (name, type)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- جدول طرح‌های پس‌انداز
CREATE TABLE IF NOT EXISTS savings_plans (
    plan_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    plan_name VARCHAR(255) NOT NULL,
    plan_type VARCHAR(50),
    target_amount DECIMAL(15, 0),
    current_amount DECIMAL(15, 0) DEFAULT 0,
    monthly_contribution DECIMAL(15, 0),
    start_date DATE NOT NULL,
    end_date DATE,
    status ENUM('active', 'completed', 'cancelled', 'paused') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_plans (user_id),
    INDEX idx_status (status)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- جدول اشتراک‌ها
CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    plan_type VARCHAR(20) NOT NULL,
    amount_paid DECIMAL(10, 0) NOT NULL,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    payment_reference VARCHAR(255),
    status ENUM('active', 'expired', 'cancelled') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_subscriptions (user_id),
    INDEX idx_status (status),
    INDEX idx_end_date (end_date)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- جدول یادآوری‌ها
CREATE TABLE IF NOT EXISTS reminders (
    reminder_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    reminder_date DATE NOT NULL,
    is_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_reminders (user_id),
    INDEX idx_reminder_date (reminder_date)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- جدول تنظیمات کاربر
CREATE TABLE IF NOT EXISTS user_settings (
    user_id BIGINT PRIMARY KEY,
    notification_enabled BOOLEAN DEFAULT TRUE,
    daily_reminder_time TIME,
    currency VARCHAR(10) DEFAULT 'تومان',
    language VARCHAR(10) DEFAULT 'fa',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- درج دسته‌بندی‌های پیش‌فرض
INSERT IGNORE INTO categories (name, type, icon, is_default) VALUES
-- دسته‌بندی‌های هزینه
('خانه', 'expense', '🏠', TRUE),
('خواربار', 'expense', '🛒', TRUE),
('رستوران و کافی‌شاپ', 'expense', '🍔', TRUE),
('حمل و نقل', 'expense', '🚗', TRUE),
('پوشاک', 'expense', '👕', TRUE),
('درمان و سلامت', 'expense', '🏥', TRUE),
('آموزش', 'expense', '📚', TRUE),
('سرگرمی', 'expense', '🎮', TRUE),
('موبایل و اینترنت', 'expense', '📱', TRUE),
('تعمیرات', 'expense', '🔧', TRUE),
('هدیه', 'expense', '🎁', TRUE),
('اقساط و وام', 'expense', '💳', TRUE),
('مالیات', 'expense', '🏢', TRUE),
('سفر', 'expense', '✈️', TRUE),
('سایر', 'expense', '💰', TRUE),
-- دسته‌بندی‌های درآمد
('حقوق', 'income', '💼', TRUE),
('کسب و کار', 'income', '🏪', TRUE),
('سرمایه‌گذاری', 'income', '💹', TRUE),
('اجاره', 'income', '🏠', TRUE),
('پروژه', 'income', '🎯', TRUE),
('هدیه', 'income', '🎁', TRUE),
('سایر', 'income', '💸', TRUE);