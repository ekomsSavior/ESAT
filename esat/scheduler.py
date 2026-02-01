"""
Campaign Scheduler
Manages scheduled email campaigns
"""

import schedule
import time
import threading
from datetime import datetime, timedelta
import json
from pathlib import Path
import logging
from enum import Enum
import pytz
from dateutil import parser as date_parser

class ScheduleStatus(Enum):
    """Schedule status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class CampaignScheduler:
    def __init__(self, storage_dir="schedules"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        self.schedules_file = self.storage_dir / "scheduled_campaigns.json"
        self.running = False
        self.scheduler_thread = None
        self.active_schedules = {}
        self.scheduled_campaigns = []
        
        self.logger = self._setup_logging()
        self._load_schedules()
    
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _load_schedules(self):
        """Load scheduled campaigns from storage"""
        if self.schedules_file.exists():
            try:
                with open(self.schedules_file, 'r') as f:
                    data = json.load(f)
                    self.scheduled_campaigns = data.get('campaigns', [])
                    
                    # Filter out completed/cancelled campaigns older than 7 days
                    cutoff = datetime.now() - timedelta(days=7)
                    self.scheduled_campaigns = [
                        s for s in self.scheduled_campaigns
                        if s.get('status') not in [ScheduleStatus.COMPLETED.value, 
                                                  ScheduleStatus.CANCELLED.value]
                        or datetime.fromisoformat(s.get('created', cutoff.isoformat())) > cutoff
                    ]
                    
                    self.logger.info(f"Loaded {len(self.scheduled_campaigns)} scheduled campaigns")
            except Exception as e:
                self.logger.error(f"Error loading schedules: {e}")
                self.scheduled_campaigns = []
    
    def _save_schedules(self):
        """Save scheduled campaigns to storage"""
        try:
            data = {
                'campaigns': self.scheduled_campaigns,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.schedules_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving schedules: {e}")
    
    def create_schedule(self, campaign_config, schedule_config):
        """
        Create a new scheduled campaign
        
        Args:
            campaign_config: Campaign configuration
            schedule_config: Schedule configuration with:
                - type: 'once', 'interval', 'daily', 'weekly', 'cron'
                - time: For 'once' - datetime string
                       For 'interval' - {'seconds', 'minutes', 'hours'}
                       For 'daily' - time string 'HH:MM'
                       For 'weekly' - {'day': 'monday', 'time': 'HH:MM'}
                       For 'cron' - cron expression
                - timezone: Timezone string (optional)
                - end_after: Number of repetitions (optional)
                - end_at: End datetime string (optional)
        
        Returns:
            str: Schedule ID
        """
        from uuid import uuid4
        
        schedule_id = str(uuid4())
        
        schedule_entry = {
            'id': schedule_id,
            'campaign_config': campaign_config,
            'schedule_config': schedule_config,
            'status': ScheduleStatus.PENDING.value,
            'created': datetime.now().isoformat(),
            'next_run': None,
            'last_run': None,
            'run_count': 0,
            'error_count': 0,
            'results': []
        }
        
        # Calculate next run time
        self._calculate_next_run(schedule_entry)
        
        self.scheduled_campaigns.append(schedule_entry)
        self._save_schedules()
        
        self.logger.info(f"Created schedule {schedule_id} for campaign '{campaign_config.get('campaign_name')}'")
        return schedule_id
    
    def _calculate_next_run(self, schedule_entry):
        """Calculate next run time for a schedule"""
        config = schedule_entry['schedule_config']
        schedule_type = config.get('type', 'once')
        timezone_str = config.get('timezone', 'UTC')
        
        try:
            tz = pytz.timezone(timezone_str)
        except:
            tz = pytz.UTC
        
        now = datetime.now(tz)
        
        if schedule_type == 'once':
            run_time = date_parser.parse(config['time'])
            if run_time.tzinfo is None:
                run_time = tz.localize(run_time)
            schedule_entry['next_run'] = run_time.isoformat()
            
        elif schedule_type == 'interval':
            interval = config['time']
            if 'seconds' in interval:
                next_run = now + timedelta(seconds=interval['seconds'])
            elif 'minutes' in interval:
                next_run = now + timedelta(minutes=interval['minutes'])
            elif 'hours' in interval:
                next_run = now + timedelta(hours=interval['hours'])
            else:
                next_run = now + timedelta(minutes=5)
            schedule_entry['next_run'] = next_run.isoformat()
            
        elif schedule_type == 'daily':
            run_time_str = config.get('time', '09:00')
            run_time = datetime.strptime(run_time_str, '%H:%M').time()
            next_run = tz.localize(
                datetime.combine(now.date(), run_time)
            )
            
            # If time already passed today, schedule for tomorrow
            if next_run < now:
                next_run += timedelta(days=1)
            
            schedule_entry['next_run'] = next_run.isoformat()
            
        elif schedule_type == 'weekly':
            day_str = config.get('day', 'monday').lower()
            time_str = config.get('time', '09:00')
            
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 
                   'friday', 'saturday', 'sunday']
            
            if day_str not in days:
                day_str = 'monday'
            
            target_day = days.index(day_str)
            current_day = now.weekday()
            
            run_time = datetime.strptime(time_str, '%H:%M').time()
            next_run = tz.localize(
                datetime.combine(now.date(), run_time)
            )
            
            # Calculate days to add
            days_ahead = target_day - current_day
            if days_ahead <= 0:  # Target day already passed this week
                days_ahead += 7
            
            next_run += timedelta(days=days_ahead)
            schedule_entry['next_run'] = next_run.isoformat()
            
        elif schedule_type == 'cron':
            # Simplified cron-like scheduling
            # Format: "minute hour day month day_of_week"
            cron_parts = config.get('time', '0 9 * * *').split()
            if len(cron_parts) != 5:
                cron_parts = ['0', '9', '*', '*', '*']
            
            # For now, use simple daily at specified hour/minute
            if cron_parts[0] != '*' and cron_parts[1] != '*':
                minute = int(cron_parts[0]) if cron_parts[0] != '*' else 0
                hour = int(cron_parts[1]) if cron_parts[1] != '*' else 9
                
                run_time = datetime.strptime(f"{hour:02d}:{minute:02d}", '%H:%M').time()
                next_run = tz.localize(
                    datetime.combine(now.date(), run_time)
                )
                
                # If time already passed today, schedule for tomorrow
                if next_run < now:
                    next_run += timedelta(days=1)
                
                schedule_entry['next_run'] = next_run.isoformat()
        
        # Check if schedule should end
        self._check_schedule_end(schedule_entry)
    
    def _check_schedule_end(self, schedule_entry):
        """Check if schedule should end based on end conditions"""
        config = schedule_entry['schedule_config']
        
        # Check end_after condition
        if 'end_after' in config:
            if schedule_entry['run_count'] >= config['end_after']:
                schedule_entry['status'] = ScheduleStatus.COMPLETED.value
                schedule_entry['next_run'] = None
        
        # Check end_at condition
        if 'end_at' in config:
            try:
                end_time = date_parser.parse(config['end_at'])
                now = datetime.now(end_time.tzinfo if end_time.tzinfo else pytz.UTC)
                
                if now >= end_time:
                    schedule_entry['status'] = ScheduleStatus.COMPLETED.value
                    schedule_entry['next_run'] = None
            except:
                pass
    
    def get_schedule(self, schedule_id):
        """Get schedule by ID"""
        for schedule in self.scheduled_campaigns:
            if schedule['id'] == schedule_id:
                return schedule
        return None
    
    def update_schedule(self, schedule_id, updates):
        """Update schedule configuration"""
        for i, schedule in enumerate(self.scheduled_campaigns):
            if schedule['id'] == schedule_id:
                self.scheduled_campaigns[i].update(updates)
                self._save_schedules()
                return True
        return False
    
    def delete_schedule(self, schedule_id):
        """Delete a schedule"""
        self.scheduled_campaigns = [
            s for s in self.scheduled_campaigns 
            if s['id'] != schedule_id
        ]
        self._save_schedules()
        return True
    
    def list_schedules(self, status_filter=None):
        """List all schedules, optionally filtered by status"""
        if status_filter:
            return [
                s for s in self.scheduled_campaigns
                if s['status'] == status_filter.value
            ]
        return self.scheduled_campaigns.copy()
    
    def start(self, campaign_executor_callback):
        """
        Start the scheduler
        
        Args:
            campaign_executor_callback: Function to execute campaigns
                                        Should accept campaign_config and return results
        """
        if self.running:
            self.logger.warning("Scheduler already running")
            return
        
        self.running = True
        self.campaign_executor = campaign_executor_callback
        
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True
        )
        self.scheduler_thread.start()
        
        self.logger.info("Scheduler started")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                self._check_schedules()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)
    
    def _check_schedules(self):
        """Check and execute due schedules"""
        now = datetime.now(pytz.UTC)
        
        for schedule in self.scheduled_campaigns:
            if schedule['status'] != ScheduleStatus.PENDING.value:
                continue
            
            if not schedule['next_run']:
                continue
            
            try:
                next_run = date_parser.parse(schedule['next_run'])
                if next_run.tzinfo is None:
                    next_run = pytz.UTC.localize(next_run)
                
                if now >= next_run:
                    self._execute_schedule(schedule)
                    
            except Exception as e:
                self.logger.error(f"Error checking schedule {schedule['id']}: {e}")
    
    def _execute_schedule(self, schedule):
        """Execute a scheduled campaign"""
        schedule_id = schedule['id']
        campaign_name = schedule['campaign_config'].get('campaign_name', 'Unknown')
        
        self.logger.info(f"Executing scheduled campaign: {campaign_name} ({schedule_id})")
        
        # Update schedule status
        schedule['status'] = ScheduleStatus.RUNNING.value
        schedule['last_run'] = datetime.now().isoformat()
        self._save_schedules()
        
        try:
            # Execute campaign
            if self.campaign_executor:
                results = self.campaign_executor(schedule['campaign_config'])
                
                # Record results
                schedule['results'].append({
                    'timestamp': datetime.now().isoformat(),
                    'results': results
                })
                schedule['run_count'] += 1
                
                # Update status based on results
                if results.get('success', False):
                    schedule['status'] = ScheduleStatus.COMPLETED.value
                    schedule['next_run'] = None
                    self.logger.info(f"Campaign {campaign_name} completed successfully")
                else:
                    schedule['status'] = ScheduleStatus.FAILED.value
                    schedule['error_count'] += 1
                    self.logger.error(f"Campaign {campaign_name} failed")
            
            else:
                raise ValueError("No campaign executor configured")
                
        except Exception as e:
            schedule['status'] = ScheduleStatus.FAILED.value
            schedule['error_count'] += 1
            self.logger.error(f"Error executing schedule {schedule_id}: {e}")
            
            # Record error
            schedule['results'].append({
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            })
        
        # Recalculate next run if needed
        if schedule['status'] == ScheduleStatus.FAILED.value:
            # For failed schedules, retry after 1 hour
            retry_time = datetime.now(pytz.UTC) + timedelta(hours=1)
            schedule['next_run'] = retry_time.isoformat()
            schedule['status'] = ScheduleStatus.PENDING.value
        
        elif schedule['status'] == ScheduleStatus.RUNNING.value:
            # For recurring schedules, calculate next run
            schedule_type = schedule['schedule_config'].get('type')
            if schedule_type in ['interval', 'daily', 'weekly', 'cron']:
                schedule['status'] = ScheduleStatus.PENDING.value
                self._calculate_next_run(schedule)
            else:
                schedule['status'] = ScheduleStatus.COMPLETED.value
                schedule['next_run'] = None
        
        self._save_schedules()
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        self.logger.info("Scheduler stopped")
    
    def pause_schedule(self, schedule_id):
        """Pause a schedule"""
        schedule = self.get_schedule(schedule_id)
        if schedule and schedule['status'] == ScheduleStatus.PENDING.value:
            schedule['status'] = ScheduleStatus.CANCELLED.value
            self._save_schedules()
            return True
        return False
    
    def resume_schedule(self, schedule_id):
        """Resume a paused schedule"""
        schedule = self.get_schedule(schedule_id)
        if schedule and schedule['status'] == ScheduleStatus.CANCELLED.value:
            schedule['status'] = ScheduleStatus.PENDING.value
            self._calculate_next_run(schedule)
            self._save_schedules()
            return True
        return False
    
    def execute_now(self, schedule_id):
        """Execute a schedule immediately"""
        schedule = self.get_schedule(schedule_id)
        if schedule:
            # Create a thread to execute immediately
            thread = threading.Thread(
                target=self._execute_schedule,
                args=(schedule,)
            )
            thread.start()
            return True
        return False
    
    def get_upcoming_schedules(self, hours_ahead=24):
        """Get schedules due in the next specified hours"""
        now = datetime.now(pytz.UTC)
        cutoff = now + timedelta(hours=hours_ahead)
        
        upcoming = []
        
        for schedule in self.scheduled_campaigns:
            if schedule['status'] != ScheduleStatus.PENDING.value:
                continue
            
            if not schedule['next_run']:
                continue
            
            try:
                next_run = date_parser.parse(schedule['next_run'])
                if next_run.tzinfo is None:
                    next_run = pytz.UTC.localize(next_run)
                
                if now <= next_run <= cutoff:
                    upcoming.append(schedule)
                    
            except:
                pass
        
        # Sort by next_run time
        upcoming.sort(key=lambda x: date_parser.parse(x['next_run']))
        return upcoming

# CLI interface for scheduler management
class SchedulerCLI:
    """Command-line interface for scheduler management"""
    
    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.commands = {
            'list': self.list_schedules,
            'create': self.create_schedule,
            'delete': self.delete_schedule,
            'pause': self.pause_schedule,
            'resume': self.resume_schedule,
            'execute': self.execute_now,
            'upcoming': self.show_upcoming,
            'status': self.show_status,
            'help': self.show_help
        }
    
    def run_interactive(self):
        """Run interactive CLI"""
        print("\n" + "="*50)
        print("Campaign Scheduler Management")
        print("="*50)
        
        while True:
            print("\nCommands: list, create, delete, pause, resume, execute, upcoming, status, help, quit")
            command = input("\nScheduler> ").strip().lower()
            
            if command == 'quit':
                break
            
            if command in self.commands:
                self.commands[command]()
            else:
                print(f"Unknown command: {command}")
    
    def list_schedules(self):
        """List all schedules"""
        schedules = self.scheduler.list_schedules()
        
        if not schedules:
            print("No scheduled campaigns.")
            return
        
        print(f"\n{'ID':<36} {'Campaign Name':<30} {'Status':<12} {'Next Run':<25}")
        print("-" * 110)
        
        for schedule in schedules:
            schedule_id = schedule['id'][:8] + "..."
            campaign_name = schedule['campaign_config'].get('campaign_name', 'Unknown')[:28]
            status = schedule['status']
            next_run = schedule.get('next_run', 'N/A')
            
            if next_run != 'N/A':
                try:
                    next_run_dt = date_parser.parse(next_run)
                    next_run = next_run_dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            print(f"{schedule_id:<36} {campaign_name:<30} {status:<12} {next_run:<25}")
    
    def create_schedule(self):
        """Create a new scheduled campaign"""
        print("\nCreate New Scheduled Campaign")
        print("-" * 30)
        
        # Get campaign configuration
        campaign_config = {}
        campaign_config['campaign_name'] = input("Campaign Name: ").strip()
        campaign_config['smtp_server'] = input("SMTP Server: ").strip()
        campaign_config['sender_email'] = input("Sender Email: ").strip()
        campaign_config['sender_password'] = input("Sender Password: ").strip()
        
        targets = input("Target Emails (comma-separated): ").strip()
        campaign_config['targets'] = [t.strip() for t in targets.split(',')]
        
        campaign_config['rate_limit'] = float(input("Rate Limit (emails/second): ").strip() or "1")
        
        # Get schedule configuration
        schedule_config = {}
        
        print("\nSchedule Type:")
        print("1. Once (run at specific time)")
        print("2. Interval (run every X seconds/minutes/hours)")
        print("3. Daily (run at specific time each day)")
        print("4. Weekly (run on specific day/time each week)")
        print("5. Cron (advanced schedule)")
        
        type_choice = input("Choice (1-5): ").strip()
        
        type_map = {
            '1': 'once',
            '2': 'interval',
            '3': 'daily',
            '4': 'weekly',
            '5': 'cron'
        }
        
        schedule_config['type'] = type_map.get(type_choice, 'once')
        
        if schedule_config['type'] == 'once':
            run_time = input("Run Date/Time (YYYY-MM-DD HH:MM): ").strip()
            schedule_config['time'] = run_time
            
        elif schedule_config['type'] == 'interval':
            unit = input("Unit (seconds/minutes/hours): ").strip().lower()
            value = int(input(f"Every how many {unit}?: ").strip())
            schedule_config['time'] = {unit: value}
            
        elif schedule_config['type'] == 'daily':
            run_time = input("Run Time (HH:MM): ").strip()
            schedule_config['time'] = run_time
            
        elif schedule_config['type'] == 'weekly':
            day = input("Day of week (monday/tuesday/...): ").strip().lower()
            time = input("Time (HH:MM): ").strip()
            schedule_config['day'] = day
            schedule_config['time'] = time
            
        elif schedule_config['type'] == 'cron':
            cron_expr = input("Cron Expression (min hour day month day_of_week): ").strip()
            schedule_config['time'] = cron_expr
        
        # Optional timezone
        timezone = input("Timezone (optional, default UTC): ").strip()
        if timezone:
            schedule_config['timezone'] = timezone
        
        # Optional end conditions
        end_choice = input("End after X runs? (y/n): ").strip().lower()
        if end_choice == 'y':
            schedule_config['end_after'] = int(input("Number of runs: ").strip())
        
        # Create schedule
        try:
            schedule_id = self.scheduler.create_schedule(campaign_config, schedule_config)
            print(f"\n✓ Schedule created successfully!")
            print(f"Schedule ID: {schedule_id}")
        except Exception as e:
            print(f"\n✗ Error creating schedule: {e}")
    
    def delete_schedule(self):
        """Delete a schedule"""
        schedule_id = input("Schedule ID to delete: ").strip()
        
        if self.scheduler.delete_schedule(schedule_id):
            print("✓ Schedule deleted successfully!")
        else:
            print("✗ Schedule not found.")
    
    def pause_schedule(self):
        """Pause a schedule"""
        schedule_id = input("Schedule ID to pause: ").strip()
        
        if self.scheduler.pause_schedule(schedule_id):
            print("✓ Schedule paused successfully!")
        else:
            print("✗ Schedule not found or cannot be paused.")
    
    def resume_schedule(self):
        """Resume a paused schedule"""
        schedule_id = input("Schedule ID to resume: ").strip()
        
        if self.scheduler.resume_schedule(schedule_id):
            print("✓ Schedule resumed successfully!")
        else:
            print("✗ Schedule not found or cannot be resumed.")
    
    def execute_now(self):
        """Execute a schedule immediately"""
        schedule_id = input("Schedule ID to execute now: ").strip()
        
        if self.scheduler.execute_now(schedule_id):
            print("✓ Schedule execution started!")
        else:
            print("✗ Schedule not found.")
    
    def show_upcoming(self):
        """Show upcoming schedules"""
        hours = input("Hours ahead to show (default 24): ").strip()
        hours = int(hours) if hours else 24
        
        upcoming = self.scheduler.get_upcoming_schedules(hours)
        
        if not upcoming:
            print(f"No scheduled campaigns in the next {hours} hours.")
            return
        
        print(f"\nUpcoming campaigns (next {hours} hours):")
        print("-" * 80)
        
        for schedule in upcoming:
            campaign_name = schedule['campaign_config'].get('campaign_name', 'Unknown')
            next_run = schedule.get('next_run', 'N/A')
            
            if next_run != 'N/A':
                try:
                    next_run_dt = date_parser.parse(next_run)
                    next_run = next_run_dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            print(f"• {campaign_name}: {next_run}")
    
    def show_status(self):
        """Show scheduler status"""
        schedules = self.scheduler.list_schedules()
        
        status_counts = {}
        for schedule in schedules:
            status = schedule['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("\nScheduler Status:")
        print(f"Total schedules: {len(schedules)}")
        print("Status breakdown:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
        
        if self.scheduler.running:
            print("\n✓ Scheduler is running")
        else:
            print("\n✗ Scheduler is not running")
    
    def show_help(self):
        """Show help information"""
        print("\nAvailable Commands:")
        print("  list      - List all scheduled campaigns")
        print("  create    - Create a new scheduled campaign")
        print("  delete    - Delete a schedule")
        print("  pause     - Pause a schedule")
        print("  resume    - Resume a paused schedule")
        print("  execute   - Execute a schedule immediately")
        print("  upcoming  - Show upcoming schedules")
        print("  status    - Show scheduler status")
        print("  help      - Show this help")
        print("  quit      - Exit the scheduler CLI")
