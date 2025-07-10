# EcoTrackBin 🌱

### An End-to-End Smart Recycling Solution with Personalization and Real-Time Monitoring

[![Demo Video](https://img.shields.io/badge/Demo-Video-red?style=for-the-badge&logo=youtube)](https://youtu.be/JYBZmQIwdjY)
[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-blue?style=for-the-badge&logo=github)](https://github.com/medex256/BinDesignWebApp)

---

## 🌍 Project Overview

EcoTrackBin is an innovative IoT-based smart recycling system designed to revolutionize waste management and promote sustainable recycling habits. Our solution combines cutting-edge hardware with an intuitive web application to create a seamless, gamified recycling experience.

### 🎯 Key Features

- **🤖 Smart Hardware Integration**: ESP32-based bins with automated lid control and trash counting
- **📱 Interactive Web Application**: User-friendly interface for session management and progress tracking
- **🎮 Gamification Elements**: Leaderboards, user rankings, and achievement tracking
- **📊 Real-Time Analytics**: Live monitoring dashboard with comprehensive statistics
- **🔍 AI-Powered Classification**: Intelligent waste categorization system
- **📍 Bin Finder**: Location-based bin discovery feature
- **👥 Community Building**: Social features to encourage collective recycling efforts

---

## 🎥 Demo Video

Watch our complete system demonstration showcasing all features:

[![EcoTrackBin Demo](https://img.youtube.com/vi/JYBZmQIwdjY/0.jpg)](https://youtu.be/JYBZmQIwdjY)

**Video Link**: https://youtu.be/JYBZmQIwdjY

---

## 🏗️ System Architecture

### Hardware Components

- **ESP32 Microcontroller**: Central processing unit
- **Ultrasonic Sensor**: Distance measurement for trash counting
- **Servo Motor**: Automated lid control mechanism
- **OLED Display**: Real-time user information display
- **E-Paper Display**: QR code generation for bin identification

### Software Stack

- **Backend**: Python Flask with SQLAlchemy ORM
- **Frontend**: Responsive HTML/CSS with JavaScript
- **Mobile App**: MIT App Inventor integration
- **Database**: SQLite for data persistence
- **Cloud Hosting**: Google Cloud Platform
- **AI Integration**: Hugging Face Transformers for waste classification

### System Flow

```
User → QR Code Scan → Session Start → Waste Disposal →
Trash Counting → Session End → Data Sync → Leaderboard Update
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Flask framework
- ESP32 development environment
- MIT App Inventor (for mobile app)

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/medex256/BinDesignWebApp
   cd BinDesignWebApp
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Database Setup**

   ```bash
   python app.py
   ```

4. **Run the Application**

   ```bash
   flask run
   ```

5. **Access the Web Interface**
   - Open your browser and navigate to `http://localhost:5000`

### Hardware Setup

1. **ESP32 Configuration**

   - Connect ultrasonic sensor to designated GPIO pins
   - Attach servo motor for lid control
   - Set up OLED and E-Paper displays
   - Configure WiFi credentials

2. **Sensor Calibration**
   - Calibrate ultrasonic sensor for accurate distance measurement
   - Test servo motor functionality
   - Verify display outputs

---

## 📦 Dependencies

Our project uses the following Python packages:

```python
Flask==3.0.3
Flask-SQLAlchemy==3.0.3
Flask-Bcrypt==1.0.1
Flask-WTF==1.0.1
WTForms==3.0.1
Flask-Login==0.6.2
pyplot==5.24.1
pytz==2024.2
```

---

## 📱 Features in Detail

### 🎮 Gamification System

- **Leaderboards**: Real-time ranking based on recycling activity
- **User Tiers**: Progressive achievement levels
- **Heatmap Visualization**: GitHub-style activity tracking
- **Progress Tracking**: Personal recycling statistics

### 🔧 Admin Dashboard

- **User Management**: Create, update, and manage user accounts
- **Bin Management**: Add, modify, and monitor recycling bins
- **Analytics**: Comprehensive usage statistics and insights

### 🤖 AI Integration

- **Waste Classification**: Automated material type detection
- **Smart Recommendations**: Personalized recycling suggestions
- **Pattern Analysis**: Usage behavior insights

---

## 📂 Project Structure

```
BinDesignWebApp/
├── app.py                 # Main Flask application backend
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── templates/            # Frontend HTML pages
│   ├── index.html
│   ├── dashboard.html
│   ├── leaderboard.html
│   └── ...
├── static/               # CSS, JS, and image files
│   ├── css/
│   ├── js/
│   └── images/
├── hardware/             # ESP32 Arduino code
└── mobile/               # MIT App Inventor files
```

---

## 📊 Technical Specifications

| Component | Technology            | Purpose                     |
| --------- | --------------------- | --------------------------- |
| Backend   | Flask + SQLAlchemy    | API and database management |
| Frontend  | HTML/CSS/JavaScript   | User interface              |
| Mobile    | MIT App Inventor      | Mobile application          |
| Hardware  | ESP32                 | IoT device control          |
| Database  | SQLite                | Data persistence            |
| AI        | Hugging Face          | Waste classification        |
| Cloud     | Google Cloud Platform | Hosting and deployment      |

---

## 🌟 Project Impact

### Environmental Benefits

- Reduced landfill waste through improved recycling habits
- Increased recycling participation rates
- Data-driven waste management optimization

### Social Impact

- Community engagement through gamification
- Educational value in recycling awareness
- Scalable solution for urban waste management

---

## 👥 Team Members

- **Kaiyrkhan Madi** - Hardware Development & System Integration
- **Fernandez Lance Saquilabon** - Full-Stack Development & UI/UX
- **Wong Wing Yui** - Backend Development & Database Management
- **Tse Tak Sum** - AI Integration & Mobile Development

---

## 📈 Future Enhancements

- **IoT Network Expansion**: City-wide bin network integration
- **Advanced Analytics**: Machine learning for waste prediction
- **Mobile App Enhancement**: Native iOS/Android applications
- **Reward System**: Partnership with local businesses for incentives

---

## 🔧 Development Notes

### Backend (`app.py`)

The main Flask application contains all backend logic including:

- User authentication and session management
- Database models and relationships
- API endpoints for ESP32 communication
- Admin dashboard functionality

### Frontend (`templates/`)

All HTML templates are located in the templates directory, featuring:

- Responsive design for mobile and desktop
- Interactive dashboards and visualizations
- User-friendly interface components

---

## 📄 License

This project is part of the EE3070 course at City University of Hong Kong.

---

## 🤝 Contributing

We welcome contributions to improve EcoTrackBin! Please feel free to:

- Report bugs and issues
- Suggest new features
- Submit pull requests
- Provide feedback on our demo

---

## 📞 Contact

For questions, feedback, or collaboration opportunities, please reach out through our GitHub repository or demo video comments.

**Project Repository**: https://github.com/medex256/BinDesignWebApp

---

<div align="center">
  <strong>Making Recycling Smart, Simple, and Social 🌱</strong>
</div>
