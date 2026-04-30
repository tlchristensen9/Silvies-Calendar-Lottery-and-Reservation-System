# Hunting Club Reservation System

A professional PyQt5 application for managing cabin reservations during the May-July hunting season using a fair lottery system.

## Features

- **21 Member Management**: Complete member database with contact information
- **Fair Lottery System**: Random selection with no priority system
- **7-Day Reservation Periods**: Friday to Thursday weekly periods
- **5-Day Confirmation Window**: Winners have 5 days to confirm reservations
- **Visual Calendar Interface**: Color-coded period display
- **Comprehensive Statistics**: Member participation and fairness tracking
- **Data Persistence**: JSON-based storage with backup capabilities
- **Professional UI**: Outdoor hunting theme with intuitive navigation

## System Requirements

- Python 3.8 or higher
- PyQt5
- Operating System: Windows, macOS, or Linux

## Installation

1. **Clone or download the project files**
2. **Install Python dependencies**:
   ```bash
   pip install PyQt5
   ```
3. **Create the project directory structure**:
   ```
   hunting_club_app/
   ├── main.py
   ├── models/
   │   ├── __init__.py
   │   ├── member.py
   │   ├── reservation.py
   │   └── lottery.py
   ├── views/
   │   ├── __init__.py
   │   ├── main_window.py
   │   ├── calendar_widget.py
   │   └── dialogs.py
   ├── controllers/
   │   ├── __init__.py
   │   ├── app_controller.py
   │   └── lottery_controller.py
   ├── utils/
   │   ├── __init__.py
   │   ├── data_manager.py
   │   └── constants.py
   └── data/
       ├── members.json
       ├── reservations.json
       └── lottery_history.json
   ```

## Quick Start

1. **Run the application**:
   ```bash
   python main.py
   ```

2. **Select a member** from the dropdown in the left panel

3. **View the calendar** to see available periods (green), reserved periods (brown), and periods in lottery (amber)

4. **Create a lottery**:
   - Click "Create New Lottery" button
   - Select an available period
   - Choose participants
   - Run the draw

5. **Confirm reservations**:
   - Click on periods with "Pending Confirmation" status
   - Confirm within 5 days or the period expires

## Usage Guide

### Member Management
- All 21 club members are pre-loaded
- Select any member to view the system from their perspective
- All users have admin rights

### Reservation System
- **Season**: May through July (approximately 13 weeks)
- **Periods**: 7-day periods from Friday to Thursday
- **Rule**: One reservation per member per season
- **Availability**: All periods start as available

### Lottery Process
1. **Admin adds members** to a lottery for a specific period
2. **Members select** their preferred week (one per lottery)
3. **System randomly selects** winner
4. **Winner has 5 days** to confirm reservation
5. **Confirmed periods** are reserved; unconfirmed periods return to available pool

### Visual Indicators
- **Green**: Available periods
- **Brown**: Reserved periods
- **Amber**: Periods currently in lottery
- **Orange**: Periods pending confirmation
- **Red**: Expired confirmation periods

### Statistics & Reports
- View member participation rates
- Track lottery fairness
- Export data for external analysis
- Generate comprehensive reports

## File Structure

### Core Application Files
- `main.py` - Application entry point
- `models/` - Data models (Member, Reservation, Lottery)
- `views/` - User interface components
- `controllers/` - Business logic controllers
- `utils/` - Utility modules and constants

### Data Files
- `data/members.json` - Member information
- `data/reservations.json` - Reservation periods and status
- `data/lottery_history.json` - Complete lottery history

## Configuration

### Season Configuration
Edit `utils/constants.py` to modify:
- Season months (default: May, June, July)
- Confirmation period (default: 5 days)
- Number of members (default: 21)
- UI colors and styling

### Member Management
Members are defined in `utils/constants.py` in the `DEFAULT_MEMBERS` list. Modify this list to change member information.

## Features in Detail

### Fair Lottery System
- **Random Selection**: Uses Python's random module for fair draws
- **No Priority**: All participants have equal chances
- **Transparency**: Complete lottery history tracking
- **Fairness Monitoring**: Statistics show participation distribution

### Data Management
- **JSON Storage**: Human-readable data format
- **Automatic Backups**: System creates backups before major operations
- **Data Validation**: Integrity checks on startup and operations
- **Export Capabilities**: Export data for external analysis

### User Interface
- **Professional Design**: Hunting/outdoor themed colors
- **Responsive Layout**: Adapts to different screen sizes
- **Intuitive Navigation**: Clear visual hierarchy and controls
- **Comprehensive Tooltips**: Hover information for all elements

## Troubleshooting

### Common Issues

1. **Application won't start**:
   - Ensure Python 3.8+ is installed
   - Verify PyQt5 installation: `pip show PyQt5`
   - Check file permissions in the application directory

2. **Data not loading**:
   - Ensure `data/` directory exists
   - Check file permissions for JSON files
   - Review log files for specific errors

3. **Lottery draw issues**:
   - Verify period is available
   - Ensure participants are valid members
   - Check for conflicting reservations

### Log Files
The application creates a log file `hunting_club.log` in the application directory. Check this file for detailed error information.

### Data Recovery
If data files become corrupted:
1. Check the `data/backup_*` directories for recent backups
2. Restore from the most recent valid backup
3. If no backups exist, delete the JSON files and restart the application to regenerate default data

## Development

### Code Structure
The application follows the Model-View-Controller (MVC) pattern:
- **Models**: Data structures and business logic
- **Views**: User interface components
- **Controllers**: Coordinate between models and views

### Adding Features
1. **New Models**: Add to `models/` directory
2. **UI Components**: Add to `views/` directory
3. **Business Logic**: Add to `controllers/` directory
4. **Configuration**: Update `utils/constants.py`

### Testing
The application includes basic validation and error handling. For production use, consider adding:
- Unit tests for core functionality
- Integration tests for UI components
- Data validation tests

## License

This project is provided as-is for the hunting club's internal use. Modify and distribute as needed for your organization.

## Support

For technical issues or feature requests, refer to the application logs and source code documentation. The codebase is well-documented with comprehensive docstrings and comments.

## Version History

- **v1.0.0** - Initial release with core lottery and reservation functionality

## Acknowledgments

Built with Python and PyQt5 for a fair and transparent hunting club reservation system.