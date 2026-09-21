# 💬 Chat App

A full-featured real-time chat application with text, emoji, photos, videos, voice messages, and camera recording.

## ✨ Features

### 💬 Core Chat
- User registration and login
- Multiple chat rooms
- Real-time message polling (3-second refresh)
- Message history
- Online users indicator
- Delete your own messages

### 😊 Rich Messaging
- **Emoji picker** (56 emojis)
- **Photo uploads** (inline display with lightbox)
- **Video uploads** (inline player)
- **Voice messages** (record with mic)
- **Camera recording** (record video with device camera)
- **Any file type** (PDF, docs, ZIPs, etc.)

### 🔔 Notifications
- Sound alerts on new messages (Web Audio API)
- Floating banner (top-right)
- Tab title flashing (when on another tab)
- Browser notifications (OS-level popups)

### 🎨 Design
- Beautiful gradient UI
- User avatars with initials
- Chat bubbles (like WhatsApp/Telegram)
- Fully responsive (mobile + tablet + desktop)
- Smooth animations

## 🛠️ Technologies Used

- **Backend:** Flask (Python)
- **Database:** SQLite with SQLAlchemy
- **Authentication:** Flask-Bcrypt, Sessions
- **File uploads:** Werkzeug secure_filename
- **Frontend:** Bootstrap 5, Font Awesome, Plus Jakarta Sans
- **Media APIs:** MediaRecorder, getUserMedia (browser native)
- **Deployment:** Render

## 🚀 Live Demo

🔗 [View Live App](https://chat-app-1-3s6i.onrender.com) *(update after deployment)*

## ⚠️ Free Tier Note

This app is deployed on Render's free tier, which uses ephemeral storage:
- Uploaded files reset on every redeploy
- Database (users, rooms, messages) resets on restart
- Perfect for demo/portfolio purposes

**For production:** Use PostgreSQL + Cloudinary/S3 for persistence.

## 🏁 Getting Started

### Prerequisites
- Python 3.8+
- pip
- Modern browser (Chrome/Edge/Firefox for camera/mic)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/guyodika6891-lgtm/chat_app.git
   cd chat_app
