"""
SMTP Configuration Manager
Handles different SMTP server configurations and connections
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from pathlib import Path
import time
from enum import Enum
import logging

class SMTPAuthType(Enum):
    """SMTP authentication types"""
    NONE = "none"
    PLAIN = "plain"
    LOGIN = "login"
    CRAM_MD5 = "cram-md5"

class SMTPEncryption(Enum):
    """SMTP encryption types"""
    NONE = "none"
    STARTTLS = "starttls"
    SSL_TLS = "ssl_tls"

class SMTPManager:
    def __init__(self, config_dir="config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "smtp_configs.json"
        self.configs = {}
        self.current_config = None
        self.logger = self._setup_logging()
        
        self._load_configs()
    
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _load_configs(self):
        """Load SMTP configurations from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.configs = json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading SMTP configs: {e}")
                self.configs = {}
        else:
            self._create_default_configs()
    
    def _create_default_configs(self):
        """Create default SMTP configurations"""
        self.configs = {
            "gmail": {
                "name": "Gmail",
                "server": "smtp.gmail.com",
                "port": 587,
                "encryption": "starttls",
                "auth_type": "login",
                "timeout": 30,
                "description": "Google Gmail SMTP"
            },
            "outlook": {
                "name": "Outlook",
                "server": "smtp-mail.outlook.com",
                "port": 587,
                "encryption": "starttls",
                "auth_type": "login",
                "timeout": 30,
                "description": "Microsoft Outlook SMTP"
            },
            "yahoo": {
                "name": "Yahoo",
                "server": "smtp.mail.yahoo.com",
                "port": 587,
                "encryption": "starttls",
                "auth_type": "login",
                "timeout": 30,
                "description": "Yahoo Mail SMTP"
            },
            "local": {
                "name": "Local Test",
                "server": "localhost",
                "port": 25,
                "encryption": "none",
                "auth_type": "none",
                "timeout": 10,
                "description": "Local mail server for testing"
            }
        }
        self.save_configs()
    
    def save_configs(self):
        """Save SMTP configurations to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.configs, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving SMTP configs: {e}")
            return False
    
    def get_config(self, config_name):
        """Get SMTP configuration by name"""
        return self.configs.get(config_name)
    
    def create_config(self, config_name, config_data):
        """Create new SMTP configuration"""
        required_fields = ['server', 'port']
        for field in required_fields:
            if field not in config_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults
        config_data.setdefault('encryption', 'starttls')
        config_data.setdefault('auth_type', 'login')
        config_data.setdefault('timeout', 30)
        config_data.setdefault('name', config_name)
        
        self.configs[config_name] = config_data
        self.save_configs()
        return True
    
    def update_config(self, config_name, updates):
        """Update existing SMTP configuration"""
        if config_name not in self.configs:
            return False
        
        self.configs[config_name].update(updates)
        self.save_configs()
        return True
    
    def delete_config(self, config_name):
        """Delete SMTP configuration"""
        if config_name in self.configs:
            del self.configs[config_name]
            self.save_configs()
            return True
        return False
    
    def list_configs(self):
        """List all available SMTP configurations"""
        return list(self.configs.keys())
    
    def set_current_config(self, config_name, credentials=None):
        """Set current SMTP configuration to use"""
        if config_name not in self.configs:
            raise ValueError(f"Configuration '{config_name}' not found")
        
        self.current_config = self.configs[config_name].copy()
        
        if credentials:
            self.current_config.update(credentials)
        
        return self.current_config
    
    def test_connection(self, config_name=None, credentials=None):
        """Test SMTP connection"""
        config = self.current_config if config_name is None else self.get_config(config_name)
        
        if not config:
            raise ValueError("No configuration specified")
        
        if credentials:
            config = config.copy()
            config.update(credentials)
        
        try:
            # Connect to server
            if config['encryption'] == 'ssl_tls':
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(
                    config['server'],
                    config['port'],
                    timeout=config.get('timeout', 30),
                    context=context
                )
            else:
                server = smtplib.SMTP(
                    config['server'],
                    config['port'],
                    timeout=config.get('timeout', 30)
                )
            
            # Start TLS if required
            if config['encryption'] == 'starttls':
                server.starttls()
            
            # Authenticate if required
            if config['auth_type'] != 'none' and 'username' in config and 'password' in config:
                server.login(config['username'], config['password'])
            
            # Test connection
            server.ehlo_or_helo_if_needed()
            
            # Quit gracefully
            server.quit()
            
            return {
                "success": True,
                "message": f"Successfully connected to {config['server']}:{config['port']}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}"
            }
    
    def send_email(self, from_addr, to_addrs, message, config_name=None, credentials=None):
        """Send email using specified configuration"""
        config = self.current_config if config_name is None else self.get_config(config_name)
        
        if not config:
            raise ValueError("No SMTP configuration specified")
        
        if credentials:
            config = config.copy()
            config.update(credentials)
        
        try:
            # Connect to server
            if config['encryption'] == 'ssl_tls':
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(
                    config['server'],
                    config['port'],
                    timeout=config.get('timeout', 30),
                    context=context
                )
            else:
                server = smtplib.SMTP(
                    config['server'],
                    config['port'],
                    timeout=config.get('timeout', 30)
                )
            
            server.set_debuglevel(0)  # Set to 1 for debug output
            
            # Start TLS if required
            if config['encryption'] == 'starttls':
                server.starttls()
            
            # Authenticate if required
            if config['auth_type'] != 'none' and 'username' in config and 'password' in config:
                server.login(config['username'], config['password'])
            
            # Send email
            if isinstance(to_addrs, str):
                to_addrs = [to_addrs]
            
            for to_addr in to_addrs:
                server.sendmail(from_addr, to_addr, message.as_string())
                time.sleep(0.1)  # Small delay between sends
            
            # Quit gracefully
            server.quit()
            
            return {
                "success": True,
                "sent_to": to_addrs
            }
            
        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP error: {e}")
            return {
                "success": False,
                "error": f"SMTP error: {str(e)}"
            }
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def create_message(self, from_addr, to_addr, subject, body, html_body=None, attachments=None):
        """Create email message"""
        if html_body:
            msg = MIMEMultipart('alternative')
            msg.attach(MIMEText(body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
        else:
            msg = MIMEText(body, 'plain')
        
        msg['From'] = from_addr
        msg['To'] = to_addr
        msg['Subject'] = subject
        msg['Date'] = time.strftime('%a, %d %b %Y %H:%M:%S %z')
        
        # TODO: Add attachment support
        # if attachments:
        #     for attachment in attachments:
        #         # Add attachment logic here
        #         pass
        
        return msg
