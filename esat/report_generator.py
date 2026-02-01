"""
Report Generator
Creates detailed reports and analytics for email campaigns
"""

import json
import csv
import pandas as pd
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from jinja2 import Template
import logging

class ReportGenerator:
    def __init__(self, reports_dir="reports"):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Create subdirectories
        (self.reports_dir / "json").mkdir(exist_ok=True)
        (self.reports_dir / "csv").mkdir(exist_ok=True)
        (self.reports_dir / "pdf").mkdir(exist_ok=True)
        (self.reports_dir / "html").mkdir(exist_ok=True)
    
    def generate_report(self, campaign_data, output_format="all"):
        """Generate campaign report in specified format(s)"""
        campaign_id = campaign_data.get('campaign_id', 
                                      f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"{campaign_id}_{timestamp}"
        
        report = self._prepare_report_data(campaign_data)
        
        formats = [output_format] if output_format != "all" else ["json", "csv", "pdf", "html"]
        
        generated_files = []
        
        for fmt in formats:
            try:
                if fmt == "json":
                    filename = self._generate_json_report(report, base_filename)
                elif fmt == "csv":
                    filename = self._generate_csv_report(report, base_filename)
                elif fmt == "pdf":
                    filename = self._generate_pdf_report(report, base_filename)
                elif fmt == "html":
                    filename = self._generate_html_report(report, base_filename)
                else:
                    continue
                
                if filename:
                    generated_files.append(filename)
                    
            except Exception as e:
                self.logger.error(f"Error generating {fmt} report: {e}")
        
        return {
            "success": len(generated_files) > 0,
            "files": generated_files,
            "report_data": report
        }
    
    def _prepare_report_data(self, campaign_data):
        """Prepare and enrich report data"""
        report = campaign_data.copy()
        
        # Calculate additional metrics
        if 'stats' in report:
            stats = report['stats']
            
            # Calculate success rate
            total = stats.get('sent', 0) + stats.get('failed', 0)
            if total > 0:
                stats['success_rate'] = (stats.get('sent', 0) / total) * 100
            
            # Calculate duration
            if 'start_time' in stats and 'end_time' in stats:
                start = datetime.fromisoformat(stats['start_time'])
                end = datetime.fromisoformat(stats['end_time'])
                duration = (end - start).total_seconds()
                stats['duration_seconds'] = duration
                stats['duration_formatted'] = str(end - start)
                
                # Calculate average rate
                if duration > 0:
                    stats['avg_rate_sec'] = stats.get('sent', 0) / duration
                    stats['avg_rate_min'] = stats.get('sent', 0) / (duration / 60)
        
        # Add timestamp
        report['report_generated'] = datetime.now().isoformat()
        
        return report
    
    def _generate_json_report(self, report_data, base_filename):
        """Generate JSON report"""
        filename = self.reports_dir / "json" / f"{base_filename}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            self.logger.info(f"JSON report saved: {filename}")
            return str(filename)
            
        except Exception as e:
            self.logger.error(f"Error saving JSON report: {e}")
            return None
    
    def _generate_csv_report(self, report_data, base_filename):
        """Generate CSV report"""
        filename = self.reports_dir / "csv" / f"{base_filename}.csv"
        
        try:
            # Flatten report data for CSV
            flat_data = self._flatten_dict(report_data)
            
            # Write CSV
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write headers
                writer.writerow(['Metric', 'Value'])
                
                # Write data
                for key, value in flat_data.items():
                    writer.writerow([key, str(value)])
            
            self.logger.info(f"CSV report saved: {filename}")
            return str(filename)
            
        except Exception as e:
            self.logger.error(f"Error saving CSV report: {e}")
            return None
    
    def _flatten_dict(self, d, parent_key='', sep='.'):
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _generate_pdf_report(self, report_data, base_filename):
        """Generate PDF report with charts"""
        filename = self.reports_dir / "pdf" / f"{base_filename}.pdf"
        
        try:
            with PdfPages(filename) as pdf:
                # Create figures
                self._create_summary_page(report_data, pdf)
                
                if 'stats' in report_data:
                    self._create_statistics_charts(report_data['stats'], pdf)
                
                if 'targets' in report_data:
                    self._create_targets_page(report_data, pdf)
                
                # Add metadata
                pdf.infodict()['Title'] = f"Campaign Report: {report_data.get('campaign_name', 'Unknown')}"
                pdf.infodict()['Author'] = 'Email Security Assessment Tool'
                pdf.infodict()['Subject'] = 'Campaign Analysis Report'
                pdf.infodict()['Keywords'] = 'security,email,campaign,report'
                pdf.infodict()['CreationDate'] = datetime.now()
            
            self.logger.info(f"PDF report saved: {filename}")
            return str(filename)
            
        except Exception as e:
            self.logger.error(f"Error generating PDF report: {e}")
            return None
    
    def _create_summary_page(self, report_data, pdf):
        """Create summary page for PDF"""
        fig, ax = plt.subplots(figsize=(11, 8))
        fig.patch.set_visible(False)
        ax.axis('tight')
        ax.axis('off')
        
        # Summary table
        summary_data = [
            ["Campaign Name:", report_data.get('campaign_name', 'N/A')],
            ["Campaign ID:", report_data.get('campaign_id', 'N/A')],
            ["Start Time:", report_data.get('stats', {}).get('start_time', 'N/A')],
            ["End Time:", report_data.get('stats', {}).get('end_time', 'N/A')],
            ["Duration:", report_data.get('stats', {}).get('duration_formatted', 'N/A')],
            ["Total Sent:", str(report_data.get('stats', {}).get('sent', 0))],
            ["Total Failed:", str(report_data.get('stats', {}).get('failed', 0))],
            ["Success Rate:", f"{report_data.get('stats', {}).get('success_rate', 0):.1f}%"],
            ["Target Count:", str(len(report_data.get('targets', [])))],
            ["Report Generated:", report_data.get('report_generated', 'N/A')]
        ]
        
        table = ax.table(cellText=summary_data, 
                        colWidths=[0.3, 0.7],
                        cellLoc='left',
                        loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)
        
        plt.title(f"Campaign Summary: {report_data.get('campaign_name', 'Unknown')}", 
                 fontsize=16, fontweight='bold')
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _create_statistics_charts(self, stats, pdf):
        """Create statistics charts for PDF"""
        # Success vs Failed chart
        if stats.get('sent', 0) > 0 or stats.get('failed', 0) > 0:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            labels = ['Successful', 'Failed']
            values = [stats.get('sent', 0), stats.get('failed', 0)]
            colors = ['#4CAF50', '#F44336']
            
            ax.bar(labels, values, color=colors)
            ax.set_ylabel('Count')
            ax.set_title('Email Delivery Results')
            
            # Add value labels on bars
            for i, v in enumerate(values):
                ax.text(i, v + max(values)*0.01, str(v), ha='center')
            
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
    
    def _create_targets_page(self, report_data, pdf):
        """Create targets page for PDF"""
        fig, ax = plt.subplots(figsize=(11, 8))
        fig.patch.set_visible(False)
        ax.axis('tight')
        ax.axis('off')
        
        targets = report_data.get('targets', [])
        if len(targets) > 50:
            targets_display = targets[:50] + [f"... and {len(targets) - 50} more"]
        else:
            targets_display = targets
        
        # Create target table
        target_data = [[f"Target {i+1}:", target] for i, target in enumerate(targets_display)]
        
        if target_data:
            table = ax.table(cellText=target_data,
                           colWidths=[0.2, 0.8],
                           cellLoc='left',
                           loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.2, 0.5)
        
        plt.title(f"Target List ({len(targets)} total)", fontsize=14, fontweight='bold')
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _generate_html_report(self, report_data, base_filename):
        """Generate HTML report"""
        filename = self.reports_dir / "html" / f"{base_filename}.html"
        
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Campaign Report: {{ campaign_name }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }
                h1 { color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }
                h2 { color: #555; margin-top: 30px; }
                .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }
                .summary-card { background: #f9f9f9; padding: 20px; border-radius: 8px; border-left: 5px solid #4CAF50; }
                .stat-highlight { font-size: 2em; font-weight: bold; color: #4CAF50; }
                .targets-list { max-height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
                .success { color: #4CAF50; }
                .failed { color: #F44336; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
                tr:hover { background-color: #f5f5f5; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Campaign Report: {{ campaign_name }}</h1>
                
                <div class="summary-grid">
                    <div class="summary-card">
                        <h3>Campaign ID</h3>
                        <p>{{ campaign_id }}</p>
                    </div>
                    <div class="summary-card">
                        <h3>Duration</h3>
                        <p>{{ stats.duration_formatted }}</p>
                    </div>
                    <div class="summary-card">
                        <h3>Total Emails</h3>
                        <p class="stat-highlight">{{ stats.sent|int + stats.failed|int }}</p>
                    </div>
                    <div class="summary-card">
                        <h3>Success Rate</h3>
                        <p class="stat-highlight success">{{ "%.1f"|format(stats.success_rate) }}%</p>
                    </div>
                </div>
                
                <h2>📈 Detailed Statistics</h2>
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Emails Sent Successfully</td>
                        <td class="success">{{ stats.sent|int }}</td>
                    </tr>
                    <tr>
                        <td>Emails Failed</td>
                        <td class="failed">{{ stats.failed|int }}</td>
                    </tr>
                    <tr>
                        <td>Average Rate (per minute)</td>
                        <td>{{ "%.2f"|format(stats.avg_rate_min) }}</td>
                    </tr>
                    <tr>
                        <td>Start Time</td>
                        <td>{{ stats.start_time }}</td>
                    </tr>
                    <tr>
                        <td>End Time</td>
                        <td>{{ stats.end_time }}</td>
                    </tr>
                </table>
                
                <h2>🎯 Targets ({{ targets|length }} total)</h2>
                <div class="targets-list">
                    {% for target in targets[:100] %}
                    <div>{{ loop.index }}. {{ target }}</div>
                    {% endfor %}
                    {% if targets|length > 100 %}
                    <div>... and {{ targets|length - 100 }} more</div>
                    {% endif %}
                </div>
                
                <h2>⚙️ Configuration</h2>
                <table>
                    <tr>
                        <th>Setting</th>
                        <th>Value</th>
                    </tr>
                    {% for key, value in config.items() %}
                    <tr>
                        <td>{{ key }}</td>
                        <td>{{ value }}</td>
                    </tr>
                    {% endfor %}
                </table>
                
                <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #777; font-size: 0.9em;">
                    <p>Report generated: {{ report_generated }}</p>
                    <p>Tool: Email Security Assessment Tool</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            template = Template(html_template)
            html_content = template.render(**report_data)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"HTML report saved: {filename}")
            return str(filename)
            
        except Exception as e:
            self.logger.error(f"Error generating HTML report: {e}")
            return None
    
    def generate_comparison_report(self, campaign_reports, output_format="pdf"):
        """Generate comparison report for multiple campaigns"""
        if len(campaign_reports) < 2:
            raise ValueError("Need at least 2 campaigns for comparison")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.reports_dir / f"comparison_{timestamp}.{output_format}"
        
        # Prepare comparison data
        comparison_data = []
        for report in campaign_reports:
            stats = report.get('stats', {})
            comparison_data.append({
                'campaign_name': report.get('campaign_name', 'Unknown'),
                'campaign_id': report.get('campaign_id', 'N/A'),
                'sent': stats.get('sent', 0),
                'failed': stats.get('failed', 0),
                'success_rate': stats.get('success_rate', 0),
                'duration': stats.get('duration_seconds', 0),
                'avg_rate_min': stats.get('avg_rate_min', 0),
                'target_count': len(report.get('targets', []))
            })
        
        # Generate comparison report
        if output_format == "csv":
            return self._generate_comparison_csv(comparison_data, filename)
        elif output_format == "pdf":
            return self._generate_comparison_pdf(comparison_data, filename)
        else:
            raise ValueError(f"Unsupported format: {output_format}")
    
    def _generate_comparison_csv(self, comparison_data, filename):
        """Generate CSV comparison report"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=comparison_data[0].keys())
                writer.writeheader()
                writer.writerows(comparison_data)
            
            return str(filename)
        except Exception as e:
            self.logger.error(f"Error generating comparison CSV: {e}")
            return None
    
    def _generate_comparison_pdf(self, comparison_data, filename):
        """Generate PDF comparison report"""
        try:
            with PdfPages(filename) as pdf:
                fig, ax = plt.subplots(figsize=(12, 8))
                
                # Extract data
                campaigns = [d['campaign_name'] for d in comparison_data]
                sent = [d['sent'] for d in comparison_data]
                failed = [d['failed'] for d in comparison_data]
                
                # Create grouped bar chart
                x = np.arange(len(campaigns))
                width = 0.35
                
                ax.bar(x - width/2, sent, width, label='Sent', color='#4CAF50')
                ax.bar(x + width/2, failed, width, label='Failed', color='#F44336')
                
                ax.set_xlabel('Campaign')
                ax.set_ylabel('Count')
                ax.set_title('Campaign Comparison: Sent vs Failed')
                ax.set_xticks(x)
                ax.set_xticklabels(campaigns, rotation=45, ha='right')
                ax.legend()
                
                plt.tight_layout()
                pdf.savefig(fig, bbox_inches='tight')
                plt.close()
            
            return str(filename)
        except Exception as e:
            self.logger.error(f"Error generating comparison PDF: {e}")
            return None
