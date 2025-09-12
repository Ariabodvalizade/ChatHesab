#!/usr/bin/env python3
"""
Comprehensive test script for the Finance Bot Web Application
Tests all features end-to-end to ensure everything works properly
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
API_BASE_URL = "http://localhost:8001"
REACT_APP_URL = "http://localhost:5173"


class FinanceBotTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.account_id = None
        self.test_results = []

    def log_test(self, test_name, success, message="", data=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }
        self.test_results.append(result)

        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if data and not success:
            print(f"   Data: {data}")

    def test_api_health(self):
        """Test API health endpoint"""
        try:
            response = self.session.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_test("API Health Check", True, f"Status: {data.get('status')}")
                return True
            else:
                self.log_test(
                    "API Health Check", False, f"Status code: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test("API Health Check", False, str(e))
            return False

    def test_user_creation(self, telegram_id=99999):
        """Test user creation and authentication"""
        try:
            # Create user
            user_data = {
                "telegram_id": telegram_id,
                "username": f"test_user_{telegram_id}",
                "first_name": "تست",
                "last_name": "کاربر",
            }

            response = self.session.post(f"{API_BASE_URL}/api/users", json=user_data)

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.token = data.get("token")
                    self.user_id = data.get("user_id")
                    self.log_test(
                        "User Creation",
                        True,
                        f"User ID: {self.user_id}, Token: {self.token}",
                    )
                    return True
                else:
                    self.log_test("User Creation", False, "Success flag is False", data)
                    return False
            else:
                self.log_test(
                    "User Creation",
                    False,
                    f"Status code: {response.status_code}",
                    response.text,
                )
                return False
        except Exception as e:
            self.log_test("User Creation", False, str(e))
            return False

    def test_authentication(self):
        """Test authentication with token"""
        if not self.token:
            self.log_test("Authentication", False, "No token available")
            return False

        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.session.get(f"{API_BASE_URL}/api/users/me", headers=headers)

            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Authentication",
                    True,
                    f"User: {data.get('first_name')} {data.get('last_name')}",
                )
                return True
            else:
                self.log_test(
                    "Authentication", False, f"Status code: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test("Authentication", False, str(e))
            return False

    def test_account_management(self):
        """Test bank account creation and retrieval"""
        if not self.token:
            self.log_test("Account Management", False, "No token available")
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }

            # Create account
            account_data = {
                "bank_name": "بانک تست",
                "account_name": "حساب آزمایشی",
                "initial_balance": 1000000,
            }

            response = self.session.post(
                f"{API_BASE_URL}/api/accounts", json=account_data, headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.account_id = data.get("account_id")
                    self.log_test(
                        "Account Creation", True, f"Account ID: {self.account_id}"
                    )

                    # Get accounts
                    response = self.session.get(
                        f"{API_BASE_URL}/api/accounts", headers=headers
                    )
                    if response.status_code == 200:
                        accounts = response.json()
                        self.log_test(
                            "Account Retrieval", True, f"Found {len(accounts)} accounts"
                        )
                        return True
                    else:
                        self.log_test(
                            "Account Retrieval",
                            False,
                            f"Status code: {response.status_code}",
                        )
                        return False
                else:
                    self.log_test(
                        "Account Creation", False, "Success flag is False", data
                    )
                    return False
            else:
                self.log_test(
                    "Account Creation", False, f"Status code: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test("Account Management", False, str(e))
            return False

    def test_transaction_management(self):
        """Test transaction creation and retrieval"""
        if not self.token or not self.account_id:
            self.log_test(
                "Transaction Management", False, "No token or account available"
            )
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }

            # Create income transaction
            income_data = {
                "account_id": self.account_id,
                "transaction_type": "income",
                "amount": 500000,
                "category": "حقوق",
                "description": "حقوق ماهانه تست",
            }

            response = self.session.post(
                f"{API_BASE_URL}/api/transactions", json=income_data, headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    income_id = data.get("transaction_id")
                    self.log_test(
                        "Income Transaction", True, f"Transaction ID: {income_id}"
                    )
                else:
                    self.log_test(
                        "Income Transaction", False, "Success flag is False", data
                    )
                    return False
            else:
                self.log_test(
                    "Income Transaction", False, f"Status code: {response.status_code}"
                )
                return False

            # Create expense transaction
            expense_data = {
                "account_id": self.account_id,
                "transaction_type": "expense",
                "amount": 80000,
                "category": "خواربار",
                "description": "خرید مواد غذایی",
            }

            response = self.session.post(
                f"{API_BASE_URL}/api/transactions", json=expense_data, headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    expense_id = data.get("transaction_id")
                    self.log_test(
                        "Expense Transaction", True, f"Transaction ID: {expense_id}"
                    )
                else:
                    self.log_test(
                        "Expense Transaction", False, "Success flag is False", data
                    )
                    return False
            else:
                self.log_test(
                    "Expense Transaction", False, f"Status code: {response.status_code}"
                )
                return False

            # Get transactions
            response = self.session.get(
                f"{API_BASE_URL}/api/transactions", headers=headers
            )
            if response.status_code == 200:
                transactions = response.json()
                self.log_test(
                    "Transaction Retrieval",
                    True,
                    f"Found {len(transactions)} transactions",
                )
                return True
            else:
                self.log_test(
                    "Transaction Retrieval",
                    False,
                    f"Status code: {response.status_code}",
                )
                return False

        except Exception as e:
            self.log_test("Transaction Management", False, str(e))
            return False

    def test_ai_processing(self):
        """Test AI message processing"""
        if not self.token:
            self.log_test("AI Processing", False, "No token available")
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }

            test_messages = [
                "۵۰ هزار تومان قهوه خریدم",
                "دیروز ۲۰۰ تومان اتوبوس",
                "۱ میلیون تومان حقوق گرفتم",
            ]

            all_passed = True

            for message in test_messages:
                response = self.session.post(
                    f"{API_BASE_URL}/api/ai/process-message",
                    json={"message": message},
                    headers=headers,
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        self.log_test(
                            f"AI Processing: '{message}'",
                            True,
                            f"Type: {data.get('transaction_type')}, Amount: {data.get('amount')}, Category: {data.get('category')}",
                        )
                    else:
                        self.log_test(
                            f"AI Processing: '{message}'",
                            False,
                            "Success flag is False",
                            data,
                        )
                        all_passed = False
                else:
                    self.log_test(
                        f"AI Processing: '{message}'",
                        False,
                        f"Status code: {response.status_code}",
                    )
                    all_passed = False

            return all_passed

        except Exception as e:
            self.log_test("AI Processing", False, str(e))
            return False

    def test_savings_plans(self):
        """Test savings plans creation"""
        if not self.token:
            self.log_test("Savings Plans", False, "No token available")
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }

            # Create savings plan
            plan_data = {
                "plan_name": "خرید خانه",
                "plan_type": "بلندمدت",
                "target_amount": 10000000,
                "monthly_contribution": 200000,
                "end_date": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
            }

            response = self.session.post(
                f"{API_BASE_URL}/api/savings-plans", json=plan_data, headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    plan_id = data.get("plan_id")
                    self.log_test("Savings Plan Creation", True, f"Plan ID: {plan_id}")

                    # Get savings plans
                    response = self.session.get(
                        f"{API_BASE_URL}/api/savings-plans", headers=headers
                    )
                    if response.status_code == 200:
                        plans = response.json()
                        self.log_test(
                            "Savings Plans Retrieval", True, f"Found {len(plans)} plans"
                        )
                        return True
                    else:
                        self.log_test(
                            "Savings Plans Retrieval",
                            False,
                            f"Status code: {response.status_code}",
                        )
                        return False
                else:
                    self.log_test(
                        "Savings Plan Creation", False, "Success flag is False", data
                    )
                    return False
            else:
                self.log_test(
                    "Savings Plan Creation",
                    False,
                    f"Status code: {response.status_code}",
                )
                return False

        except Exception as e:
            self.log_test("Savings Plans", False, str(e))
            return False

    def test_check_management(self):
        """Test check creation"""
        if not self.token or not self.account_id:
            self.log_test("Check Management", False, "No token or account available")
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }

            # Create check
            check_data = {
                "account_id": self.account_id,
                "type": "issued",
                "amount": 300000,
                "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "recipient_issuer": "شرکت ABC",
                "description": "پرداخت اجاره",
            }

            response = self.session.post(
                f"{API_BASE_URL}/api/checks", json=check_data, headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    check_id = data.get("check_id")
                    self.log_test("Check Creation", True, f"Check ID: {check_id}")

                    # Get checks
                    response = self.session.get(
                        f"{API_BASE_URL}/api/checks", headers=headers
                    )
                    if response.status_code == 200:
                        checks = response.json()
                        self.log_test(
                            "Check Retrieval", True, f"Found {len(checks)} checks"
                        )
                        return True
                    else:
                        self.log_test(
                            "Check Retrieval",
                            False,
                            f"Status code: {response.status_code}",
                        )
                        return False
                else:
                    self.log_test(
                        "Check Creation", False, "Success flag is False", data
                    )
                    return False
            else:
                self.log_test(
                    "Check Creation", False, f"Status code: {response.status_code}"
                )
                return False

        except Exception as e:
            self.log_test("Check Management", False, str(e))
            return False

    def test_reports(self):
        """Test reports generation"""
        if not self.token:
            self.log_test("Reports", False, "No token available")
            return False

        try:
            headers = {"Authorization": f"Bearer {self.token}"}

            # Get transaction summary
            response = self.session.get(
                f"{API_BASE_URL}/api/transactions/summary", headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Transaction Summary",
                    True,
                    f"Income: {data.get('income', {}).get('total', 0)}, Expense: {data.get('expense', {}).get('total', 0)}",
                )
            else:
                self.log_test(
                    "Transaction Summary", False, f"Status code: {response.status_code}"
                )
                return False

            # Get category summary
            response = self.session.get(
                f"{API_BASE_URL}/api/transactions/categories", headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                self.log_test("Category Summary", True, f"Found {len(data)} categories")
                return True
            else:
                self.log_test(
                    "Category Summary", False, f"Status code: {response.status_code}"
                )
                return False

        except Exception as e:
            self.log_test("Reports", False, str(e))
            return False

    def test_categories(self):
        """Test categories endpoint"""
        try:
            response = self.session.get(f"{API_BASE_URL}/api/categories")
            if response.status_code == 200:
                data = response.json()
                expense_count = len(data.get("expense", []))
                income_count = len(data.get("income", []))
                self.log_test(
                    "Categories",
                    True,
                    f"Expense: {expense_count}, Income: {income_count}",
                )
                return True
            else:
                self.log_test(
                    "Categories", False, f"Status code: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test("Categories", False, str(e))
            return False

    def test_frontend_accessibility(self):
        """Test if React frontend is accessible"""
        try:
            response = self.session.get(REACT_APP_URL)
            if response.status_code == 200:
                self.log_test("Frontend Accessibility", True, "React app is accessible")
                return True
            else:
                self.log_test(
                    "Frontend Accessibility",
                    False,
                    f"Status code: {response.status_code}",
                )
                return False
        except Exception as e:
            self.log_test("Frontend Accessibility", False, str(e))
            return False

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting comprehensive Finance Bot Web Application tests...\n")

        # Basic connectivity tests
        print("📡 Testing basic connectivity...")
        self.test_api_health()
        self.test_frontend_accessibility()
        self.test_categories()

        print("\n👤 Testing user management...")
        self.test_user_creation()
        self.test_authentication()

        print("\n🏦 Testing account management...")
        self.test_account_management()

        print("\n💰 Testing transaction management...")
        self.test_transaction_management()

        print("\n🤖 Testing AI processing...")
        self.test_ai_processing()

        print("\n🎯 Testing savings plans...")
        self.test_savings_plans()

        print("\n📋 Testing check management...")
        self.test_check_management()

        print("\n📊 Testing reports...")
        self.test_reports()

        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests

        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['message']}")

        print(
            "\n🎯 Overall Status:",
            (
                "✅ ALL TESTS PASSED!"
                if failed_tests == 0
                else f"❌ {failed_tests} TESTS FAILED"
            ),
        )

        # Save detailed results
        with open(
            "/Users/ariabod/finance_bot/test_results.json", "w", encoding="utf-8"
        ) as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)

        print(
            f"\n📄 Detailed results saved to: /Users/ariabod/finance_bot/test_results.json"
        )


if __name__ == "__main__":
    tester = FinanceBotTester()
    tester.run_all_tests()
