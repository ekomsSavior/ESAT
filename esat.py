#!/usr/bin/env python3
"""
Email Security Assessment Tool (ESAT) - Main Script
Simple Advanced Campaign Implementation
"""

import sys
import os
import json
import time
import random
import threading
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from esat import (
        TemplateManager,
        SMTPManager,
        ReportGenerator,
        RateLimiterManager,
        CampaignScheduler,
        SchedulerCLI
    )
except ImportError as e:
    print(f"Error importing ESAT modules: {e}")
    print("Make sure all modules are in the 'esat' directory with __init__.py")
    sys.exit(1)

class ESAT:
    """Main ESAT class"""
    
    def __init__(self):
        self.template_manager = TemplateManager()
        self.smtp_manager = SMTPManager()
        self.report_generator = ReportGenerator()
        self.rate_limiter = None
        self.scheduler = CampaignScheduler()
        self.is_running = False
    
    def show_banner(self):
        """Display the ESAT banner"""
        banner = """
╔═══════════════════════════════════════════════════════════╗
║    ███████╗███████╗ █████╗ ████████╗                      ║
║    ██╔════╝██╔════╝██╔══██╗╚══██╔══╝                      ║
║    █████╗  ███████╗███████║   ██║                         ║
║    ██╔══╝  ╚════██║██╔══██║   ██║                         ║
║    ███████╗███████║██║  ██║   ██║                         ║
║    ╚══════╝╚══════╝╚═╝  ╚═╝   ╚═╝                         ║
║                                                           ║
║    Email Security Assessment Tool                         ║
║    by ek0ms savi0r                                        ║
╚═══════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def disclaimer(self):
        """Show legal disclaimer"""
        print("\n" + "="*60)
        print("  IMPORTANT LEGAL DISCLAIMER")
        print("="*60)
        print("This tool is for AUTHORIZED security testing ONLY.")
        print("="*60)
        
        response = input("\nDo you accept full responsibility for proper use? (yes/NO): ").strip().lower()
        return response == 'yes'
    
    def main_menu(self):
        """Display main menu"""
        while True:
            print("\n" + "="*50)
            print("MAIN MENU")
            print("="*50)
            print("1. Quick Campaign")
            print("2. Advanced Campaign")
            print("3. Manage Templates")
            print("4. Manage SMTP Configs")
            print("5. Schedule Campaign")
            print("6. View Reports")
            print("7. Exit")
            print("="*50)
            
            choice = input("\nSelect option (1-7): ").strip()
            
            if choice == "1":
                self.quick_campaign()
            elif choice == "2":
                self.advanced_campaign()
            elif choice == "3":
                self.manage_templates_menu()
            elif choice == "4":
                self.manage_smtp_menu()
            elif choice == "5":
                self.schedule_menu()
            elif choice == "6":
                self.view_reports_menu()
            elif choice == "7":
                print("\nExiting ESAT. Stay secure!")
                break
            else:
                print("Invalid choice. Please try again.")
    
    def quick_campaign(self):
        """Quick campaign setup"""
        print("\n" + "="*50)
        print("QUICK CAMPAIGN")
        print("="*50)
        
        # Get basic info
        target = input("Target email: ").strip()
        if not target:
            print("Target email required!")
            return
        
        # Select SMTP config
        configs = self.smtp_manager.list_configs()
        if not configs:
            print("No SMTP configurations found!")
            print("Please create one in 'Manage SMTP Configs' first.")
            return
        
        print("\nAvailable SMTP Configurations:")
        for i, config_name in enumerate(configs, 1):
            config = self.smtp_manager.get_config(config_name)
            print(f"{i}. {config['name']}")
        
        try:
            choice = int(input(f"\nSelect config (1-{len(configs)}): ").strip())
            config_name = configs[choice-1]
        except:
            print("Invalid selection. Using first config.")
            config_name = configs[0]
        
        # Get credentials
        print(f"\nSMTP Credentials for {config_name}:")
        username = input("Email/Username: ").strip()
        password = input("Password: ").strip()
        
        # Test connection
        print("\nTesting connection...")
        result = self.smtp_manager.test_connection(config_name, {
            'username': username,
            'password': password
        })
        
        print(f"Result: {result['message']}")
        if not result['success']:
            proceed = input("Continue anyway? (y/n): ").strip().lower()
            if proceed != 'y':
                return
        
        # Get number of emails
        try:
            count = int(input("\nNumber of emails to send: ").strip())
            if count < 1:
                print("Must send at least 1 email!")
                return
        except:
            print("Invalid number!")
            return
        
        # Get delay between emails
        try:
            delay = float(input("Delay between emails (seconds): ").strip() or "1")
        except:
            delay = 1.0
        
        # Select template
        templates = self.template_manager.get_all_templates()
        print(f"\nAvailable Templates ({len(templates)} total):")
        for i, template in enumerate(templates[:5], 1):
            print(f"{i}. {template['name']} - {template['subject'][:30]}...")
        
        if len(templates) > 5:
            print(f"... and {len(templates) - 5} more")
        
        template_choice = input("\nSelect template (number or 'random'): ").strip().lower()
        
        if template_choice == 'random':
            template = self.template_manager.get_template(random_select=True)
        elif template_choice.isdigit():
            idx = int(template_choice) - 1
            if 0 <= idx < len(templates):
                template = templates[idx]
            else:
                template = self.template_manager.get_template(random_select=True)
        else:
            template = self.template_manager.get_template(random_select=True)
        
        # Confirm
        print("\n" + "="*50)
        print("QUICK CAMPAIGN SUMMARY")
        print("="*50)
        print(f"Target: {target}")
        print(f"SMTP Config: {config_name}")
        print(f"Emails to send: {count}")
        print(f"Delay: {delay} seconds")
        print(f"Template: {template['name']}")
        print("="*50)
        
        confirm = input("\nStart campaign? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Campaign cancelled.")
            return
        
        # Run campaign
        print(f"\nStarting campaign to {target}...")
        
        stats = {
            'sent': 0,
            'failed': 0,
            'start_time': datetime.now().isoformat()
        }
        
        try:
            for i in range(count):
                print(f"\nSending email {i+1}/{count}...")
                
                # Render template with variables
                rendered = self.template_manager.render_template(template, {
                    'name': target.split('@')[0],
                    'email': target,
                    'count': i+1,
                    'total': count
                })
                
                # Create message
                from esat.smtp_manager import SMTPManager
                smtp = SMTPManager()
                
                message = smtp.create_message(
                    from_addr=username,
                    to_addr=target,
                    subject=rendered['subject'],
                    body=rendered['body']
                )
                
                # Send email
                result = smtp.send_email(
                    from_addr=username,
                    to_addrs=target,
                    message=message,
                    config_name=config_name,
                    credentials={
                        'username': username,
                        'password': password
                    }
                )
                
                if result['success']:
                    stats['sent'] += 1
                    print(f"✓ Email {i+1} sent successfully!")
                else:
                    stats['failed'] += 1
                    print(f"✗ Failed to send email {i+1}: {result.get('error', 'Unknown error')}")
                
                # Delay if not last email
                if i < count - 1:
                    time.sleep(delay)
        
        except KeyboardInterrupt:
            print("\n\nCampaign interrupted by user.")
        except Exception as e:
            print(f"\nError during campaign: {e}")
        finally:
            stats['end_time'] = datetime.now().isoformat()
            
            # Generate report
            campaign_data = {
                'campaign_name': f"Quick_Campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'campaign_id': f"quick_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'config': {
                    'target': target,
                    'smtp_config': config_name,
                    'count': count,
                    'delay': delay
                },
                'stats': stats,
                'targets': [target]
            }
            
            print("\nGenerating report...")
            report_result = self.report_generator.generate_report(campaign_data, output_format="json")
            
            if report_result['success']:
                print(f"✓ Report saved: {report_result['files'][0]}")
            
            print(f"\n{'='*50}")
            print("CAMPAIGN COMPLETE")
            print(f"Total sent: {stats['sent']}")
            print(f"Total failed: {stats['failed']}")
            print(f"Success rate: {(stats['sent']/(stats['sent']+stats['failed'])*100 if (stats['sent']+stats['failed']) > 0 else 0):.1f}%")
            print(f"{'='*50}")
    
    def advanced_campaign(self):
        """Advanced campaign setup - SIMPLE BUT FUNCTIONAL"""
        print("\n" + "="*50)
        print("ADVANCED CAMPAIGN")
        print("="*50)
        print("Features:")
        print("• Multiple targets")
        print("• Multiple templates")
        print("• Variable delays")
        print("• Batch sending")
        print("="*50)
        
        # Get targets
        target_input = input("\nTarget emails (comma-separated or file path): ").strip()
        if Path(target_input).exists():
            with open(target_input, 'r') as f:
                targets = [line.strip() for line in f if line.strip()]
        else:
            targets = [t.strip() for t in target_input.split(',')]
        
        if not targets:
            print("No targets specified!")
            return
        
        print(f"Loaded {len(targets)} targets")
        
        # Select SMTP config
        configs = self.smtp_manager.list_configs()
        if not configs:
            print("No SMTP configurations found!")
            return
        
        print("\nAvailable SMTP Configurations:")
        for i, config_name in enumerate(configs, 1):
            config = self.smtp_manager.get_config(config_name)
            print(f"{i}. {config['name']}")
        
        try:
            choice = int(input(f"\nSelect config (1-{len(configs)}): ").strip())
            config_name = configs[choice-1]
        except:
            config_name = configs[0]
        
        config = self.smtp_manager.get_config(config_name)
        
        # Get credentials
        print(f"\nSMTP Credentials for {config['name']}:")
        username = input("Email/Username: ").strip()
        password = input("Password: ").strip()
        
        credentials = {'username': username, 'password': password}
        
        # Test connection
        print("\nTesting connection...")
        result = self.smtp_manager.test_connection(config_name, credentials)
        print(f"Result: {result['message']}")
        
        if not result['success']:
            proceed = input("Continue anyway? (y/n): ").strip().lower()
            if proceed != 'y':
                return
        
        # Get templates
        templates = self.template_manager.get_all_templates()
        if not templates:
            print("No templates found!")
            return
        
        print(f"\nAvailable Templates ({len(templates)} total)")
        print("1. Use all templates (random rotation)")
        print("2. Select specific templates")
        print("3. Use single template")
        
        template_choice = input("\nTemplate selection (1-3): ").strip()
        
        if template_choice == "1":
            selected_templates = templates
            print(f"Using all {len(templates)} templates in random rotation")
        elif template_choice == "2":
            print("\nSelect templates (comma-separated numbers):")
            for i, template in enumerate(templates[:10], 1):
                print(f"{i}. {template['name']}")
            
            if len(templates) > 10:
                print(f"... and {len(templates) - 10} more")
            
            selection = input("\nSelection: ").strip()
            selected_indices = [int(idx.strip()) - 1 for idx in selection.split(',')]
            selected_templates = [templates[i] for i in selected_indices if i < len(templates)]
            print(f"Selected {len(selected_templates)} templates")
        else:
            # Single template
            print("\nSelect single template:")
            for i, template in enumerate(templates[:10], 1):
                print(f"{i}. {template['name']}")
            
            try:
                choice = int(input(f"\nSelect template (1-{min(10, len(templates))}): ").strip())
                selected_templates = [templates[choice-1]]
            except:
                selected_templates = [templates[0]]
            print(f"Using template: {selected_templates[0]['name']}")
        
        # Campaign parameters
        print("\n" + "="*50)
        print("ADVANCED PARAMETERS")
        print("="*50)
        
        emails_per_target = int(input("Emails per target (default 1): ").strip() or "1")
        
        print("\nDelay Pattern:")
        print("1. Constant delay")
        print("2. Random delay between range")
        print("3. Increasing delay")
        print("4. Decreasing delay")
        
        delay_pattern = input("\nSelect pattern (1-4, default 1): ").strip() or "1"
        
        if delay_pattern == "1":
            base_delay = float(input("Delay between emails (seconds): ").strip() or "1")
            delay_func = lambda i: base_delay
            pattern_name = "constant"
        elif delay_pattern == "2":
            min_delay = float(input("Minimum delay (seconds): ").strip() or "0.5")
            max_delay = float(input("Maximum delay (seconds): ").strip() or "3")
            delay_func = lambda i: random.uniform(min_delay, max_delay)
            pattern_name = "random"
        elif delay_pattern == "3":
            start_delay = float(input("Starting delay (seconds): ").strip() or "0.5")
            increment = float(input("Delay increment per email: ").strip() or "0.1")
            delay_func = lambda i: start_delay + (i * increment)
            pattern_name = "increasing"
        elif delay_pattern == "4":
            start_delay = float(input("Starting delay (seconds): ").strip() or "3")
            decrement = float(input("Delay decrement per email: ").strip() or "0.1")
            delay_func = lambda i: max(0.1, start_delay - (i * decrement))
            pattern_name = "decreasing"
        else:
            delay_func = lambda i: 1.0
            pattern_name = "constant"
        
        # Batch sending option
        use_batches = input("\nUse batch sending? (y/n, default n): ").strip().lower() == 'y'
        batch_size = 1
        batch_delay = 0
        
        if use_batches:
            batch_size = int(input("Batch size (emails per batch): ").strip() or "5")
            batch_delay = float(input("Delay between batches (seconds): ").strip() or "10")
        
        # Confirm
        total_emails = len(targets) * emails_per_target
        estimated_time = total_emails * (delay_func(0) if callable(delay_func) else 1.0)
        
        print("\n" + "="*50)
        print("ADVANCED CAMPAIGN SUMMARY")
        print("="*50)
        print(f"Targets: {len(targets)}")
        print(f"Emails per target: {emails_per_target}")
        print(f"Total emails: {total_emails}")
        print(f"Templates: {len(selected_templates)}")
        print(f"Delay pattern: {pattern_name}")
        
        if use_batches:
            print(f"Batch size: {batch_size}")
            print(f"Batch delay: {batch_delay}s")
        
        print(f"Estimated time: {estimated_time:.1f} seconds")
        print("="*50)
        
        confirm = input("\nStart campaign? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Campaign cancelled.")
            return
        
        # Run advanced campaign
        print(f"\nStarting advanced campaign...")
        
        stats = {
            'sent': 0,
            'failed': 0,
            'start_time': datetime.now().isoformat(),
            'targets': targets,
            'pattern': pattern_name,
            'templates_used': len(selected_templates)
        }
        
        try:
            email_count = 0
            batch_count = 0
            
            for target_idx, target in enumerate(targets):
                print(f"\nProcessing target {target_idx + 1}/{len(targets)}: {target}")
                
                for email_idx in range(emails_per_target):
                    email_count += 1
                    
                    # Select template
                    if len(selected_templates) > 1:
                        template = selected_templates[email_count % len(selected_templates)]
                    else:
                        template = selected_templates[0]
                    
                    print(f"  Sending email {email_count}/{total_emails} using '{template['name']}'...")
                    
                    # Render template
                    rendered = self.template_manager.render_template(template, {
                        'name': target.split('@')[0],
                        'email': target,
                        'target_number': target_idx + 1,
                        'total_targets': len(targets),
                        'email_number': email_idx + 1,
                        'total_emails': emails_per_target
                    })
                    
                    # Create and send message
                    message = self.smtp_manager.create_message(
                        from_addr=username,
                        to_addr=target,
                        subject=rendered['subject'],
                        body=rendered['body']
                    )
                    
                    result = self.smtp_manager.send_email(
                        from_addr=username,
                        to_addrs=target,
                        message=message,
                        config_name=config_name,
                        credentials=credentials
                    )
                    
                    if result['success']:
                        stats['sent'] += 1
                        print(f"    ✓ Sent successfully!")
                    else:
                        stats['failed'] += 1
                        print(f"    ✗ Failed: {result.get('error', 'Unknown error')[:50]}")
                    
                    # Apply delay
                    if email_count < total_emails:
                        delay = delay_func(email_count) if callable(delay_func) else 1.0
                        time.sleep(delay)
                    
                    # Batch delay
                    if use_batches and batch_size > 0:
                        batch_count += 1
                        if batch_count >= batch_size:
                            print(f"    Batch complete. Waiting {batch_delay}s...")
                            time.sleep(batch_delay)
                            batch_count = 0
        
        except KeyboardInterrupt:
            print("\n\nCampaign interrupted by user.")
        except Exception as e:
            print(f"\nError during campaign: {e}")
            import traceback
            traceback.print_exc()
        finally:
            stats['end_time'] = datetime.now().isoformat()
            
            # Generate report
            campaign_data = {
                'campaign_name': f"Advanced_{pattern_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'campaign_id': f"adv_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'campaign_type': 'advanced',
                'config': {
                    'smtp_config': config_name,
                    'targets_count': len(targets),
                    'emails_per_target': emails_per_target,
                    'pattern': pattern_name,
                    'batch_mode': use_batches,
                    'batch_size': batch_size if use_batches else None
                },
                'stats': stats,
                'targets': targets
            }
            
            print("\nGenerating report...")
            report_result = self.report_generator.generate_report(campaign_data, output_format="json")
            
            if report_result['success']:
                print(f"✓ Report saved: {report_result['files'][0]}")
            
            print(f"\n{'='*50}")
            print("ADVANCED CAMPAIGN COMPLETE")
            print(f"Total targets: {len(targets)}")
            print(f"Total sent: {stats['sent']}")
            print(f"Total failed: {stats['failed']}")
            print(f"Success rate: {(stats['sent']/(stats['sent']+stats['failed'])*100 if (stats['sent']+stats['failed']) > 0 else 0):.1f}%")
            print(f"Pattern used: {pattern_name}")
            print(f"{'='*50}")
    
    def manage_templates_menu(self):
        """Template management menu"""
        print("\n" + "="*50)
        print("TEMPLATE MANAGEMENT")
        print("="*50)
        
        while True:
            print("\n1. List templates")
            print("2. Create template")
            print("3. View template details")
            print("4. Delete template")
            print("5. Back to main menu")
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == "1":
                templates = self.template_manager.get_all_templates()
                print(f"\nTotal templates: {len(templates)}")
                for template in templates:
                    print(f"\nID: {template['id']}")
                    print(f"Name: {template['name']}")
                    print(f"Subject: {template['subject'][:50]}...")
                    print(f"Category: {template['category']}")
                    print("-" * 30)
            
            elif choice == "2":
                print("\nCreate New Template")
                print("-" * 30)
                
                name = input("Template name: ").strip()
                if not name:
                    print("Name required!")
                    continue
                
                subject = input("Email subject: ").strip()
                if not subject:
                    print("Subject required!")
                    continue
                
                print("\nEmail body (type 'END' on a new line to finish):")
                lines = []
                while True:
                    line = input()
                    if line == "END":
                        break
                    lines.append(line)
                
                body = "\n".join(lines)
                if not body:
                    print("Body required!")
                    continue
                
                category = input("Category (default: general): ").strip() or "general"
                
                template_data = {
                    'name': name,
                    'subject': subject,
                    'body': body,
                    'category': category
                }
                
                try:
                    template_id = self.template_manager.create_template(template_data)
                    print(f"✓ Template created with ID: {template_id}")
                except Exception as e:
                    print(f"✗ Error creating template: {e}")
            
            elif choice == "3":
                template_id = input("Template ID to view: ").strip()
                template = self.template_manager.get_template(template_id)
                
                if template:
                    print(f"\nTemplate: {template['name']} ({template['id']})")
                    print(f"Category: {template['category']}")
                    print(f"Created: {template.get('created', 'N/A')}")
                    print(f"\nSubject: {template['subject']}")
                    print(f"\nBody:\n{template['body']}")
                else:
                    print("Template not found!")
            
            elif choice == "4":
                template_id = input("Template ID to delete: ").strip()
                template = self.template_manager.get_template(template_id)
                
                if template:
                    confirm = input(f"Delete template '{template['name']}'? (y/n): ").strip().lower()
                    if confirm == 'y':
                        if self.template_manager.delete_template(template_id):
                            print("✓ Template deleted!")
                        else:
                            print("✗ Error deleting template!")
                else:
                    print("Template not found!")
            
            elif choice == "5":
                break
    
    def manage_smtp_menu(self):
        """SMTP management menu"""
        print("\n" + "="*50)
        print("SMTP CONFIGURATION MANAGEMENT")
        print("="*50)
        
        while True:
            print("\n1. List configurations")
            print("2. Create configuration")
            print("3. Test configuration")
            print("4. Delete configuration")
            print("5. Back to main menu")
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == "1":
                configs = self.smtp_manager.list_configs()
                print(f"\nTotal configurations: {len(configs)}")
                for config_name in configs:
                    config = self.smtp_manager.get_config(config_name)
                    print(f"\nName: {config_name}")
                    print(f"  Server: {config['server']}:{config['port']}")
                    print(f"  Encryption: {config['encryption']}")
                    print(f"  Auth Type: {config['auth_type']}")
                    print(f"  Description: {config.get('description', 'N/A')}")
            
            elif choice == "2":
                print("\nCreate New SMTP Configuration")
                print("-" * 30)
                
                name = input("Configuration name: ").strip()
                if not name:
                    print("Name required!")
                    continue
                
                server = input("SMTP server (e.g., smtp.gmail.com): ").strip()
                if not server:
                    print("Server required!")
                    continue
                
                port = input("Port (default 587): ").strip()
                port = int(port) if port else 587
                
                encryption = input("Encryption (none/starttls/ssl_tls, default starttls): ").strip().lower()
                if encryption not in ['none', 'starttls', 'ssl_tls']:
                    encryption = 'starttls'
                
                auth_type = input("Auth type (none/plain/login, default login): ").strip().lower()
                if auth_type not in ['none', 'plain', 'login']:
                    auth_type = 'login'
                
                description = input("Description (optional): ").strip()
                
                config_data = {
                    'name': name,
                    'server': server,
                    'port': port,
                    'encryption': encryption,
                    'auth_type': auth_type,
                    'description': description,
                    'timeout': 30
                }
                
                try:
                    self.smtp_manager.create_config(name, config_data)
                    print(f"✓ Configuration '{name}' created!")
                except Exception as e:
                    print(f"✗ Error creating configuration: {e}")
            
            elif choice == "3":
                config_name = input("Configuration name to test: ").strip()
                config = self.smtp_manager.get_config(config_name)
                
                if not config:
                    print("Configuration not found!")
                    continue
                
                print(f"\nTesting configuration: {config_name}")
                print(f"Server: {config['server']}:{config['port']}")
                
                username = input("Username/Email: ").strip()
                password = input("Password: ").strip()
                
                print("\nTesting connection...")
                result = self.smtp_manager.test_connection(config_name, {
                    'username': username,
                    'password': password
                })
                
                if result['success']:
                    print("✓ Connection successful!")
                else:
                    print(f"✗ Connection failed: {result['message']}")
            
            elif choice == "4":
                config_name = input("Configuration name to delete: ").strip()
                config = self.smtp_manager.get_config(config_name)
                
                if config:
                    confirm = input(f"Delete configuration '{config_name}'? (y/n): ").strip().lower()
                    if confirm == 'y':
                        if self.smtp_manager.delete_config(config_name):
                            print("✓ Configuration deleted!")
                        else:
                            print("✗ Error deleting configuration!")
                else:
                    print("Configuration not found!")
            
            elif choice == "5":
                break
    
    def schedule_menu(self):
        """Schedule management menu"""
        print("\n" + "="*50)
        print("SCHEDULE MANAGEMENT")
        print("="*50)
        
        print("\nScheduling feature coming soon!")
        print("Check back in the next update.")
    
    def view_reports_menu(self):
        """View reports menu"""
        print("\n" + "="*50)
        print("REPORTS")
        print("="*50)
        
        reports_dir = Path("reports")
        
        # Check each report type
        report_types = {
            'JSON': list(reports_dir.glob("json/*.json")),
            'CSV': list(reports_dir.glob("csv/*.csv")),
            'PDF': list(reports_dir.glob("pdf/*.pdf")),
            'HTML': list(reports_dir.glob("html/*.html"))
        }
        
        total_reports = sum(len(reports) for reports in report_types.values())
        
        if total_reports == 0:
            print("\nNo reports found!")
            print("Run a campaign first to generate reports.")
            return
        
        print(f"\nTotal reports: {total_reports}")
        for report_type, reports in report_types.items():
            if reports:
                latest = max(reports, key=lambda x: x.stat().st_mtime)
                mod_time = datetime.fromtimestamp(latest.stat().st_mtime)
                print(f"\n{report_type}: {len(reports)} reports")
                print(f"  Latest: {latest.name}")
                print(f"  Modified: {mod_time.strftime('%Y-%m-%d %H:%M')}")
        
        print("\nReports are stored in:")
        print("  reports/json/ - JSON format")
        print("  reports/csv/  - CSV format")
        print("  reports/pdf/  - PDF format (if generated)")
        print("  reports/html/ - HTML format (if generated)")

def main():
    """Main entry point"""
    # Create necessary directories
    Path("config").mkdir(exist_ok=True)
    Path("templates").mkdir(exist_ok=True)
    Path("target_lists").mkdir(exist_ok=True)
    Path("reports/json").mkdir(exist_ok=True, parents=True)
    Path("reports/csv").mkdir(exist_ok=True, parents=True)
    Path("reports/pdf").mkdir(exist_ok=True, parents=True)
    Path("reports/html").mkdir(exist_ok=True, parents=True)
    Path("logs").mkdir(exist_ok=True)
    
    # Initialize ESAT
    esat = ESAT()
    
    # Show banner
    esat.show_banner()
    
    # Show disclaimer
    if not esat.disclaimer():
        print("\nDisclaimer not accepted. Exiting.")
        return
    
    # Run main menu
    esat.main_menu()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting ESAT. Goodbye!")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
