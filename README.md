# ESAT - Email Security Assessment Tool (email flood town)

![ek0ms Banner](https://img.shields.io/badge/ek0ms-certified_ethcial_hacker-blue)


**ESAT** is a professional email security testing tool designed for **really cool ethical hackers** and security professionals to test and validate email security controls, spam filters, and user awareness training.

> ** IMPORTANT LEGAL NOTICE:** This tool is for **AUTHORIZED SECURITY TESTING ONLY**. You **MUST** have explicit written permission to test any email system.

##  What Does ESAT Do?

ESAT allows security teams to:
- **Test email security controls** (spam filters, rate limiting, content filtering)
- **Conduct phishing simulation exercises** for security awareness training
- **Stress test email servers** with various sending patterns
- **Validate incident response** to email-based attacks
- **Generate detailed reports** for compliance and analysis

##  Features

- **Quick Campaign** - Simple one-target, one-template testing
- **Advanced Campaign** - Multi-target, multi-template with variable timing patterns
- **Multiple SMTP configurations** (Gmail, Outlook, Yahoo, custom)
- **Template management system** with variables and categories
- **Rate limiting controls** to avoid overwhelming systems
- **Multiple sending patterns** (constant, random, increasing, decreasing)
- **Batch sending** for organized campaigns
- **Detailed reporting** (JSON, CSV, PDF, HTML formats)
- **Campaign scheduling** (coming soon)

##  Installation

### Step-by-Step Installation

# 1. Clone the repository
```bash
git clone https://github.com/ekomsSavior/ESAT.git
cd ESAT
```

# 2. Install Python dependencies
```bash
pip3 install schedule pytz python-dateutil matplotlib jinja2 pandas --break-system-packages
```
do a venv if you dont like running --break-system-packages

# 3. Run the tool
```bash
python3 esat.py
```


##  Setting Up SMTP Accounts

###  Gmail Setup (App Password Required)
Gmail requires an **App Password** instead of your regular password:

1. **Enable 2-Step Verification:**
   - Go to https://myaccount.google.com/
   - Click "Security" → "2-Step Verification" → Enable it

2. **Generate App Password:**
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" as app
   - Select "Other" as device, name it "ESAT"
   - Click "Generate"
   - Copy the **16-character password** (looks like: `xxxx xxxx xxxx xxxx`)

3. **Use in ESAT:**
   - Username: Your full Gmail address (e.g., `yourname@gmail.com`)
   - Password: The 16-character app password (**remove spaces**)

###  Other Email Providers
- **Outlook/Hotmail:** Similar process - generate app password from account security
- **Custom SMTP:** Use your organization's SMTP server
- **Transactional Services:** SendGrid, Mailgun, etc. work great

##  Creating Realistic Email Templates

### Default Templates Included
ESAT comes with 3 default templates:
1. **Security Awareness Test** - For training exercises
2. **Password Reset Required** - Urgent-style emails
3. **Meeting Invitation** - Business-style emails

### Editing Templates
From the main menu, select **"3. Manage Templates"**:

1. **View existing templates** - See what's available
2. **Create new templates** - Design your own
3. **Edit templates** - Modify existing ones

### Making Emails Believable
Use these tips for realistic templates:

```plaintext
# Example variables you can use in templates:
{name} - Target's name (from email address)
{email} - Target's full email
{date} - Current date
{count} - Email number in sequence
{total} - Total emails in campaign

# Realistic elements to include:
• Company logos/branding
• Personalization ("Hi {name},")
• Legitimate-looking links (use your own test domains)
• Professional signatures
• Realistic sender addresses
```

### Advanced Template Variables
Create templates with dynamic content:
```plaintext
Subject: Urgent: Action Required for {name}

Body:
Dear {name},

Our records show your account ({email}) requires immediate attention.

Please review by {date}.

Best regards,
Security Team
Company Name
```

##  Using Custom Files and Lists

### Target Email Lists
ESAT can read target lists from files:

1. **Create a text file** with one email per line:
   ```txt
   user1@example.com
   user2@example.com
   user3@example.com
   admin@example.com
   ```

2. **Save it** in the `target_lists/` directory

3. **Use in campaigns:**
   - When prompted for targets, enter the file path:
   ```
   Target emails (comma-separated or file path): target_lists/my_targets.txt
   ```

### Template Files
You can also create template JSON files:

1. **Export templates** from the tool
2. **Edit the JSON file** with your custom templates
3. **Import** or place in `templates/` directory

##  How to Use ESAT

### Quick Start: Simple Test
```bash
# Run the tool
python3 esat.py

# Accept the disclaimer
# Select "1. Quick Campaign"
# Follow the prompts:
#   - Enter target email
#   - Select SMTP config (Gmail recommended)
#   - Enter your app password
#   - Set number of emails and delay
#   - Choose template
#   - Confirm and run!
```

### Advanced Campaign Example
```bash
# For more sophisticated testing:
1. Select "2. Advanced Campaign"
2. Enter multiple targets (comma-separated or file)
3. Choose multiple templates for rotation
4. Select delay pattern:
   - Random: 0.5-3 seconds (unpredictable)
   - Increasing: Start fast, get slower
   - Decreasing: Start slow, get faster
   - Constant: Steady pace
5. Enable batch sending for organized campaigns
```

### Managing Configurations
```bash
# Add new SMTP configurations:
1. Select "4. Manage SMTP Configs"
2. Choose "2. Create configuration"
3. Enter server details:
   - Name: YourConfigName
   - Server: smtp.yourserver.com
   - Port: 587 (or 465 for SSL)
   - Encryption: starttls (recommended)
   - Auth type: login
```

##  Reports and Analytics

After each campaign, ESAT generates detailed reports in:
- **JSON** (`reports/json/`) - Machine-readable data
- **CSV** (`reports/csv/`) - Spreadsheet-friendly
- **PDF** (`reports/pdf/`) - Printable reports
- **HTML** (`reports/html/`) - Web-viewable format

**Report includes:**
- Campaign statistics (sent/failed/success rate)
- Timing information
- Target lists
- Configuration used
- Pattern analysis

##  Pro Tips

### For Effective Security Testing
1. **Start small** - Test with 1-2 emails first
2. **Use realistic templates** - More effective for training
3. **Vary sending patterns** - Test different attack vectors
4. **Document everything** - Essential for compliance
5. **Review reports** - Analyze what got through filters

### Template Design Tips
- Use your organization's real email templates as base
- Include both obvious and subtle phishing indicators
- Test various subject lines and content types
- Rotate between different template categories

### Performance Optimization
- Use local SMTP server for development/testing
- Create target lists in advance
- Save frequently used configurations
- Use batch sending for large campaigns

---
##  Disclaimer

**ESAT IS FOR AUTHORIZED SECURITY TESTING ONLY.**

The developer assumes **NO liability** and is **NOT responsible** for any misuse or damage caused by this tool. 


**Happy (and responsible) testing!** 🚀
