# 📸 Insta No Crop

**Insta No Crop** is a production-ready web application that resizes images for Instagram **without cropping**, adds a blurred background, and provides a **Remini-style face enhancement feature** — all running efficiently on a CPU-only server.

This project demonstrates **real-world backend engineering, image processing, Dockerization, CI/CD automation, and production deployment**.

---

## 🚀 Live Demo
👉 https://instanocrop.duckdns.org  

---

## 🧩 Problem Statement

Instagram enforces strict aspect ratios. When users upload:
- Portrait images
- Images with different dimensions  

Important parts (especially faces) often get cropped or lose clarity.

Most existing solutions:
- Are paid
- Require heavy AI/GPU resources
- Are not self-hosted or developer-friendly

---

## ✅ Solution

**Insta No Crop** solves this by:
- Preserving the full image
- Automatically generating a blurred background
- Centering the original image
- Enhancing facial clarity with a Remini-like effect
- Running fast on a standard EC2 CPU instance

---

## 🧱 Architecture Overview


User (Browser)
↓
Nginx (Reverse Proxy + HTTPS)
↓
FastAPI Backend (Image Processing)
↓
Docker Containers
↓
AWS EC2 (Production Server)


### Benefits
- Fast deployments (seconds)
- Zero unnecessary rebuilds
- Secure SSH agent-based authentication
- No service interruption

---

## ⚡ Performance & Optimization

- Selective face enhancement (not whole image)
- Minimal memory usage
- Fast response time on EC2
- Automated Docker cleanup
- Backend-only rebuilds during deploy

---

## 🔐 Security Practices

- HTTPS enforced
- SSH key-based authentication
- GitHub Secrets for credentials
- No secrets hard-coded
- Production-safe Nginx config

---

## 📈 Future Improvements

- Batch image upload with ZIP download
- Before/After image comparison
- Image compression slider
- HD upscaling option
- Usage analytics
- Rate limiting
- Health-check based deployments
- Zero-downtime blue-green deploy

---

## 🧠 What This Project Demonstrates

- Real-world problem solving
- Backend & frontend integration
- Image processing fundamentals
- Docker & CI/CD expertise
- Production debugging skills
- DevOps-oriented thinking

---

## 📄 Resume-Ready Description

> Built a production-ready web application using FastAPI, OpenCV, and Docker to resize images for Instagram without cropping. Implemented Remini-style face enhancement using face detection and selective image processing. Deployed on AWS EC2 with Nginx, HTTPS (Let’s Encrypt), and a GitHub Actions CI/CD pipeline for fast, secure auto-deployments.

---

## 👤 Author

**Arpit Dixit**  
DevOps & Backend Enthusiast  

---

⭐ If you like this project, give it a star!
