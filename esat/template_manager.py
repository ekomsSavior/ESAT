"""
Email Template Manager
Handles creation, storage, and management of email templates
"""

import json
import random
from pathlib import Path
from datetime import datetime
import csv

class TemplateManager:
    def __init__(self, templates_dir="templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        self.templates_file = self.templates_dir / "email_templates.json"
        self.categories_file = self.templates_dir / "categories.json"
        self.templates = []
        self.categories = []
        
        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize template and category files if they don't exist"""
        if not self.templates_file.exists():
            self.templates = self._create_default_templates()
            self.save_templates()
        else:
            self.load_templates()
        
        if not self.categories_file.exists():
            self.categories = self._create_default_categories()
            self.save_categories()
        else:
            self.load_categories()
    
    def _create_default_templates(self):
        """Create default email templates for security testing"""
        return [
            {
                "id": "training_001",
                "name": "Security Awareness Test",
                "subject": "Security Test - Phishing Simulation",
                "body": """This is a security awareness test email.

Our security team is conducting phishing simulation exercises to help improve our defenses.

Please remain vigilant for suspicious emails in your inbox.

Best regards,
Security Team""",
                "category": "training",
                "priority": "low",
                "variables": ["name", "department"],
                "created": datetime.now().isoformat(),
                "tags": ["test", "training", "security"]
            },
            {
                "id": "urgent_001",
                "name": "Password Reset Required",
                "subject": "URGENT: Password Reset Required",
                "body": """Dear {name},

Our security system has detected unusual activity on your account. 
To protect your account, please reset your password immediately.

Click here to reset: https://test.example.com/reset

If you did not request this change, please contact IT immediately.

Sincerely,
IT Security Department""",
                "category": "urgent",
                "priority": "high",
                "variables": ["name", "position"],
                "created": datetime.now().isoformat(),
                "tags": ["urgent", "password", "security"]
            },
            {
                "id": "business_001",
                "name": "Meeting Invitation",
                "subject": "Meeting Invitation: Quarterly Review",
                "body": """Hello {name},

You are invited to attend our quarterly review meeting.

Date: {date}
Time: 2:00 PM EST
Location: Conference Room B / Zoom

Please RSVP by Friday.

Best regards,
{manager_name}
Department Head""",
                "category": "business",
                "priority": "medium",
                "variables": ["name", "department", "date", "manager_name"],
                "created": datetime.now().isoformat(),
                "tags": ["meeting", "business", "invitation"]
            }
        ]
    
    def _create_default_categories(self):
        """Create default template categories"""
        return [
            {"id": "training", "name": "Training", "description": "Security awareness emails"},
            {"id": "urgent", "name": "Urgent", "description": "Time-sensitive emails"},
            {"id": "business", "name": "Business", "description": "Regular business emails"},
            {"id": "newsletter", "name": "Newsletter", "description": "Newsletter-style emails"},
            {"id": "phishing", "name": "Phishing", "description": "Phishing simulation emails"}
        ]
    
    def load_templates(self):
        """Load templates from JSON file"""
        try:
            with open(self.templates_file, 'r') as f:
                self.templates = json.load(f)
        except Exception as e:
            print(f"Error loading templates: {e}")
            self.templates = self._create_default_templates()
    
    def save_templates(self):
        """Save templates to JSON file"""
        try:
            with open(self.templates_file, 'w') as f:
                json.dump(self.templates, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving templates: {e}")
            return False
    
    def load_categories(self):
        """Load categories from JSON file"""
        try:
            with open(self.categories_file, 'r') as f:
                self.categories = json.load(f)
        except Exception as e:
            print(f"Error loading categories: {e}")
            self.categories = self._create_default_categories()
    
    def save_categories(self):
        """Save categories to JSON file"""
        try:
            with open(self.categories_file, 'w') as f:
                json.dump(self.categories, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving categories: {e}")
            return False
    
    def get_template(self, template_id=None, category=None, random_select=False):
        """Get template by ID, category, or random"""
        if template_id:
            for template in self.templates:
                if template['id'] == template_id:
                    return template
            return None
        
        if category:
            filtered = [t for t in self.templates if t['category'] == category]
            if filtered:
                if random_select:
                    return random.choice(filtered)
                return filtered[0]
        
        if random_select:
            return random.choice(self.templates)
        
        return self.templates[0] if self.templates else None
    
    def create_template(self, template_data):
        """Create a new template"""
        template_data['id'] = f"{template_data['category']}_{len(self.templates) + 1:03d}"
        template_data['created'] = datetime.now().isoformat()
        
        # Ensure required fields
        required = ['name', 'subject', 'body', 'category']
        for field in required:
            if field not in template_data:
                raise ValueError(f"Missing required field: {field}")
        
        self.templates.append(template_data)
        self.save_templates()
        return template_data['id']
    
    def update_template(self, template_id, updates):
        """Update an existing template"""
        for i, template in enumerate(self.templates):
            if template['id'] == template_id:
                self.templates[i].update(updates)
                self.save_templates()
                return True
        return False
    
    def delete_template(self, template_id):
        """Delete a template"""
        self.templates = [t for t in self.templates if t['id'] != template_id]
        self.save_templates()
        return True
    
    def export_templates_csv(self, output_file="templates_export.csv"):
        """Export templates to CSV"""
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                if self.templates:
                    fieldnames = self.templates[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.templates)
            return True
        except Exception as e:
            print(f"Error exporting templates: {e}")
            return False
    
    def get_all_templates(self):
        """Return all templates"""
        return self.templates
    
    def get_categories(self):
        """Return all categories"""
        return self.categories
    
    def render_template(self, template, variables=None):
        """Render template with variables"""
        if variables is None:
            variables = {}
        
        subject = template['subject']
        body = template['body']
        
        # Replace variables in subject and body
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            subject = subject.replace(placeholder, str(value))
            body = body.replace(placeholder, str(value))
        
        return {
            'subject': subject,
            'body': body,
            'template_id': template['id'],
            'template_name': template['name']
        }
