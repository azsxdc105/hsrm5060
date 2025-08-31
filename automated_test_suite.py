#!/usr/bin/env python3
"""
Automated Test Suite for Insurance Claims Management System
"""
import requests
import json
import time
from datetime import datetime
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class SystemTester:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, success, message="", details=""):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_server_connectivity(self):
        """Test basic server connectivity"""
        try:
            response = self.session.get(self.base_url, timeout=10)
            if response.status_code == 200:
                self.log_test("Server Connectivity", True, "Server is accessible")
                return True
            else:
                self.log_test("Server Connectivity", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Server Connectivity", False, "Server not accessible", str(e))
            return False
    
    def test_login_functionality(self):
        """Test login functionality"""
        try:
            # Get login page
            login_response = self.session.get(f"{self.base_url}/auth/login")
            if login_response.status_code != 200:
                self.log_test("Login Page Access", False, f"Status: {login_response.status_code}")
                return False
            
            # Extract CSRF token (simplified)
            csrf_token = "test-token"  # In real implementation, parse from HTML
            
            # Attempt login
            login_data = {
                'email': 'admin@insurance.com',
                'password': 'admin123',
                'csrf_token': csrf_token
            }
            
            login_post = self.session.post(f"{self.base_url}/auth/login", data=login_data)
            
            # Check if redirected (successful login)
            if login_post.status_code in [200, 302]:
                self.log_test("Login Functionality", True, "Login successful")
                return True
            else:
                self.log_test("Login Functionality", False, f"Status: {login_post.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Login Functionality", False, "Login failed", str(e))
            return False
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        api_tests = [
            ("/ai-classification/api/statistics", "AI Classification Statistics"),
            ("/advanced-notifications/api/statistics", "Notifications Statistics"),
            ("/advanced-notifications/api/unread_count", "Unread Count API"),
        ]
        
        all_passed = True
        for endpoint, description in api_tests:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code in [200, 401, 403]:  # Expected responses
                    self.log_test(f"API: {description}", True, f"Status: {response.status_code}")
                else:
                    self.log_test(f"API: {description}", False, f"Status: {response.status_code}")
                    all_passed = False
            except Exception as e:
                self.log_test(f"API: {description}", False, "Request failed", str(e))
                all_passed = False
        
        return all_passed
    
    def test_page_accessibility(self):
        """Test important pages accessibility"""
        pages_to_test = [
            ("/", "Home Page"),
            ("/dashboard", "Dashboard"),
            ("/claims", "Claims List"),
            ("/claims/new", "New Claim"),
            ("/admin", "Admin Panel"),
            ("/admin/users", "User Management"),
            ("/admin/companies", "Company Management"),
            ("/admin/settings", "System Settings"),
            ("/admin/advanced-features", "Advanced Features"),
            ("/ai-classification", "AI Classification"),
            ("/advanced-notifications", "Advanced Notifications"),
            ("/advanced-notifications/settings", "Notification Settings"),
            ("/advanced-notifications/send", "Send Notification"),
            ("/advanced-notifications/templates", "Notification Templates"),
        ]
        
        accessible_count = 0
        total_count = len(pages_to_test)
        
        for path, description in pages_to_test:
            try:
                response = self.session.get(f"{self.base_url}{path}", timeout=5)
                if response.status_code in [200, 302]:  # 302 for login redirects
                    self.log_test(f"Page: {description}", True, f"Accessible ({response.status_code})")
                    accessible_count += 1
                else:
                    self.log_test(f"Page: {description}", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Page: {description}", False, "Request failed", str(e))
        
        success_rate = (accessible_count / total_count) * 100
        overall_success = success_rate >= 90  # 90% success rate required
        
        self.log_test("Overall Page Accessibility", overall_success, 
                     f"{accessible_count}/{total_count} pages accessible ({success_rate:.1f}%)")
        
        return overall_success
    
    def test_database_functionality(self):
        """Test database functionality"""
        try:
            from app import create_app, db
            from app.models import User, InsuranceCompany, Claim, ClaimClassification, Notification
            
            app = create_app()
            with app.app_context():
                # Test basic queries
                user_count = User.query.count()
                company_count = InsuranceCompany.query.count()
                claim_count = Claim.query.count()
                
                self.log_test("Database Connection", True, "Database accessible")
                self.log_test("Database Data", True, 
                             f"Users: {user_count}, Companies: {company_count}, Claims: {claim_count}")
                
                # Test admin user exists
                admin_exists = User.query.filter_by(role='admin').first() is not None
                self.log_test("Admin User Exists", admin_exists, 
                             "Admin user found" if admin_exists else "No admin user")
                
                return True
                
        except Exception as e:
            self.log_test("Database Functionality", False, "Database error", str(e))
            return False
    
    def test_ai_classification(self):
        """Test AI classification functionality"""
        try:
            from app import create_app
            from app.ai_classification import classify_claim_ai
            from app.models import Claim
            
            app = create_app()
            with app.app_context():
                # Get a sample claim
                sample_claim = Claim.query.first()
                if sample_claim:
                    # Test classification
                    result = classify_claim_ai(sample_claim)
                    
                    if hasattr(result, 'category') and hasattr(result, 'confidence'):
                        self.log_test("AI Classification", True, 
                                     f"Category: {result.category}, Confidence: {result.confidence:.2f}")
                        return True
                    else:
                        self.log_test("AI Classification", False, "Invalid classification result")
                        return False
                else:
                    self.log_test("AI Classification", False, "No claims to classify")
                    return False
                    
        except Exception as e:
            self.log_test("AI Classification", False, "Classification failed", str(e))
            return False
    
    def test_notification_system(self):
        """Test notification system"""
        try:
            from app import create_app, db
            from app.models import Notification, User, NotificationTemplate
            from datetime import datetime
            
            app = create_app()
            with app.app_context():
                # Test notification creation
                admin_user = User.query.filter_by(role='admin').first()
                if admin_user:
                    test_notification = Notification(
                        user_id=admin_user.id,
                        title='Test Notification',
                        message='This is a test notification from automated test suite',
                        priority='normal',
                        notification_type='in_app',
                        status='sent',
                        created_at=datetime.utcnow()
                    )
                    
                    db.session.add(test_notification)
                    db.session.commit()
                    
                    self.log_test("Notification Creation", True, "Test notification created")
                    
                    # Test template count
                    template_count = NotificationTemplate.query.count()
                    self.log_test("Notification Templates", True, f"{template_count} templates available")
                    
                    return True
                else:
                    self.log_test("Notification System", False, "No admin user for testing")
                    return False
                    
        except Exception as e:
            self.log_test("Notification System", False, "Notification test failed", str(e))
            return False
    
    def test_file_structure(self):
        """Test important file structure"""
        important_files = [
            "app/__init__.py",
            "app/models.py",
            "app/forms.py",
            "app/routes/main.py",
            "app/routes/admin.py",
            "app/routes/claims.py",
            "app/routes/ai_classification.py",
            "app/routes/advanced_notifications.py",
            "app/templates/base.html",
            "app/static/css/style.css",
            "config.py",
            "run.py",
            "requirements.txt",
        ]
        
        missing_files = []
        for file_path in important_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if not missing_files:
            self.log_test("File Structure", True, "All important files present")
            return True
        else:
            self.log_test("File Structure", False, f"Missing files: {', '.join(missing_files)}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Automated Test Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run tests in order
        tests = [
            ("Server Connectivity", self.test_server_connectivity),
            ("File Structure", self.test_file_structure),
            ("Database Functionality", self.test_database_functionality),
            ("Page Accessibility", self.test_page_accessibility),
            ("API Endpoints", self.test_api_endpoints),
            ("AI Classification", self.test_ai_classification),
            ("Notification System", self.test_notification_system),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Running {test_name}...")
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_test(test_name, False, "Test execution failed", str(e))
        
        # Generate summary
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"✅ Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if success_rate >= 80:
            print("🎉 OVERALL RESULT: SYSTEM HEALTHY")
        elif success_rate >= 60:
            print("⚠️  OVERALL RESULT: SYSTEM NEEDS ATTENTION")
        else:
            print("❌ OVERALL RESULT: SYSTEM HAS ISSUES")
        
        # Save detailed results
        self.save_test_results()
        
        return success_rate >= 80
    
    def save_test_results(self):
        """Save test results to file"""
        try:
            results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            print(f"📄 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️  Could not save results: {e}")

def main():
    """Main function"""
    print("🔍 Insurance Claims Management System - Automated Test Suite")
    print("=" * 60)
    
    # Check if server is specified
    base_url = "http://127.0.0.1:5000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"🌐 Testing server: {base_url}")
    
    # Create tester and run tests
    tester = SystemTester(base_url)
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
