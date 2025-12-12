## First-Time Setup

1. **Run the initial data collection script**:
python garmin_training_load.py
- You'll be prompted to enter your Garmin Connect credentials
- The script will also ask for heart rate parameters for TRIMP calculation

2. **Create a user account**:
python create_user.py
- Enter an email and password for accessing the dashboard
- This is separate from your Garmin credentials and used only for local login

## Running the Application

1. **Start the server**:
python app.py

2. **Access the dashboard**:
- Open a web browser and navigate to: `http://localhost:5001`
- From other devices on your network: `http://your-computer-ip:5001`
- Log in with the user credentials you created

## Updating Your Data

To fetch new activities from Garmin Connect:
python garmin_training_load.py

Run this periodically to keep your dashboard updated with your latest activities.

## Local Network Access
192.168.1.239:5001 or fit.local:5001

## Understanding the Metrics

### External Load (Miles)
The combined distance in miles plus an elevation load factor (elevation gain in feet / 1000)

### Internal Load (TRIMP)
Training Impulse calculated using Banister's formula based on heart rate data

### Acute:Chronic Workload Ratio (ACWR)
The ratio between your 7-day average load and 28-day average load. Values between 0.8-1.3 are considered optimal. Values above 1.3 indicate increased injury risk.

### Normalized Divergence
Shows the relationship between external and internal ACWR:
- Negative values: Internal stress (TRIMP) is higher than external load, suggesting potential overtraining
- Near zero: Balanced training
- Positive values: Efficient adaptation, external work exceeds internal stress

## Project Structure

- `app.py`: Main Flask application
- `garmin_training_load.py`: Script for fetching and processing Garmin data
- `auth.py`: Authentication system
- `db_utils.py`: Database utilities
- `frontend/`: React dashboard application
- `data/`: Database and configuration files
- `templates/`: HTML templates for login


## Acknowledgments

- [garminconnect](https://github.com/cyberjunky/python-garminconnect) for the Garmin Connect API
- [Recharts](https://recharts.org/) for chart visualizations