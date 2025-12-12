# Account Creation Email Template

## Subject: Welcome to Your Training Monkey - Get Started in 2 Minutes

---

**Hi [Name],**

Welcome to Your Training Monkey! We're excited to help you prevent injuries and train smarter with our patent-pending training load divergence analysis.

## How to Create Your Account

Creating your account is quick and easy - it takes just 2 minutes:

### Step 1: Visit Our Landing Page
Go to: **https://yourtrainingmonkey.com/landing**

### Step 2: Connect Your Strava Account
- Click the **"Connect with Strava"** button
- You'll be redirected to Strava to authorize the connection
- Click **"Authorize"** to grant access to your training data

### Step 3: Automatic Account Creation
- Your Training Monkey account is created automatically
- You're logged in immediately - no password needed!
- Your account email will be: `strava_[your-athlete-id]@training-monkey.com`

### Step 4: Set Your Goals (Optional)
- Choose your training goals and preferences
- This helps us provide personalized recommendations

### Step 5: Start Training Smarter
- View your training dashboard
- Get AI-powered recommendations
- See your divergence analysis (requires 14+ days of training data)

## What Makes Us Different

Unlike other platforms that only show distance and pace, Your Training Monkey reveals the **hidden physiological stress** that leads to injury:

- **Divergence Analysis**: See when your body and training are out of sync
- **Injury Prevention**: Spot dangerous trends weeks before they become problems
- **Built for Trail Runners**: Includes vertical gain in our calculations
- **AI Recommendations**: Get daily guidance on training decisions

## Data Requirements

For the most accurate analysis, we need:
- **Minimum**: 14 days of training data
- **Optimal**: 28+ days of training data
- **Activities**: Running, cycling, and other endurance activities

## Security & Privacy

- Your Strava data is encrypted and stored securely
- We only access the data you authorize
- Your account is protected with industry-standard security
- You can revoke access anytime through Strava

## Need Help?

If you have any questions or run into issues:

- **Email**: support@yourtrainingmonkey.com
- **Documentation**: https://yourtrainingmonkey.com/getting-started
- **FAQ**: Check our getting started page for common questions

## Ready to Get Started?

Click here to create your account: **https://yourtrainingmonkey.com/landing**

We're here to help you train smarter and avoid injuries. Welcome to the Your Training Monkey community!

---

**Best regards,**
The Your Training Monkey Team

---

*P.S. - Your Training Monkey is currently in beta. We'd love your feedback as we continue to improve the platform!*

---

## Email Variations

### Short Version (for social media/quick shares)

**Subject: Train Smarter with Your Training Monkey**

Hi [Name],

Ready to prevent injuries and train smarter? Your Training Monkey uses patent-pending divergence analysis to show you when your body and training are out of sync.

**Get started in 2 minutes:**
1. Go to: https://yourtrainingmonkey.com/landing
2. Click "Connect with Strava"
3. Authorize the connection
4. Start training smarter!

No password needed - your account is created automatically.

[Your Name]

### Technical Version (for developers/technical users)

**Subject: Your Training Monkey - OAuth Account Creation Process**

Hi [Name],

Your Training Monkey uses a streamlined OAuth integration with Strava for account creation. Here's how it works:

**Account Creation Process:**
1. User visits `/landing` and clicks "Connect with Strava"
2. OAuth flow redirects to Strava for authorization
3. Upon successful OAuth, system automatically:
   - Creates account with email: `strava_{athlete_id}@training-monkey.com`
   - Generates secure 16-character password
   - Logs user in automatically
   - Redirects to welcome page

**Technical Details:**
- Uses Strava OAuth 2.0 with `read,activity:read_all` scope
- Account detection by Strava athlete ID
- Automatic token refresh mechanism
- PostgreSQL database with encrypted storage

**Getting Started:**
Visit: https://yourtrainingmonkey.com/landing

Let me know if you need any technical details or have questions about the implementation.

[Your Name]

### Support Version (for existing users having issues)

**Subject: Having Trouble Creating Your Account? We're Here to Help

Hi [Name],

We noticed you might be having trouble creating your Your Training Monkey account. Don't worry - we're here to help!

**Common Issues & Solutions:**

**Issue**: "I can't find the Connect with Strava button
**Solution**: Make sure you're on the landing page: https://yourtrainingmonkey.com/landing

**Issue**: "Strava authorization failed"
**Solution**: Try clearing your browser cache and cookies, then try again

**Issue**: "I'm not getting redirected after Strava"
**Solution**: Check that your browser allows pop-ups and redirects

**Issue**: "I already have a Strava account but it's not working"
**Solution**: The system will either log you into your existing account or create a new one

**Still Having Issues?**
- Email us: support@yourtrainingmonkey.com
- Include your Strava athlete ID (found in your Strava profile URL)
- Let us know what step you're stuck on

**Alternative: Manual Account Creation**
If OAuth continues to fail, we can create your account manually. Just email us with:
- Your preferred email address
- Your Strava athlete ID
- Confirmation that you want to connect your Strava account

We're committed to getting you set up and training smarter!

**The Your Training Monkey Team**

---

## Usage Notes

- Replace `[Name]` with the recipient's name
- Customize the tone based on your audience
- Include your actual support email address
- Update URLs if using a different domain
- Consider A/B testing different subject lines
- Personalize based on how the user was referred (social media, friend, etc.)
