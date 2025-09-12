# 🔍 Molaison Research Agent

> AI-powered research and web crawling agent for the Molaison Executive Assistant Suite

## 📋 Overview

The Molaison Research Agent is a Flask-based web service that provides autonomous web research and data extraction capabilities. It's part of the comprehensive Molaison Executive Assistant ecosystem.

## ✨ Features

- **Web Research**: Autonomous web content analysis and extraction
- **Data Processing**: Intelligent content parsing and structure analysis
- **RESTful API**: Clean HTTP endpoints for integration
- **Real-time Status**: Health monitoring and diagnostics
- **Scalable Architecture**: Built for production deployment

## 🚀 Deployment

This agent is designed for Railway deployment with automatic configuration.

### Railway Deployment
1. Connect this repository to Railway
2. Railway will automatically detect the `Procfile`
3. Dependencies are installed from `requirements.txt`
4. The service starts on the assigned PORT

### Local Development
```bash
pip install -r requirements.txt
python crawler_agent.py
```

## 🔗 API Endpoints

- **`/`** - Main interface with web dashboard
- **`/status`** - Health check and agent information
- **`/test`** - URL analysis testing endpoint

## 🏗️ Architecture

```
┌─────────────────┐
│   Web Interface │
├─────────────────┤
│   Flask App     │
├─────────────────┤
│   Core Engine   │ 
├─────────────────┤
│   Data Export   │
└─────────────────┘
```

## 📦 Dependencies

- **Flask 3.0.0** - Web framework
- **Requests 2.31.0** - HTTP client
- **BeautifulSoup4 4.12.2** - HTML parsing
- **Rich 13.7.0** - Terminal formatting

## 🔧 Configuration

The agent automatically configures itself for Railway deployment:
- Uses `PORT` environment variable
- Serves on all interfaces (`0.0.0.0`)
- Production-ready error handling

## 🤖 Part of Molaison Suite

This agent works alongside:
- **Email Management Agent** - Email processing and organization
- **Memory & Context Agent** - Persistent data storage
- **Social Media Agent** - Social media automation
- **Voice Command Router** - Voice interface integration

## 📊 Status

- **Status**: ✅ Production Ready
- **Deployment**: Railway Compatible
- **Integration**: Molaison Suite Compatible

## 🔗 Related Services

- **Main Email Agent**: https://molaison-executive-assistant-production.up.railway.app
- **Memory Agent**: Coming Soon
- **Social Agent**: Coming Soon

---

**Built with ❤️ for the Molaison Executive Assistant Suite**